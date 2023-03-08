import logging

from src.core.strategy import DefaultStrategy
from src.config import trade
from src.notifier import notifier
from src.calc import mlt, add, sub, div


class Martin(DefaultStrategy):

    def __init__(self, inst: str, indicator):
        DefaultStrategy.__init__(self, inst, indicator)
        self._trading = False
        self._pos_side = ''
        self._orders = []

        self._follow = False
        self._counter = 0
        self._idx = -1

    async def handle(self, data):
        if self._trading:
            self._follow_order(data['data'][0])
        else:
            self._first_order(data['data'][0])

    def _first_order(self, data: dict):
        conf = trade(self.inst())
        pos_side = conf['pos_side']
        if not pos_side:
            t = self.indicator().trend()
            if t == 0:
                return
            pos_side = 'long' if t > 0 else 'short'

        self._pos_side, px, sz = pos_side, float(data['last']), conf['martin']['first_size']
        self._order_place(px, sz)
        self._order_fill(px, sz)

        self._counter += 1
        self._trading = True
        self._follow = False

    def _follow_order(self, data: dict):
        if self._follow:
            return

        conf = trade(self.inst())['martin']
        fr, sz, inc = conf['follow_rates'], conf['first_size'], conf['increment']
        fpx = self._orders[0][0]
        for i in range(0, conf['max_orders'] - 1):
            sz *= inc
            next_px = next_price(self.inst(), i, fpx, self._pos_side)
            self._order_place(next_px, sz)
        self._follow = True

    def _market(self, data: dict):
        px, fpx = data['last'], self._orders[0][0]
        sl = stop_loss(self.inst(), fpx, self._pos_side)
        if not is_profit(self._pos_side, sl, px):
            logging.info('close order by stop loss')
            self._order_close(px)
            return

        tp = take_profit(self.inst(), self._avg_px(), self._idx, self._pos_side)
        if is_profit(self._pos_side, tp, px):
            logging.info('take profit by fixed rate')
            self._order_close(px)
            return

        next_px = next_price(self.inst(), self._idx + 1, fpx, self._pos_side)
        if not is_profit(self._pos_side, next_px, px):
            self._order_fill(px, self._next_sz())

    def _order_place(self, px, sz):
        logging.info('placed order at %s %s %s' % (px, sz, self._pos_side))

    def _order_fill(self, px, sz):
        fpx = px if not self._orders else self._orders[0][0]
        nxt = next_price(self.inst(), self._idx + 1, fpx, self._pos_side)
        sl = stop_loss(self.inst(), fpx, self._pos_side)
        logging.info('order filled at %s %s %s next=%s sl=%s' % (px, sz, self._pos_side, nxt, sl))
        notifier.order_filled(f'fill at {px} {sz} {self._pos_side}\nnext={nxt} sl={sl}')
        self._idx += 1
        self._orders.append([px, sz])

    def _order_close(self, px: float):
        avg_px, ttl_sz = self._avg_px(), self._filled_sz()
        pnl = calc_pnl(self.inst(), avg_px, px, ttl_sz, self._pos_side)
        logging.info('%d close at %s %s pnl=%s avg=%s max=%s' % (self._counter, px, ttl_sz, pnl, avg_px, self._max_profit_px))
        notifier.order_closed('%d close at %s %s\npnl=%s\navg=%s max=%s' % (self._counter, px, ttl_sz, pnl, avg_px, self._max_profit_px))
        self._idx = -1
        self._orders.clear()
        self._pos_side = ''
        self._trading = False

        if self.finished_stop:
            self.stop()

    def _avg_px(self) -> float:
        avg = .0
        if not self._orders:
            return avg

        ttl_sz = .0
        for o in self._orders:
            avg = add(avg, mlt(o[0], o[1]))
            ttl_sz = add(ttl_sz, o[1])
        return div(avg, ttl_sz)

    def _filled_sz(self) -> float:
        ttl_sz = .0
        if not self._orders:
            return ttl_sz

        for o in self._orders:
            ttl_sz = add(ttl_sz, o[1])
        return ttl_sz

    def _next_sz(self) -> float:
        conf = trade(self.inst())['martin']
        sz, inc = conf['first_size'], conf['increment']
        for i in range(0, self._idx + 1):
            sz *= inc
        return sz


def take_profit(inst: str, avg_px: float, idx: int, pos_side: str) -> float:
    conf = trade(inst)['martin']
    rate = conf['profit_rates'][idx]
    return mlt(avg_px, add(1, rate if pos_side == 'long' else -rate))


def stop_loss(inst: str, first_px: float, pos_side: str) -> float:
    conf = trade(inst)['martin']
    sl_rate = conf['follow_rates'][-1]
    return mlt(first_px, add(1.0, sl_rate if pos_side == 'short' else -sl_rate))


def next_price(inst: str, idx: int, first_px: float, pos_side: str) -> float:
    conf = trade(inst)['martin']
    next_rate = conf['follow_rates'][idx]
    return mlt(first_px, add(1.0, next_rate if pos_side == 'short' else -next_rate))


def is_profit(pos_side: str, old_px: float, new_px: float) -> bool:
    if pos_side == 'long':
        return old_px < new_px
    return old_px > new_px


def calc_pnl(inst: str, avg_px: float, close_px: float, ttl_sz: float, pos_side: str) -> float:
    conf = trade(inst)['martin']
    if pos_side == 'long':
        diff = sub(close_px, avg_px)
    else:
        diff = sub(avg_px, close_px)
    value = div(mlt(avg_px, ttl_sz), conf['lever'])
    return mlt(value, div(diff, avg_px))

