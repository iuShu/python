import time
import traceback

from martin.mo import MartinOrder
from martin.strategy.simple import SimpleMAStrategy
from core.utils import sub
from config.api_config import conf

from okx.v5.subscriber import Subscriber
from okx.v5.account import Account
from okx.v5.utils import log, check_resp
from okx.v5.consts import *


START_POS_NUM = 10          # equals to 0.01 BTC
FOLLOW_PX_GAP = 10          # 10 USDT
ENSURE_MAX_COUNT = 30       # max order state ensuring count
ENSURE_INTERVAL = 1000      # millisecond


class MartinAutoBot(Subscriber):

    def __init__(self, inst_id: str, bar=BAR_1M):
        Subscriber.__init__(self)
        self._client = self._init_client()
        self._inst_id = inst_id
        self._last_px = None
        self._order = None
        self._bar = bar
        self._strategy = SimpleMAStrategy(self._client, self._bar)
        self.subscribe('tickers', self._inst_id)
        self.subscribe('candle' + self._bar, self._inst_id)

    def _handle(self, channel: str, inst_id: str, data):
        if not self.is_running():
            log.warning('bot already stop')
            return

        # TODO check whether the program running time would affect the speed of data handling

        # handle candle data
        if channel.startswith('candle'):
            self._strategy.feed(data)
            return

        # handle tickers data
        try:
            self._detect_last_px(data)
            if self._order:
                self._trace()
            else:
                self._initial()
        except Exception:
            traceback.print_exc()
            log.error('handle data error')
            self.stop()

    def _initial(self):
        if not self._strategy.can_execute(self._last_px):
            log.info('[initial] not a good point')
            return

        order = MartinOrder(START_POS_NUM)
        if not self._place_order(order, SIDE_SELL, ORDER_TYPE_MARKET):
            self.stop()

    def _trace(self):
        if not self._order or self._order.state != STATE_FILLED:
            log.fatal('[trace-%d] illegal order %s', self._order.index(), self._order)
            self.stop()
            return

        profit_price = self._order.profit_price()
        follow_price = self._order.follow_price()
        px_gap = abs(sub(self._last_px, follow_price))
        if px_gap <= 10:
            log.info('[trace] prepare to place next order for order-%d', self._order.index())
            nxt = self._order.create_next()
            if not self._place_order(nxt, SIDE_SELL, ORDER_TYPE_LIMIT, px=str(nxt.px)):
                self.stop()
            if nxt.index() == nxt.max_order():
                log.info('[trace] it\'s the last order, calm down and good lucky.')
                self.stop()
        elif (self._order.pos_side == POS_SIDE_SHORT and self._last_px <= profit_price) or \
                (self._order.pos_side == POS_SIDE_LONG and self._last_px >= profit_price):
            log.info('[trace] active algos and remove all pos')
            log.info('[trace] ♥♥♥♥♥♥♥♥♥♥♥♥ Winner-%d ♥♥♥♥♥♥♥♥♥♥♥♥', self._order.index())
            self._order = None
            self.stop()     # for testing
        else:
            log.info('[trace] continue %f %f', profit_price, follow_price)

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
        if not self._ensure_order(order):
            return False
        if not self._follow_algos():
            return False
        return self._add_margin_balance()

    def stop(self):
        self._order = None
        log.info('[stop] stop bot')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        self.shutdown()

    def _ensure_order(self, order: MartinOrder) -> bool:
        for i in range(ENSURE_MAX_COUNT):
            res = self._client.get_order_info(inst_id=self._inst_id, ord_id=order.ord_id)
            data = check_resp(res)
            if not data:
                log.error('[ensure] %d order info request error %s', i+1, res)
                if i+1 != ENSURE_MAX_COUNT:
                    time.sleep(ENSURE_INTERVAL / 1000)
                continue

            state = data['state']
            if state == STATE_FILLED:
                order.state = state
                order.px = float(data['fillPx'])
                order.ctime = data['cTime']
                order.utime = data['uTime']
                self._order = order
                log.info('[ensure] %d filled order %s', i+1, self._order)
                return True
            elif state == STATE_CANCELED:
                log.info('[ensure] %d order was canceled due to unknown reason, stop the bot', i+1)
                log.info('[ensure] %d canceled order %s', i+1, order)
                return False
            elif i+1 != ENSURE_MAX_COUNT:
                log.info('[ensure] %d/%d waiting order be filled', i+1, ENSURE_MAX_COUNT)
                time.sleep(ENSURE_INTERVAL / 1000)

        log.info('[ensure] order still not be filled, canceled order and stop the bot')
        res = self._client.cancel_order(inst_id=self._inst_id, ord_id=order.ord_id)
        data = check_resp(res)
        if data and data['ordId'] == order.ord_id:
            log.info('[ensure] canceled order success %s', order)
            return True
        log.error('[ensure] canceled order error %s', res)
        return False

    def _follow_algos(self) -> bool:
        if not self._order or self._order.state != STATE_FILLED:
            log.fatal('[follow] illegal order %s', self._order)
            return False

        tpx = str(self._order.profit_price())
        spx = str(self._order.stop_loss_price())
        full_pos = str(self._order.full_pos())
        side = SIDE_BUY if self._order.pos_side == POS_SIDE_SHORT else SIDE_SELL
        algo = self._client.create_algo_oco(inst_id=self._inst_id, td_mode=self._order.pos_type,
                                            algo_type=ALGO_TYPE_OCO, side=side, sz=full_pos,
                                            tp_tri_px=tpx, sl_tri_px=spx, pos_side=self._order.pos_side)
        res = self._client.place_algo_oco(algo)
        data = check_resp(res)
        if not data:
            log.error('[follow] place algo resp error %s', res)
            log.error('[follow] error at place algo %s', self._order)
            return False
        log.info('[follow] algo order placed with tp-%s sl-%s fpos-%s', tpx, spx, full_pos)
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
        return True

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
        log.info('[update] px %f', self._last_px)

    @staticmethod
    def _init_client():
        c = conf('okx')
        return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'], test=True)


if __name__ == '__main__':
    bot = MartinAutoBot(INST_BTC_USDT_SWAP)
    bot.startup()



