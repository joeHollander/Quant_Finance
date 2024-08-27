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
from nautilus_trader.backtest.node import BacktestNode, BacktestVenueConfig, BacktestDataConfig, BacktestRunConfig, BacktestEngineConfig
from nautilus_trader.config import ImportableStrategyConfig,  ImportableActorConfig, StreamingConfig
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.core.datetime import dt_to_unix_nanos
#from util import yf_to_timeseries
from nautilus_trader.core.data import Data

from itertools import repeat
from nautilus_trader.model.objects import Price

# other file related imports
from pathlib import Path
import fsspec 
import shutil

from nautilus_trader.core.datetime import dt_to_unix_nanos, unix_nanos_to_dt, format_iso8601
import msgspec
import pyarrow as pa

def unix_nanos_to_str(unix_nanos):
    return format_iso8601(unix_nanos_to_dt(unix_nanos))

class SingleBar(Data):
    def __init__(self, instrument_id: InstrumentId, price: float, ts_event=0, ts_init=0):
        self.instrument_id = instrument_id
        self.price = price
        self._ts_event = ts_event  
        self._ts_init = ts_init 

    def __repr__(self):
        return (f"SingleBar("
                f"price={self.price:.2f}, "
                f"ts_event={unix_nanos_to_str(self._ts_event)}, "
                f"ts_init={unix_nanos_to_str(self._ts_init)}, ")

    @property
    def ts_event(self) -> int:
        return self._ts_event
    
    @ts_event.setter
    def ts_event(self, value):
        self._ts_event = value 

    @property
    def ts_init(self) -> int:
        return self._ts_init
    
    @ts_init.setter
    def ts_init(self, value):
        self._ts_init = value  

    def to_dict(self):
        return {
            "price": self.price,
            "ts_event": self._ts_event,
            "ts_init": self._ts_init
        }

    @classmethod
    def from_dict(cls, data: dict):
        return SingleBar(data["price"], data["ts_event"], data["ts_init"])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls.from_dict(msgspec.msgpack.decode(data))
    
    def to_bytes(self):
        return msgspec.msgpack.encode(self.to_dict())


    def to_catalog(self):
        return pa.RecordBatch.from_pylist([self.to_dict()], schema=SingleBar.schema())

    @classmethod
    def from_catalog(cls, table: pa.Table):
        return [SingleBar.from_dict(d) for d in table.to_pylist()]

    @classmethod
    def schema(cls):
        return pa.schema(
            {
                "price": pa.float64(),
                "ts_event": pa.int64(),
                "ts_init": pa.int64()
            }
        )