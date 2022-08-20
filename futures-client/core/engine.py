import queue
import threading
from concurrent.futures import ThreadPoolExecutor

from config.api_config import conf
from okx.v5 import stream
from okx.v5.subscriber import Subscriber
from okx.v5.account import Account

from logger import log


class SubscriberEngine(Subscriber):

    def __init__(self):
        Subscriber.__init__(self)
        self._client = self._init_client()

    def subscribe(self, channel: str, inst_id: str):
        raise NotImplementedError('deprecated method')

    def _handle(self, channel: str, inst_id: str, data):
        raise NotImplementedError('deprecated method')

    def add_engine(self, engine):
        if not hasattr(engine, 'handle'):
            raise TypeError('illegal engine object')
        engine._client = self._client
        self._subscribe_channel(engine)
        engine.init()

    def remove_engine(self, engine):
        if not hasattr(engine, 'handle'):
            raise TypeError('illegal engine object')
        engine._client = None
        self._unsubscribe_channel(engine)
        if not self._channels:
            log.warning('no active engine, shutdown subscriber')
            self.shutdown()

    def startup(self):
        if not self._channels:
            raise ValueError('no engine to startup')
        if self._running:
            log.warning('already in running')
            return

        for v in self._channels.values():
            for e in v:
                if not e.is_alive():
                    e._running = True
                    e.start()

        self._running = True
        stream.register(self)
        stream.startup()

    def shutdown(self):
        if not self._running:
            log.warning('not in running')
            return

        self._running = False
        stream.shutdown()
        log.info('subscriber shutdown')

    def on_data(self, resp):
        if not self._running:
            log.warning('subscriber shutdown, stop receiving data')
            return

        if 'arg' not in resp or 'data' not in resp:
            log.warning('unknown recv data')
            return
        arg = resp['arg']
        key = self._channel_key(arg['channel'], arg['instId'])
        engines = self._channels.get(key)
        if not engines:
            # TODO unsubscribe cooperated channel
            return
        for e in engines:
            if e.is_running():
                e.add_data(resp)
            else:
                self.remove_engine(e)

    def _subscribe_channel(self, engine):
        cis = engine.channels()
        if not cis:
            raise ValueError('an engine must subscribe at least ONE channel')
        for ci in cis:
            stream.add_channel(*ci)
            key = self._channel_key(*ci)
            engines: list = self._channels.get(key)
            if not engines:
                engines = list()
                self._channels[key] = engines
            engines.append(engine)

    def _unsubscribe_channel(self, engine):
        cis = engine.channels()
        if not cis:
            raise ValueError('an engine must subscribe at least ONE channel')
        for ci in cis:
            key = self._channel_key(*ci)
            engine: list = self._channels.get(key)
            if not engine:
                raise RuntimeError('no such an engine')
            elif len(engine) == 1:
                self._channels.pop(key)
            else:
                engine.remove(engine)

    @staticmethod
    def _init_client():
        c = conf('okx')
        return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'], test=True)


class Engine(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self._client = None
        self._queue = queue.Queue()
        self._running = False

    def init(self):
        pass

    def channels(self) -> list:
        # [('tickers', 'BTC-USDT-SWAP'), ('candle1m', 'BTC-USDT-SWAP')]
        pass

    def add_data(self, data):
        self._queue.put_nowait(data)

    def run(self) -> None:
        while self._running:
            data = self._queue.get(block=True)
            if data:
                arg = data['arg']
                self.handle(arg['channel'], arg['instId'], data['data'])

    def handle(self, channel: str, inst_id: str, data):
        pass

    def is_running(self) -> bool:
        return self._running
