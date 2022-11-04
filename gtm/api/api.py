from .binance_api_manager import Binance_API_Manager
from binance.exceptions import BinanceAPIException
from ..data.database.model.Coin import Coin
from ..data.database.model.Trade import Trade
from ..data.config import Config
from ..data.data import Data
from gtm_notify.notify.logger import Logger


import time


class Api:

    FEE = 99925 / 100000

    def __init__(
        self,
        client: Binance_API_Manager,
        logger: Logger,
    ):
        self.client = client.client
        self.logger = logger

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   GET CANDLES
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def get_candles(
        self,
        symbol: str,
        interval: str,
        limit=100,
    ):
        return self._try(
            self.client.get_klines, symbol=symbol, limit=limit, interval=interval
        )

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   GET PRICE
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _get_price(self, symbol: str, isBuy: bool):

        """
        It returns last price of coin respect from orderbook
        @params
            - symbol : str
            - isBuy : bool

        @return
            - price : int
        """

        obt = self.client.get_orderbook_ticker(symbol=symbol)

        return obt["askPrice"] if isBuy else obt["bidPrice"]

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   ORDER CHECKER
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _order_checker(self, symbol: str, order_id: int):

        """
        It waits until order completed  and return order json

        @params
            - symbol : str
            - order_id : int

        @return
            - order : dict
        """

        while True:
            try:
                order_status = self.client._get_order(symbol=symbol, orderId=order_id)
                return order_status
            except BinanceAPIException as e:

                self.logger.info(e)

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Unexpected error : {e}")
                time.sleep(1)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   TRY X TIMES
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _try(self, func, max_attempts=10, *args, **kwargs):

        """
        It retries any function until arrive attempts count
        @params
            - func : function
            - args
            - kwargs

        @return
            - func
        """

        attempts = 0

        max_attempts = max_attempts or 10

        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)

            except Exception as e:

                self.logger.info(f"Something wrong. Error :{e}")

                if attempts == 0:
                    self.logger.info(e)

                attempts += 1

        return None

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 QUICK LIMIT ORDER
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _quick_limit_order(self, func, symbol: str, coin: Coin):

        """
        It puts an order on the table which given buy an sell function.

        @params
            - func : function (buy & sell)
            - symbol : str
            - coin : Coin

        @return
            - Trade : self
        """

        order = None

        while order is None:

            try:

                price = self._get_price(symbol, False)

                order = func(symbol=str, price=price, quantity=coin.amount)

            except BinanceAPIException as e:
                self.logger.info(e)
                time.sleep(1)

            except Exception as e:
                self.logger.error("Failed to Buy/Sell. Trying Again.")
                time.sleep(1)

        return order

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                     BUY COIN
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def buy(self, coin: Coin):

        """
        BUY COIN
        @params
            - coin : Coin

        @return
            - None
        """

        parity = Data.spot[Config.BRIDGE]

        symbol = coin.generate_pair(parity.name)

        order = self._quick_limit_order(self.client.order_market_buy, symbol, parity)

        if order == None:
            return None

        price = order["price"]

        order_id = order["orderId"]

        state = self._order_checker(symbol, order_id)

        if state == None:
            return None

        amount = (parity.amount / price) * Api.FEE

        trade = Trade(None, parity, coin, amount, price)

        coin.amount = amount

        parity.amount = 0

        self._save_trade_action(trade, coin, parity)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   SELL COIN
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def sell(self, coin: Coin, trade_id: int):

        """
        SELL COIN
        @params
            - coin : Coin
            - trade_id : int

        @return
            - None
        """

        trade = Data.th[trade_id]

        parity = Data.spot[Config.BRIDGE]

        symbol = coin.generate_pair(parity.name)

        order = self._quick_limit_order(self.client.order_market_sell, symbol, coin)

        if order == None:
            return None

        price = order["price"]

        order_id = order["orderId"]

        state = self._order_checker(symbol, order_id)

        if state == None:
            return None

        total = coin.amount * price

        coin.amount = 0

        trade.sell(price)

        parity.amount = total

        self._save_trade_action(trade, coin, parity)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                SAVE TRADE ACTION
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _save_trade_action(self, trade: Trade, coin: Coin, parity: Coin):

        """
        it saves all changes to list of trades and spot
        @params
            - trade : Trade
            - coin : Coin
            - parity : Coin

        @return
            - None
        """

        coin.save()
        trade.save()
        parity.save()

        Data.th[trade.id] = trade
        Data.spot[coin.name] = coin
        Data.spot[Config.BRIDGE] = parity

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 GET ORDER BOOK
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _get_order_book(self, symbol: str, limit=500):

        return self._try(self.client.get_order_book, symbol=symbol, limit=limit)
