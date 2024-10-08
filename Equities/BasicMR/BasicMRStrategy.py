# nautilus trader imports
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType, DataType, Bar, BarSpecification, TradeTick
from nautilus_trader.model.enums import AccountType, OrderSide, PositionSide, TimeInForce, OmsType, AggregationSource
from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.identifiers import Venue, InstrumentId, PositionId, ClientId
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders.list import OrderList
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.model.position import Position
from decimal import Decimal
from typing import Optional
from nautilus_trader.core.data import Data
from nautilus_trader.model.position import Position
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.serialization.base import register_serializable_type
from nautilus_trader.model.events.position import (
    PositionChanged,
    PositionClosed,
    PositionEvent,
    PositionOpened,
)

# normal imports
import pandas as pd
import numpy as np
from datetime import datetime
from BasicMRData import SingleBar
#import matplotlib.pyplot as plt

# make timestamps readable
def human_readable_duration(ns: float):
    from dateutil.relativedelta import relativedelta  # type: ignore

    seconds = ns / 1e9
    delta = relativedelta(seconds=seconds)
    attrs = ["months", "days", "hours", "minutes", "seconds"]
    return ", ".join(
        [
            f"{getattr(delta, attr)} {attr if getattr(delta, attr) > 1 else attr[:-1]}"
            for attr in attrs
            if getattr(delta, attr)
        ]
    )


class BasicMRConfig(StrategyConfig):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal

class BasicMR(Strategy):
    def __init__(self, config: BasicMRConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size
        self.recent_date = None
        self.recent_open = None
        self.recent_close = None
        self.val = None
        self.position: Position = None
        self.avg_quantity = None 


    def on_start(self):
        # subscribe to data
        self.subscribe_trade_ticks(self.instrument_id)
        
        self.log.info("STARTING", color=LogColor.GREEN)

    def check_for_entry(self):
        if not self.avg_quantity:
            return 
        
        v = self.cache.trade_ticks(self.instrument_id)[1].size

        if self.val >= 0.01 and self.val <= 0.02 and v < self.avg_quantity: 
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_int(self.trade_size),
            )
            self.submit_order(order)
        elif self.val <= -0.01 and self.val >= -0.02 and v < self.avg_quantity:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_int(self.trade_size),
            )
            self.submit_order(order)

    def exit_position(self):
        if self.position:
            self.close_position(self.position)

        self.log.info(f"Closed position: {self.position}", color=LogColor.RED)


    def on_trade_tick(self, trade_tick: TradeTick):
        #self.log.info(f"Tick: {trade_tick.price, datetime.fromtimestamp(trade_tick.ts_event / 1e9).strftime('%m/%d/%Y, %H:%M:%S')}", color=LogColor.BLUE)
        date = datetime.fromtimestamp(trade_tick.ts_event / 1e9).date()

        if self.recent_date is None:
            self.recent_date = date
        elif self.recent_date == date:
            self.recent_close = trade_tick.price
            self.exit_position()
        elif self.recent_date != date:
            self.recent_open = trade_tick.price
            if self.recent_close is None or self.recent_open is None:
                return
            else:
                self.val = -np.log(float(self.recent_open) / float(self.recent_close))
                self.check_for_entry()

        self.recent_date = date

        if not self.val:
            return
        
        if len(self.cache.trade_ticks(self.instrument_id)) >= 10:
            last_quantities = [x.size for x in self.cache.trade_ticks(self.instrument_id)[:10]]
            self.avg_quantity = float(sum(last_quantities)) / (len(last_quantities) / 2)


    def on_event(self, event):
        if isinstance(event, (PositionOpened, PositionChanged)):
            self.position = self.cache.position(event.position_id)
            #self._log.info(f"{self.position}", color=LogColor.YELLOW)

    def on_data(self, data: Data):
        self.log.info("Got Data", color=LogColor.GREEN)
        if isinstance(data, SingleBar):
            self.log.info(f"Data: {data.price}", color=LogColor.GREEN)  

    def on_stop(self):
        # unsubscribe from data
        self.unsubscribe_trade_ticks(self.instrument_id)
        self.log.info("STOPPING", color=LogColor.RED)



