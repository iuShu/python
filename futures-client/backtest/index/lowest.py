from backtest.index import DataIndex, ftime


class Lowest(DataIndex):

    def __init__(self):
        DataIndex.__init__(self, 'lowest price')

    def feed(self, data):
        low = float(data[3])
        if self.val == 0 or self.val > low:
            self.ts = int(data[0].timestamp())
            self.val = low
            return

    def __str__(self) -> str:
        return f'{self.name} {self.val} at {ftime(self.ts)}'


