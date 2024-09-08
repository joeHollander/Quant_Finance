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

class OBDisplay():
    def __init__(self, offers: pd.DataFrame, bids: pd.DataFrame):
        bids.sort_values(by="price", ascending=True, inplace=True)
        offers.sort_values(by="price", ascending=True, inplace=True)

        # cumulative volume
        bids["total"] = (bids["volume"][::-1].cumsum())[::-1]
        offers["total"] = offers["volume"].cumsum()

        self.offers = offers
        self.bids = bids

    def plot_total(self):
        



# plotting
bar_width = 0.25  # reduce width to leave space between bars
bids_offset = bids["price"].values - bar_width / 2  # shift left
offers_offset = offers["price"].values + bar_width / 2  # shift right

plt.bar(bids_offset, bids["total"].values, width=bar_width, color='green', label='Bids')
plt.bar(offers_offset, offers["total"].values, width=bar_width, color='red', label='Offers')

plt.xlabel("Price")
plt.ylabel("Cumulative Volume")
plt.legend()

plt.show()

# vwap
vwap = np.average(np.append(bids["price"].values, offers["price"].values), weights=np.append(bids["volume"].values, offers["volume"].values))
#print(vwap)
print(bids)