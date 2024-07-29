from nautilus_trader.core.data import Data
from nautilus_trader.common.actor import Actor, ActorConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos, unix_nanos_to_dt, format_iso8601


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
        return (f"SingleBar(instrument_id={self.instrument_id}, 
                ts_event={unix_nanos_to_str(self._ts_event)},
                  ts_init={unix_nanos_to_str(self._ts_init)},
                    bar_data={self.bar_data:.2f})")
    
    @property
    def ts_init(self):
        return self._ts_init

    
