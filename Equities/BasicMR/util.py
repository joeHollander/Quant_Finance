# imports
import pandas as pd 
import numpy as np
import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime
import matplotlib.pyplot as plt

# function to convert yfinance bar data to timeseries
def yf_to_timeseries(df, periods_per_day=7):
    # find start and end
    start = pd.to_datetime(df.index[0])
    end = pd.to_datetime(df.index[-1])

    # get holidays 
    holidays = mcal.get_calendar('NYSE').holidays()
    holidays = list(holidays.holidays) # NYSE Holidays

    # get business days
    day_diff = np.busday_count(start.date(), end.date(), holidays=holidays)
    
    #days_allowed = day_diff - (day_diff % 5)

    # crate array to hold open close values
    oc = np.zeros((len(df) + day_diff, ))

    # open values
    oc[::8] = df.loc[::7, "Open"]
    # close values
    oc_idx = np.ones((len(oc), ), dtype=bool)
    oc_idx[::8] = False
    oc[oc_idx] = df.loc[:, "Adj Close"].values[:sum(oc_idx)]

    # creating index for dates
    idx = np.ones((len(oc), ), dtype=bool)
    idx[7::8] = False
    dates = np.zeros(oc.shape, dtype="datetime64[ns]")
    dates[idx] = df.index
    # setting index for end of dates
    later_index = df.index + pd.Timedelta(minutes=30)
    dates[~idx] = later_index[6::7].values[:sum(~idx)]

    # create and return new df
    new_df = pd.DataFrame(data=oc, index=dates, columns=["Price"])
    return new_df

if __name__ == "__main__":
    aapl = yf.download("AAPL", "2024-01-01", "2024-01-31", interval="1h")
    aapl = yf_to_timeseries(aapl)
    aapl.plot()
    plt.show()