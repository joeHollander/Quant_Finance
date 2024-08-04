# normal imports
import time
import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
from datetime import datetime

# nautilus trader imports
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue, ClientId
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders.list import OrderList
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import OrderSide, PositionSide, TimeInForce
from IntradayBreakoutStrategy import IntradayBreakout, IntradayTrendConfig, EmptyConfig, EmptyStrategy
from IntradayModel import BoundsData, MoveData
from decimal import Decimal

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

# function to load bounds data
def load_bounds_data(upper_bound_col, lower_bound_col, date_index):
    return [BoundsData(ub, lb, d.timestamp() * 1e9, date_index[0].timestamp() * 1e9) for ub, lb, d in zip(upper_bound_col, lower_bound_col, date_index)]
    
bounds_data = load_bounds_data(flat.loc[:, "upper_bound"], flat.loc[:, "lower_bound"], flat.index)

# engine
engine = BacktestEngine()

#venue
SIM = Venue("SIM")
engine.add_venue(
    venue=SIM,
    oms_type=OmsType.NETTING,  # Venue will generate position IDs
    account_type=AccountType.CASH,
    base_currency=None,  # Standard single-currency account
    starting_balances=[Money(100_000, USD)]  # Single-currency or multi-currency accounts
)

# creating MSFT instrument
MSFT_SIM = TestInstrumentProvider.equity(symbol="MSFT", venue="SIM")
engine.add_instrument(MSFT_SIM)

# process into nautilus objects
bartype = BarType.from_str("MSFT.SIM-1-HOUR-LAST-EXTERNAL")

wrangler = BarDataWrangler(bar_type=bartype, instrument=MSFT_SIM)
bars = wrangler.process(flat.loc[:, "open":"close"])

# adding data
engine.add_data(bars)

# strat config
strat_config = IntradayTrendConfig(
    instrument_id=MSFT_SIM.id,
    bounds_data_client_id = ClientId("BOUNDS"),
    bar_type=bartype,
    bounds_data=bounds_data,
    trade_size=Decimal("0.10")
)

# empty config
empty_config = EmptyConfig(
    InstrumentId=MSFT_SIM.id,
    bar_type=bartype
)

# adding strategy
# strategy = IntradayBreakout(strat_config)
strategy = EmptyStrategy(empty_config)
engine.add_strategy(strategy=strategy)

# run
engine.run()

# report 
print(engine.trader.generate_account_report(SIM))

# dispose of engine
engine.dispose()

print(type(bounds_data))

