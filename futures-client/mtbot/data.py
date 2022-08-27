from config.api_config import conf
from mtbot.okx.aioclient import AioClient
from mtbot.setting import *
from mtbot.okx.stream import *


class ValueHolder:

    def __init__(self, value=None):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


TICKERS = 'tickers'
CANDLE = 'candle' + CANDLE_BAR_TYPE

CHANNELS = [
    [TICKERS, INST_BTC_USDT_SWAP],
    [CANDLE, INST_BTC_USDT_SWAP]
]

PIPES = {
    TICKERS: [],
    CANDLE: []
}
STARTED = ValueHolder(False)
RUNNING = ValueHolder(False)

cf = conf(EXCHANGE)
# CLIENT = Account(api_key=cf['apikey'], api_secret_key=cf['secretkey'], passphrase=cf['passphrase'], test=True)
CLIENT = AioClient(apikey=cf['apikey'], secretkey=cf['secretkey'], passphrase=cf['passphrase'], test=True)


class Subscriber:

    @staticmethod
    async def on_data(resp):
        if 'arg' not in resp or 'data' not in resp:
            log.warning('unknown recv data')
            return

        queues: list = PIPES.get(resp['arg']['channel'])
        if queues:
            for queue in queues:
                await queue.put(resp['data'])


async def close():
    RUNNING.value = False
    await CLIENT.close()
    shutdown()


async def channel():
    [add_channel(*c) for c in CHANNELS]
    subscriber = Subscriber()
    register(subscriber)
    RUNNING.value = True
    STARTED.value = True
    await connect()
