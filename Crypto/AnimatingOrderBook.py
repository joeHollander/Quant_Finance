import ccxt.pro
import asyncio
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt
from DisplayingOrderBook import OBDisplay

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    exchange = ccxt.pro.kraken({
        'options': {
            'defaultType': 'future',
        },
    })
    symbol = 'MKR/USD'
    ob_display = OBDisplay()
    start_time = time.time()
    while time.time() - start_time < 120:  # Run for 30 seconds
        try:
            orderbook = await exchange.watch_order_book(symbol, limit=25)
            ob_display.animate_total(orderbook)
            await asyncio.sleep(0)

        except Exception as e:
            print(type(e).__name__, str(e))
    await exchange.close()

# Run the async event loop
asyncio.run(main())
