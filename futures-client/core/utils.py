import time
from decimal import Decimal

ROUND_SCALE = 6


class Computable:

    def __init__(self, val):
        self._val = val

    def val(self, value=None):
        if not value:
            return self._val
        self._val = value
        return self

    def __abs__(self):
        return abs(self._val)

    def __add__(self, other):
        return add(self._val, other.val())

    def __sub__(self, other):
        return sub(self._val, other.val())

    def __mul__(self, other):
        return mlt(self._val, other.val())

    def __truediv__(self, other):
        return div(self._val, other.val())

    def __mod__(self, other):
        return mod(self._val, other.val())


def ms_time():
    return int(time.time() * 1000)


def add(f1: float, f2: float) -> float:
    return round(Decimal(f1) + Decimal(f2), ROUND_SCALE)


def sub(f1: float, f2: float) -> float:
    return round(Decimal(f1) - Decimal(f2), ROUND_SCALE)


def mlt(f1: float, f2: float) -> float:
    return round(Decimal(f1) * Decimal(f2), ROUND_SCALE)


def div(f1: float, f2: float) -> float:
    return round(Decimal(f1) / Decimal(f2), ROUND_SCALE)


def mod(f1: float, f2: float) -> float:
    return round(Decimal(f1) % Decimal(f2), ROUND_SCALE)


if __name__ == '__main__':
    # r = add(.01, 22.3)
    # print(r)
    pass
