from decimal import Decimal

import pandas as pd

from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.core.data import Data
from nautilus_trader.core.message import Event
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy

from IntradayIndicator import BoundsIndicator

class BoundsBreakoutConfig(StrategyConfig):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal = Decimal(10)

class BoundsBreakout(Strategy):
    def __init__(self, config: BoundsBreakoutConfig):

        super().__init__(config)

        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = Decimal(config.trade_size)

        self.bounds_indicator = BoundsIndicator()

    def on_start(self):

        self.instrument = self.cache.instrument(self.instrument_id)

        self.register_indicator_for_bars(self.bar_type, self.bounds_indicator) 

        self.request_bars(self.bar_type)
        self.subscribe_bars(self.bar_type)


    def on_bar(self, bar: Bar):

        if not bar:
            return
        
        self.log.info(repr(bar), LogColor.CYAN)

        if self.bounds_indicator.upper_bound == 0 or self.bounds_indicator.lower_bound == 0:
            return

        # long 
        if bar.close >= self.bounds_indicator.upper_bound:
            if self.portfolio.is_flat(self.instrument_id):
                self.buy()
        # short
        elif bar.close <= self.bounds_indicator.lower_bound:
            if self.portfolio.is_flat(self.instrument_id):
                self.sell()
        # close long
        elif bar.close <= self.bounds_indicator.lower_bound:
            if self.portfolio.is_net_long(self.instrument_id):
                self.close_all_positions(self.instrument_id)
        # close short
        elif bar.close >= self.bounds_indicator.upper_bound:
            if self.portfolio.is_net_short(self.instrument_id):
                self.close_all_positions(self.instrument_id)

    def buy(self):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )

        self.submit_order(order)

        self.log.info("BUY", color=LogColor.GREEN)

    def sell(self):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )

        self.submit_order(order)

        self.log.info("BUY", color=LogColor.RED)

    def on_stop(self):
        self.cancel_all_orders(self.instrument_id)
        self.close_all_positions(self.instrument_id)

        self.unsubscribe_bars(self.bar_type)
        bounds = [[float(a), float(b)] for a, b in zip(self.bounds_indicator.upper_bounds, self.bounds_indicator.lower_bounds)]
        print(bounds[-5:])




