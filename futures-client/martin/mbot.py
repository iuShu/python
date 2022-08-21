import copy
import logging
import time

from logger import log

from martin.mo import MartinOrder
from martin.strategy.simple import SimpleMAStrategy
from core.utils import sub
from config.api_config import conf

from okx.v5.subscriber import Subscriber
from okx.v5.account import Account
from okx.v5.utils import check_resp
from okx.v5.consts import *


START_POS_NUM = 10          # equals to 0.01 BTC
FOLLOW_PX_GAP = 10          # 10 USDT
CONFIRM_INTERVAL = 2        # second


class MartinAutoBot(Subscriber):

    def __init__(self, inst_id: str, bar=BAR_1M):
        Subscriber.__init__(self)
        self._client = self._init_client()
        self._inst_id = inst_id
        self._last_px = None
        self._order = None
        self._pending = None
        self._bar = bar
        self._strategy = SimpleMAStrategy(self._client, self._bar)
        self.subscribe('tickers', self._inst_id)
        self.subscribe('candle' + self._bar, self._inst_id)
        self._next_confirm = 0

    def _handle(self, channel: str, inst_id: str, data):
        if not self.is_running():
            log.warning('bot already stop')
            return

        # handle candle data
        if channel.startswith('candle'):
            self._strategy.feed(data)
            return

        try:
            self._detect_last_px(data)

            if self._order:
                self._trace()
            elif not self._pending:
                self._initial()

            if not self._pending:
                return
            if self._next_confirm == 0 or int(time.time()) - self._next_confirm >= 0:
                self._confirm()
                self._next_confirm = int(time.time()) + CONFIRM_INTERVAL
        except Exception:
            log.error('handle data error', exc_info=True)
            self.stop()

    def _initial(self):
        if not self._strategy.can_execute(self._last_px):
            log.debug('[initial] not a good point')
            return

        order = MartinOrder(START_POS_NUM)
        if not self._place_order(order, SIDE_SELL, ORDER_TYPE_MARKET):
            self.stop()

    def _confirm(self):
        res = self._client.get_order_info(inst_id=self._inst_id, ord_id=self._pending.ord_id)
        data = check_resp(res)
        if not data:
            log.error('[confirm] order info request error %s', res)
            return

        state = data['state']
        if state == STATE_FILLED:
            self._pending.state = state
            self._pending.px = float(data['fillPx'])
            self._pending.ctime = data['cTime']
            self._pending.utime = data['uTime']
            self._order = copy.deepcopy(self._pending)
            self._pending = None
            log.info('[confirm] order has been filled (%s)', self._order)
        elif state == STATE_CANCELED:
            log.info('[confirm] canceled order (%s)', self._pending)
            log.info('[confirm] order has been canceled due to unknown reason, stop the bot')
            if not self._order:
                self.stop()         # first order has been canceled
            # what if the follow order being canceled
            return
        else:
            log.info('[confirm] waiting ')
            return

        if not self._follow_algos():
            self.stop()
            return

        if not self._add_margin_balance():
            self.stop()
            return

    def _trace(self):
        if not self._order or self._order.state != STATE_FILLED:
            log.fatal('[trace] illegal order %s', self._order)
            self.stop()
            return

        profit_price = self._order.profit_price()
        follow_price = self._order.follow_price()
        px_gap = abs(sub(self._last_px, follow_price))
        if px_gap <= FOLLOW_PX_GAP:
            if self._pending:   # follow order already placed
                return

            log.info('[trace] place next for ord-%d at px-%f', self._order.index(), follow_price)
            nxt = self._order.create_next()
            if not self._place_order(nxt, SIDE_SELL, ORDER_TYPE_LIMIT, px=str(nxt.px)):
                self.stop()
            if nxt.index() == nxt.max_order():
                log.info('[trace] it\'s the last order, calm down and good lucky.')
                self.stop()
                # TODO stop directly ?
        elif px_gap > (FOLLOW_PX_GAP * 2) and self._pending:
            self._cancel_pending()
        elif (self._order.pos_side == POS_SIDE_SHORT and self._last_px <= profit_price) or \
                (self._order.pos_side == POS_SIDE_LONG and self._last_px >= profit_price):
            log.info('[trace] active algos and remove all pos')
            log.info('[trace] ♥♥♥♥♥♥♥♥♥♥♥♥ Winner-%d ♥♥♥♥♥♥♥♥♥♥♥♥', self._order.index())
            self._close_all()       # close all position (prevent the algo order not be filled)
            # TODO cold down strategy ?
        else:
            log.debug('[trace] continue %f %f', profit_price, follow_price)

    def _place_order(self, order: MartinOrder, side: str, ord_type: str, px=''):
        o = self._client.create_order(inst_id=self._inst_id, td_mode=order.pos_type, side=side, pos_side=order.pos_side,
                                      ord_type=ord_type, sz=str(order.pos), px=px)
        res = self._client.place_order(o)
        data = check_resp(res)
        if not data:
            log.error('[place] place order resp error %s', res)
            log.error('[place] error at place order %s', order)
            return False

        order.ord_id = data['ordId']
        order.state = STATE_LIVE
        log.info('[place] placed an market-price order with pos-%d', order.pos)
        self._pending = order
        return True

    def _follow_algos(self) -> bool:
        if not self._order or self._order.state != STATE_FILLED:
            log.fatal('[follow] illegal order %s', self._order)
            return False

        prev = self._order.prev
        if prev:    # cancel previous algo order
            res = self._client.cancel_algo_oco(self._inst_id, algo_ids=[prev.algo_id])
            data = check_resp(res)
            if not data:
                log.error('[follow] error at cancel previous algo-%d', prev.index())
                return False
            log.info('[follow] cancel previous algo with tp-%f sl-%f', prev.profit_price(), prev.stop_loss_price())

        tpx = str(self._order.profit_price())
        spx = str(self._order.stop_loss_price())
        full_pos = str(self._order.full_pos())
        side = SIDE_BUY if self._order.pos_side == POS_SIDE_SHORT else SIDE_SELL
        algo = self._client.create_algo_oco(inst_id=self._inst_id, td_mode=self._order.pos_type,
                                            algo_type=ALGO_TYPE_OCO, side=side, sz=full_pos,
                                            tp_tri_px=tpx, sl_tri_px=spx, pos_side=self._order.pos_side)
        log.info('[follow] prepare algo: ', algo)
        res = self._client.place_algo_oco(algo)
        data = check_resp(res)
        if not data:
            log.error('[follow] place algo resp error %s', res)
            log.error('[follow] error at place algo tp-%s sl-%s fp-%s', tpx, spx, full_pos)
            return False
        log.info('[follow] algo order placed with tp-%s sl-%s fp-%s', tpx, spx, full_pos)
        self._order.algo_id = data['algoId']
        return True

    def _add_margin_balance(self) -> bool:
        emb = self._order.extra_margin_balance()
        if not emb:
            log.info('[balance] enough margin balance')
            return True

        res = self._client.margin_balance(inst_id=self._inst_id, pos_side=self._order.pos_side,
                                          _type=MARGIN_BALANCE_ADD, amt=str(emb))
        data = check_resp(res)
        if not data or data['instId'] != self._inst_id:
            log.error('[balance] adjust margin balance error %s', res)
            return False
        log.info('[balance] added extra margin balance %f', emb)
        return True

    def _cancel_pending(self):
        res = self._client.cancel_order(inst_id=self._inst_id, ord_id=self._pending.ord_id)
        data = check_resp(res)
        if not data:
            log.error('[cancel] error at cancel pending order (%s)', self._pending)
        else:
            log.info('[cancel] cancel pending order %s', self._pending.ord_id)
            self._pending = None

    def _close_all(self):
        res = self._client.close_position(inst_id=self._inst_id, pos_side=self._order.pos_side,
                                          mgn_mode=self._order.pos_type, auto_cancel=True)
        data = check_resp(res)
        if data:
            log.info('[close] close all position at %f', self._last_px)
        else:
            log.warning('[close] close pos failed: %s', res)
            if self._pending:
                res = self._client.cancel_order(inst_id=self._inst_id, ord_id=self._pending.ord_id)
                data = check_resp(res)
                if data and data['ordId'] == self._pending.ord_id:
                    log.info('[close] canceled order success (%s)', self._pending)
                else:
                    log.error('[close] close order failed: %s', res)
                    self.stop()     # unknown order state, human check
                    return

        self._order = None          # start next
        self._pending = None        # clear unfilled order
        log.info('[trace] Let\'s go next')

    def stop(self):
        self._order = None
        log.info('[stop] stop bot')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        self.shutdown()

    def _detect_last_px(self, data):
        if not data:
            self._last_px = None
            return
        px, ts = .0, 0
        for d in data:
            t = int(d['ts'])
            if t > ts:
                px = float(d['last'])
        self._last_px = px
        log.debug('px %f', self._last_px)

    @staticmethod
    def _init_client():
        c = conf('okx')
        return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'], test=True)


if __name__ == '__main__':
    log.setLevel(logging.INFO)
    bot = MartinAutoBot(INST_BTC_USDT_SWAP)
    bot.startup()

