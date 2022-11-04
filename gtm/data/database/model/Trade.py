from .Model import Model
from .Coin import Coin
from ...data import Data
from ...config import Config

import time

pos_fee = 0.99925  # 0.075 fee

pob_fee = 1.00075


class Trade(Model):

    column_name = "trade_history"

    def __init__(
        self,
        _id,
        bridge,
        coin,
        amount,
        buy_price,
        buy_time=None,
        sell_time=None,
        sell_price=None,
        result=None,
        profit=None,
    ):

        super().__init__()
        self.id = _id if _id != None else None
        self.coin = coin
        self.bridge = bridge
        self.amount = amount
        self.buy_price = buy_price

        self.buy_time = buy_time if buy_time != None else time.time()

        self.sell_time = sell_time
        self.sell_price = sell_price
        self.result = result
        self.profit = profit

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                    SELL COIN
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def sell(self, sell_price):

        """
        This function adds sell point attributes to the
        instance and calculate profit of this trade action as a
        result of that
        @params
            - sell_price : int
            - result : int

        @return
            - Trade : self
        """

        self.sell_price = sell_price

        self.result = self.amount * sell_price * pos_fee

        self.sell_time = time.time()

        self.profit = (
            self.calculate_profit(self.buy_price, sell_price)
            if sell_price != None
            else None
        )

        return self

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                  CALCULATE PROFIT
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def calculate_profit(self, buy, sell):
        return ((sell * pos_fee - buy * pob_fee) / buy) * 100

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   INSERT TRADE
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def insert(self):

        """
        This function inserts Trade into the database.
        @params
            - None

        @return
            - Trade : self
        """

        dict_form = self.to_json()

        self.id = self.trade_history.insert_one(dict_form).inserted_id

        return self

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                GET ALL TRADE HISTORY
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def get_all_history(query={}):

        """
        This function gets all trades from database. Then , creates instances of these trades and returns
        @params
            - None

        @return
            - list : (an array which is inside Trades)
        """

        cursor = Trade.get_all(query)

        th_list = Trade.from_jsons(cursor)

        return {str(th.id): th for th in th_list}

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 GET A TRADE HISTORY
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def get():
        """
        This function gets single Trade record from database and return query result.
        @params
            - None

        @return
            - Coin
        """

        query_dict = {}
        coin = Model.get(query_dict, "trade_history")
        return Trade.from_json(coin)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #             GENERATE A JSON FROM TRADE
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def to_json(self):

        return {
            "coin": self.coin,
            "bridge": self.bridge,
            "buy_price": self.buy_price,
            "buy_time": self.buy_time,
            "amount": self.amount,
            "sell_price": self.sell_price,
            "sell_time": self.sell_time,
            "result": self.result,
            "profit": self.profit,
        }

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #          CALCULATE AVAILABLE BRIDGE AMOUNT
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def available_bridge(coin: Coin):

        # calculate all wallet value
        total = Coin.wallet_sum()

        # divide this value by 4
        separated = total / 4

        coin_name = coin.name + Config.BRIDGE

        price = Data.poc[coin_name]["close"][-1]

        # discard already given
        separated -= price * coin.amount

        return (separated / 2) if separated > 20 else separated
