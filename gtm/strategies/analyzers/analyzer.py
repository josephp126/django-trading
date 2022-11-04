import pandas
from .indicators import Indicators
from ...data.data import Data
from .analyzer_utils import calc_depth_movement

import pandas as pd


# = = = = = = = = = = = = = = = = = = = = = = = = = =
#               DEPTH  WALL CHECKER
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def _wallchecker(df: pd.DataFrame, n=20):

    wc = len(df[df.index <= n - 1])

    if wc > 0:
        return True

    else:
        return False


# = = = = = = = = = = = = = = = = = = = = = = = = = =
#                  ANALYZE DEPTH
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def analyze_depth(pair, n=20):

    depth = calc_depth_movement(pair)

    # ask walls & bids walls
    aw = depth["asks"]["walls"]
    bw = depth["bids"]["walls"]

    awi20, bwi20 = None, None

    if aw.shape[0] > 0:
        # ask walls in 20
        awi20 = _wallchecker(aw, n)

    if aw.shape[0] > 0:
        # bids walls in 20
        bwi20 = _wallchecker(bw, n)

    depth["20"] = {"asks_walls": awi20, "bids_walls": bwi20}

    return depth

# = = = = = = = = = = = = = = = = = = = = = = = = = =
#                    ANALYZE 3M 
# = = = = = = = = = = = = = = = = = = = = = = = = = =

def analyze3m(df):
    sp = 5
    sph = sp / 2

    limit = len(df.index)

    indicators = Indicators(df)

    df = indicators.calculate(sma1=9, sma2=21)

    ## MACD Variables

    macd_delta_diff = df["macd_delta"].diff().fillna(0)

    sorted_d = macd_delta_diff.sort_values().tolist()

    ## RSI Variables

    rsi_diffs = df["rsi"].diff().fillna(0)
    sorted_rsi_diffs = rsi_diffs.sort_values().tolist()

    ## CCI Variables

    cci_diffs = df["cci"].diff().fillna(0)
    sorted_cci_diffs = cci_diffs.sort_values().tolist()

    ## SMA Variables

    # delta_sma = df["sma_21"] - df["sma_51"]

    sma_diffs = df["sma_21"].diff().fillna(0)

    sorted_sma_diffs = sma_diffs.sort_values().tolist()

    if "score" in df:
        start = len(df.index) - 1

    else:
        start = 0
        df["score"] = 0
        df["sma_score"] = 0
        df["rsi_score"] = 0
        df["cci_score"] = 0
        df["macd_score"] = 0

    for i in range(start, len(df.index)):

        score = 0

        ## MACD VARIABLES
        diff = macd_delta_diff[i]
        idx = sorted_d.index(diff) * (20 / limit)

        trend_momentum = 0

        ## ----------------  MACD SCORE IMPLEMENTATION  ----------------
        macd = 0

        if df["macd_delta"][i] > 0:

            macd = idx - sp if diff > 0 else -(idx + sp)

        else:

            macd = idx + sp if diff >= 0 else -(idx + sp)

        df["macd_score"][i] = macd
        score += macd

        # ## RSI Variables

        rsi_v = df["rsi"][i]
        rsi_diff_v = rsi_diffs[i]

        idx = sorted_rsi_diffs.index(rsi_diff_v) * (10 / limit)

        ## ----------------  RSI SCORE IMPLEMENTATION  ----------------

        rs = 0

        if rsi_v > 70:

            rs = idx - sph if rsi_diff_v > 0 else -(15 - idx)

        if 70 >= rsi_v >= 30:

            rs = idx if rsi_diff_v > 0 else (idx + sph - 10)

        if 30 > rsi_v:

            rs = idx + sph if rsi_diff_v >= 0 else (idx + sph - 10)

        trend_momentum += rs
        df["rsi_score"][i] = rs

        ## CCI Variables

        cci_v = df["cci"][i]
        cci_diff_v = cci_diffs[i]

        idx = sorted_cci_diffs.index(cci_diff_v) * (10 / limit)

        cci = 0

        if cci_v > 100:
            ## FIX THIS
            cci = idx - 10 - sph
            trend_momentum += cci

        if 100 >= cci_v > 0:

            cci = idx if cci_diff_v > 0 else (idx - 10 - sph)

        if 0 >= cci_v > -100:

            cci = idx + sph if cci_diff_v > 0 else (idx - 10 - sph)

            trend_momentum += cci

        if -100 >= cci_v:

            cci = idx if cci_diff_v > 0 else (idx - 10 - sph)

            trend_momentum += cci

        df["cci_score"][i] = cci

        ## SMA Variables

        sma_10 = df["sma_9"][i]
        sma_20 = df["sma_21"][i]
        price = df["close"][i]
        sma_diff = sma_diffs[i]

        idx = sorted_sma_diffs.index(sma_diff) * (20 / limit)

        sma = 0

        if sma_10 > sma_20 and price >= sma_10:

            sma = idx + sp if sma_diff > 0 else idx - (20 + sp)

            score += sma

        if sma_10 > sma_20 and sma_10 > price:
            ## going Down! SELL

            sma = idx if sma_diff > 0 else idx - (20 + sp)

            score += sma

        if sma_10 == sma_20:

            sma = idx if sma_diff > 0 else idx - 20

            score += sma

        if sma_20 > sma_10 and sma_10 > price:
            ## Going Down! SELL

            sma = idx if sma_diff > 0 else idx - (20 + sp)

            score += sma

        if sma_20 > sma_10 and price >= sma_10:

            sma = idx if sma_diff > 0 else idx - 20

            score += sma

            ## Depending on price changes.

        df["sma_score"][i] = sma

        score += trend_momentum

        df["score"][i] = score

    return df
