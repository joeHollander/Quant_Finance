import ccxt.pro
import asyncio
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class OBDisplay:
    def __init__(self):
        plt.ion()  # Enable interactive mode
        self.fig, self.ax = plt.subplots()
        self.bid_bars = None
        self.offer_bars = None
        self.legend_added = False  # To ensure legend is added only once

    def display_orderbook(self, orderbook):
        bids = pd.DataFrame(orderbook['bids'], columns=["price", "volume"])
        offers = pd.DataFrame(orderbook['asks'], columns=["price", "volume"])

        bids.sort_values(by="price", ascending=True, inplace=True)
        offers.sort_values(by="price", ascending=True, inplace=True)

        bids["total"] = (bids["volume"][::-1].cumsum())[::-1]
        offers["total"] = offers["volume"].cumsum()

        bar_width = 0.25
        bids_offset = bids["price"].values - bar_width / 2  # shift left
        offers_offset = offers["price"].values + bar_width / 2  # shift right

        if self.bid_bars is None and self.offer_bars is None:
            # First time plotting
            self.bid_bars = self.ax.bar(bids_offset, bids["total"].values, width=bar_width, color='green', label='Bids')
            self.offer_bars = self.ax.bar(offers_offset, offers["total"].values, width=bar_width, color='red', label='Offers')

            # Add legend only once
            if not self.legend_added:
                self.ax.legend()
                self.legend_added = True
        else:
            # Update the heights of the existing bars
            for bar, new_height in zip(self.bid_bars, bids["total"].values):
                bar.set_height(new_height)
            for bar, new_height in zip(self.offer_bars, offers["total"].values):
                bar.set_height(new_height)

            # Update the x-axis positions if the price values have changed
            for bar, new_x in zip(self.bid_bars, bids_offset):
                bar.set_x(new_x)
            for bar, new_x in zip(self.offer_bars, offers_offset):
                bar.set_x(new_x)

        self.ax.set_xlabel("Price")
        self.ax.set_ylabel("Cumulative Volume")

        # Redraw the figure without clearing
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.1)

async def main():
    exchange = ccxt.pro.kraken({
        'options': {
            'defaultType': 'future',
        },
    })
    symbol = 'BTC/USDT'
    ob_display = OBDisplay()
    start_time = time.time()
    while time.time() - start_time < 30:  # Run for 30 seconds
        try:
            orderbook = await exchange.watch_order_book(symbol, limit=10)
            ob_display.display_orderbook(orderbook)
            await asyncio.sleep(0.1)

        except Exception as e:
            print(type(e).__name__, str(e))
    await exchange.close()

# Run the async event loop
asyncio.run(main())
