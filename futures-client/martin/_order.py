import copy
import time

from core.utils import *

LONG_ORDER = 'long'
SHORT_ORDER = 'short'

ISOLATED_POSITION = 'isolated'
CROSS_POSITION = 'cross'

LAST_PRICE = 'last'
INDEX_PRICE = 'index'
MARK_PRICE = 'mark'


class MartinOrder:

    def __init__(self):
        self._id = ms_time() * 100
        self._direction = SHORT_ORDER
        self._pos_type = ISOLATED_POSITION
        self._price_type = LAST_PRICE
        self._price = 0
        self._pos_num = .0
        self._leverage = 100
        self._take_profit = .0
        self._stop_loss = .0
        self._max_order = 5
        self._fluctuate_rate = .004

        self._owner = None
        self._next_order = None

    def price(self, price: float):
        if not price:
            return self._price
        self._price = price
        return self

    def pos_num(self, pos_num: float):
        if not pos_num:
            return self._pos_num
        self._pos_num = pos_num
        return self

    def pos_type(self, pos_type: str):
        if not pos_type:
            return self._pos_type
        self._pos_type = pos_type
        return self

    def leverage(self, leverage: int):
        if not leverage:
            return self._leverage
        self._leverage = leverage
        return self

    def take_profit(self, take_profit: float):
        if not take_profit:
            return self._take_profit
        self._take_profit = take_profit
        return self

    def stop_loss(self, stop_loss: float):
        if not stop_loss:
            return self._stop_loss
        self._stop_loss = stop_loss
        return self

    def price_type(self, price_type: str):
        if not price_type:
            return self._price_type
        self._price_type = price_type
        return self

    def direction(self, direction: str):
        if not direction:
            return self._direction
        self._direction = direction
        return self

    def max_order(self, max_order=-1):
        if max_order < 0:
            return self._max_order
        self._max_order = max_order
        return self

    def expected_profit(self) -> float:
        if self._take_profit:
            return mlt(self._take_profit, div(self._price, self._leverage))

    def expected_loss(self) -> float:
        if self._stop_loss:
            return mlt(self._stop_loss, div(self._price, self._leverage))

    def take_profit_price(self) -> float:
        if self._take_profit:
            if self._direction == LONG_ORDER:
                return add(self._price, mlt(self._take_profit, self._price))
            return sub(self._price, mlt(self._take_profit, self._price))

    def stop_loss_price(self) -> float:
        if self._stop_loss:
            if self._direction == LONG_ORDER:
                return sub(self._price, mlt(self._stop_loss, self._price))
            return add(self._price, mlt(self._stop_loss, self._price))

    def take_profit_value(self) -> float:
        val = mlt(self.pos_value(), mlt(self._take_profit, self._leverage))
        if self._owner:
            return sub(val, self._owner.stop_loss_value())
        return val

    def stop_loss_value(self) -> float:
        val = mlt(self.pos_value(), mlt(self._stop_loss, self._leverage))
        if self._owner:
            return add(val, self._owner.stop_loss_value())
        return val

    def pos_value(self) -> float:
        return mlt(div(self._price, self._leverage), self._pos_num)

    def next_order(self, next_price=.0):
        if not self._max_order:
            return None

        next_order = copy.copy(self)
        next_order._id = self._id + 1
        next_order.price(next_price if next_price else self.stop_loss_price())
        next_order.max_order(self._max_order - 1)
        next_order.pos_num(mlt(self._pos_num, 2))

        # next_order = MartinOrder()
        # next_order._id = self._id + 1
        # next_order.price(next_price if next_price else self.stop_loss_price()).take_profit(self._take_profit)
        # next_order.stop_loss(self._stop_loss).leverage(self._leverage).max_order(self._max_order - 1)
        # next_order.direction(self._direction).pos_type(self._pos_type).pos_num(mlt(self._pos_num, 2))
        # next_order.price_type(self._price_type)
        next_order._owner = self
        self._next_order = next_order
        return next_order

    def pretty_print(self):
        print('%20s' % 'id:', '%20s' % self._id)
        print('%20s' % 'direction:', '%20s' % self._direction)
        print('%20s' % 'position type:', '%20s' % self._pos_type)
        print('%20s' % 'price:', '%20s' % self._price, self._price_type)
        print('%20s' % 'positions:', '%20s' % self._pos_num)
        print('%20s' % 'value:', '%20s' % self.pos_value())
        print('%20s' % 'leverage:', '%20s' % self._leverage)
        print('%20s' % 'take profit rate:', '%20s' % (self._take_profit * 100), '%')
        print('%20s' % 'stop loss rate:', '%20s' % (self._stop_loss * 100), '%')
        print('%20s' % 'take profit price:', '%20s' % self.take_profit_price(), self._price_type)
        print('%20s' % 'stop loss price:', '%20s' % self.stop_loss_price(), self._price_type)
        print('%20s' % 'take profit:', '%20s' % self.take_profit_value())
        print('%20s' % 'stop loss:', '%20s' % self.stop_loss_value())
        print('%20s' % 'max order num:', '%20s' % self._max_order)


if __name__ == '__main__':
    mo = MartinOrder()
    mo.price(22710).pos_num(.01).take_profit(.005).stop_loss(.005).pretty_print()

    nxt = mo
    for i in range(mo.max_order()):
        nxt = nxt.next_order()
        if nxt:
            nxt.pretty_print()

    pass
