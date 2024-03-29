from src.base import repo
from src.calc import add, mlt, sub, div
from src.okx.consts import *

KEY_ORDER_RUNNING = 'morder-running'
KEY_ORDER_PENDING = 'morder-pending'


class MartinOrder:

    def __init__(self, pos: int, follow_rate=.004, profit_step_rate=.0002, max_order=5,
                 pos_type=TD_MODE_ISOLATE, pos_side=POS_SIDE_SHORT):
        self.pos = pos
        self.pos_type = pos_type
        self.pos_side = pos_side
        self.open_type = SIDE_SELL if pos_side is POS_SIDE_SHORT else SIDE_BUY
        self.close_type = SIDE_BUY if self.open_type is SIDE_SELL else SIDE_SELL
        self.ord_type = ORDER_TYPE_MARKET
        self._follow_rate = follow_rate
        self._profit_step_rate = profit_step_rate
        self._max_order = max_order
        self._index = 0
        self._level = 100

        self.px = None
        self.state = None
        self.ord_id = None
        self.algo_id = None
        self.ctime = None
        self.utime = None

        self.extra_margin = 0

        self.prev = None
        self.next = None

    def index(self) -> int:
        return self._index

    def as_first_order(self):
        self._index = 0
        self.prev = None
        self.next = None

    def max_order(self) -> int:
        return self._max_order

    def full_pos(self) -> int:
        head = self.head_order()
        pos = 0
        while head:
            pos += head.pos
            head = head.next
        return pos

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
            return self.prev.stop_loss_price()
        rate = self._follow_rate if self.pos_side == POS_SIDE_SHORT else (-1 * self._follow_rate)
        rate = mlt(rate, self._max_order - self._index + 1)
        return mlt(self.px, add(1.0, rate))

    def extra_margin_balance(self) -> float:
        value = div(mlt(self.px, div(self.pos, 1000)), self._level)
        rate = mlt(mlt(self._follow_rate, self._max_order - self._index + 1), self._level)
        emb = mlt(value, rate)
        return 0 if value > emb else sub(emb, value)

    def create_next(self):
        if self._index == self._max_order:
            return None

        nxt = MartinOrder(pos=self.pos * 2)
        nxt.pos_type = self.pos_type
        nxt.pos_side = self.pos_side
        nxt.open_type = self.open_type
        nxt.close_type = self.close_type
        nxt.ord_type = ORDER_TYPE_LIMIT
        nxt._follow_rate = self._follow_rate
        nxt._profit_step_rate = self._profit_step_rate
        nxt._max_order = self._max_order
        nxt._index = self._index + 1
        nxt._level = self._level
        nxt.px = self.follow_price()
        nxt.prev = self
        self.next = nxt
        return nxt

    def head_order(self):
        if self.prev:
            head = self
            while head.prev:
                head = head.prev
            return head
        return self

    def __str__(self):
        return f'{self.pos} {self.pos_type} {self.pos_side} {self._follow_rate} {self._profit_step_rate} ' \
               f'{self._index} {self._max_order} {self.px} {self.state} {self.ord_id} {self.algo_id} ' \
               f'{self.extra_margin} {self.prev.ord_id if self.prev else -1} {self.prev.algo_id if self.prev else -1}' \
               f' {self.next.ord_id if self.next else -1} {self.next.algo_id if self.next else -1}'


def order() -> MartinOrder:
    return repo.get(KEY_ORDER_RUNNING)


def set_order(o):
    repo[KEY_ORDER_RUNNING] = o


def pending() -> MartinOrder:
    return repo.get(KEY_ORDER_PENDING)


def set_pending(o):
    repo[KEY_ORDER_PENDING] = o


def check_attributes(attr, name: str):
    if not attr:
        raise ValueError(f'{name} is {attr}')


title = []


def print_mo(order: MartinOrder):
    fstr = ' '.join(['%14s' for i in range(8)])
    if not title:
        print(fstr % ('stop loss', 'follow px', 'price', 'profit px', 'profit rate', 'margin', 'pos', 'full pos'))
        title.append('title')
    print(fstr % (order.stop_loss_price(), order.follow_price(), order.px, order.profit_price(), order.profit_rate(),
                  order.extra_margin_balance(), order.pos, order.full_pos()))


if __name__ == '__main__':
    mo = MartinOrder(10)
    mo.state = STATE_FILLED
    mo.px = 22995.000000
    print_mo(mo)
    mo = mo.create_next()
    print_mo(mo)
    mo = mo.create_next()
    print_mo(mo)
    mo = mo.create_next()
    print_mo(mo)
    mo = mo.create_next()
    print_mo(mo)
    mo = mo.create_next()
    print_mo(mo)
    mo = mo.create_next()
    print(mo)
