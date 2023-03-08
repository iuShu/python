import atexit
import logging
import time
from abc import ABCMeta, abstractmethod

from src.calc import add, mlt, div
from src.config import trade, last_ema, save_ema
from src.rest import api
from src.listener import ZeroListener

period2ms = {
    '1m': 60000,
    '2m': 60000 * 2,
    '5m': 60000 * 5,
    '10m': 60000 * 10,
    '15m': 60000 * 15,
    '30m': 60000 * 30,
    '1H': 60000 * 60,
    '4H': 60000 * 60 * 4,
    '1D': 60000 * 60 * 4 * 24,
    '1W': 60000 * 60 * 4 * 24 * 7,
}


class Indicator(metaclass=ABCMeta):

    @abstractmethod
    def trend(self):
        pass


class EmaIndicator(ZeroListener, Indicator):

    def __init__(self, inst: str, inst_id: str, inst_type: str):
        ZeroListener.__init__(self, inst, inst_id, inst_type)
        self._period = '15m'
        self._ema_period = 0.0
        self._ema_last_time = ''
        self._ema_last_val = 0.0

        self._ema = 0.0
        self._history = []
        self._ts = 0

    def channel(self) -> str:
        return 'candle' + self._period

    def prepare(self):
        conf = trade(self._inst)
        inst_id, candle = conf['inst_id'], conf['indicator']
        history = last_ema(inst_id)
        self._period = candle['period']
        self._ema_period = candle['ema_period']
        self._ema_last_val = float(history[1])
        self._ema_last_time = str(int(time.mktime(time.strptime(history[0], '%Y-%m-%d %H:%M:%S'))))

        cache = []
        candle = api.get_candle(inst_id, self._period, limit=100)
        require = True
        for c in candle:    # candle data order: 2023 2022 2021 ...
            if c[0][:-3] == self._ema_last_time:
                require = False
            if require and c[-1] == '1':    # ended candle
                cache.insert(0, (float(c[4]), int(c[0][:-3])))

        if require:
            logging.error('last ema value too old')
            raise SystemExit(1)

        self._ema = self._ema_last_val
        for cpx in cache:
            self._ema = self._calc(cpx[0], self._ema)
            self._history.insert(0, [cpx[0], self._ema, cpx[1]])
        self._ts = cache[-1][1]
        logging.info('%s %s ema is %s' % (self.inst(), self.ts2format(self._ts), self._ema))

        self.register_on_exit()

    async def consume(self, data: dict):
        if len(data['data']) != 1:
            logging.warning('unexpected data %s' % data)

        ticker = data['data'][0]
        if ticker[-1] != '1':   # candle not end
            return

        ts = int(ticker[0][:-3])
        if ts - self._ts != period2ms[self._period]:
            logging.warning('unexpected data %s after %s' % (self.ts2format(ts), self.ts2format(self._ts)))
            return
        if ts <= self._ts:
            return

        cpx = float(ticker[4])
        self._ts = ts
        self._ema = self._calc(cpx, self._ema)
        self._history.insert(0, [cpx, self._ema, ts])
        logging.info('%s %s close=%s ema%d=%s' % (self.inst(), self.ts2format(ts), cpx, self._ema_period, self._ema))

    def trend(self) -> int:
        """
        trend_candles: better be an even number
        :return: 1: long, -1: short, 0: not enough data
        """
        decide = trade(self._inst)['indicator']['trend_candles']
        if len(self._history) < decide:
            return 0

        long, short = 0, 0
        for h in self._history[:decide]:
            long += 1 if h[0] > h[1] else 0
            short += 1 if h[0] <= h[1] else 0
        return 1 if long > short else -1

    def _calc(self, cpx, last=0.0) -> float:
        ema = cpx if last == 0 else last
        t = div(mlt(2, cpx), self._ema_period + 1)
        return add(t, div(mlt(self._ema_period - 1, ema), self._ema_period + 1))

    def register_on_exit(self):
        def delegate():
            ema = self._history[11] if len(self._history) >= 12 else self._history[-1]
            save_ema(self.inst_id(), self.ts2format(ema[2]), ema[1])
        atexit.register(delegate)

    @staticmethod
    def ts2format(ts: int) -> str:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))

    @staticmethod
    def format2ts(t: str) -> int:
        return int(time.mktime(time.strptime(t, '%Y-%m-%d %H:%M:%S')))


if __name__ == '__main__':
    # d = [0.5989, 0.6558, 0.7578, 0.7841, 0.7741, 0.8937, 0.9356, 0.9422, 1.1726, 1.1225,
    # d = [1.0875, 1.0654, 0.9314, 0.8880, 0.9462, 0.9048, 0.9172, 0.9458, 1.0087, 0.9788]
    # for i in d[:3]:
    #     print(i)
    pass
