import logging
from abc import ABCMeta, abstractmethod

import src.core.martin
import src.core.trailing
import src.core.shadow.martin
import src.core.shadow.trailing
from src.config import sys, trade


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
    def stop(self):
        pass

    @abstractmethod
    def finish_stop(self):
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

        self._finish_stop = True
        self._stop = True

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

    def prepare(self):
        self._stop = False
        self._finish_stop = False

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

    def stop(self):
        self._stop = True
        self._finish_stop = True

    def finish_stop(self):
        self._finish_stop = True

    def is_stop(self):
        return self._stop

    def is_finish_stop(self):
        return self._finish_stop


class InstListener(ZeroListener):

    def __init__(self, inst: str, inst_id: str, inst_type: str, indicator):
        ZeroListener.__init__(self, inst, inst_id, inst_type)

        self._strategy = ''
        self._trading = None
        self._switch = None

        self._finish_stop = True
        self._stop = True

        self._indicator = indicator

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
            if self._switch:
                logging.info("switch strategy from %s to %s" % (self._strategy, self._switch[1]))
                self._trading = self._switch[0]
                self._strategy = self._switch[1]
                self._switch = None
            else:
                self._stop = True
                self._indicator.stop()
                logging.info("%s stop at finish" % self.inst())
        else:
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

    def stop(self):
        self._stop = True
        self._finish_stop = True
        self._trading.stop()
        self._indicator.stop()

    def finish_stop(self):
        self._finish_stop = True
        self._trading.finish_stop()

    def is_stop(self):
        return self._stop

    def is_finish_stop(self):
        return self._finish_stop

    def _get(self, strategy: str):
        if strategy == 'martin':
            return src.core.shadow.martin.Martin(self.inst(), self._indicator) if sys('env') == 'shadow' \
                else src.core.martin.Martin(self.inst(), self._indicator)
        elif strategy == 'trailing':
            return src.core.shadow.trailing.Trailing(self.inst(), self._indicator) if sys('env') == 'shadow' \
                else src.core.trailing.Trailing(self.inst(), self._indicator)
        return None
