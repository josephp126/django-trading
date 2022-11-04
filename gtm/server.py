from .data.config import Config as C
from .api.binance_api_manager import Binance_API_Manager
from .data.database.database_manager import DatabaseManager
from .trader.auto_trader import AutoTrader
from .data.data import Data
from gtm_notify.notify.logger import Logger
from gtm_notify.notify.notify import Notify


class Server:
    def __init__(self):
        pass
    
    def start(self):
        C.read_config()

        Data.logger["server"] = Logger("server")
        Data.logger["database"] = Logger("database")
        Data.logger["trade"] = Logger("trade")

        Data.nh = Notify(C.INSTAGRAM["USERNAME"], C.INSTAGRAM["PASSWORD"])

        Data.bm = Binance_API_Manager()
        Data.db = DatabaseManager()

        trader = AutoTrader()

        Data.logger["server"].info("Server Started")

        trader.start()
