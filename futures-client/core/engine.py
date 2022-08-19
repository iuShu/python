from concurrent.futures import ThreadPoolExecutor

from config.api_config import conf
from okx.v5 import stream
from okx.v5.subscriber import Subscriber
from okx.v5.account import Account

from logger import log


class SubscriberEngine(Subscriber):

    def __init__(self):
        Subscriber.__init__(self)
        self._engines = []
        self._client = self._init_client()
        self._channels = dict()
        self._thread_pool = None

    def subscribe(self, channel: str, inst_id: str):
        raise NotImplementedError('deprecated method')

    def _handle(self, channel: str, inst_id: str, data):
        raise NotImplementedError('deprecated method')

    def add_engine(self, engine):
        if not hasattr(engine, '_handle'):
            raise TypeError('illegal engine object')
        engine._client = self._client
        self._subscribe_channel(engine)
        self._engines.append(engine)

    def startup(self):
        if not self._engines:
            raise ValueError('no engine to startup')
        if self._running:
            log.warning('already in running')
            return
        self._thread_pool = ThreadPoolExecutor(max_workers=len(self._engines))
        stream.register(self)
        self._running = True
        stream.startup()

    def shutdown(self):
        if not self._running:
            log.warning('not in running')
            return
        self._running = False
        stream.shutdown()

    def on_data(self, resp):
        if 'arg' not in resp or 'data' not in resp:
            log.warning('unknown recv data')
            return
        arg = resp['arg']
        key = self._channel_key(arg['channel'], arg['instId'])
        engines = self._channels.get(key)
        if not engines:
            return
        for e in engines:
            self._thread_pool.submit(self._exec, (e, resp))

    @staticmethod
    def _exec(engine, resp):
        arg = resp['arg']
        engine.handle(arg['channel'], arg['instId'], resp['data'])

    def _subscribe_channel(self, engine):
        cis = engine.channels()
        if not cis:
            raise ValueError('an engine must subscribe at least ONE channel')
        for ci in cis:
            key = self._channel_key(*ci)
            engines: list = self._channels.get(key)
            if not engines:
                engines = list()
                self._channels[key] = engines
            engines.append(engine)

    @staticmethod
    def _init_client():
        c = conf('okx')
        return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'], test=True)


class Engine:

    def __init__(self):
        self._client = None

    def channels(self) -> list:
        # [('tickers', 'BTC-USDT-SWAP'), ('candle1m', 'BTC-USDT-SWAP')]
        pass

    def handle(self, channel: str, inst_id: str, data):
        pass
