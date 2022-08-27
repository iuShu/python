from logger import log
from asyncio import Queue
from mtbot.data import PIPES, STARTED, RUNNING, TICKERS, CLIENT, close
from mtbot.mo import ORDER, PENDING


async def trace():
    while not STARTED.value:
        pass

    queues: list = PIPES.get(TICKERS)
    pipe = Queue()
    queues.append(pipe)
    log.info('trace start')

    while RUNNING.value:
        tick = await pipe.get()
        if not ORDER:
            continue

        data = tick[0]
        px = data['last']
        log.info('trace %s', px)
        await place_next(px)
        await cancel_pending(px)
        await ensure_close(px)
        pipe.task_done()


async def place_next(px):
    pass


async def cancel_pending(px):
    pass


async def ensure_close(px):
    pass
