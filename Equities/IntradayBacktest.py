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
from nautilus_trader.test_kit.providers import TestInstrumentProvider, TestDataProvider
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders.list import OrderList
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import OrderSide, PositionSide, TimeInForce
from IntradayBreakoutStrategy import IntradayBreakout, IntradayBreakoutConfig
from IntradayModel import BoundsData, MoveData, BoundsBreakoutActor, BoundsBreakoutConfig
from decimal import Decimal

from ProcessingData import flat

# engine config
engine_config =  BacktestEngineConfig(
    trader_id = "BACKTESTER-1",
    logging=LoggingConfig(log_level="INFO")
)

# engine
engine = BacktestEngine(config=engine_config)

#venue
SIM = Venue("SIM")
engine.add_venue(
    venue=SIM,
    oms_type=OmsType.HEDGING,  # Venue will generate position IDs
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

# actor config
actor_config = BoundsBreakoutConfig(
    instrument_id=MSFT_SIM.id
)

# adding actor
actor = BoundsBreakoutActor(actor_config)
engine.add_actor(actor=actor)

# strat config
strat_config = IntradayBreakoutConfig(
    instrument_id=MSFT_SIM.id,
    bar_type=bartype,
    trade_size=Decimal("0.10")
)

# adding strategy
strategy = IntradayBreakout(strat_config)
engine.add_strategy(strategy=strategy)


# run
engine.run()

# report 
print(engine.trader.generate_account_report(SIM))

# dispose of engine
engine.dispose()
