import requests
from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import schedule
import sys
import os
from functools import partial
import asyncio
import aiohttp
import subprocess

githubtoken = os.getenv("GITHUB_TOKEN")

# symbol = input("Enter symbol: ")
# currency = input("Enter currency: ")
# interval = int(input("Enter interval in seconds: "))

# saving: 
# vpoc, max delta, min delta, current delta, vwap, 
# number of bids and asks, timestamp
# imbalance ratio: b - a / b + a, liquidity gap, spread

def agg_data(bids, asks, trades, dict=False):
    if delta(trades) is None:
        curr_delta, max_delta, min_delta = 0, 0, 0
    else:
        curr_delta, max_delta, min_delta = delta(trades)
    best_bid = bids["price"].max()
    best_ask = asks["price"].min()
    bid_vpoc = agg_vol(bids, 0.2)
    ask_vpoc = agg_vol(asks, 0.2)
    data = {"timestamp": time.time(), "mid_price": 0.5 * (best_bid + best_ask), 
            "best_bid": best_bid, "best_ask": best_ask,
            "bids": len(bids), "asks": len(asks),
            "curr_delta": curr_delta, "max_delta": max_delta, "min_delta": min_delta,
            "bid_vpoc": bid_vpoc, "ask_vpoc": ask_vpoc,
            "trades": len(trades), "trades_vol": trades["volume"].sum()}
    if dict:
        return data
    else:
        return list(data.keys()), list(data.values())
            

# vpoc
def agg_vol(data, agg_val=None, agg_price_col=False):
    if agg_val is None:
        agg_price = data["price"]
    else:
        agg_price = [agg_val * round(x/agg_val) for x in data["price"]]
    res = data["volume"].groupby(agg_price).sum()
    vpoc = (res.idxmax(), res.max())

    if agg_price_col:
        return res, vpoc
    return vpoc

def delta(data, percent=True):
    if data is None or data.empty:
        return
    side = [float(vol) if x == "b" else -float(vol) for x, vol in zip(data["order_side"], data["volume"])]
    data["delta"] = np.cumsum(side)
    total_vol = data["volume"].astype(float).sum()
    if percent:
        data["delta"] = data["delta"] / total_vol
    return ((data.iloc[-1, :]["delta"], data.index[-1].timestamp()), 
            (data["delta"].max(), data["delta"].idxmax().timestamp()), 
            (data["delta"].min(), data["delta"].idxmin().timestamp()))

def push_to_github(fname, github_token = githubtoken, commit_message=None, branch="main"):
    # change working directory to crypto
    os.chdir(os.path.abspath(""))
    fname = os.path.abspath(fname).replace("\\", "/")

    short_fname = fname.split("/")[-1]

    if commit_message is None:
        commit_message = f"Committing data: {fname}"

    try:
        subprocess.run(["git", "add", fname], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(['git', 'push', f'https://{github_token}:x-oauth-basic@github.com/joeHollander/Quant_Finance.git', branch], check=True)
    except subprocess.CalledProcessError as e:
        print("Error: Failed to push changes to GitHub: ", e)

def csv_to_parquet(fname, remove_csv=False, github=True):
    df = pd.read_csv(fname)
    df.to_parquet(fname.replace(".csv", ".parquet"), engine='pyarrow', compression='snappy')
    if remove_csv:
        os.remove(fname)
    if github:
        push_to_github(fname.replace(".csv", ".parquet"))


date_started = None
async def job(symbol="ETH", currency="USD", interval=30):
    global date_started
    date = datetime.now().date()    
    if date_started is None:
        date_started = datetime.now().date()
    elif date_started != date:
        new_date = True
    else: 
        new_date = False
    date_started = datetime.now().date()
    trades_url = "https://api.kraken.com/0/public/Trades"
    ob_url = "https://api.kraken.com/0/public/Depth"
    unix_sec = np.round(time.time())

    headers = {
      'Accept': 'application/json'
    }
    trades_params = {
      'pair': symbol + currency,
      'since': unix_sec - interval
    }

    ob_params = {
      'pair': symbol + currency,
      'count': 500
    }

    # requesting data
    async with aiohttp.ClientSession() as session:
        async with session.get(trades_url, params=trades_params, headers=headers) as response:
            trades = await response.json()
        async with session.get(ob_url, params=ob_params, headers=headers) as response:
            ob = await response.json()
    
    trades = trades["result"]
    ob = ob["result"]
    trades_key = list(trades.keys())[0]
    ob_key = list(ob.keys())[0]
    ob = ob[ob_key]
    
    # processing bids
    bids = pd.DataFrame(ob["bids"], dtype=float, columns=["price", "volume", "timestamp"])
    bids.set_index("timestamp", inplace=True)
    bids.index = pd.to_datetime(bids.index, unit="s")

    # processing asks
    asks = pd.DataFrame(ob["asks"], dtype=float, columns=["price", "volume", "timestamp"])
    asks.set_index("timestamp", inplace=True)
    asks.index = pd.to_datetime(asks.index, unit="s")

    # processing trades
    trades_df = pd.DataFrame(trades[trades_key], 
                   columns=["price", "volume", "timestamp", "order_side", "order_type", "misc", "id"])
    trades_df = trades_df.astype({"price": float, "volume": float, "timestamp": float})
    trades_df.set_index("timestamp", inplace=True)
    trades_df.index = pd.to_datetime(trades_df.index, unit="s")

    keys, values = agg_data(bids, asks, trades_df, dict=False)
    str_date = datetime.now().strftime("%Y%m%d")
    str_yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    str_keys = ",".join(map(str, keys))
    str_values = ",".join(map(str, values))
    fname = f"Data/kraken_files/kraken_{symbol}_{currency}_{str_date}.csv"
    yesterday_fname = f"Data/kraken_files/kraken_{symbol}_{currency}_{str_yesterday}.csv"

    file_exist = None
    if os.path.exists(fname):
        file_exist = True
    else:
        file_exist = False
        if os.path.exists(yesterday_fname):
            await csv_to_parquet(yesterday_fname, remove_csv=True, github=True)

    # with open("Data/kraken_files/btc.txt", "a") as f:
    #     f.write("test")
    # push_to_github("Data/kraken_files/btc.txt")
    
    with open(fname, "a") as f:
        if not file_exist:
            f.write(str_keys + "\n")
        f.write(str_values + "\n")
        print("written to file!")

async def main(symbols, currencies, intervals):
        args = [job(symbol, currency, interval) for symbol, currency, interval in zip(symbols, currencies, intervals)]
        await asyncio.gather(*args)
       
if __name__ == "__main__":
    symbols = ["SOL"]
    currencies = ["USD"]
    intervals = [30]  
    start_date = datetime.now().date()

    try:
        while datetime.now().date() - start_date < timedelta(days=89):
            asyncio.run(main(symbols, currencies, intervals))
            time.sleep(30)
    except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(130)
            except SystemExit:
                os._exit(130)
