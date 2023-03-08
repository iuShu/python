from abc import ABCMeta, abstractmethod
from src.notifier import notifier


class Strategy(metaclass=ABCMeta):

    @abstractmethod
    def inst(self):
        pass

    @abstractmethod
    def indicator(self):
        pass

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    async def handle(self, data):
        pass

    @abstractmethod
    def finish_stop(self, fs=True):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def is_stop(self) -> bool:
        pass


class DefaultStrategy(Strategy, metaclass=ABCMeta):

    def __init__(self, inst: str, indicator):
        self._inst = inst
        self._indicator = indicator

        self.finished_stop = False
        self.stopped = False

    def inst(self):
        return self._inst

    def indicator(self):
        return self._indicator

    def prepare(self):
        self.finished_stop = False
        self.stopped = False

    def finish_stop(self, fs=True):
        self.finished_stop = fs

    def stop(self):
        self.stopped = True
        self.finished_stop = True
        notifier.trade_stop(f'{self.inst()} stop trade')

    def is_stop(self) -> bool:
        return self.stopped
