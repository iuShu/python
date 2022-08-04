from core.utils import *

LAST_PRICE = 'last'
INDEX_PRICE = 'index'
MARK_PRICE = 'mark'


class Price(Computable):

    def __init__(self, price: float, price_type: str):
        Computable.__init__(self, price)
        self._type = price_type

    def price(self, price=None):
        if not price:
            return self.val()
        self.val(price)
        return self

    def price_type(self, price_type=None):
        if not price_type:
            return self._type
        self._type = price_type
        return self

    def __str__(self):
        return f'{self.val()} {self._type}'


class LastPrice(Price):

    def __init__(self, price=.0):
        Price.__init__(self, price, LAST_PRICE)


class IndexPrice(Price):

    def __init__(self, price=.0):
        Price.__init__(self, price, INDEX_PRICE)


class MarkPrice(Price):

    def __init__(self, price=.0):
        Price.__init__(self, price, MARK_PRICE)


if __name__ == '__main__':
    total = LastPrice(.45) + LastPrice(.4)
    print(total)

