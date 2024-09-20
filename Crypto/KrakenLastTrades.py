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

bids.columns = ["price", "volume", "timestamp"]
bids["agg_price"] = [round(2 * float(x)) / 2 for x in bids["price"]]
agg_vol = bids["volume"].groupby(bids["agg_price"]).sum().idxmax()
print(agg_vol.idxmax())
#print(bids.loc[bids[max_agg_vol_idx], "agg_price"])

#print(bids)
#print(pd.DataFrame(trades.json()["result"]["XETHZUSD"]))