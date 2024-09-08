import krakenex
from pykrakenapi import KrakenAPI
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class OBDisplay():
    def __init__(self, offers: pd.DataFrame, bids: pd.DataFrame):
        self.fig, self.ax = plt.subplots()

        bids.sort_values(by="price", ascending=True, inplace=True)
        offers.sort_values(by="price", ascending=True, inplace=True)

        # cumulative volume
        if "total" not in bids.columns:
            bids["total"] = (bids["volume"][::-1].cumsum())[::-1]
        if "total" not in offers.columns:
            offers["total"] = offers["volume"].cumsum()

        self.offers = offers
        self.bids = bids

    def plot_total(self, bar_width=0.25):
        self.ax.clear()

        bids_offset = bids["price"].values - bar_width / 2  # shift left
        offers_offset = offers["price"].values + bar_width / 2  # shift right

        self.ax.bar(bids_offset, bids["total"].values, width=bar_width, color='green', label='Bids')
        self.ax.bar(offers_offset, offers["total"].values, width=bar_width, color='red', label='Offers')

        self.ax.xlabel("Price")
        self.ax.ylabel("Cumulative Volume")
        self.ax.legend()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def vwap(self, exponent=1):
        vwap = np.average(np.append(bids["price"].values, offers["price"].values), weights=np.append(bids["volume"].values, offers["volume"].values)**exponent)
        return vwap

    def vvwap(self, v_exponent=1, var_exponent=1):
        bids["diff"] = 0.01 -(bids["price"] - bids["price"].iloc[-1])
        offers["diff"] = 0.01 + offers["price"] - offers["price"].iloc[0]
        weights = (np.append(bids["volume"].values, offers["volume"].values)**v_exponent) / (np.append(bids["diff"].values, offers["diff"].values)**var_exponent)
        vvwap = np.average(np.append(bids["price"].values, offers["price"].values), weights=weights)
        return vvwap

if __name__ == "__main__":
    api = krakenex.API()
    k = KrakenAPI(api)
    res = k.get_order_book("ENS/USD", 20)
    offers = pd.DataFrame(res[0], dtype=float)
    bids = pd.DataFrame(res[1], dtype=float)

    print("normal vwap: ", OBDisplay(offers, bids).vwap())
    print("squared vwap: ", OBDisplay(offers, bids).vwap(exponent=2))
    print("normal var vwap: ", OBDisplay(offers, bids).vvwap())
    print("squared var vwap: ", OBDisplay(offers, bids).vvwap(v_exponent=1, var_exponent=2))
    OBDisplay(offers, bids).plot_total()


