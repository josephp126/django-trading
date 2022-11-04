from .Model import Model
from ...data import Data
from ...config import Config


class Coin(Model):

    column_name = "spot_wallet"

    def __init__(self, _id, name, amount, open_trades):
        super().__init__()
        self.id = _id if _id != None else None
        self.name = name
        self.amount = amount
        self.open_trades = open_trades

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                      GET COIN
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def get(coin_name):
        """
        This function gets single Coin record from database and return query result.
        @params
            - coin_name : str

        @return
            - Coin
        """

        query_dict = {"name": coin_name}
        coin = Model.get(query_dict, "spot_wallet")

        if coin == None:
            return None
        else:
            return Coin.from_json(coin)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   INSERT COIN
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def insert(self):

        """
        This function inserts Coin into the database. If already is inserted, then saves this coin via new changes.
        @params
            - None

        @return
            - Coin
        """

        coin = Coin.get(self.name)

        if coin == None:

            _id = self.spot_wallet.insert_one(self.to_json())
            self.id = str(_id.inserted_id)

        else:
            self.id = coin.id
            coin.amount += self.amount
            self.save()

        return self

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #               GET ALL COINS (SPOT)
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def get_spot():

        """
        This function gets all coins from database. Then , creates instances of these coins and returns.
        @params
            - None

        @return
            - list : (an array which is inside Coins)
        """

        cursor = Coin.get_all()

        spot_list = Coin.from_jsons(cursor)

        spot_dict = {c.name: c for c in spot_list}

        return spot_dict

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #             GENEREATE A JSON FROM COIN
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def to_json(self):
        return {
            "name": self.name,
            "amount": self.amount,
            "open_trades": self.open_trades,
        }

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                  GENERATE A PAIR
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def generate_pair(self, parity):
        """
        This function generate coin/parity conjugate. Example : BTC -> USDT :  BTCUSDT
        @params
            - parity : str

        @return
            - parity conjugate : str
        """
        return self.name + parity

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                CALCULATE WALLET SUM
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    def wallet_sum(func=None, *args):

        if func != None:
            func(*args)

        sow = 0

        for cn in Data.spot:

            coin = Data.spot[cn]

            if cn != Config.BRIDGE:

                pair = cn + Config.BRIDGE

                df = Data.poc[pair]

            if cn == Config.BRIDGE:

                sow += coin.amount

            elif df.empty is not True:

                price = df["close"][-1]

                sow += coin.amount * price

        Data.sow = sow

        return sow
