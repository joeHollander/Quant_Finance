# imports
import pandas as pd 
import numpy as np
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime
from datetime import time 
import matplotlib.pyplot as plt
from typing import Literal

# function to convert yfinance bar data to timeseries
def yf_to_timeseries(df: pd.DataFrame, periods_per_day: int, exchange: Literal["NYSE", "NASDAQ"] = "NYSE"):
    ppd = periods_per_day

    if df is None:
        print("df is None. Most likely because of an invalid timeframe for yfinance.")

    # adjusting weird yf format 
    df.index = pd.DatetimeIndex(df.index.strftime("%Y-%m-%d %H:%M"))

    # find start and end
    start = pd.to_datetime(df.index[0])
    end = pd.to_datetime(df.index[-1])

    # get holidays 
    holidays = mcal.get_calendar('NYSE').holidays()
    holidays = list(holidays.holidays) # NYSE Holidays

    # get business days (end date isn't counted so adding another)
    day_diff = np.busday_count(start.date(), end.date() + pd.Timedelta(days=1), holidays=holidays)
    
    # crate array to hold open close values
    oc = np.zeros((len(df) + day_diff, ))

    # open values
    oc[::ppd+1] = df.loc[::ppd, "Open"]
    # close values
    oc_idx = np.ones((len(oc), ), dtype=bool)
    oc_idx[::ppd+1] = False
    oc[oc_idx] = df.loc[:, "Adj Close"].values

    # creating index for dates
    idx = np.ones((len(oc), ), dtype=bool)
    idx[ppd::ppd+1] = False
    dates = np.zeros(oc.shape, dtype=datetime)
    dates[idx] = df.index
    # setting index for end of dates
    eod_index = [x.date() for x in df.index]
    dates[~idx] = [datetime.combine(date, time(hour=16)) for date in eod_index[ppd-1::ppd]]

    # create and return new df
    new_df = pd.DataFrame(data=oc, index=dates, columns=["Price"])
    return new_df

if __name__ == "__main__":
    aapl = yf.download("AAPL", "2024-01-01", "2024-03-31", interval="1h")
    aapl = yf_to_timeseries(aapl, 7, exchange="NASDAQ")
    print(aapl.head(10))

