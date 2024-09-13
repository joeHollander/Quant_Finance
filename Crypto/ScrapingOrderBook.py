# uploading to csv or json and then batch into parquet 
import ccxt.pro
import asyncio
import sys
import time
import pandas as pd
from pytz import timezone
import aiofiles
from datetime import datetime

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def scraping(symbol, exchange, num_of_sec, limit=25, sleep_interval=1):
    ccxt_exchange = exchange({
        'options': {
            'defaultType': 'future',
        },
    })
    start_time = time.time()

    res = pd.DataFrame()
    last_timestamp = None
    
    while time.time() - start_time < num_of_sec:  # run for num_of_sec seconds
        try:
            orderbook = await ccxt_exchange.watch_order_book(symbol, limit=limit)
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

    await ccxt_exchange.close()
    return(res)

def main(symbol, exchange, ename, num_of_sec, limit=25, sleep_interval=1):
    res = asyncio.run(scraping(symbol, exchange, num_of_sec, limit=limit, sleep_interval=sleep_interval))
    ny = timezone('America/New_York')
    start = datetime.fromtimestamp(res.index[0] / 1e3, tz=ny)
    end = datetime.fromtimestamp(res.index[-1] / 1e3, tz=ny)
    if start.date() != end.date():
        fname = f"{ename}_{symbol.replace("/", "")}_{start.strftime("%d-%m-%Y-%H:%M")}-{end.strftime("%d-%m-%Y-%H:%M")}.parquet"
    else:
        fname = f"{ename}_{symbol.replace("/", "")}_{start.strftime("%d-%m-%Y-%H:%M")}-{end.strftime("%H:%M")}.parquet"
    
    fname = "Data/OrderBook/" + fname
    res.to_parquet(fname, engine='pyarrow')


# Run the async event loop
print(main("ETH/USD", ccxt.pro.kraken, "kraken", 2, sleep_interval=1))