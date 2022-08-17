from statistics import mean
from logger import log
from martin.strategy.core import Strategy
from okx.v5.consts import POS_SIDE_SHORT, INST_BTC_USDT_SWAP
from okx.v5.utils import check_resp

CLOSE_PX_INDEX = 4
MAX_REPO_TIMES = 5
BAR_INTERVAL = {
    '1m': 60,
    '15m': 60 * 15,
    '30m': 60 * 30
}


class SimpleMAStrategy(Strategy):

    def __init__(self, client, bar: str, duration=10, pos_side=POS_SIDE_SHORT):
        Strategy.__init__(self)
        self._duration = duration
        self._bar = bar
        self._pos_side = pos_side
        self._valid_duration()
        self._client = client

        self._repo = []
        self._ts = 0
        self._d = []

    def feed(self, data):
        self._prepare()
        for d in data:
            ts = int(d[0])
            if not self._ts:
                self._valid_data(ts)
            if ts > self._ts and self._ts:
                self._repo.append(self._d)
                if len(self._repo) > (MAX_REPO_TIMES * self._duration):
                    self._repo.pop(0)
            self._ts = ts
            self._d = d

    def can_execute(self, px: float) -> bool:
        if len(self._repo) < self._duration:
            return False

        close_pxs = [float(r[4]) for r in self._repo[-self._duration:]]
        avg = mean(close_pxs)
        log.debug('[strategy] %f %f %s', avg, px, close_pxs)
        if self._pos_side == POS_SIDE_SHORT:
            return avg > px
        return avg < px

    def duration(self) -> int:
        return self._duration

    def _valid_duration(self):
        if self._duration <= 0:
            raise ValueError('MA index duration recommend greater than 5 due to the precision of the market forcasting')

    def _prepare(self):
        if self._repo:
            return

        resp = self._client.get_candles(inst_id=INST_BTC_USDT_SWAP, bar=self._bar, limit=str(self._duration + 5))
        data = check_resp(resp, True)
        if not data:
            log.error('[strategy] get candle request error: %s', resp)
            log.error('[strategy] waiting websocket feeding market data')
            return

        for d in data:
            self._repo.insert(0, d)
        self._repo.pop(-1)  # remove incomplete latest data
        log.info('[strategy] prepared candle data %d', len(self._repo))

    def _valid_data(self, ts: int):
        last_ts = int(self._repo[-1][0])
        interval = BAR_INTERVAL[self._bar]
        if ts > last_ts and ((ts - last_ts) / 1000) == interval:
            return
        self._repo.clear()  # old data
