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
    await log.info('trace start')

    while not stream.started():
        await asyncio.sleep(.5)

    while stream.running():
        tick = await pipe.get()
        try:
            if not ORDER.value:
                continue

            data = tick[0]
            px = data['last']
            await log.debug('trace %s', px)
        except Exception:
            await log.error('trace error', exc_info=True)
        finally:
            pipe.task_done()


async def ensure_close(px):
    pass
