# uploading to csv or json and then batch into parquet 
import ccxt.pro
import asyncio
import sys
import time
import pandas as pd
import aiofiles

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main(symbol, num_of_sec, limit=25, sleep_interval=1):
    exchange = ccxt.pro.kraken({
        'options': {
            'defaultType': 'future',
        },
    })
    symbol = f"{symbol}/USD"
    start_time = time.time()

    res = pd.DataFrame()
    last_timestamp = None
    
    while time.time() - start_time < num_of_sec:  # run for num_of_sec seconds
        try:
            orderbook = await exchange.watch_order_book(symbol, limit=limit)
            ob_df = pd.DataFrame() 
            ob_df[['bid_price', 'bid_volume']] = pd.DataFrame(orderbook['bids'], columns=["bid_price", "bid_volume"])
            ob_df[['ask_price', 'ask_volume']] = pd.DataFrame(orderbook['asks'], columns=["ask_price", "ask_volume"])
            ob_df['timestamp'] = orderbook['timestamp']
            ms_later = orderbook['timestamp'] - last_timestamp if last_timestamp is not None else 0
            last_timestamp = orderbook['timestamp']
            ob_df.set_index('timestamp', inplace=True)
            res = pd.concat([res, ob_df])
            print(f"NEW ORDERBOOK {ms_later / 1e3} seconds later")
            await asyncio.sleep(sleep_interval)

        except Exception as e:
            print(type(e).__name__, str(e))

    await exchange.close()
    return(res)

# Run the async event loop
asyncio.run(main("ETH", 10, sleep_interval=0))