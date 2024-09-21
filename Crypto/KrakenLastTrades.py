import requests
from datetime import datetime
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# saving: 
# vpoc, max delta, min delta, current delta, distance between vpoc and current mid, vwap, number of bids and asks, timestamp

data_to_save = {}

trades_url = "https://api.kraken.com/0/public/Trades"
ob_url = "https://api.kraken.com/0/public/Depth"
unix_sec = np.round(time.time())

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
asks = pd.DataFrame(ob["asks"], dtype=float)

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

data2, vals2 = agg_vol(bids, 1, True)
data5, vals5 = agg_vol(bids, agg_price_col=True)
print(len(data5.values))
plt.scatter(data2.index, data2.values)
plt.scatter(data5.index, data5.values)
plt.show()
#print(bids)
#print(pd.DataFrame(trades.json()["result"]["XETHZUSD"]))