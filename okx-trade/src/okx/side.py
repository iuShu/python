from mtbot.okx.consts import POS_SIDE_SHORT, POS_SIDE_LONG


class _Side:

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def is_profit(self, px: float, lpx: float):
        pass

    def is_loss(self, px: float, lpx: float):
        pass


class ShortSide(_Side):

    def __init__(self):
        _Side.__init__(self, POS_SIDE_SHORT)

    def is_profit(self, px: float, lpx: float):
        return px > lpx

    def is_loss(self, px: float, lpx: float):
        return px < lpx


class LongSide(_Side):

    def __init__(self):
        _Side.__init__(self, POS_SIDE_LONG)

    def is_profit(self, px: float, lpx: float):
        return px < lpx

    def is_loss(self, px: float, lpx: float):
        return px > lpx
