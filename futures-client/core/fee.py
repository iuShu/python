from core.position import Position
from core.utils import Computable


class Fee:

    def __init__(self, fee_rate: float):
        self._fee_rate = Computable(fee_rate)

    def fee(self, pos: Position) -> float:
        if not pos:
            raise ValueError('pos is None')
        total_value = pos.price() * Computable(pos.pos())
        return Computable(total_value) * self._fee_rate


class MakerFee(Fee):

    def __init__(self, fee_rate: float):
        Fee.__init__(self, fee_rate)


class TakerFee(Fee):

    def __init__(self, fee_rate: float):
        Fee.__init__(self, fee_rate)


if __name__ == '__main__':
    print(MakerFee(.0005).fee(2300))
    print(TakerFee(.0004).fee(2300))
