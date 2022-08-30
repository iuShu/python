import asyncio

from src.base import log
from src.okx import stream
from .morder import MartinOrder, ORDER, PENDING
from .opertaions import place_order
from .strategy import satisfy
from .setting import *


async def initiate():
    pipe = await stream.subscribe('tickers', INST_ID)
    await log.info('init start')

    while not stream.started():
        await asyncio.sleep(.5)

    while stream.running():
        tick = await pipe.get()
        try:
            if ORDER.value or PENDING.value:
                continue

            data = tick[0]
            px = float(data['last'])
            satisfied = await satisfy(px)
            if not satisfied:
                continue

            await log.info('place first order at %f', px)
            placed = await place_first()
            if not placed:
                await log.fatal('place first order failed')
                await stream.close()
                break
        except Exception:
            await log.error('init error', exc_info=True)
        finally:
            pipe.task_done()
    await log.info('init end')


async def place_first() -> bool:
    order = MartinOrder(pos=ORDER_START_POS, follow_rate=ORDER_FOLLOW_RATE, profit_step_rate=ORDER_PROFIT_STEP_RATE,
                        max_order=ORDER_MAX_COUNT, pos_type=ORDER_POS_TYPE, pos_side=ORDER_POS_SIDE.name)
    return await place_order(order)
