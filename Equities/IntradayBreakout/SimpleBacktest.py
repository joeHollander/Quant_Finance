import backtesting
import backtesting
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
import yfinance as yf

#loading data
msft = yf.download("MSFT", "2023-01-01", "2023-12-31", interval="1h")

# initializing df for organization
df = pd.DataFrame()
df["closes"] = msft["Close"].groupby(msft.index.floor("d")).apply(list)
df["open"] = [x[0] for x in msft["Open"].groupby(msft.index.floor("d")).apply(list)]
df.index = pd.to_datetime(df.index.date)

# dropping because of missing data
df = df.drop(["2023-07-03", "2023-11-24"], axis=0)

# finding hourly move
def move(closes, open):
    return [np.abs(close/open - 1) for close in closes]

df["moves"] = df.apply(lambda x: move(x["closes"], x["open"]), axis=1)

# moving average of move values
def moving_average(data, n=14):
    ma = []
    for i in range(len(data)):
        if i < n:
            ma.append(data[i])
        else:
            window = data[i-n:i]
            ma.append(sum(window) / n)
    return ma

move_arr = np.stack(df["moves"].values)
open_arr = np.array([[val] * 7 for val in df["open"]])

avg_move_arr = np.apply_along_axis(moving_average, axis=0, arr=move_arr)

# upper and lower bounds
df["upper_bound"] = (open_arr * (1 + avg_move_arr)).tolist()
df["lower_bound"] = (open_arr * (1 - avg_move_arr)).tolist()

# account for 14 day lag from moving average and bad dates
df_lagged = df[14:]
msft_lagged = msft[msft.index.tz_localize(None) >= df.index[14]]
baddates = (msft_lagged.index.date != pd.Timestamp("2023-07-03").date()) & (msft_lagged.index.date != pd.Timestamp("2023-11-24").date())
msft_lagged = msft_lagged[baddates]

# flattening into one df
flat = pd.DataFrame(
    {"open": msft_lagged.loc[:, "Open"],
     "high": msft_lagged.loc[:, "High"],
     "low": msft_lagged.loc[:, "Low"],
     "close": np.stack(df_lagged["closes"]).flatten(),
     "upper_bound": np.stack(df_lagged["upper_bound"]).flatten(),
     "lower_bound": np.stack(df_lagged["lower_bound"]).flatten()},
     index=msft_lagged.index
)

flat.index = pd.DatetimeIndex(flat.index)

class IntradayBreakout(Strategy):

    def init(self):
        self.upper_bound = flat.loc[:, "Upper_bound"]
        self.lower_bound = flat.loc[:, "Lower_bound"]
        
    def next(self):
        index = self.data.index[-1]
        if crossover(self.data.Close, self.upper_bound.loc[index]):
            self.position.close()
            self.buy()

        elif crossover(self.lower_bound.loc[index], self.data.Close):
            self.position.close()
            self.sell()

        elif crossover(self.upper_bound.loc[index], self.data.Close):
            self.position.close()

        elif crossover(self.data.Close, self.lower_bound.loc[index]):
            self.position.close()

flat.columns = map(lambda x: str(x).capitalize(), flat.columns)
# print(flat.head())
bt = Backtest(flat.loc[:, "Open": "Close"], IntradayBreakout, commission=0.002)
stats = bt.run()
print(stats)
print(stats['_equity_curve'])
print(stats['_trades'].describe())
bt.plot()