from statistics import mean

from martin.strategy.core import Strategy
from okx.v5.consts import POS_SIDE_SHORT

CLOSE_PX_INDEX = 4


class SimpleMAStrategy(Strategy):

    def __init__(self, duration=10, pos_side=POS_SIDE_SHORT):
        Strategy.__init__(self)
        self._duration = duration
        self._pos_side = pos_side
        self._valid_duration()

    def can_execute(self, px: str, data) -> bool:
        if not data or len(data) < self._duration:
            return False

        raw = [float(data[i][CLOSE_PX_INDEX]) for i in range(1, self._duration + 1)]
        avg = mean(raw)
        print(raw, avg, px)
        if self._pos_side == POS_SIDE_SHORT:
            return avg > float(px)
        return avg < float(px)

    def duration(self) -> int:
        return self._duration

    def _valid_duration(self):
        if self._duration <= 0:
            raise ValueError('MA index duration recommend greater than 5 due to the precision of the market forcasting')



