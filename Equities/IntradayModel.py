from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos, unix_nanos_to_dt, format_iso8601
from nautilus_trader.model.data import DataType
from nautilus_trader.serialization.base import register_serializable_type
from nautilus_trader.model.identifiers import InstrumentId
import msgspec


def unix_nanos_to_str(unix_nanos):
    return format_iso8601(unix_nanos_to_dt(unix_nanos))

class BoundsData(Data):
    def __init__(self, instrument_id: str, upper_bound_data: float, lower_bound_data: float, ts_event=0, ts_init=0):
        super().__init__()

        self.instrument_id = instrument_id
        self.ts_event = 0
        self.ts_init = 0

        self.upper_bound_data = upper_bound_data
        self.lower_bound_data = lower_bound_data

    def __repr__(self):
        return (f"SingleBar(instrument_id={self.instrument_id}, \
                ts_event={unix_nanos_to_str(self._ts_event)}, \
                  ts_init={unix_nanos_to_str(self._ts_init)}, \
                    upper_bound_data={self.upper_bound_data:.2f}, \
                        lower_bound_data={self.lower_bound_data:.2f})")
    @property
    def ts_event(self):
        return self._ts_event
    
    @ts_event.setter
    def ts_event(self, value):
        self._ts_event = value

    @property
    def ts_init(self):
        return self._ts_init
    
    @ts_init.setter
    def ts_init(self, value):
        self.ts_init = value

    def to_dict(self):
        return {
            "instrument_id": self.instrument_id.value,
            "ts_event": self._ts_event,
            "ts_init": self._ts_init,
            "upper_bound_data": self.upper_bound_data,
            "lower_bound_data": self.lower_bound_data

        }

    def to_bytes(self):
        return msgspec.msgpack.encode(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict):
        return BoundsData(InstrumentId.from_str(data["instrument_id"]), data["ts_event"], data["ts_init"], 
                          data["upper_bound_data"], data["lower_bound_data"])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls.from_dict(msgspec.msgpack.decode(data))
