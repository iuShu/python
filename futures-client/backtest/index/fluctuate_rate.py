from backtest.index import DataIndex, ftime
from core.utils import sub


class FluctuateRate(DataIndex):

    def __init__(self):
        DataIndex.__init__(self, 'fluctuate rate')

    def feed(self, data):
        high, low = float(data[2]), float(data[3])
        diff = sub(high, low)
        if self.val == 0 or self.val < diff:
            self.ts = data[0].timestamp()
            self.val = diff

    def __str__(self) -> str:
        return f'{self.name} {self.val} at {ftime(self.ts)}'


