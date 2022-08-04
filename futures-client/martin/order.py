import copy
from core.position import Position, Isolated
from core.price import LastPrice
from core.scope import TakeProfit, StopLoss
from core.side import ShortSide, LongSide
from core.fee import MakerFee
from core.utils import ms_time, add, sub, mlt, Computable


class Order:

    def __init__(self):
        self._id = ms_time() * 100 + 1
        self._start_price = None
        self._side = None
        self._position = None
        self._open_fee = None
        self._close_fee = None
        self._take_profit = None
        self._stop_loss = None

        self._current_price = None

    def id(self):
        return self._id

    def start_price(self, price=None):
        if not price:
            return self._start_price
        self._start_price = price
        return self

    def current_price(self, price=None):
        if not price:
            return self._current_price
        if price.price_type() != self._start_price.price_type():
            raise ValueError('price type should be ' + self._start_price.price_type())
        self._current_price = price
        return self

    def side(self, side=None):
        if not side:
            return self._side
        self._side = side
        return self

    def position(self, pos=None):
        if not pos:
            return self._position
        self._position = pos
        return self

    def open_fee(self, fee=None):
        if not fee:
            return self._open_fee
        self._open_fee = fee
        return self

    def close_fee(self, fee=None):
        if not fee:
            return self._close_fee
        self._close_fee = fee
        return self

    def take_profit(self, take_profit=None):
        if not take_profit:
            return self._take_profit
        self._take_profit = take_profit
        return self

    def stop_loss(self, stop_loss=None):
        if not stop_loss:
            return self._stop_loss
        self._stop_loss = stop_loss
        return self

    def open_order(self):
        pass

    def close_order(self):
        pass

    def value(self) -> float:
        start_value = self._position.value()
        if not self._current_price:
            return start_value

        diff = self._side.diff(self._start_price, self._current_price)
        floating_rate = Computable(diff) / self._start_price
        actual_rate = add(1, mlt(self._position.lever(), floating_rate))
        return Computable(start_value) * Computable(actual_rate)

    def fee(self) -> float:
        if not self._open_fee or not self._close_fee:
            return .0
        open_fee = self._open_fee.fee(self._position)
        if not self._current_price:
            return open_fee
        close_pos = copy.deepcopy(self._position)
        close_pos.price(self._current_price)
        close_fee = self._close_fee.fee(close_pos)
        return add(open_fee, close_fee)

    def expected_profit(self) -> float:
        return sub(self.value(), self._position.value())

    def profit(self) -> float:
        expected = self.expected_profit()
        if expected == 0:
            return -self.fee()
        return expected - self.fee()


if __name__ == '__main__':
    sd = ShortSide()
    # sd = LongSide()
    start_price = LastPrice(23000)
    position = Isolated(0.1, start_price, 100)
    tp = TakeProfit(start_price, sd).rate(.004)
    sl = StopLoss(start_price, sd).price(LastPrice(22000))
    fee = MakerFee(.0005)

    o = Order()
    o.start_price(position.price()).position(position).side(sd)
    o.take_profit(tp).stop_loss(sl).open_fee(fee).close_fee(fee)

    print(o.start_price())
    print(o.position())
    print(o.take_profit())
    print(o.stop_loss())
    print(o.value())
    print(o.expected_profit())
    print(o.profit())

    o.current_price(LastPrice(22908))
    print(o.value())
    print(o.expected_profit())
    print(o.profit())
