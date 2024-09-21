import requests
from datetime import datetime
import time
import pandas as pd
import numpy as np

trades_url = "https://api.kraken.com/0/public/Trades"
ob_url = "https://api.kraken.com/0/public/Depth"
unix_sec = np.round(time.time())

payload = {}
headers = {
  'Accept': 'application/json'
}
trades_params = {
  'pair': 'ETHUSD',
  'since': unix_sec - 60
}

ob_params = {
  'pair': 'ETHUSD',
}

trades = requests.request("GET", trades_url, params=trades_params, headers=headers)
ob = requests.request("GET", ob_url, params=ob_params, headers=headers).json()["result"]["XETHZUSD"]
bids = pd.DataFrame(ob["bids"], dtype=float)
asks = pd.DataFrame(ob["asks"])

def agg_vol(data, agg_val, agg_price_col=False):
    data.columns = ["price", "volume", "timestamp"]  

    agg_price = [round(x/agg_val) for x in data["price"]]
    res = data["volume"].groupby(agg_price).sum()
    if agg_price_col:
        return res
    return (res.idxmax(), res.max())

print(agg_vol(bids, 0.2, True))
print(agg_vol(bids, 0.5, False))
#print(bids.loc[bids[max_agg_vol_idx], "agg_price"])

#print(bids)
#print(pd.DataFrame(trades.json()["result"]["XETHZUSD"]))