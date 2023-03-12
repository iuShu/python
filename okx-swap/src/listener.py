import logging
from abc import ABCMeta, abstractmethod
from src.config import sys, trade
from src.core.shadow.martin import Martin
from src.core.shadow.trailing import Trailing


class Listener(metaclass=ABCMeta):

    @abstractmethod
    def inst(self) -> str:
        pass

    @abstractmethod
    def inst_id(self) -> str:
        pass

    @abstractmethod
    def inst_type(self) -> str:
        pass

    @abstractmethod
    def owner(self, owner):
        pass

    @abstractmethod
    def channel(self) -> str:
        pass

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def consumable(self, data: dict) -> bool:
        pass

    @abstractmethod
    async def consume(self, data: dict):
        pass

    @abstractmethod
    def switch_strategy(self, strategy: str):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def finish_stop(self, fs=True):
        pass

    @abstractmethod
    def is_stop(self):
        pass

    @abstractmethod
    def is_finish_stop(self):
        pass


class ZeroListener(Listener, metaclass=ABCMeta):

    def __init__(self, inst: str, inst_id: str, inst_type: str):
        self._inst = inst
        self._inst_id = inst_id
        self._inst_type = inst_type

        self.client = None
        self.msg_id = ''

    def inst(self) -> str:
        return self._inst

    def inst_id(self) -> str:
        return self._inst_id

    def inst_type(self) -> str:
        return self._inst_type

    def owner(self, client):
        self.client = client

    def consumable(self, data: dict) -> bool:
        msg_id = data.get('id')
        if msg_id == self.msg_id:
            return True

        if 'data' not in data:
            return False

        arg = data.get('arg')
        if not arg:
            return False
        if arg['instId'] != self.inst_id():
            return False
        if arg['channel'] != self.channel():
            return False
        return True

    def switch_strategy(self, strategy: str):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def finish_stop(self, fs=True):
        pass

    def is_stop(self):
        return False

    def is_finish_stop(self):
        return False


class InstListener(ZeroListener):

    def __init__(self, inst: str, inst_id: str, inst_type: str, indicator):
        ZeroListener.__init__(self, inst, inst_id, inst_type)

        self._strategy = ''
        self._trading = None
        self._switch = None

        self._martin = None
        self._trailing = None

        self._finish_stop = True
        self._stop = True

        for stg in sys('strategies'):
            if stg == 'martin':
                self._martin = Martin(inst, indicator)
            elif stg == 'trailing':
                self._trailing = Trailing(inst, indicator)

    def channel(self) -> str:
        return "tickers"

    def prepare(self):
        stg = trade(self.inst())['strategy']
        self._trading = self._get(stg)
        self._strategy = stg
        self._stop = False
        self._finish_stop = False
        logging.info("%s inst using %s strategy" % (self.inst(), stg))

    async def consume(self, data: dict):
        if self._trading.is_stop():
            if self._finish_stop:
                self._stop = True
                logging.info("%s stop at finish" % self.inst())
                return
            if self._switch:
                logging.info("switch strategy from %s to %s" % (self._strategy, self._switch[1]))
                self._trading = self._switch[0]
                self._strategy = self._switch[1]
                self._switch = None

        if self._trading:
            await self._trading.handle(data)

    def switch_strategy(self, strategy: str):
        if self._stop or self._strategy == strategy:
            return

        if not trade(self.inst()).get(strategy):
            logging.error("%s did not config the %s strategy" % (self.inst(), strategy))
            return

        self._trading.finish_stop()
        nxt = self._get(strategy)
        self._switch = nxt, strategy
        nxt.prepare()

    def start(self):
        if self._stop and self._finish_stop:
            self.prepare()
            self._trading.prepare()

    def stop(self):
        self._stop = True
        self._finish_stop = True
        self._trading.stop()

    def finish_stop(self, fs=True):
        self._finish_stop = fs
        self._trading.finish_stop(fs)

    def is_stop(self):
        return self._stop

    def is_finish_stop(self):
        return self._finish_stop

    def _get(self, strategy: str):
        if strategy == 'martin':
            return self._martin
        elif strategy == 'trailing':
            return self._trailing
        return None
