from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos, unix_nanos_to_dt, format_iso8601
from nautilus_trader.model.data import DataType, BarType, Bar
from nautilus_trader.serialization.base import register_serializable_type
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.enums import AggregationSource
import msgspec


def unix_nanos_to_str(unix_nanos):
    return format_iso8601(unix_nanos_to_dt(unix_nanos))

def make_bar_type(instrument_id: InstrumentId, bar_spec) -> BarType:
    return BarType(instrument_id=instrument_id, bar_spec=bar_spec, aggregation_source=AggregationSource.INTERNAL)

class BoundsData(Data):
    def __init__(self, upper_bound_data: float, lower_bound_data: float, ts_event: int, ts_init: int) -> None:
        super().__init__()

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
