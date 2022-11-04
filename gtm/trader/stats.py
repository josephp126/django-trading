from asyncio.tasks import sleep
from gtm.strategies.helper import tomorrow
from ..data.database.model.Trade import Trade
from ..data.data import Data

from gtm_notify.notify.image_conv import ImageConv
import asyncio as aio
from datetime import datetime, timedelta, date
import time

import traceback


class Stats:
    def __init__(self) -> None:
        self.image_conv = ImageConv()
        self.logger = Data.logger["server"]

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                   WAIT UNTIL
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    @staticmethod
    async def wait_until(dt):
        # sleep until specified time

        now = datetime.now()
        return await aio.sleep((dt - now).total_seconds())
    
    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                  RUN AT FOREVER
    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    
    @staticmethod
    async def run_at_and_forever(dt, coro):

        await Stats.wait_until(dt)

        while True:

            try:

                coro()

                dt += timedelta(days=1)

                await Stats.wait_until(dt)

            except KeyboardInterrupt:
                break

            except:
                exc = traceback.format_exc()
                Data.logger["server"].error(exc)
                time.sleep(1)
    
    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 DAILY STATS
    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    
    def daily_stats(self):
        
        today_date = date.today()
        yestarday_date = today_date - timedelta(days=1)

        # today & yesterday in second
        nows = time.mktime(today_date.timetuple())
        yestardays = time.mktime(yestarday_date.timetuple())

        for i in range(5):
            try:

                trades = Trade.get_all_history(
                    {
                        "sell_time": {
                            "$gte": yestardays,
                            "$lte": nows,
                        }
                    }
                )

                if trades:
                    images = self.image_conv.generate_trading_image(trades)
                    
                    if images:    
                        Data.nh.upload_image(images, self._generate_caption(today_date))

                break

            except:
                exc = traceback.format_exc()
                self.logger.error(exc)
                time.sleep(1)

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                 GENERATE CAPTION
    # = = = = = = = = = = = = = = = = = = = = = = = = = =

    def _generate_caption(self, date):
        caption =  f"Daily Trading 🚀 on {date.strftime('%d, %b %Y')} 📅\n\n\n\n\n\
                            We shares our daily tradings everyday.⏰\n\n~ ~ ~ ~ ~\
                            𝐍𝐨 𝐈𝐧𝐯𝐞𝐬𝐭𝐦𝐞𝐧𝐭 𝐀𝐝𝐯𝐢𝐜𝐞\n\
                            👉 @gtmtrade.👌🏽\n\
                            🅶🆃🅼🆃🆁🅰🅳🅴 🤖⚙\n\n\n\n\
                            #trading #bitcoin #coin #tradebot #binance #crypto #cryptocurrency #gotomoon #long #short\
                            #bnb #xrp #cordano #ada #elonmusk #doge #kucoin #gate #listing",
        

        return caption[0]
