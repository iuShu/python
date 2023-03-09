import logging

from src.core.strategy import DefaultStrategy
from src.config import trade
from src.calc import add, mlt, sub, div
from src.notifier import notifier


class Trailing(DefaultStrategy):

    def __init__(self, inst: str, indicator):
        DefaultStrategy.__init__(self, inst, indicator)
        self._trading = False
        self._orders = []
        self._pos_side = ''
        self._idx = 0
        self._follow = False

        self._counter = 0
        self._max_profit_px = .0

    async def handle(self, data):
        # logging.debug("trailing %s %s %s" % (self.finished_stop, self.stopped, data))
        if self._trading:
            self._follow_order(data['data'][0])
            self._mock_algo(data['data'][0])
            self._take_profit(data['data'][0])
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

        self._pos_side, px, sz = pos_side, float(data['last']), conf['trailing']['try_sizes'][0]
        self._order_place(px, sz)
        self._order_fill(px, sz)

        self._counter += 1
        self._trading = True
        self._follow = False

    def _follow_order(self, data: dict):
        if self._follow:
            return

        conf = trade(self.inst())['trailing']
        sizes, rng, idx = conf['try_sizes'], conf['range'], self._idx
        fpx = self._orders[0][0]
        while idx < len(sizes):
            next_px = next_price(self.inst(), idx, fpx, self._pos_side)
            self._order_place(next_px, sizes[idx])
            idx += 1
        self._follow = True

    def _mock_algo(self, data: dict):
        px = float(data['last'])
        if is_profit(self._pos_side, self._max_profit_px, px):
            self._max_profit_px = px
            # lpx = self._orders[-1][0]
            # callback_px = next_price(self.inst(), 1, self._max_profit_px, self._pos_side)
            # rate = abs(mlt(div(sub(self._max_profit_px, lpx), self._max_profit_px), 100))
            # logging.info("fill=%s max=%s(%s) back=%s" % (lpx, self._max_profit_px, rate, callback_px))

        conf = trade(self.inst())['trailing']
        sizes, fpx = conf['try_sizes'], self._orders[0][0]
        if self._idx < len(sizes):
            next_px = next_price(self.inst(), self._idx, fpx, self._pos_side)
            if not is_profit(self._pos_side, next_px, px):
                self._order_fill(px, sizes[self._idx])
                return

        sl_px = stop_loss(self.inst(), fpx, self._pos_side)
        if not is_profit(self._pos_side, sl_px, px):
            logging.info('%s close order by stop loss' % self.inst())
            self._order_close(px)
            return

        sizes, rng = conf['try_sizes'], conf['range']
        if self._idx == len(sizes):     # all try_size orders have been filled
            rate = abs(div(sub(self._max_profit_px, px), self._max_profit_px))
            if rate >= rng:
                logging.info('%s close order by trailing range %s' % (self.inst(), round(rate, 2)))
                self._order_close(px)

    def _take_profit(self, data: dict):
        if not self._trading:
            return

        conf = trade(self.inst())['trailing']
        sizes = conf['try_sizes']
        if sizes == 1 or self._idx == len(sizes):
            return

        px, fpx = float(data['last']), self._orders[-1][0]
        if not is_profit(self._pos_side, fpx, px):
            return
        if px == self._max_profit_px or fpx == self._max_profit_px:
            return

        rate = abs(div(sub(self._max_profit_px, px), self._max_profit_px))
        if rate >= conf['range']:
            logging.info('%s take profit by trailing range %s' % (self.inst(), round(rate, 6)))
            self._order_close(px)

    def _order_place(self, px, sz):
        size = mlt(self.face_value(), sz)
        logging.info('%s placed order at %s %s %dx %s' % (self.inst(), px, size, self.lever(), self._pos_side))

    def _order_fill(self, px, sz):
        fpx = px if not self._orders else self._orders[0][0]
        size = mlt(self.face_value(), sz)
        nxt = next_price(self.inst(), self._idx + 1, fpx, self._pos_side)
        sl = stop_loss(self.inst(), fpx, self._pos_side)
        logging.info('%s order filled at %s %s %dx %s next=%s sl=%s'
                     % (self.inst(), px, size, self.lever(), self._pos_side, nxt, sl))
        notifier.order_filled(f'{self.inst()} fill at {px} {size}\n{self.lever()} {self._pos_side}\nnext={nxt} sl={sl}')
        self._idx += 1
        self._orders.append([px, sz])
        self._max_profit_px = px

    def _order_close(self, px: float):
        avg_px, ttl_sz = self._avg_px(), self._filled_sz()
        ttl_size = mlt(self.face_value(), ttl_sz)
        pnl = calc_pnl(avg_px, px, ttl_sz, self._pos_side)
        ap_rate, mp_rate = calc_rate(avg_px, px), calc_rate(self._max_profit_px, avg_px)
        logging.info('%s %d close at %s %s %dx %s pnl=%s avg=%s(%s) max=%s(%s)'
                     % (self.inst(), self._counter, px, ttl_size, self.lever(), self._pos_side, pnl, avg_px, ap_rate, self._max_profit_px, mp_rate))
        notifier.order_closed('%s %d close at %s %s\n %dx %s pnl=%s\navg=%s(%s) max=%s(%s)'
                              % (self.inst(), self._counter, px, ttl_size, self.lever(), self._pos_side, pnl, avg_px, ap_rate, self._max_profit_px, mp_rate))
        self._idx = 0
        self._orders.clear()
        self._pos_side = ''
        self._max_profit_px = .0
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

    def face_value(self) -> float:
        return trade(self.inst())['face_value']

    def lever(self) -> int:
        return trade(self.inst())['trailing']['lever']


def stop_loss(inst: str, first_px: float, pos_side: str) -> float:
    conf = trade(inst)['trailing']
    sl_rate = mlt(conf['range'], len(conf['try_sizes']))
    return mlt(first_px, add(1.0, sl_rate if pos_side == 'short' else -sl_rate))


def next_price(inst: str, idx: int, first_px: float, pos_side: str) -> float:
    conf = trade(inst)['trailing']
    next_rate = mlt(idx, conf['range'])
    return mlt(first_px, add(1.0, next_rate if pos_side == 'short' else -next_rate))


def is_profit(pos_side: str, old_px: float, new_px: float) -> bool:
    if pos_side == 'long':
        return old_px < new_px
    return old_px > new_px


# def calc_pnl(inst: str, avg_px: float, close_px: float, ttl_sz: float, pos_side: str) -> float:
def calc_pnl(avg_px: float, close_px: float, ttl_sz: float, pos_side: str) -> float:
    # conf = trade(inst)['trailing']
    if pos_side == 'long':
        diff = sub(close_px, avg_px)
    else:
        diff = sub(avg_px, close_px)
    # value = div(mlt(avg_px, ttl_sz), conf['lever'])
    # return mlt(value, div(diff, avg_px))
    return mlt(diff, ttl_sz)


def calc_rate(from_px: float, to_px: float) -> float:
    return round(abs(mlt(div(sub(from_px, to_px), from_px), 100)), 2)


if __name__ == '__main__':
    pass
