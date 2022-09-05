import time


class DataIndex:

    def __init__(self, name: str):
        self._name = name
        self._ts = 0
        self._val = 0

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, val):
        self._val = val

    @property
    def ts(self):
        return self._ts

    @ts.setter
    def ts(self, ts):
        self._ts = ts

    def feed(self, data):
        pass


def ftime(ts: int) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))


def duration(start: int, end: int, dur=60) -> float:
    return (end - start) / dur
