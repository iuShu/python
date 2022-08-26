from asyncio import Queue
from config.api_config import conf
from mtbot.okx.stream import *
from mtbot.okx.account import Account
from mtbot.okx.consts import INST_BTC_USDT_SWAP


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
CANDLE = 'candle1m'

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

cf = conf('okx')
CLIENT = Account(api_key=cf['apikey'], api_secret_key=cf['secretkey'], passphrase=cf['passphrase'], test=True)


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


def close():
    RUNNING.value = False
    shutdown()


async def channel():
    [add_channel(*c) for c in CHANNELS]
    subscriber = Subscriber()
    register(subscriber)
    RUNNING.value = True
    STARTED.value = True
    await connect()
