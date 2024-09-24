import requests
from datetime import datetime
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# saving: 
# vpoc, max delta, min delta, current delta, distance between vpoc and current mid, vwap, 
# number of bids and asks, timestamp
# imbalance ratio: b - a / b + a, liquidity gap, spread

data_to_save = {}

trades_url = "https://api.kraken.com/0/public/Trades"
ob_url = "https://api.kraken.com/0/public/Depth"
unix_sec = np.round(time.time())

headers = {
  'Accept': 'application/json'
}
trades_params = {
  'pair': 'ETHUSD',
  'since': unix_sec - 100
}

ob_params = {
  'pair': 'ETHUSD',
}

trades = requests.request("GET", trades_url, params=trades_params, headers=headers)
ob = requests.request("GET", ob_url, params=ob_params, headers=headers).json()["result"]["XETHZUSD"]
bids = pd.DataFrame(ob["bids"], dtype=float)
asks = pd.DataFrame(ob["asks"], dtype=float)

def agg_data(bids, asks):
    return 

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

trades_df = pd.DataFrame(trades.json()["result"]["XETHZUSD"], 
                   columns=["price", "volume", "timestamp", "order_side", "order_type", "misc", "id"])
trades_df.set_index("timestamp", inplace=True)
trades_df.index = pd.to_datetime(trades_df.index, unit="s")
trades_df["side"] = [float(vol) if x == "b" else -float(vol) for x, vol in zip(trades_df["order_side"], trades_df["volume"])]
trades_df["delta"] = trades_df["side"].cumsum()
print(trades_df)
print("max delta: ", (trades_df["delta"].max(), trades_df.index[-1] - trades_df["delta"].idxmax()))
print("min delta: ", (trades_df["delta"].min(), trades_df.index[-1] - trades_df["delta"].idxmin()))
print("total volume")

print("best bid: ", bids.iloc[0, 0])
print("best ask: ", asks.iloc[0, 0])