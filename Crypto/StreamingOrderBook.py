import ccxt.pro
import asyncio
import sys
import time

if sys.platform == 'win32':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    exchange = ccxt.pro.kraken({
        'options': {
            'defaultType': 'future',
        },
    })
    symbol = 'BTC/USDT'
    time_now = time.time()
    while time.time() - time_now < 1:
        try:
            orderbook = await exchange.watch_order_book(symbol, limit=10)
            #print("time: ", round(time.time() * 1000),"bids: ", sorted(orderbook['bids'][:3], key=lambda x: x[0]), "asks: ", sorted(orderbook['asks'][:3], key=lambda x: x[0]))\
            print(orderbook)
        except Exception as e:
            print(type(e).__name__, str(e))
    await exchange.close()


asyncio.run(main())