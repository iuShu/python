from core.utils import Computable
from core.price import Price

ISOLATED_POSITION = 'isolated'
CROSS_POSITION = 'cross'


class Position:

    def __init__(self, pos: float, pos_type: str, price: Price, lever: int):
        self._pos = pos
        self._pos_type = pos_type
        self._price = price
        self._lever = lever

    def pos(self, pos=None):
        if not pos:
            return self._pos
        self._pos = pos
        return self

    def lever(self, lever=0):
        if not lever:
            return self._lever
        self._lever = lever
        return self

    def price(self, price=None):
        if not price:
            return self._price
        self._price = price
        return self

    def value(self) -> float:
        total = Computable(self._price * Computable(self._pos))
        return total / Computable(self._lever)

    def __str__(self):
        return f'{self._pos} {self._price} {self._lever} {self.value()}'


class Isolated(Position):

    def __init__(self, pos: float, price: Price, lever=0):
        Position.__init__(self, pos, ISOLATED_POSITION, price, lever)


class Cross(Position):

    def __init__(self, pos: float, price: Price, lever=0):
        Position.__init__(self, pos, CROSS_POSITION, price, lever)
