import requests
from datetime import datetime
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# saving: 
# vpoc, max delta, min delta, current delta, vwap, 
# number of bids and asks, timestamp
# imbalance ratio: b - a / b + a, liquidity gap, spread

data_to_save = {}

trades_url = "https://api.kraken.com/0/public/Trades"
ob_url = "https://api.kraken.com/0/public/Depth"
unix_sec = np.round(time.time())

symbol = "ETH"
currency = "USD"

headers = {
  'Accept': 'application/json'
}
trades_params = {
  'pair': symbol + currency,
  'since': unix_sec - 100
}

ob_params = {
  'pair': symbol + currency,
}

trades = requests.request("GET", trades_url, params=trades_params, headers=headers)
ob = requests.request("GET", ob_url, params=ob_params, headers=headers).json()["result"][f"X{symbol}Z{currency}"]
bids = pd.DataFrame(ob["bids"], dtype=float)
asks = pd.DataFrame(ob["asks"], dtype=float)

# def agg_data(bids, asks):
#     data = {"bids": len(bids), "asks": len(asks),
#             "timestamp"

# vpoc
def agg_vol(data, agg_val=None, agg_price_col=False):
    data.columns = ["price", "volume", "timestamp"]  

    if agg_val is None:
        agg_price = data["price"]
    else:
        agg_price = [agg_val * round(x/agg_val) for x in data["price"]]
    res = data["volume"].groupby(agg_price).sum()
    vpoc = (res.idxmax(), res.max())
    if agg_price_col:
        return res, vpoc
    return vpoc

# col, vals = agg_vol(bids, 0.1, True)
# print(col)
# print(type(col))

def delta(data, percent=True):
    side = [float(vol) if x == "b" else -float(vol) for x, vol in zip(data["order_side"], data["volume"])]
    data["delta"] = np.cumsum(side)
    total_vol = data["volume"].astype(float).sum()
    if percent:
        data["delta"] = data["delta"] / total_vol
    return (data.loc[data.index[-1], "delta"], data.index[-1]), (data["delta"].max(), data["delta"].idxmax()), (data["delta"].min(), data["delta"].idxmin())


trades_df = pd.DataFrame(trades.json()["result"][f"X{symbol}Z{currency}"], 
                   columns=["price", "volume", "timestamp", "order_side", "order_type", "misc", "id"])
trades_df.set_index("timestamp", inplace=True)
trades_df.index = pd.to_datetime(trades_df.index, unit="s")
print(delta(trades_df))

print("best bid: ", bids.iloc[0, 0])
print("best ask: ", asks.iloc[0, 0])
print(bids)