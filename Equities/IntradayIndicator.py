from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.indicators.base.indicator import Indicator
from nautilus_trader.model.data import Bar
from nautilus_trader.common.enums import LogColor
from IntradayModel import MoveData
from datetime import datetime
import numpy as np
import pandas as pd


class BoundsIndicator(Indicator):

    def __init__(self):
        self.day_open = 0
        self.day_open_date = None
        self.moves = []

    def handle_bar(self, bar: Bar):
        self._find_move(bar)
        # if self._check_data_length(bar):
        #     self._find_bounds(bar)
        if len(self.moves) >= 64:
            self._find_bounds(bar)

    def _check_data_length(self, bar: Bar):
        bars = self.cache.bars(bar_type=self.bar_type)
        if not bars:
            return False
        time_from_start = self.clock.timestamp_ns() - bar.ts_event
        return time_from_start >= pd.Timedelta("14 days").nanoseconds

    def _find_open(self, bar: Bar):
        date = datetime.fromtimestamp(bar.ts_event // 1e9).date()
        if date != self.day_open_date:
            self.day_open = bar.open
            self.day_open_date = bar.ts_event

    def _find_move(self, bar):
        if not bar:
            return
        
        self._find_open(bar)
        if self.day_open is None:
            return
        
        move = np.abs(bar.close/self.day_open - 1)
        self.moves.append(move)

        #move_update = MoveData(self.symbol_id.value, move, ts_event=bar.ts_event, ts_init=bar.ts_init)
        #self.cache.add(f"move", move_update.to_bytes())

    def _find_bounds(self, bar: Bar):
        move_avg = np.average(self.moves[-64::7])
        
        self.upper_bound = self.day_open * (1 + move_avg)
        self.lower_bound = self.day_open * (1 - move_avg)

        self.log.info("Found bound", color=LogColor.CYAN)
    
    def _reset(self):
        self.day_open = 0
        self.day_open_date = None
        self.moves = []


        
        

    