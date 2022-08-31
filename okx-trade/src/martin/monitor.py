import asyncio
from asyncio import Queue
from src.base import log
from src.okx import stream
from .morder import ORDER, PENDING
from .setting import INST_ID

# TODO store history data to determine whether it should regardless algo order and close all position manually
_REPO = []


async def monitoring():
    pipe: Queue = await stream.subscribe('tickers', INST_ID)
    await log.info('monitor start')

    while not stream.started():
        await asyncio.sleep(.5)

    while stream.running():
        tick = await pipe.get()
        try:
            if stream.close_signal(tick):
                break
            if not ORDER.value:
                continue

            data = tick[0]
            px = data['last']
            await log.debug('monitor %s' % px)
        except Exception:
            await log.error('monitor error', exc_info=True)
        finally:
            pipe.task_done()
    await log.info('monitor stop')


async def ensure_close(px):
    pass
