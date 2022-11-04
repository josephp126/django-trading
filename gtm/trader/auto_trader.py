from ..api.api import Api
from ..strategies.stream_strategy import StreamStrategy
from .explore import Explore
from pandas.core.common import SettingWithCopyWarning
from .auto_test_trader import AutoTestTrader
from ..data.database.model.Trade import Trade
from ..data.database.model.Coin import Coin
from ..data.config import Config
from ..data.data import Data


import traceback
import time
import warnings


import asyncio as aio


class AutoTrader:
    def __init__(self):
        self.strategy = StreamStrategy(limit=20)
        self.logger = Data.logger["server"]
        self.bm = Data.bm
        self.test_trader = AutoTestTrader(self.strategy)
        self._init_spot()

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                START AUTO TRADER
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def start(self):

        warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

        api = Api(self.bm, self.logger)

        explore = Explore(api, self.bm.client, self.logger, self.strategy)

        try:
            aio.run(explore.start(self.bm.client.KLINE_INTERVAL_3MINUTE, self.trade))
        
        except Exception:

            exc = traceback.format_exc()

            self.logger.error(exc)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                       TRADE
    # = = = = = = = = = = = = = = = = = = = = = = = = = =


    @aio.coroutine
    async def trade(self):

        Coin.wallet_sum(time.sleep, 1)

        while True:

            try:

                await aio.sleep(1)

                self.test_trader.trade()

            except KeyboardInterrupt:
                
                raise KeyboardInterrupt

            except Exception:

                exc = traceback.format_exc()

                self.logger.error(exc)

                await aio.sleep(1)


    
    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                INITIALIZE SPOT
    # = = = = = = = = = = = = = = = = = = = = = = = = = = 

    def _init_spot(self):

        """
        This function initialize coins. If coins already inserted to database , it fetcged from them.
        Otherwise,it creates new one and pushs them

        @params
            - None

        @return
            - None
        """

        spot = Coin.get_spot()

        for pair in Config.PAIRS:

            name = pair[: len(pair) - 4]

            if spot.get(name) == None:

                coin = Coin(None, name, 0, [])
                coin.insert()
                spot[coin.name] = coin

        if spot.get(Config.BRIDGE) == None:
            coin = Coin(None, Config.BRIDGE, 1000, [])
            coin.insert()
            spot[coin.name] = coin

        th = Trade.get_all_history()

        Data.spot = spot
        Data.th = th
