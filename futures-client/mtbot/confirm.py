from logger import log
from asyncio import Queue
from mtbot.data import PIPES, STARTED, RUNNING, TICKERS, CLIENT, close
from mtbot.mo import ORDER, PENDING


async def confirm():
    while not STARTED:
        pass

    queues: list = PIPES.get(TICKERS)
    pipe = Queue()
    queues.append(pipe)
    log.info('confirm start')

    while RUNNING.value:
        tick = await pipe.get()
        data = tick[0]
        px = data['last']
        log.info('confirm %s', px)
        pipe.task_done()
