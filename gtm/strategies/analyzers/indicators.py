import pandas as pd
import numpy as np


PERIOD_5 = 5
PERIOD_7 = 7
PERIOD_8 = 8
PERIOD_12 = 12
PERIOD_13 = 13
PERIOD_14 = 14
PERIOD_20 = 20
PERIOD_26 = 26

FIBONACCI_SHORT_PERIOD = 21
FIBONACCI_LONG_PERIOD = 51

SHORT_TERM_PERIOD = 9
MIN_PERIOD = 0


class Indicators:
    def __init__(self, data):

        self.df = data

    def calculate(
        self,
        rsi_p=PERIOD_14,
        sma1=FIBONACCI_SHORT_PERIOD,
        sma2=FIBONACCI_LONG_PERIOD,
        ema_p=SHORT_TERM_PERIOD,
        cci_p=PERIOD_20,
    ):

        self.MACD()
        self.RSI(rsi_p)
        self.SMA(sma1)
        self.SMA(sma2)
        self.EMA(ema_p)
        self.CCI(cci_p)
        return self.df

    def MACD(self, short_ema_period=PERIOD_12, long_ema_period=PERIOD_26):

        """

        Calculating Moving Average converge/diverge of Coin, by using 9/12/26 period time.
        In addition, this function generate a score for buy/sell movement.

        If weight close to buy: score < 0
        Else weight close to sell : score > 0

        Constraints :
        a < score < b (WILL CALCULATE)

        @params => None

        @return macd : list

        """

        shortEMA = self.df.close.ewm(
            span=short_ema_period, min_periods=0, adjust=False
        ).mean()
        longEMA = self.df.close.ewm(
            span=long_ema_period, min_periods=0, adjust=False
        ).mean()

        macd = shortEMA - longEMA

        signal = macd.ewm(span=SHORT_TERM_PERIOD, adjust=False).mean()

        macd_delta = macd - signal

        self.df["macd"] = macd
        self.df["macd_signal"] = signal
        self.df["macd_delta"] = macd_delta

        return macd

    def RSI(self, window):
        """

        The Relative Strength Index (RSI) is a momentum indicator which is
        measures the magnitude of recent price changes to evaluate
        overbought or oversold conditions.

        If RSI < 30 , Coin is  exposed to oversold. This case
        is interpretable as the price of this coin will dump

        If RSI > 70, Coin is exposed to overbought. This case
        is interpretable as the price of this coin will going up


        @params n (period) : int
        @return rsi : list


        """

        close = self.df.close

        delta = close.diff().dropna()

        self.df["change"] = delta

        u = delta * 0
        d = u.copy()
        u[delta > 0] = delta[delta > 0]
        d[delta < 0] = -delta[delta < 0]

        u[u.index[window - 1]] = np.mean(u[:window])  # first value is sum of avg gains
        u = u.drop(u.index[: (window - 1)])

        d[d.index[window - 1]] = np.mean(d[:window])  # first value is sum of avg losses
        d = d.drop(d.index[: (window - 1)])

        rs = (
            pd.DataFrame.ewm(u, com=window - 1, adjust=False).mean()
            / pd.DataFrame.ewm(d, com=window - 1, adjust=False).mean()
        )
        rsi = 100 - 100 / (1 + rs)

        self.df["rsi"] = rsi

        return rsi

    def SMA(self, n=PERIOD_7, **kwargs):
        """

        What is the Moving Average (MA)?

        Moving Average is a tool that calculate active price of coin .

        Simple Moving Average. Periods are the time frame. For example, a period of 50 would be a 50 day
        moving average. Values are usually the stock closes but can be passed any values

        - What is the difference SMA from EMA?

        SMA is more faster than EMA, If coin price just changes, firstly SMA is effected by that.
        So, Only one difference between them. Speed!

        @params => n (period) : int

        @return sma : list

        Checkout
        https://corporatefinanceinstitute.com/resources/knowledge/trading-investing/simple-moving-average-sma/


        """

        prices = self.df.close

        sma = prices.rolling(n, min_periods=MIN_PERIOD).mean()

        self.df["sma_" + str(n)] = sma

        return sma

    def EMA(self, n=SHORT_TERM_PERIOD):

        """
        Exponential Moving Average. Periods are the time frame. For example, a period of 50 would be a 50 day
        moving average. Values are usually the stock closes but can be passed any values


        - What is the best period for EMA Indicator ?

            + (9) Short term * * *
            + (21) Medium **


        TIPS:
        https://tradeciety.com/how-to-use-moving-averages/


        @params n (period) : int
        @return ema : list


        """
        prices = self.df.close

        ema = prices.ewm(span=n, adjust=False).mean()

        self.df["ema"] = ema

        return ema

    def CCI(self, n=PERIOD_20, constant=0.015):

        """


        Community Channel Index (CCI) is used to determine oversold and overbought conditions.
        In generally, this indicator is used with RSI. Indicator is bounded by -200 and 200.

        200/100 => Overbought
        100/0 => highly bought
        0/-100 => highly sold
        -100/-200 => Oversold

        Constraints :
        a < score < b (WILL CALCULATE)

        @params => n (period) : int,

        @return CCI : list

        """

        df = self.df

        def mad(v):
            """
            Mean Absolute Devination Calculator
            """
            return np.mean(np.abs(v - np.mean(v)))

        typical_price = (df.high + df.low + df.close) / 3

        rolled_price = typical_price.rolling(n, min_periods=0)

        cci = (typical_price - rolled_price.mean()) / (
            constant * rolled_price.apply(mad, True)
        )

        self.df["cci"] = cci.fillna(0)

        return cci