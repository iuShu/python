from core.utils import add, sub, Computable
from core.price import Price

LONG_SIDE = 'long'
SHORT_SIDE = 'short'


class Side:

    def __init__(self, side: str):
        self._side = side

    def profit_price(self, price: Price, rate: float) -> float:
        pass

    def loss_price(self, price: Price, rate: float) -> float:
        pass

    def gt(self, start_price: Price, current_price: Price) -> bool:
        pass

    def lt(self, start_price: Price, current_price: Price) -> bool:
        pass

    def diff(self, start_price: Price, current_price: Price) -> float:
        pass

    def __str__(self):
        return self._side


class LongSide(Side):

    def __init__(self):
        Side.__init__(self, LONG_SIDE)

    def profit_price(self, price: Price, rate: float) -> float:
        if price and rate:
            return price * Computable(add(1.0, rate))

    def loss_price(self, price: Price, rate: float) -> float:
        if price and rate:
            return price * Computable(sub(1.0, rate))

    def gt(self, start_price: Price, current_price: Price) -> bool:
        return start_price.price() > current_price.price()

    def lt(self, start_price: Price, current_price: Price) -> bool:
        return start_price.price() < current_price.price()

    def diff(self, start_price: Price, current_price: Price) -> float:
        return current_price - start_price


class ShortSide(Side):

    def __init__(self):
        Side.__init__(self, SHORT_SIDE)

    def profit_price(self, price: Price, rate: float) -> float:
        if price and rate:
            return price * Computable(sub(1.0, rate))

    def loss_price(self, price: Price, rate: float) -> float:
        if price and rate:
            return price * Computable(add(1.0, rate))

    def gt(self, start_price: Price, current_price: Price) -> bool:
        return start_price.price() < current_price.price()

    def lt(self, start_price: Price, current_price: Price) -> bool:
        return start_price.price() < current_price.price()

    def diff(self, start_price: Price, current_price: Price) -> float:
        return start_price - current_price


if __name__ == '__main__':
    p = LongSide().profit_price(Price(23000, '1'), 0.004)
    print(p)
    p = ShortSide().profit_price(Price(23000, '1'), 0.004)
    print(p)
