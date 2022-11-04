from binance.client import Client
from ..data.config import Config
from ..data.data import Data


import traceback


class Binance_API_Manager:
    def __init__(self):

        logger = Data.logger["server"]

        while True:

            try:

                self.client = Client(
                    Config.API["API_KEY"], Config.API["API_SECRET_KEY"]
                )

            except Exception:

                exc = traceback.format_exc()

                logger.error(exc)

                continue

            finally:
                break