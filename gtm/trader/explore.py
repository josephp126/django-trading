from binance.client import Client
from ..data.config import Config
from ..api.api import Api
from ..strategies.analyzers.analyzer_utils import convert_to_dataframe, conv_df
from ..data.data import Data
from gtm_notify.notify.logger import Logger
from .stats import Stats
from ..strategies.helper import tomorrow


from asyncio.exceptions import CancelledError
from datetime import datetime
from websockets.exceptions import ConnectionClosedError

import json
import websockets
import asyncio as aio
import time
import pandas as pd
import traceback


class Explore:

    # pairs_of_candles

    def __init__(self, api: Api, client: Client, logger: Logger, strategy):
        self.client = client
        self.logger = logger
        self.api = api
        self.strategy = strategy

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   GET STREAM DATA
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    async def _get_stream_data(self, fp: str, op: str):

        """
        It fetches candles and depth every second from stream API

        @params :
            - fp (str) : first part of stream subscribing
            - op (str) : operation part (main part)

        @returns :
            - None

        """

        url = "wss://stream.binance.com:9443/ws/"  # steam address

        async with websockets.connect(url + fp) as sock:

            await sock.send(op)

            while True:

                while not sock.open:

                    try:

                        self.logger.info("Websocket is NOT Connected. Reconnecting...")

                        sock = await websockets.connect(url + fp)

                        await sock.send(op)

                        self.logger.info("Websocket is Connected")

                    except:

                        self.logger.info("Unable to reconnect, trying again")
                        time.sleep(1)
                try:

                    async for resp in sock:

                        if resp is not None:

                            if "result" in resp:
                                continue

                            resp = json.loads(resp)

                            if resp.get("e") == "depthUpdate":

                                self._update_depth(resp)

                            elif resp.get("e") == "kline":

                                kline = resp["k"]

                                self._update_candle(kline)

                except KeyboardInterrupt:

                    raise KeyboardInterrupt

                except ConnectionClosedError:
                    self.logger.info("Connection is closed suddenly. Reconnecting...")
                
                except Exception as e:

                    exc = traceback.format_exc()
                    self.logger.error(exc)
                    self.logger.error(e)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #               START MULTPPAIR PROCESS
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    async def start(self, interval: str, func):

        """

        @asyncrhon_func
        This function brings together candles stream with candles analyzer&trader.

        @params
            - interval : str
            - func (trader_func)

        @return
            - None

        """

        fp, lp = self._generate_socket_payload(interval)

        self._get_pairs_candles(interval)

        self._get_pairs_orderbooks()

        loop = aio.get_event_loop()

        future = aio.Future()

        stats = Stats()

        run_time = tomorrow()

        tasks = [
            aio.create_task(func()),
            aio.create_task(self._get_stream_data(fp, lp)),
            aio.create_task(Stats.run_at_and_forever(run_time, stats.daily_stats)),
        ]

        try:
            await aio.gather(*tasks)

        except CancelledError:
            future.set_result("stop")

        except Exception:

            exc = traceback.format_exc()

            self.logger.error(exc)

        finally:

            for task in tasks:
                task.cancel()

            self.logger.info("All Task Concluded.")

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                  GET PAIRS CANDLES
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _get_pairs_candles(self, interval: str):

        """
        It gets current candles of given pairs from api

        @params :
            - interval (str) : fetched candle count

        @returns :
            - None

        """

        candles = {}

        pairs = Config.PAIRS

        for pair in pairs:

            candle = self.api.get_candles(symbol=pair, interval=interval, limit=20)

            if candle == None:
                # if tries get candle for 20 times but couldn't fetched
                pass

            candles[pair] = convert_to_dataframe(candle)

        Data.poc = candles

        self.logger.info("Candles Loaded")

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 GET PAIRS ORDERBOOKS
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _get_pairs_orderbooks(self):

        pairs = Config.PAIRS

        for pair in pairs:

            ob = self.api._get_order_book(pair, limit=1000)

            bids = conv_df(ob["bids"])
            asks = conv_df(ob["asks"])

            ob = {"bids": {"table": bids}, "asks": {"table": asks}}

            Data.pod[pair] = ob

        self.logger.info("Order Books Loaded")

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 UPDATE CANDLES
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _update_candle(self, d: dict):

        """
        It merges pre_candles with last updated candle row (only one).
        @params :
            - d (dict) : updated_candle

        @returns :
            - None

        """

        symbol = d["s"]

        okt = d["t"]

        df = Data.poc[symbol]

        ckt = int(df.iloc[-1, df.columns.get_loc("opentimeStamp")])

        row_values = {
            "opentimeStamp": int(okt),
            "open": float(d["o"]),
            "high": float(d["h"]),
            "low": float(d["l"]),
            "close": float(d["c"]),
            "volume": float(d["v"]),
            "closetimeStamp": float(d["T"]),
            "quote_asset_volume": float(d["q"]),
            "number_of_trades": int(d["n"]),
            "tbb_asset_volume": float(d["V"]),
            "tbq_asset_volume": float(d["Q"]),
            "ignored": float(d["B"]),
        }

        if ckt != okt:
            # new row
            df = df.iloc[1:]
        else:
            # update row
            df = df.iloc[:-1]

        df.loc[len(df.index)] = row_values

        df.index = df.opentimeStamp.apply(
            lambda x: pd.to_datetime(datetime.fromtimestamp(x / 1000).strftime("%c"))
        )

        Data.poc[symbol] = df

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 UPDATE DEPTHS
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _update_depth(self, d: dict):

        """
        It merges new orderbook limits with pre_book.

        @params :
            - d (dict) : update_depth

        @returns :
            - None

        """

        pair = d["s"]
        # check if the latest depth Infos overdate from 10 second
        pre_pod = Data.pod[pair]

        bids1 = pre_pod["bids"]["table"]
        asks1 = pre_pod["asks"]["table"]

        bids2 = conv_df(d["b"])
        asks2 = conv_df(d["a"])

        if bids2.empty:
            bids_new = bids1
        else:

            bids_new = (
                pd.concat([bids1, bids2])
                .drop_duplicates("price", keep="last")
                .sort_values("price")
                .reset_index()
            )

            bids_new.drop("index", axis=1, inplace=True)

        if asks2.empty:
            asks_new = asks1
        else:

            asks_new = (
                pd.concat([asks1, asks2])
                .drop_duplicates("price", keep="last")
                .sort_values("price")
                .reset_index()
            )
            asks_new.drop("index", axis=1, inplace=True)

        bids_new = bids_new[bids_new.quantity != 0].head(500)
        asks_new = asks_new[asks_new.quantity != 0].head(500)

        Data.pod[pair] = {"bids": {"table": bids_new}, "asks": {"table": asks_new}}

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #              GENERATE SOCKET PAYLOAD
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _generate_socket_payload(self, interval):

        km = f"@kline_{interval}"

        dm = "@depth"

        pairs = [p.lower() + km for p in Config.PAIRS]

        depths = [p.lower() + dm for p in Config.PAIRS]

        fp = pairs[0]

        op = pairs[1:] + depths

        lp = json.dumps({"method": "SUBSCRIBE", "params": op, "id": 1})

        return fp, lp