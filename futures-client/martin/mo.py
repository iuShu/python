import copy

from core.utils import *
from okx.v5.consts import *


class MartinOrder:

    def __init__(self, pos: int, follow_rate=.004, profit_step_rate=.0002, max_order=5,
                 pos_type=TD_MODE_ISOLATE, pos_side=POS_SIDE_SHORT):
        self.pos = pos
        self.pos_type = pos_type
        self.pos_side = pos_side
        self._follow_rate = follow_rate
        self._profit_step_rate = profit_step_rate
        self._max_order = max_order
        self._index = 0

        self.px = None
        self.state = None
        self.ord_id = None
        self.ctime = None
        self.utime = None

        self.prev = None
        self.next = None

    def index(self) -> int:
        return self._index

    def max_order(self) -> int:
        return self._max_order

    def profit_rate(self) -> float:
        check_attributes(self._follow_rate, 'follow-rate')
        check_attributes(self._profit_step_rate, 'profit-step-rate')
        return add(self._follow_rate, mlt(self._profit_step_rate, self._index))

    def profit_price(self) -> float:
        check_attributes(self.px, 'price')
        return mlt(self.px, sub(1.0, self.profit_rate()))

    def follow_price(self) -> float:
        if self.state != STATE_FILLED:
            raise ValueError(f'inappropriate state: {self.state}')
        check_attributes(self.px, 'price')
        check_attributes(self._follow_rate, 'follow-rate')

        rate = self._follow_rate if self.pos_side == POS_SIDE_SHORT else (-1 * self._follow_rate)
        return mlt(self.px, add(1.0, rate))

    def stop_loss_price(self) -> float:
        if self.state != STATE_FILLED:
            raise ValueError(f'inappropriate state: {self.state}')
        check_attributes(self.px, 'price')
        check_attributes(self._follow_rate, 'follow-rate')
        check_attributes(self._profit_step_rate, 'profit-step-rate')

        if self.prev:
            return self.head_order().stop_loss_price()
        rate = self._follow_rate if self.pos_side == POS_SIDE_SHORT else (-1 * self._follow_rate)
        rate = mlt(rate, self._max_order - self._index + 1)
        return mlt(self.px, add(1.0, rate))

    def create_next(self):
        if self._index == self._max_order:
            return None

        nxt: MartinOrder = copy.deepcopy(self)
        nxt._index += 1
        nxt.px = self.follow_price()
        nxt.pos = self.pos * 2
        nxt.state = STATE_FILLED    # revert to None
        nxt.ctime = None
        nxt.utime = None
        nxt.prev = self
        self.next = nxt
        return nxt

    def head_order(self):
        if self.prev:
            head = self
            while head.prev:
                head = head.prev
            return head

    def __str__(self):
        return f'{self.pos} {self.pos_type} {self.pos_side} {self._follow_rate} {self._profit_step_rate} {self._index} ' \
               f'{self._max_order} {self.px} {self.state} {self.ord_id}'


def check_attributes(attr, name: str):
    if not attr:
        raise ValueError(f'{name} is {attr}')


if __name__ == '__main__':
    mo = MartinOrder(10)
    mo.state = STATE_FILLED
    mo.px = 22995.000000
    print(mo.stop_loss_price(), mo.px, mo.profit_price(), mo.profit_rate(), mo.index(), mo.pos)
    mo = mo.create_next()
    print(mo.stop_loss_price(), mo.px, mo.profit_price(), mo.profit_rate(), mo.index(), mo.pos)
    mo = mo.create_next()
    print(mo.stop_loss_price(), mo.px, mo.profit_price(), mo.profit_rate(), mo.index(), mo.pos)
    mo = mo.create_next()
    print(mo.stop_loss_price(), mo.px, mo.profit_price(), mo.profit_rate(), mo.index(), mo.pos)
    mo = mo.create_next()
    print(mo.stop_loss_price(), mo.px, mo.profit_price(), mo.profit_rate(), mo.index(), mo.pos)
    mo = mo.create_next()
    print(mo.stop_loss_price(), mo.px, mo.profit_price(), mo.profit_rate(), mo.index(), mo.pos)
    mo = mo.create_next()
    print(mo)
