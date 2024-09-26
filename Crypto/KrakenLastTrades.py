import requests
from datetime import datetime
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
  'since': unix_sec - 30
}

ob_params = {
  'pair': symbol + currency,
}

trades = requests.request("GET", trades_url, params=trades_params, headers=headers)
ob = requests.request("GET", ob_url, params=ob_params, headers=headers).json()["result"][f"X{symbol}Z{currency}"]
bids = pd.DataFrame(ob["bids"], dtype=float, columns=["price", "volume", "timestamp"])
bids.set_index("timestamp", inplace=True)
bids.index = pd.to_datetime(bids.index, unit="s")

asks = pd.DataFrame(ob["asks"], dtype=float, columns=["price", "volume", "timestamp"])
asks.set_index("timestamp", inplace=True)
asks.index = pd.to_datetime(asks.index, unit="s")

# saving: 
# vpoc, max delta, min delta, current delta, vwap, 
# number of bids and asks, timestamp
# imbalance ratio: b - a / b + a, liquidity gap, spread

def agg_data(bids, asks, trades):
    curr_delta, max_delta, min_delta = delta(trades)
    best_bid = bids["price"].max()
    best_ask = asks["price"].min()
    bid_vpoc = agg_vol(bids, 0.2)
    ask_vpoc = agg_vol(asks, 0.2)
    data = {"timestamp": time.time(), "mid_price": 0.5 * (best_bid + best_ask), 
            "best_bid": best_bid, "best_ask": best_ask,
            "bids": len(bids), "asks": len(asks),
            "curr_delta": curr_delta, "max_delta": max_delta, "min_delta": min_delta,
            "bid_vpoc": bid_vpoc, "ask_vpoc": ask_vpoc,
            "trades": len(trades), "trades_vol": trades["volume"].sum()}
    return data
            

# vpoc
def agg_vol(data, agg_val=None, agg_price_col=False):
    if agg_val is None:
        agg_price = data["price"]
    else:
        agg_price = [agg_val * round(x/agg_val) for x in data["price"]]
    res = data["volume"].groupby(agg_price).sum()
    vpoc = (res.idxmax(), res.max())

    if agg_price_col:
        return res, vpoc
    return vpoc

def delta(data, percent=True):
    if data is None:
        return
    side = [float(vol) if x == "b" else -float(vol) for x, vol in zip(data["order_side"], data["volume"])]
    data["delta"] = np.cumsum(side)
    total_vol = data["volume"].astype(float).sum()
    if percent:
        data["delta"] = data["delta"] / total_vol
    return (data.iloc[-1, :]["delta"], data.index[-1].timestamp()), (data["delta"].max(), data["delta"].idxmax().timestamp()), (data["delta"].min(), data["delta"].idxmin().timestamp())


trades_df = pd.DataFrame(trades.json()["result"][f"X{symbol}Z{currency}"], 
                   columns=["price", "volume", "timestamp", "order_side", "order_type", "misc", "id"])
trades_df = trades_df.astype({"price": float, "volume": float, "timestamp": float})

trades_df.set_index("timestamp", inplace=True)
trades_df.index = pd.to_datetime(trades_df.index, unit="s")

print(agg_data(bids, asks, trades_df))