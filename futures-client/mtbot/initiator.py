from logger import log
from asyncio import Queue
from mtbot.data import PIPES, STARTED, RUNNING, TICKERS, CLIENT, close
from mtbot.mo import ORDER, PENDING


async def initiate():
    while not STARTED:
        pass

    queues: list = PIPES.get(TICKERS)
    pipe = Queue()
    queues.append(pipe)
    log.info('init start')

    while RUNNING.value:
        tick = await pipe.get()
        data = tick[0]
        px = data['last']
        log.info('init %s', px)
        pipe.task_done()
