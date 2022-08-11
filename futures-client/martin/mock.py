import random
import time
import traceback

from okx.v5.subscriber import Subscriber
from okx.v5.account import Account
from okx.v5.consts import *
from okx.v5.utils import log

from config.api_config import conf
from core.utils import sub
from martin.mo import MartinOrder
from martin.strategy.simple import SimpleMAStrategy


class MockAutoBot(Subscriber):

    def __init__(self):
        Subscriber.__init__(self)
        self._client = self._init_client()
        self._last_px = .0
        self._order = None
        self._bar = BAR_1M
        self._strategy = SimpleMAStrategy(self._client, self._bar)
        self.subscribe('tickers', INST_BTC_USDT_SWAP)
        self.subscribe('candle' + self._bar, INST_BTC_USDT_SWAP)

    def _handle(self, channel: str, inst_id: str, data):
        if not self.is_running():
            log.info('[handle] not running')
            return

        try:
            if channel.startswith('candle'):
                self._strategy.feed(data)
                return

            self._detect_last_px(data)
            if self._order:
                self._trace()
            else:
                self._initial()
        except Exception:
            traceback.print_exc()
            self.stop()

    def _initial(self):
        if not self._strategy.can_execute(self._last_px):
            log.info('[initial] not a good point')
            return

        order = MartinOrder(10)
        if not self._place_order(order, ORDER_TYPE_MARKET):
            self.stop()

    def _trace(self):
        if not self._order or self._order.state != STATE_FILLED:
            log.error('[trace] illegal order %s', self._order)
            self.stop()
            return

        profit_price = self._order.profit_price()
        follow_price = self._order.follow_price()
        px_gap = abs(sub(self._last_px, follow_price))
        if px_gap <= 10:
            log.info('[trace] prepare to place next order for order-%d', self._order.index())
            nxt = self._order.create_next()
            if not self._place_order(nxt, ORDER_TYPE_LIMIT, px=str(nxt.px)):
                self.stop()
            if nxt.index() == nxt.max_order():
                log.info('[trace] it\'s the last order, calm down and good lucky.')
                self.stop()
            return
        else:
            log.info('[trace] continue %f %f', profit_price, follow_price)

        if (self._order.pos_side == POS_SIDE_SHORT and self._last_px <= profit_price) or \
                (self._order.pos_side == POS_SIDE_LONG and self._last_px >= profit_price):
            log.info('[trace] active algos and remove all pos')
            log.info('[trace] ♥♥♥♥♥♥♥♥♥♥♥♥ Winner-%d ♥♥♥♥♥♥♥♥♥♥♥♥', self._order.index())
            self._order = None

    def _place_order(self, order, ord_type: str, px=''):
        log.info('[place] order-%d %s %s', order.index(), ord_type, px)
        order.ord_id = random.randrange(100000, 1000000)
        order.state = STATE_LIVE

        log.info('[place] order-%d filled', order.index())
        order.state = STATE_FILLED
        order.px = self._last_px    # mock
        order.ctime = int(time.time())
        order.utime = order.ctime
        self._order = order

        log.info('[place] order-%d follow algos', order.index())
        log.info('[place] order-%d pos-%d tp-%f sl-%f', order.index(), order.pos, order.profit_price(),
                 order.follow_price())
        return True

    def stop(self):
        log.info('[stop] stop the bot')
        self._order = None
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
        log.info('[update] px %f', self._last_px)

    @staticmethod
    def _init_client():
        c = conf('okx')
        return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'])


if __name__ == '__main__':
    bot = MockAutoBot()
    bot.startup()
