import copy
import logging

from martin.order import Order
from core.price import Price
from core.scope import TakeProfit, StopLoss
from core.utils import add, mlt, div


class MartinOrder(Order):

    def __init__(self):
        Order.__init__(self)
        self._max_order = 6
        self._step_rate = None
        self._profit_step_rate = None
        self._prev_order = None
        self._next_order = None

    def current_price(self, price=None):
        if not price:
            return self._current_price
        self._current_price = price
        if self._next_order:
            self._next_order.current_price(price)
        return self

    def step_rate(self, step_rate=None):
        if not step_rate:
            return self._step_rate
        self._step_rate = step_rate
        return self

    def profit_step_rate(self, profit_step_rate=None):
        if not profit_step_rate:
            return self._profit_step_rate
        self._profit_step_rate = profit_step_rate
        return self

    def max_order(self, max_order=None):
        if not max_order:
            return self._max_order
        self._max_order = max_order
        return self

    def create_next(self):
        if not self._take_profit or not self._stop_loss:
            logging.warning('please open order first')
            return
        if self._max_order <= 1 or self._next_order or not self._step_rate:
            logging.warning('can not create next martin order')
            return

        # rate = mlt(self._step_rate, self._head().max_order() - self._max_order + 1)
        # np = self._side.loss_price(self._head().start_price(), rate)
        np = self._side.loss_price(self._start_price, self._step_rate)
        nxt = copy.deepcopy(self)
        nxt._id += 1
        nxt._max_order -= 1
        nxt._start_price = Price(np, self._start_price.price_type())
        nxt._position.pos(mlt(self._position.pos(), 2.0))
        nxt._position.price(nxt._start_price)
        self._next_order = nxt
        nxt._prev_order = self
        nxt._set_tp()
        nxt._set_sl()
        return nxt

    def total_value(self) -> float:
        tail = self._tail()
        val = tail.value()
        while tail._prev_order:
            tail = tail._prev_order
            val = add(val, tail.value())
        return val

    def total_expected_profit(self) -> float:
        if not self._current_price:
            return .0

        tail = self._tail()
        ep = tail.expected_profit()
        while tail._prev_order:
            tail = tail._prev_order
            ep = add(ep, tail.expected_profit())
        return ep

    def total_profit(self) -> float:
        if not self._current_price:
            return .0

        tail = self._tail()
        profit = tail.profit()
        while tail._prev_order:
            tail = tail._prev_order
            profit = add(profit, tail.profit())
        return profit

    def total_fee(self) -> float:
        tail = self._tail()
        fee = tail.fee()
        while tail._prev_order:
            tail = tail._prev_order
            fee = add(fee, tail.fee())
        return fee

    def open_order(self):
        self._set_tp()
        self._set_sl()

    def close_all(self):
        tail = self._tail()
        tail.close_order()
        while tail._prev_order:
            tail = tail._prev_order
            tail.close_order()

    def _set_tp(self):
        if not self._step_rate or not self._max_order or not self._profit_step_rate:
            logging.warning('still not set step_rate or max_order or profit_step_rate')
            return
        step = mlt(self._profit_step_rate, self._head().max_order() - self._max_order)
        rate = add(self._step_rate, step)
        self._take_profit = TakeProfit(self._start_price, self._side).rate(rate)

    def _set_sl(self):
        if not self._step_rate or not self._max_order:
            logging.warning('still not set step_rate or max_order')
            return

        if self._head() != self:
            slp = Price(self._stop_loss.stop_price(), self._start_price.price_type())
            self._stop_loss = StopLoss(self._start_price, self._side).price(slp)
            return

        rate = mlt(self._step_rate, self._max_order)
        np = self._side.loss_price(self._head().start_price(), rate)
        slp = Price(np, self._start_price.price_type())
        self._stop_loss = StopLoss(self._start_price, self._side).price(slp)

    def _head(self):
        head = self
        while head._prev_order:
            head = head._prev_order
        return head

    def _tail(self):
        tail = self
        while tail._next_order:
            tail = tail._next_order
        return tail


if __name__ == '__main__':
    from core.price import LastPrice
    from core.position import Isolated
    from core.side import ShortSide
    from core.fee import MakerFee

    p = LastPrice(23000)
    sd = ShortSide()
    pos = Isolated(.1, p, 100)
    mf = MakerFee(.0005)

    mo = MartinOrder()
    mo.start_price(p).position(pos).side(sd).open_fee(mf).close_fee(mf)
    mo.step_rate(.004).profit_step_rate(.0002)
    mo.open_order()

    tail = mo.create_next().create_next().create_next().create_next().create_next()
    print(mo.total_value())

    mo.current_price(LastPrice(23346.376525))

    print(mo.total_value())
    print(mo.total_expected_profit())
    print(mo.total_fee())
    print(mo.total_profit())

