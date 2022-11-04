from ..helper import strArrToIntArr_2d
from ...data.data import Data

from datetime import datetime

import pandas as pd
import numpy as np

# = = = = = = = = = = = = = = = = = = = = = = = = = =
#              CALCULATE DEPTH MOVEMENT
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def calc_depth_movement(pair: str):

    """
    It calculates total bids & asks quantity and return given dict

    @params
        - depth : dict

    @return
        - depth : dict

    """

    depth = Data.pod[pair]

    sensivity = Data.WALL_SENSIVITY

    bids = depth["bids"]["table"]

    asks = depth["asks"]["table"]

    sum_bids = bids["quantity"].sum()

    sum_asks = asks["quantity"].sum()

    dom_bids = sum_bids * 100 / (sum_bids + sum_asks)

    dom_asks = sum_asks * 100 / (sum_bids + sum_asks)

    avg_bids = bids["price"].sum() / sum_bids

    avg_asks = asks["price"].sum() / sum_asks

    bid_walls = bids[bids.quantity / sum_bids > sensivity]

    ask_walls = asks[asks.quantity / sum_asks > sensivity]

    depth = {
        "bids": {
            "table": bids,
            "total": sum_bids,
            "dominance": dom_bids,
            "avg": avg_bids,
            "walls": bid_walls,
        },
        "asks": {
            "table": asks,
            "total": sum_asks,
            "dominance": dom_asks,
            "avg": avg_asks,
            "walls": ask_walls,
        },
    }

    return depth


# = = = = = = = = = = = = = = = = = = = = = = = = = =
#                CONVERT TO DATAFRAME
# = = = = = = = = = = = = = = = = = = = = = = = = = =


def convert_to_dataframe(hd):
    """Convert historical data matrix to a pandas dataframe

    @args => historical_data (List) : a matrix of historical OHCLV data

    @return => pandas.DataFrame : Contains the historical data in a pandas dataFrame

    """

    hd = strArrToIntArr_2d(hd)

    df = pd.DataFrame(hd)

    df.transpose()

    df.columns = [
        "opentimeStamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "closetimeStamp",
        "quote_asset_volume",
        "number_of_trades",
        "tbb_asset_volume",
        "tbq_asset_volume",
        "ignored",
    ]

    df["datetime"] = df.opentimeStamp.apply(
        lambda x: pd.to_datetime(datetime.fromtimestamp(x / 1000).strftime("%c"))
    )

    df.set_index("datetime", inplace=True, drop=True)
    # df.drop("opentimeStamp", axis=1, inplace=True)

    return df

# = = = = = = = = = = = = = = = = = = = = = = = = = =
#            CONVERT DATAFRAME
# = = = = = = = = = = = = = = = = = = = = = = = = = =

def conv_df(arr):
    """
    it transform array to pandas Dataframe

    @params:
        - arr : list

    @return:
        - df : DataFrame

    """
    rr = np.array(arr).astype(np.float)

    df = pd.DataFrame(rr)

    if df.empty:
        return df

    df.columns = ["price", "quantity"]

    return df