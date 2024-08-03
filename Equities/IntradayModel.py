from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos, unix_nanos_to_dt, format_iso8601
from nautilus_trader.model.data import DataType, BarType, Bar, BarSpecification
from nautilus_trader.serialization.base import register_serializable_type
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.enums import AggregationSource
from datetime import datetime 
import msgspec
from typing import List
import pandas as pd
import numpy as np


def unix_nanos_to_str(unix_nanos):
    return format_iso8601(unix_nanos_to_dt(unix_nanos))

def make_bar_type(instrument_id: InstrumentId, bar_spec) -> BarType:
    return BarType(instrument_id=instrument_id, bar_spec=bar_spec, aggregation_source=AggregationSource.INTERNAL)

def bars_to_dataframe(symbol_id: str, symbol_bars: List[Bar], n: int = 64) -> pd.DataFrame:
    def _bars_to_frame(bars, instrument_id):
        df = pd.DataFrame([t.to_dict(t) for t in bars[-n::7]]).astype({"close": float})
        df.loc[:, "ts_init"] = [datetime.fromtimestamp(x // 1e9) for x in df.loc[:, "ts_init"]]
        res = df.assign(instrument_id=instrument_id)
        

    df = _bars_to_frame(bars=symbol_bars, instrument_id=symbol_id)
    data = df["close"].unstack(0).sort_index().fillna(method="ffill")
    return data.dropna()

class BoundsBreakoutConfig(ActorConfig):
    symbol: str
    bar_spec: str = "1-HOUR-LAST"
    moving_average_length: int = 14

class BoundsBreakoutActor(Actor):
    def __init__(self, config: BoundsBreakoutConfig):
        super.__init__(config=config)

        self.symbol_id = InstrumentId.from_str(config.symbol)
        self.bar_spec = BarSpecification.from_str(self.config.bar_spec)
        self.ma_length = config.moving_average_length
        self.bar_type = make_bar_type(instrument_id=self.symbol_id, bar_spec=self.bar_spec)
        self.day_open = None
        self.day_open_date = None

    def on_start(self):
        self.instrument = self.cache.instrument(self.symbol_id)

        self.subscribe_bars(self.bar_type)
        self.subscribe_data(DataType(MoveData)) 

    def on_data(self, data):
        if isinstance(data, MoveData):
            self.cache.add(f"{self.symbol_id.value}_move", data.to_bytes())

    def on_bar(self, bar: Bar): 
        self._find_move(bar)
        if self._check_data_length(bar):
            self._find_bounds(bar)

    def _check_data_length(self, bar: Bar):
        bars = self.cache.bars(bar_type=self.bar_type)
        if not bars:
            return False
        time_from_start = self.clock.timestamp_ns() - bar.ts_init
        return time_from_start >= pd.Timedelta("14 days").nanoseconds

    def _find_open(self, bar: Bar):
        date = datetime.fromtimestamp(bar.ts_init).date()
        if date != self.day_open_date:
            self.day_open = bar.open
            self.day_open_date = bar.ts_init

    def _find_move(self, bar: Bar):
        self._find_open(bar)
        if self.day_open is None:
            return
        
        move = np.abs(bar.close/self.day_open - 1)

        move_update = MoveData(self.symbol_id.value, move, ts_init=bar.ts_init)
        self.publish_data(
            data_type=DataType(MoveData), 
            data=move_update
        )

    def _find_bounds(self, bar: Bar):
        moves = MoveData.from_bytes(self.cache.get(f"{self.symbol_id.value}"))
        move_avg = np.average(moves[-64::7])
        
        upper_bound = self.day_open * (1 + move_avg)
        lower_bound = self.day_open * (1 - move_avg)

        bounds_update = BoundsData(self.symbol_id.value, upper_bound, lower_bound, ts_init=bar.ts_init)
        self.publish_data(
            data_type=DataType(BoundsData),
            data=bounds_update
        )

class MoveData(Data):
    def __init__(self, instrument_id: str, abs_move: float, ts_event=0, ts_init=0):
        self.instrument_id = instrument_id
        self.abs_move = abs_move
        self.ts_event = ts_event
        self.ts_init = ts_init

    @property
    def ts_event(self):
        return self._ts_event

    @property
    def ts_init(self):
        return self._ts_init   

    def to_dict(self):
        return {
            "instrument_id": self.instrument_id.value,
            "abs_move": self.abs_move,
            "ts_event": self._ts_event,
            "ts_init": self._ts_init

        }

    def to_bytes(self):
        return msgspec.msgpack.encode(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict):
        return MoveData(InstrumentId.from_str(data["instrument_id"]), data["abs_move"], 
                        data["ts_event"], data["ts_init"])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls.from_dict(msgspec.msgpack.decode(data))

class BoundsData(Data):
    def __init__(self, instrument_id: str, upper_bound_data: float, lower_bound_data: float,
                  ts_event=0, ts_init=0):
        super().__init__(ts_init=ts_init, ts_event=ts_init)

        self.instrument_id = instrument_id
        self._ts_event = ts_event
        self._ts_init = ts_init

        self.upper_bound_data = upper_bound_data
        self.lower_bound_data = lower_bound_data
        self._ts_event = ts_event  
        self._ts_init = ts_init 

    def __repr__(self):
        return (f"BoundsData("
                f"upper_bound_data={self.upper_bound_data:.2f}, "
                f"lower_bound_data={self.lower_bound_data:.2f}"
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
            "upper_bound_data": self.upper_bound_data,
            "lower_bound_data": self.lower_bound_data,
            "ts_event": self._ts_event,
            "ts_init": self._ts_init
        }

    def to_bytes(self):
        return msgspec.msgpack.encode(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict):
        return BoundsData(data["upper_bound_data"], data["lower_bound_data"], data["ts_event"], data["ts_init"])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls.from_dict(msgspec.msgpack.decode(data))
