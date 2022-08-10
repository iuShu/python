import time
import traceback

from martin.mo import MartinOrder
from core.utils import sub
from config.api_config import conf

from okx.v5.handler import Handler
from okx.v5.account import Account
from okx.v5.stream import register, _shutdown_signal, startup
from okx.v5.utils import log, check_resp
from okx.v5.consts import *


START_POS_NUM = 10          # equals to 0.01 BTC
FOLLOW_PX_GAP = 10          # 10 USDT
ENSURE_MAX_COUNT = 30       # max order state ensuring count
ENSURE_INTERVAL = 1000      # millisecond


class MartinAutoBot(Handler):

    def __init__(self, channel: str, inst_id: str):
        Handler.__init__(self, channel, inst_id)
        self._client = self._init_client()
        self._last_px = None
        self._order = None
        self._stop = False
        self._strategy = None

    def _handle(self, data):
        if self._stop:
            log.warning('bot already stop')
            return

        # TODO check whether the program running time would affect the speed of data handling

        self._detect_last_px(data)
        if self._order:
            self._safe_code(self._trace())
        else:
            self._safe_code(self._initial())

    def _initial(self):
        order = MartinOrder(START_POS_NUM)
        if not self._place_order(order, ORDER_TYPE_MARKET):
            self.stop()

    def _trace(self):
        if not self._last_px:
            log.error('[trace-%d] last price is %s', self._order.index(), self._last_px)
            self.stop()
            return
        if not self._order or self._order.state != STATE_FILLED:
            log.fatal('[trace-%d] illegal order %s', self._order.index(), self._order)
            self.stop()
            return

        follow_price = self._order.follow_price()
        px_gap = abs(sub(self._last_px, follow_price))
        if px_gap > FOLLOW_PX_GAP:
            log.info('[trace] continue')
            return

        log.info('[trace-%d] prepare to place next order', self._order.index())
        nxt = self._order.create_next()
        if not self._place_order(nxt, ORDER_TYPE_LIMIT, px=str(nxt.px)):
            self.stop()
        if nxt.index() == nxt.max_order():
            log.info('[trace] we need to stop, hope you lucky.')
            self.stop()

    def _place_order(self, order: MartinOrder, ord_type: str, px=''):
        o = self._client.create_order(inst_id=self.inst_id(), td_mode=order.pos_type, side=order.pos_side,
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
        return self._follow_algos()

    def run(self):
        self._stop = False
        register(self)
        startup()

    def stop(self):
        log.info('[stop] stop bot')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        log.fatal('!!! CHECK ORDER AT PC/APP OKX !!!')
        self._stop = True
        self._order = None
        _shutdown_signal()

    def _ensure_order(self, order: MartinOrder) -> bool:
        for i in range(ENSURE_MAX_COUNT):
            res = self._client.get_order_info(inst_id=self.inst_id(), ord_id=order.ord_id)
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
                log.info('[ensure] %d order filled %s', i+1, self._order)
                return True
            elif state == STATE_CANCELED:
                log.info('[ensure] %d order was canceled due to unknown reason, stop the bot', i+1)
                log.info('[ensure] %d canceled order %s', i+1, order)
                return False
            elif i+1 != ENSURE_MAX_COUNT:
                time.sleep(ENSURE_INTERVAL / 1000)

        log.info('[ensure] order still not be filled, canceled order and stop the bot')
        res = self._client.cancel_order(inst_id=self.inst_id(), ord_id=order.ord_id)
        data = check_resp(res)
        if data:
            log.info('[ensure] canceled order success %s', order)
            return True
        return False

    def _follow_algos(self) -> bool:
        if not self._order or self._order.state != STATE_FILLED:
            log.fatal('[follow] illegal order %s', self._order)
            return False

        tpx = str(self._order.profit_price())
        spx = str(self._order.stop_loss_price())
        algo = self._client.create_algo_oco(inst_id=self.inst_id(), td_mode=self._order.pos_type,
                                            algo_type=ALGO_TYPE_OCO, side=self._order.pos_side, sz=str(self._order.pos),
                                            tp_tri_px=tpx, sl_tri_px=spx)
        res = self._client.place_algo_oco(algo)
        data = check_resp(res)
        if not data:
            log.error('[follow] place algo resp error %s', res)
            log.error('[follow] error at place algo %s', self._order)
            return False
        return True

    def _safe_code(self, func):
        try:
            func()
        except Exception:
            traceback.print_exc()
            log.fatal('[safe-code] !!! CHECK ORDER !!!')
            self.stop()

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
        return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'])


if __name__ == '__main__':
    sub = TICKERS_BTC_USDT_SWAP[0]
    bot = MartinAutoBot(sub['channel'], sub['instId'])
    bot.run()



