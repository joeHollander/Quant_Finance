# nautilus trader imports
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType, DataType
from nautilus_trader.model.enums import AccountType, OrderSide, PositionSide, TimeInForce, OmsType
from nautilus_trader.common.enums import LogColor
from nautilus_trader.model.identifiers import Venue, InstrumentId, PositionId, ClientId
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders.list import OrderList
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar, BarSpecification
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.model.position import Position
from nautilus_trader.model.enums import AggregationSource
from decimal import Decimal
from typing import Optional
from IntradayModel import BoundsData
from nautilus_trader.core.data import Data
from nautilus_trader.model.position import Position
from nautilus_trader.model.events import OrderFilled

# library code 
def make_bar_type(instrument_id: InstrumentId, bar_spec) -> BarType:
    return BarType(instrument_id=instrument_id, bar_spec=bar_spec, aggregation_source=AggregationSource.EXTERNAL)

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

# strategy
class IntradayTrendConfig(StrategyConfig):
    instrument_id: InstrumentId
    bounds_data_client_id: ClientId
    bar_type: BarType
    trade_size: Decimal
    bar_spec: str = "1-HOUR-LAST"

class IntradayBreakout(Strategy):
    def __init__(self, config: IntradayTrendConfig):
        super().__init__(config)

        # config
        self.instrument_id = config.instrument_id
        self.bounds_data_client_id = config.bounds_data_client_id
        self.bar_type = config.bar_type
        self.trade_size = Decimal(config.trade_size)
        self.bar_spec = BarSpecification.from_str(self.config.bar_spec)
        self._position_id: int = 0

    def on_start(self):
        # instruments and save in cache
        self.instrument = self.cache.instrument(self.instrument_id)

        # subscribe to data
        self.request_bars(make_bar_type(instrument_id=self.instrument_id, bar_spec=self.bar_spec))
        self.subscribe_data(
        client_id=self.bounds_data_client_id, data_type=DataType(BoundsData)
    )

    def on_bar(self, bar: Bar):
        self._check_for_entry(bar)
        self._check_for_exit(bar)
        print("close: ", self.cache.bar(self.instrument_id))

    def on_data(self, data: Data):
        if data.data_type == DataType(BoundsData):
            self.upper_bound = data.upper_bound_data
            self.lower_bound = data.lower_bound_data

    def on_order_filled(self, event: OrderFilled):
        self.position_side = Position(self.instrument, event)

    def _check_for_entry(self, bar: Bar):
        if bar.bar_type.instrument_id == self.instrument_id:
            # Send in orders
            ohlc_bar = self.cache.bar(make_bar_type(self.instrument_id, bar_spec=self.bar_spec))
            if not ohlc_bar:
                return

            close = ohlc_bar.close

            if close > self.upper_bound:
                side = OrderSide.BUY
                max_volume = int(self.config.notional_trade_size_usd / close)
                capped_volume = self._cap_volume(self.instrument_id, max_volume)
                self._log.debug(f"{side} {max_volume=} {capped_volume=}")

            elif close < self.lower_bound:
                side = OrderSide.SELL
                max_volume = int(self.config.notional_trade_size_usd / close)
                capped_volume = self._cap_volume(self.instrument_id, max_volume)
                self._log.debug(f"{side} {max_volume=} {capped_volume=}")

            else: 
                return
            
            self.order_conditions(capped_volume, side, close)
            

    def _cap_volume(self, instrument_id: InstrumentId, max_quantity: int) -> int:
        # most amount of quantity it could buy
        position_quantity = 0
        position = self.current_position(instrument_id)
        if position is not None:
            position_quantity = position.quantity
        return max(0, max_quantity - position_quantity)
    
    def _check_for_exit(self, timer=None, bar: Optional[Bar] = None):
        close = self.cache.bar(make_bar_type(self.instrument_id, bar_spec=self.bar_spec)).close

        # stop if no position
        if not self.cache.positions(strategy_id=self.id):
            return
        
        ohlc_bar = self.cache.bar(make_bar_type(self.instrument_id, bar_spec=self.bar_spec))
        if not ohlc_bar:
            return

        close = ohlc_bar.close
        
        # check if we bought and the price is below the upper bound and vice versa
        if self.position_side.is_long:
            if close < self.upper_bound:
                side = OrderSide.SELL
                max_volume = int(self.config.notional_trade_size_usd / close)
                capped_volume = self._cap_volume(self.instrument_id, max_volume)
                self._log.debug(f"{side} {max_volume=} {capped_volume=}")

        elif not self.position_side.is_long:
            if close > self.lower_bound:
                side = OrderSide.BUY
                max_volume = int(self.config.notional_trade_size_usd / close)
                capped_volume = self._cap_volume(self.instrument_id, max_volume)
                self._log.debug(f"{side} {max_volume=} {capped_volume=}")

        self.order_conditions(capped_volume, side, close)

    def order_conditions(self, capped_volume, side, close):
        if capped_volume == 0:
            # We're at our max limit, cancel any remaining orders and return
            for order in self.cache.orders_open(instrument_id=self.instrument_id, strategy_id=self.id):
                self.cancel_order(order=order)
                return
        self._log.info(
            f"Entry opportunity: {side} market={close},"
            f"{capped_volume=}",
            color=LogColor.GREEN,
            )
        # Cancel any existing orders
        for order in self.cache.orders_open(instrument_id=self.instrument_id, strategy_id=self.id):
            self.cancel_order(order=order)
        # place order
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=side,
            price=Price(close, self.instrument.price_precision),
            quantity=Quantity.from_int(capped_volume),
            time_in_force=TimeInForce.GTC,
        )
        self._log.info(f"ENTRY {order.info()}", color=LogColor.BLUE)
        self.submit_order(order, PositionId(f"instrument-{self._position_id}"))
        
    
    def current_position(self, instrument_id: InstrumentId) -> Optional[Position]:
        try:
            return self.cache.position(PositionId(f"instrument-{self._position_id}"))
        except AssertionError:
            return None




