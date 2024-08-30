# normal imports
import time
import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
from datetime import datetime
from decimal import Decimal

# nautilus trader imports
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue, ClientId
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler, TradeTickDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider, TestDataProvider
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders.list import OrderList
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.data import Bar, BarSpecification, BarType, TradeTick
from nautilus_trader.model.enums import OrderSide, PositionSide, TimeInForce
from nautilus_trader.persistence.wranglers import BarDataWrangler
from BasicMRStrategy import BasicMR, BasicMRConfig
from nautilus_trader.backtest.node import BacktestNode, BacktestVenueConfig, BacktestDataConfig, BacktestRunConfig, BacktestEngineConfig
from nautilus_trader.config import ImportableStrategyConfig,  ImportableActorConfig, StreamingConfig
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.serialization.base import register_serializable_type
from nautilus_trader.serialization.arrow.serializer import register_arrow
#from BasicMRData import SingleBar
from util import yf_to_timeseries

# other file related imports
from pathlib import Path
import fsspec 
import shutil
from itertools import repeat


# creating instrument
MSFT_SIM = TestInstrumentProvider.equity(symbol="MSFT", venue="SIM")

# downloading data
start_str = "2023-01-01"
end_str = "2023-12-31"

msft_df = yf.download("MSFT", start=start_str, end=end_str, interval="1d")
msft_ts = yf_to_timeseries(msft_df, 1).tz_localize("America/New_York")

ts_event = msft_ts.index.view(np.uint64)
ts_init = ts_event.copy()

# processing data
bartype = BarType.from_str("MSFT.SIM-1-HOUR-LAST-EXTERNAL")
instrument_id = InstrumentId.from_str("MSFT.SIM")

msft_ts.rename(columns={'Price': 'price', "Volume": "quantity"}, inplace=True)
msft_ts["quantity"] = list(map(lambda x: 1 if x == 0 else x, msft_ts["quantity"]))
msft_ts["trade_id"] = np.arange(len(msft_ts))

wrangler = TradeTickDataWrangler(instrument=MSFT_SIM)
ticks = wrangler.process(data=msft_ts, ts_init_delta=0)

# create path and clear if it exists
CATALOG_PATH = Path.cwd() / "Data" / "MSFT2023catalog"

if CATALOG_PATH.exists():
    shutil.rmtree(CATALOG_PATH)
CATALOG_PATH.mkdir(parents=True)

# create catalog
catalog = ParquetDataCatalog(CATALOG_PATH)

# write to catalog
catalog.write_data([MSFT_SIM])
catalog.write_data(ticks)

instrument = catalog.instruments()[0]

# venue config
venues = [
    BacktestVenueConfig(
        name="SIM",
        oms_type="HEDGING",
        account_type="CASH",
        base_currency="USD",
        starting_balances=["1_000_000 USD"],
    ),
]


start = dt_to_unix_nanos(pd.Timestamp(start_str, tz="America/New_York"))
end =  dt_to_unix_nanos(pd.Timestamp(end_str, tz="America/New_York"))

# data config
data = [
    BacktestDataConfig(
        catalog_path=str(CATALOG_PATH),
        data_cls=TradeTick,
        instrument_id=instrument.id,
        start_time=start,
        end_time=end,
    ),
]
# strategy 
strategy = ImportableStrategyConfig(
        strategy_path="BasicMRStrategy:BasicMR",
        config_path="BasicMRStrategy:BasicMRConfig",
        config=dict(
            instrument_id=instrument.id,
            bar_type=bartype,
            trade_size=Decimal(1),
        ),
    )

# create engine config
config = BacktestRunConfig(
    engine=BacktestEngineConfig(strategies=[strategy]),
    data=data,
    venues=venues
)


# backtest config
node = BacktestNode(configs=[config])

results = node.run() 
#print(msft_ts.head(5))
#print(catalog.trade_ticks()[:5])
