from backtest.index import DataIndex, ftime, duration
from core.utils import sub, mlt, div


class LongTrend(DataIndex):

    def __init__(self):
        DataIndex.__init__(self, 'long trend')
        self._min = 0
        self._max = 0
        self._serial = []

        self._minutes = 0
        self._duration = ()
        self._fluctuate = ()
        self._rate = .0

        self._longest_trend = 0
        self._longest_duration = ()
        self._longest_fluctuate = ()
        self._longest_rate = .0

    def feed(self, data):
        _open, close = float(data[1]), float(data[4])
        if _open < close:
            if self._min == 0:
                self._min = _open
            if self._max == 0 or self._max < close:
                self._max = close
            li = list(data)
            li[0] = int(data[0].timestamp())
            self._serial.append(li)
        else:
            if self._min == 0 or self._max == 0:
                return
            if self._min > close:
                self.calc_round()

    def calc_round(self):
        o, c = float(self._serial[0][1]), float(self._serial[-1][4])
        rate = mlt(div(sub(c, o), o), 100.0)
        dur = duration(self._serial[0][0], self._serial[-1][0])
        if rate > self._rate:
            self._rate = rate
            self._minutes = dur
            self._duration = (ftime(self._serial[0][0]), ftime(self._serial[-1][0]))
            self._fluctuate = (self._serial[0][1], self._serial[-1][4])

        if self._longest_trend == 0 or self._longest_trend < dur:
            self._longest_rate = rate
            self._longest_trend = dur
            self._longest_duration = (ftime(self._serial[0][0]), ftime(self._serial[-1][0]))
            self._longest_fluctuate = (self._serial[0][1], self._serial[-1][4])

        self._min = 0
        self._max = 0
        self._serial.clear()

    def __str__(self) -> str:
        if self._minutes == 0:
            self.calc_round()
        return f'{self.name} rate {self._rate} in {self._minutes} minutes ' \
               f'from {self._fluctuate[0]}({self._duration[0]}) ' \
               f'to {self._fluctuate[1]}({self._duration[1]})\n' \
               f'{self.name} longest {self._longest_rate} in {self._longest_trend} minutes ' \
               f'from {self._longest_fluctuate[0]}({self._longest_duration[0]}) ' \
               f'to {self._longest_fluctuate[1]}({self._longest_duration[1]})'


