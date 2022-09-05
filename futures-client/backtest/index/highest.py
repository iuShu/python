from backtest.index import DataIndex, ftime


class Highest(DataIndex):

    def __init__(self):
        DataIndex.__init__(self, 'highest price')

    def feed(self, data):
        high = float(data[2])
        if self.val == 0 or self.val < high:
            self.ts = int(data[0].timestamp())
            self.val = high
            return

    def __str__(self) -> str:
        return f'{self.name} {self.val} at {ftime(self.ts)}'


