from gtm.data.database.model.Coin import Coin
from ..data.data import Data
from ..strategies.stream_strategy import StreamStrategy
from ..data.config import Config
from ..data.database.model.Trade import Trade


from datetime import datetime
import time

FEE = 99925 / 100000


class AutoTestTrader:
    def __init__(self, strategy: StreamStrategy):
        self.strategy = strategy
        self.logger = Data.logger["trade"]

    
    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                      BUY
    # = = = = = = = = = = = = = = = = = = = = = = = = = = 

    def _buy(self, coin: Coin, price: int, amount: int):

        """
        This function handle buy request.
        Buy functionality is not connected binance api.
        Wallet is fake. Goal is testing these implementations

        @params
            - price (current price of this token) : int
            - time : datetime

        @return
            - None

        """

        a = (amount / price) * FEE

        bridge = Data.spot[Config.BRIDGE]

        buy_time = time.time()

        trade = Trade(None, Config.BRIDGE, coin.name, a, price, buy_time)

        trade.insert()

        trade_id = str(trade.id)

        bridge.amount -= amount
        coin.amount += a

        coin.open_trades.append(trade_id)

        # control updatedModelObject updatesuccess State
        bridge.save()
        coin.save()

        Data.th[trade_id] = trade
        Data.spot[coin.name] = coin
        Data.spot[Config.BRIDGE] = bridge

        Coin.wallet_sum()

        info = (
            "----------------------------------------------------\n"
            f"coin name : {coin.name} , type : BUY\n"
            f"coin amount : {a} , price : {price}, amount : {coin.amount}\n"
            f"Left bridge : {bridge.amount}\n"
            f"BALANCE SUM : {Data.sow}\n"
        )

        self.logger.info(info)

        Data.nh.send_notification(info)


    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                        SELL
    # = = = = = = = = = = = = = = = = = = = = = = = = = = 

    def _sell(self, coin, price: int, amount: int, _id=None):

        """
        This function handle sell request.
        Sell functionality is not connected binance api.
        Wallet is fake. Goal is testing these implementations

        @params
            - price (current price of this token) : int
            - time : datetime

        @return
            - None

        """

        bridge = Data.spot[Config.BRIDGE]

        total = amount * price * FEE

        profit = 0

        if coin.amount == amount:

            # close all position in this coin
            for _id in coin.open_trades:

                th = Data.th[_id]

                th.sell(price)

                profit += th.profit * th.amount

                th.save()

                Data.th[_id] = th

            profit /= len(coin.open_trades)

            coin.open_trades.clear()

        else:

            # close specify position in this coin

            Data.th[_id].sell(price)

            profit = Data.th[_id].profit

            Data.th[_id].save()

            coin.open_trades.remove(_id)

        coin.amount -= amount
        bridge.amount += total

        coin.save()
        bridge.save()

        Data.spot[Config.BRIDGE] = bridge
        Data.spot[coin.name] = coin

        Coin.wallet_sum()

        info = (
            "----------------------------------------------------\n"
            f"coin name : {coin.name} , type : SELL \n"
            f"total : {total} , price : {price}\n"
            f"amount : {amount}, left coin : {coin.amount}\n"
            f"profit : {profit}, BALANCE SUM : {Data.sow}\n"
        )

        self.logger.info(info)

        Data.nh.send_notification(info)


    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 TRADING WITH PAIR 
    # = = = = = = = = = = = = = = = = = = = = = = = = = = 

    def trade(self):

        """
        This function make buy & sell action depend on signal
        which is created from getsignal function.


        Buy Conditions :

        - Signal = BUY & already has bridge

        Sell Conditions :

        - Signal = SELL & already has coin

        - profit of open trade is negative and lower than expected.
          (only close spesific trade amount)

        @params
            - df (includes score column) : Dataframe

        @return
            - None
        """

        # pairs of candles
        poc = Data.poc

        spot = Data.spot

        th = Data.th

        pod = Data.pod

        bridge_amount = spot[Config.BRIDGE].amount

        for pair in poc:

            # dataframe of selected pair
            df = poc[pair]

            if df.empty == True or pod.get(pair) == None:
                continue

            # generate signal value and calculate values of indicators
            df, signal = self.strategy.ch3mGetSignal(df, pair)

            # candle_property = get_candle_property(df)

            price = df["close"].iloc[-1]

            coin_name = pair[: len(pair) - 4]

            coin = spot[coin_name]

            for _id in coin.open_trades:

                open_trade = th[_id]

                bp = open_trade.buy_price

                profit = (price - bp) * 100 / bp

                if profit <= Config.LOSS:

                    amount = open_trade.amount

                    # sell time because loss is higher than expcected
                    total = amount * price

                    if total >= 10:
                        self._sell(coin, price, amount, _id)

            if signal == "BUY" and bridge_amount > 0:

                amount = Trade.available_bridge(coin)

                if amount >= 10:

                    self._buy(coin, price, amount)

            if signal == "SELL" and coin.amount > 0:

                total = coin.amount * price

                if total > 10:

                    self._sell(coin, price, coin.amount)
