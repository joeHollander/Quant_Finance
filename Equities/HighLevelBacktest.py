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
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider, TestDataProvider
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders.list import OrderList
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import OrderSide, PositionSide, TimeInForce
from nautilus_trader.persistence.wranglers import BarDataWrangler
from IntradayBreakoutStrategy import IntradayBreakout, IntradayBreakoutConfig
from IntradayModel import BoundsData, MoveData, BoundsBreakoutActor, BoundsBreakoutConfig
from nautilus_trader.backtest.node import BacktestNode, BacktestVenueConfig, BacktestDataConfig, BacktestRunConfig, BacktestEngineConfig
from nautilus_trader.config import ImportableStrategyConfig,  ImportableActorConfig
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.core.datetime import dt_to_unix_nanos
import IntradayModel
import IntradayBreakoutStrategy

# other file related imports
from pathlib import Path
import fsspec 
import shutil


from ProcessingData import flat 

# creating instrument
MSFT_SIM = TestInstrumentProvider.equity(symbol="MSFT", venue="SIM")

# processing data
bartype = BarType.from_str("MSFT.SIM-1-HOUR-LAST-EXTERNAL")

wrangler = BarDataWrangler(bar_type=bartype, instrument=MSFT_SIM)
bars = wrangler.process(flat.loc[:, "open":"close"])

# create path and clear if it exists
CATALOG_PATH = Path.cwd() / "Data" / "MSFT2023catalog"

if CATALOG_PATH.exists():
    shutil.rmtree(CATALOG_PATH)
CATALOG_PATH.mkdir(parents=True)

# create catalog
catalog = ParquetDataCatalog(CATALOG_PATH)

# write to catalog
catalog.write_data([MSFT_SIM])
catalog.write_data(bars)

instrument = catalog.instruments()[0]


# venue config
venues = [
    BacktestVenueConfig(
        name="SIM",
        oms_type="NETTING",
        account_type="CASH",
        base_currency="USD",
        starting_balances=["1_000_000 USD"],
    ),
]



start = dt_to_unix_nanos(pd.Timestamp("2023-01-24", tz="EST"))
end =  dt_to_unix_nanos(pd.Timestamp("2023-12-29", tz="EST"))

# data config
data = [
    BacktestDataConfig(
        catalog_path=str(CATALOG_PATH),
        data_cls=Bar,
        instrument_id=instrument.id,
        start_time=start,
        end_time=end,
    ),
]

# actor
actor = ImportableActorConfig(
        actor_path="IntradayModel:BoundsBreakoutActor",
        config_path="IntradayModel:BoundsBreakoutConfig",
        config=dict(
            instrument_id=instrument.id
        ),
    )

# strategy 
strategy = ImportableStrategyConfig(
        strategy_path="IntradayBreakoutStrategy:IntradayBreakout",
        config_path="IntradayBreakoutStrategy:IntradayBreakoutConfig",
        config=dict(
            instrument_id=instrument.id,
            bar_type=bartype,
            trade_size=Decimal(10),
        ),
    )

# create engine config
engine = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        strategies=[strategy],
        actors=[actor])


# backtest config
run_config = BacktestRunConfig(engine=engine, venues=venues, data=data )
node = BacktestNode(configs=[run_config])

results = node.run()
print(results)


