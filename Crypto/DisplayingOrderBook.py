import krakenex
from pykrakenapi import KrakenAPI
import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class OBDisplay():
    def __init__(self, orderbook=None, bids=None, offers=None, bar_width=0.25, total=True):
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.legend_added = False
        self.bar_width = bar_width
        self.bid_bars, self.offer_bars = None, None
        self.total = total
        self.bid_text, self.offer_text = None, None

        
        if orderbook is not None:
            self.bids, self.offers = self.process_orderbook(orderbook)
        elif bids is not None and offers is not None:
            self.bids, self.offers = bids, offers
        
        if orderbook is not None or (bids is not None and offers is not None):                      
            self.best_bid = self.bids["price"].iloc[0]
            self.best_offer = self.offers["price"].iloc[0]
            self.mid = (self.best_bid + self.best_offer) / 2

            self.bids_offset = self.bids["price"].values - bar_width / 2  # shift left
            self.offers_offset = self.offers["price"].values + bar_width / 2  # shift right

    def process_orderbook(self, orderbook):
        bids = pd.DataFrame(orderbook['bids'], columns=["price", "volume"])
        offers = pd.DataFrame(orderbook['asks'], columns=["price", "volume"])

        bids.sort_values(by="price", ascending=True, inplace=True)
        offers.sort_values(by="price", ascending=True, inplace=True)

        bids["total"] = (bids["volume"][::-1].cumsum())[::-1]
        offers["total"] = offers["volume"].cumsum()

        if not self.total:
            bids["total"] = bids["volume"]
            offers["total"] = offers["volume"]

        return bids, offers

    def animate_total(self, orderbook):
        #self.ax.clear()

        self.bids, self.offers = self.process_orderbook(orderbook)
        bb = max(self.bids["price"])
        bo = min(self.offers["price"])

        self.bids_offset = self.bids["price"].values - self.bar_width / 2  # shift left
        self.offers_offset = self.offers["price"].values + self.bar_width / 2  # shift right

        if self.bid_bars is None and self.offer_bars is None:
            print("First")
            # First time plotting
            self.bid_bars = self.ax.bar(self.bids_offset, self.bids["total"].values, width=self.bar_width, color='green', label='Bids')
            self.offer_bars = self.ax.bar(self.offers_offset, self.offers["total"].values, width=self.bar_width, color='red', label='Offers')
                
            # Add legend only once
            if not self.legend_added:
                self.ax.legend()
                self.legend_added = True
        else:
            # Update the heights of the existing bars
            for bar, new_height in zip(self.bid_bars, self.bids["total"].values):
                bar.set_height(new_height)
            for bar, new_height in zip(self.offer_bars, self.offers["total"].values):
                bar.set_height(new_height)
            
            # Update the x-axis positions if the price values have changed
            for bar, new_x in zip(self.bid_bars, self.bids_offset):
                bar.set_x(new_x)
            for bar, new_x in zip(self.offer_bars, self.offers_offset):
                bar.set_x(new_x)

        self.ax.set_xlabel(f"Price, Best Bid: {bb}, Best Offer: {bo}")
        self.ax.set_ylabel("Cumulative Volume")

        # Redraw the figure without clearing
        self.fig.canvas.draw()
        plt.pause(0.001)
        self.fig.canvas.flush_events()

    def vwap(self, orderbook=None, exponent=1, mid=False):
        if orderbook is not None:
            self.bids, self.offers = self.process_orderbook(orderbook)
            
        self.best_bid = self.bids["price"].iloc[0]
        self.best_offer = self.offers["price"].iloc[0]
        self.mid = (self.best_bid + self.best_offer) / 2

        vwap = np.average(np.append(self.bids["price"].values, self.offers["price"].values), weights=np.append(self.bids["volume"].values, self.offers["volume"].values)**exponent)
        res = 2 * self.mid - vwap
        if mid:
            return self.mid
        return res

    def vvwap(self, v_exponent=1, var_exponent=1):
        self.bids["diff"] = 0.01 -(self.bids["price"] - self.bids["price"].iloc[-1])
        self.offers["diff"] = 0.01 + self.offers["price"] - self.offers["price"].iloc[0]
        weights = (np.append(self.bids["volume"].values, self.offers["volume"].values)**v_exponent) / (np.append(self.bids["diff"].values, self.offers["diff"].values)**var_exponent)
        vvwap = np.average(np.append(self.bids["price"].values, self.offers["price"].values), weights=weights)
        return vvwap

if __name__ == "__main__":
    api = krakenex.API()
    k = KrakenAPI(api)
    bids, offers = k.get_order_book("ENS/USD", 20)
    
    bids = bids.astype(np.float64)
    offers = offers.astype(np.float64)
    obd = OBDisplay(bids=bids, offers=offers, total=True)
    print("normal vwap: ", obd.vwap())
    print("squared vwap: ", obd.vwap(exponent=2))
    print("normal var vwap: ", obd.vvwap())
    print("squared var vwap: ", obd.vvwap(v_exponent=1, var_exponent=2))
    print(obd.mid)


