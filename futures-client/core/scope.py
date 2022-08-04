from core.utils import Computable
from core.price import Price
from core.side import Side


class Scope:

    def __init__(self, start_price: Price, side: Side):
        self._start_price = start_price
        self._side = side
        self._rate = .0
        self._price = None

    def rate(self, rate: float):
        if not rate:
            return self._rate
        self._rate = rate
        self._price = Price(self.stop_price(), self._start_price.price_type())
        return self

    def price(self, price: Price):
        pass

    def stop_price(self) -> float:
        pass

    def __str__(self):
        return f'{self.__class__.__name__} {self._rate} {self._price}'


class TakeProfit(Scope):

    def __init__(self, start_price: Price, side: Side):
        Scope.__init__(self, start_price, side)

    def price(self, price: Price):
        if not price:
            return self._price
        if not self._side.gt(self._start_price, price):
            raise ValueError('The take profit price need to greater than the start price.')
        self._price = price
        self._rate = Computable(self._start_price - self._price) / self._start_price
        self._rate = abs(self._rate)
        return self

    def stop_price(self) -> float:
        if self._price:
            return self._price.price()
        return self._side.profit_price(self._start_price, self._rate)


class StopLoss(Scope):

    def __init__(self, start_price: Price, side: Side):
        Scope.__init__(self, start_price, side)

    def price(self, price: Price):
        if not price:
            return self._price
        if not self._side.lt(self._start_price, price):
            raise ValueError('The stop loss price need to less than the start price.')
        self._price = price
        self._rate = Computable(self._start_price - self._price) / self._start_price
        self._rate = abs(self._rate)
        return self

    def stop_price(self) -> float:
        if self._price:
            return self._price.price()
        return self._side.loss_price(self._start_price, self._rate)



