from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos, unix_nanos_to_dt, format_iso8601
import msgspec
from nautilus_trader.core.data import Data
from nautilus_trader.model.data import DataType
from nautilus_trader.serialization.base import register_serializable_type
from nautilus_trader.model.identifiers import InstrumentId


def unix_nanos_to_str(unix_nanos):
    return format_iso8601(unix_nanos_to_dt(unix_nanos))


class BoundsDataConfig(ActorConfig):
    is_upper_bound: bool
    bar_spec: str = "1-HOUR-LAST"


class SingleBar(Data):
    def __init__(self, instrument_id: str, bar_data: float, ts_event: int, ts_init: int):
        super().__init__(ts_init=ts_init, ts_event=ts_init)
        self.instrument_id = instrument_id
        self.bar_data = bar_data
        self.ts_event = ts_event
        self.ts_init = ts_init

    def __repr__(self):
        return (f"SingleBar(instrument_id={self.instrument_id}, \
                ts_event={unix_nanos_to_str(self._ts_event)}, \
                  ts_init={unix_nanos_to_str(self._ts_init)}, \
                    bar_data={self.bar_data:.2f})")
    @property
    def ts_event(self):
        return self._ts_event

    @property
    def ts_init(self):
        return self._ts_init

    def to_dict(self):
        return {
            "instrument_id": self.instrument_id.value,
            "bar_data": self.bar_data,
            "ts_event": self._ts_event,
            "ts_init": self._ts_init,

        }

    def to_bytes(self):
        return msgspec.msgpack.encode(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict):
        return SingleBar(InstrumentId.from_str(data["instrument_id"]), data["bar_data"], data["ts_event"], data["ts_init"])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls.from_dict(msgspec.msgpack.decode(data))
    