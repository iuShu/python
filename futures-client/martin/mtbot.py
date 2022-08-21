from logger import log
from core.engine import Engine
from martin.strategy.simple import SimpleMAStrategy
from okx.v5.consts import *


class MartinAutoBot(Engine):

    def __init__(self, inst_id=INST_BTC_USDT_SWAP, inst_type=INST_TYPE_SWAP):
        Engine.__init__(self)
        self._inst_id = inst_id
        self._inst_type = inst_type
        self._bar = BAR_1M

        self._strategy = None
        self._last_px = .0
        self._order = None
        self._pending = None

    def init(self):
        self._strategy = SimpleMAStrategy(self._client, self._bar)

    def channels(self) -> list:
        return [('tickers', INST_BTC_USDT_SWAP),
                ('candle' + self._bar, INST_BTC_USDT_SWAP)]

    def handle(self, channel: str, inst_id: str, data):
        try:
            if channel.startswith('candle'):
                self._strategy.feed(data)
                return

            self._detect_last_px(data)

            if not self._order and not self._pending:
                self._place_first()

            if self._order:
                self._trace()

            if self._pending:
                self._confirm()

        except Exception:
            log.error('handle recv error', exc_info=True)
            self._running = False

    def _place_first(self):
        pass

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
        log.debug('[update] px %f', self._last_px)
