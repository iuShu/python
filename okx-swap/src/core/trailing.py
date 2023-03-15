import asyncio
import logging

from src.core.strategy import DefaultStrategy
from src.rest import api
from src.config import trade, period2ms
from src.calc import add, mlt, sub, div, ms_time
from src.notifier import notifier

PLACE_RETRY_INTERVAL = 5000
CONFIRM_INTERVAL = 300
FOLLOW_CONFIRM_INTERVAL = 1000
MAX_CONFIRM = 1000


class Trailing(DefaultStrategy):

    def __init__(self, inst: str, indicator):
        DefaultStrategy.__init__(self, inst, indicator)
        self._trading = False
        self._orders = []
        self._pos_side = ''
        self._idx = 0

        self._counter = 0
        self._max_profit_px = .0

        self._pending = []
        self._consecutive_fails = 0
        self._cooldown = 0

        self._lever = {'long': 0, 'short': 0}

    async def handle(self, data):
        # logging.debug("trailing %s %s %s" % (self.finished_stop, self.stopped, data))
        if self._trading:
            self._confirm_follow_filled()
            self._mock_algo(data['data'][0])
            self._take_profit(data['data'][0])
        elif ms_time() >= self._cooldown:
            await self._first_order(data['data'][0])

    async def _first_order(self, data: dict):
        conf = trade(self.inst())
        pos_side = conf['pos_side']
        if not pos_side:
            t = self.indicator().trend(float(data['last']))
            if t == 0:
                return
            pos_side = 'long' if t > 0 else 'short'

        # check lever
        if self._lever[pos_side] != self.lever():
            if api.set_lever(conf['inst_id'], self.lever(), conf['td_mode'], pos_side):
                logging.info('%s set %s lever to %d' % (conf['inst_id'], pos_side, self.lever()))
                self._lever[pos_side] = self.lever()
            else:
                logging.error('stop trading due to lever setting error')
                notifier.order_fail('stop trading due to lever setting error')
                self.stop()
                return

        # cost and balance

        self._pos_side, px, sz = pos_side, float(data['last']), conf['trailing']['try_sizes'][0]
        side = 'buy' if pos_side == 'long' else 'sell'
        data = api.place_order(conf['inst_id'], conf['td_mode'], 'market', side, pos_side, sz)
        if not data:
            self._cooldown = ms_time() + PLACE_RETRY_INTERVAL
            return

        size = mlt(self.face_value(), sz)
        logging.info('%s placed order at %g %g %dx %s' % (self.inst(), px, size, self.lever(), pos_side))
        if await self._confirm_filled(conf['inst_id'], data['ordId']):
            self._counter += 1
            self._trading = True
            self._follow_order()
        else:
            logging.warning('stop trading due to order have not been filled for a long time')
            self.stop()

    def _follow_order(self):
        conf = trade(self.inst())
        sizes, rng, idx = conf['trailing']['try_sizes'], conf['trailing']['range'], self._idx
        fpx, side = self._orders[0][0], 'buy' if self._pos_side == 'long' else 'sell'
        while idx < len(sizes):
            next_px = next_price(self.inst(), idx, fpx, self._pos_side)
            data = api.place_order(conf['inst_id'], conf['td_mode'], 'limit', side, self._pos_side, sizes[idx], next_px)
            if data:
                size = mlt(self.face_value(), sizes[idx])
                logging.info('%s placed order at %g %g %dx %s' % (self.inst(), next_px, size, self.lever(), self._pos_side))
                self._pending.append(data['ordId'])
                idx += 1
            else:
                logging.warning('stop trading due to follow order placing failed')
                notifier.order_fail('%s placing follow order failed' % conf['inst_id'])
                self.stop()

    def _mock_algo(self, data: dict):
        px = float(data['last'])
        if is_profit(self._pos_side, self._max_profit_px, px):
            self._max_profit_px = px
            # lpx = self._orders[-1][0]
            # callback_px = next_price(self.inst(), 1, self._max_profit_px, self._pos_side)
            # rate = abs(mlt(div(sub(self._max_profit_px, lpx), self._max_profit_px), 100))
            # logging.info("fill=%s max=%s(%s) back=%s" % (lpx, self._max_profit_px, rate, callback_px))

        conf = trade(self.inst())
        sizes, fpx = conf['trailing']['try_sizes'], self._orders[0][0]
        if self._idx != len(sizes):
            return

        # all try size orders have been filled

        factor = len(sizes) - self._idx + 1
        sl_px, rate = stop_loss(self.inst(), self._avg_px(), factor, self._pos_side), abs(div(sub(self._max_profit_px, px), self._max_profit_px))
        in_sl, in_range = is_profit(self._pos_side, sl_px, px), rate < conf['trailing']['range']
        if not in_sl or not in_range:
            text = ('%s close order by stop loss' % self.inst()) if not in_sl \
                else ('%s close order by trailing range %g %g' % (self.inst(), rate, px))
            logging.info(text)

            if api.close_position(conf['inst_id'], conf['td_mode'], self._pos_side):
                self._order_close()
                self._cancel_pending()
            else:
                logging.error('stop trading due to order closing error')
                notifier.order_fail('stop trading due to order closing error')
                self.stop()

    def _take_profit(self, data: dict):
        if not self._trading:
            return

        conf = trade(self.inst())
        sizes = conf['trailing']['try_sizes']
        if sizes == 1 or self._idx == len(sizes):
            return

        px, fpx = float(data['last']), self._orders[-1][0]
        if not is_profit(self._pos_side, fpx, px):
            return
        if px == self._max_profit_px or fpx == self._max_profit_px:
            return

        rate = abs(div(sub(self._max_profit_px, px), self._max_profit_px))
        if rate >= conf['trailing']['range']:
            logging.info('%s take profit by trailing range %g at %g' % (self.inst(), rate, px))
            if api.close_position(conf['inst_id'], conf['td_mode'], self._pos_side):
                self._order_close()
                self._cancel_pending()
            else:
                logging.error('stop trading due to order closing error')
                notifier.order_fail('stop trading due to order closing error')
                self.stop()

    async def _confirm_filled(self, inst_id: str, ord_id: str) -> bool:
        loop = MAX_CONFIRM
        while loop:
            order = api.order_detail(inst_id, ord_id)
            if order['state'] == 'filled':
                logging.info('%s' % order)
                self._order_fill(order['avgPx'], order['sz'])
                return True
            loop -= 1
            await asyncio.sleep(CONFIRM_INTERVAL / 1000)

        logging.error('%s %s order have not been filled for a long time' % (inst_id, ord_id))
        notifier.order_fail('%s %s order have not been filled for a long time' % (inst_id, ord_id))
        return False

    def _confirm_follow_filled(self):
        if not self._pending:
            return

        counter, inst_id = self._counter, trade(self.inst())['inst_id']
        order = api.order_detail(inst_id, self._pending[0])
        if order['state'] == 'filled':
            self._pending.pop(0)
            logging.info('%s' % order)
            self._order_fill(order['fillPx'], order['sz'])

    def _cancel_pending(self):
        if not self._pending:
            logging.info('no pending orders needs to cancel')
            return

        if api.cancel_orders(trade(self.inst())['inst_id'], self._pending):
            logging.info('cancel %d pending orders ok' % len(self._pending))
            self._pending.clear()
            return

        logging.error('stop trading due to order canceling error')
        notifier.order_fail('stop trading due to order canceling error')
        self.stop()

    def _order_fill(self, px, sz):
        fpx = float(px) if not self._orders else self._orders[0][0]
        size, sizes = mlt(self.face_value(), float(sz)), trade(self.inst())['trailing']['try_sizes']

        self._idx += 1
        self._orders.append([float(px), float(sz)])
        self._max_profit_px = self._avg_px()

        nxt = next_price(self.inst(), self._idx, fpx, self._pos_side) if len(sizes) != self._idx else .0
        sl = stop_loss(self.inst(), self._avg_px(), len(sizes) - self._idx + 1, self._pos_side)
        logging.info('%s order filled at %g %g %dx %s next=%g sl=%g'
                     % (self.inst(), px, size, self.lever(), self._pos_side, nxt, sl))
        notifier.order_filled('%s fill at %g %g\n%d %s\nnext=%g sl=%g'
                              % (self.inst(), px, size, self.lever(), self._pos_side, nxt, sl))

    def _order_close(self):
        conf, side = trade(self.inst()), 'buy' if self._pos_side == 'short' else 'sell'
        loop, px, ttl_sz, pnl = MAX_CONFIRM, .0, .0, .0
        while loop:
            closed = api.last_filled_order(conf['inst_id'], conf['inst_type'])
            if closed and closed['state'] == 'filled' and closed['side'] == side:
                logging.info('%s' % closed)
                px, ttl_sz, pnl = float(closed['avgPx']), float(closed['sz']), float(closed['pnl'])
                break
            loop -= 1

        if not loop:
            logging.error('stop trading due to getting closed order error')
            notifier.order_fail('stop trading due to getting closed order error')
            self.stop()
            return

        avg_px, ttl_size = self._avg_px(), mlt(self.face_value(), ttl_sz)
        # pnl = calc_pnl(avg_px, px, ttl_size, self._pos_side)
        ap_rate, mp_rate = calc_rate(avg_px, px), calc_rate(self._max_profit_px, avg_px)
        logging.info('%s %d close at %g %g %dx %s pnl=%g avg=%g(%g) max=%g(%g)'
                     % (self.inst(), self._counter, px, ttl_size, self.lever(), self._pos_side, pnl, avg_px, ap_rate, self._max_profit_px, mp_rate))
        notifier.order_closed('%s %d close at %g %g\n %dx %s pnl=%g\navg=%g(%g) max=%g(%g)'
                              % (self.inst(), self._counter, px, ttl_size, self.lever(), self._pos_side, pnl, avg_px, ap_rate, self._max_profit_px, mp_rate))

        if pnl > 0:
            self._consecutive_fails = 0
        elif pnl <= 0:
            conf['pos_side'] = 'long' if self._pos_side == 'short' else 'short'
            self._consecutive_fails += 1
            if self._consecutive_fails >= conf['trailing']['cooldown_fails']:
                logging.info('%s %s cooling down' % (self.inst(), 'tailing'))
                self._cooldown = ms_time() + (period2ms[conf['indicator']['period']] * 1000)
                self._consecutive_fails = 0

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


def stop_loss(inst: str, avg_px: float, factor: int, pos_side: str) -> float:
    conf = trade(inst)['trailing']
    sl_rate = mlt(conf['range'], factor)
    return mlt(avg_px, add(1.0, sl_rate if pos_side == 'short' else -sl_rate))


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
