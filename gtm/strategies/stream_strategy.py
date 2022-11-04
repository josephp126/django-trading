from .analyzers.analyzer import analyze3m, analyze_depth
from ..data.data import Data

import pandas as pd

import random


class StreamStrategy:
    def __init__(self, limit=100):

        self.limit = limit
        self.logger = Data.logger["server"]

    

    # = = = = = = = = = = = = = = = = = = = = = = = = = =
    #                GET 3M - CANDLE SIGNAL
    # = = = = = = = = = = = = = = = = = = = = = = = = = = 

    def ch3mGetSignal(self, df: pd.DataFrame, symbol: str):

        signal = None

        df = analyze3m(df)

        depth = analyze_depth(symbol)

        i = len(df.index) - 1

        score = df["score"][i]
        price = df["close"][i]

        # strategie scores
        macd_score = df["macd_score"][i]
        rsi_score = df["rsi_score"][i]
        sma_score = df["sma_score"][i]
        cci_score = df["cci_score"][i]

        # indicators
        rsi = df["rsi"][i]
        sma2 = df["sma_21"][i]
        [ema, ema_pre] = df["ema"][-2:]
        [sma1, sma1_pre] = df["sma_9"][-2:]

        self.last_price = price

        score_diff = df["score"].diff().fillna(0)

        aw = depth["20"]["asks_walls"]
        bw = depth["20"]["bids_walls"]

        if rsi > 30 and rsi_score > 0 and macd_score > 0:

            # * If you divide your money into any piece of count. you can decrease your loss risk for "leverage" position.

            # * sometimes score can be negative

            if ema > sma1 and sma1_pre >= ema and score > 0 and score_diff[i] > 0:

                if aw == True and bw == False:
                    signal = "BUY"

        if rsi >= 80 and rsi_score <= 0:

            signal = "SELL"

        if rsi >= 75:

            if aw == True:

                signal == "SELL"

        if (
            sma1 > ema
            and sma1_pre <= ema_pre
            and macd_score < 0
            and score < -10
            and (cci_score < 0 or rsi_score < 0)
        ):
            signal = "SELL"

        if rsi >= 70 and rsi_score <= 0 and macd_score <= 0:

            signal = "SELL"

        


        Data.poc[symbol] = df

        Data.signals[symbol] = signal

        return df, signal
