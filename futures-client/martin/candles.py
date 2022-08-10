from statistics import mean

from okx.v5.stream import startup, register
from okx.v5.handler import Handler
from okx.v5.consts import INST_BTC_USDT_SWAP


class CandleHandler(Handler):

    def __init__(self):
        Handler.__init__(self, 'candle1m', INST_BTC_USDT_SWAP)
        self._repo = []
        self._ts = 0
        self._d = []

    def _handle(self, data):
        for d in data:
            ts = int(d[0])
            if ts > self._ts and self._ts:
                self._repo.append(self._d)
                if len(self._repo) > 50:
                    self._repo.pop(0)
                print('candle complete', self._d)
                self._calc_ma()
            self._ts = ts
            self._d = d

    def _calc_ma(self):
        if len(self._repo) < 20:
            return
        close_pxs = [float(r[4]) for r in self._repo[-20:]]
        print('MA5', close_pxs, mean(close_pxs[-5:]))
        print('MA10', close_pxs, mean(close_pxs[-10:]))
        print('MA20', close_pxs, mean(close_pxs))


if __name__ == '__main__':
    register(CandleHandler())
    startup()


