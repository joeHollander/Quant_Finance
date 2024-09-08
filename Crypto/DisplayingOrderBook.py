import krakenex
from pykrakenapi import KrakenAPI
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class OBDisplay():
    def __init__(self, offers: pd.DataFrame, bids: pd.DataFrame):
        plt.ion()
        self.fig = plt.figure() 
        self.ax = self.fig.add_subplot(111) 
        self.i = True

        bids.sort_values(by="price", ascending=True, inplace=True)
        offers.sort_values(by="price", ascending=True, inplace=True)

        # cumulative volume
        if "total" not in bids.columns:
            bids["total"] = (bids["volume"][::-1].cumsum())[::-1]
        if "total" not in offers.columns:
            offers["total"] = offers["volume"].cumsum()

        self.offers = offers
        self.bids = bids

    def plot_total(self, bar_width=0.25, dynamic=False):
        self.ax.clear()
        
        bids_offset = self.bids["price"].values - bar_width / 2  # shift left
        offers_offset = self.offers["price"].values + bar_width / 2  # shift right

        if self.i:
            bid_bars = self.ax.bar(bids_offset, self.bids["total"].values, width=bar_width, color='green', label='Bids')
            offer_bars = self.ax.bar(offers_offset, self.offers["total"].values, width=bar_width, color='red', label='Offers')
            self.i = False
        else:
            bid_bars.set_ydata(self.bids["total"].values)
            offer_bars.set_ydata(self.offers["total"].values)

        self.ax.set_xlabel("Price")
        self.ax.set_ylabel("Cumulative Volume")

        if not self.ax.get_legend():
            self.ax.legend()
        
        if dynamic:
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(1)
        else:
            plt.show()

    def vwap(self, exponent=1):
        vwap = np.average(np.append(self.bids["price"].values, self.offers["price"].values), weights=np.append(self.bids["volume"].values, self.offers["volume"].values)**exponent)
        return vwap

    def vvwap(self, v_exponent=1, var_exponent=1):
        self.bids["diff"] = 0.01 -(self.bids["price"] - self.bids["price"].iloc[-1])
        self.offers["diff"] = 0.01 + self.offers["price"] - self.offers["price"].iloc[0]
        weights = (np.append(self.bids["volume"].values, self.offers["volume"].values)**v_exponent) / (np.append(self.bids["diff"].values, self.offers["diff"].values)**var_exponent)
        vvwap = np.average(np.append(self.bids["price"].values, self.offers["price"].values), weights=weights)
        return vvwap

if __name__ == "__main__":
    api = krakenex.API()
    k = KrakenAPI(api)
    res = k.get_order_book("ENS/USD", 20)
    offers = pd.DataFrame(res[0], dtype=float)
    bids = pd.DataFrame(res[1], dtype=float)

    obd = OBDisplay(offers, bids)
    print("normal vwap: ", obd.vwap())
    print("squared vwap: ", obd.vwap(exponent=2))
    print("normal var vwap: ", obd.vvwap())
    print("squared var vwap: ", obd.vvwap(v_exponent=1, var_exponent=2))
    obd.plot_total()


