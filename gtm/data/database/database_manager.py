from pymongo import MongoClient
from pymongo.errors import *
from ..config import Config
from ..data import Data
import traceback



class DatabaseManager:
    def __init__(self):
        
        logger  = Data.logger["database"]
        
        while True:

            try:
                self.client = MongoClient(Config.DATABASE["URI"])
                self.db = self.client["binance_gtm"]

            except Exception as e:
                # traceback.print_exception(type(e), e, e.__traceback__)
                logger.error(e)
                continue

            break

        pass
