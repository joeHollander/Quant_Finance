import krakenex
from pykrakenapi import KrakenAPI
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

api = krakenex.API()
k = KrakenAPI(api)
res = k.get_order_book("ENS/USD", 20)
offers = pd.DataFrame(res[0], dtype=float)
bids = pd.DataFrame(res[1], dtype=float)

# if not os.path.isfile("Data/orderbook.txt"):
#     f = open("Data/orderbook.txt", "x")
# else:
#     f = open("Data/orderbook.txt", "a")

# plotting
bids.sort_values(by="price", ascending=False, inplace=True)
offers.sort_values(by="price", ascending=True, inplace=True)

bids["total"] = bids["volume"].cumsum()
offers["total"] = offers["volume"].cumsum()


plt.bar(bids["price"], bids["total"])

plt.bar(bids["price"], bids["total"], width=0.5, color='green', label='Bids')
plt.bar(offers["price"], offers["total"], width=0.5, color='red', label='Offers')

plt.xlabel("Price")
plt.ylabel("Cumulative Volume")
plt.legend()

plt.show()

# vwap
vwap = np.average(np.append(bids["price"].values, offers["price"].values), weights=np.append(bids["volume"].values, offers["volume"].values))
print(vwap)
