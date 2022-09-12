import asyncio

from src.base import log
from src.config import conf
from src.okx import stream, client
from . import morder
from .opertaions import place_order
from .strategy import satisfy
from .setting import *


async def initiate():
    pipe = await stream.subscribe('tickers', INST_ID)
    cli = await client.create(conf(EXCHANGE), test=True)

    while not stream.started():
        await asyncio.sleep(.5)

    await asyncio.sleep(5)  # waiting others
    await log.info('initiator start')
    while stream.running():
        tick = await pipe.get()
        try:
            if stream.close_signal(tick):
                break
            if morder.order() or morder.pending():
                continue

            data = tick[0]
            px = float(data['last'])
            satisfied = await satisfy(px)
            if not satisfied:
                continue

            await log.info('place first order at %f' % px)
            placed = await place_first(cli)
            if not placed:
                await log.fatal('place first order failed')
                await stream.close()
                break
        except Exception:
            await log.error('initiator error', exc_info=True)
        finally:
            pipe.task_done()
    await cli.close()
    await log.info('initiator stop')


async def place_first(cli: client.AioClient) -> bool:
    order = morder.MartinOrder(pos=ORDER_START_POS, follow_rate=ORDER_FOLLOW_RATE,
                               profit_step_rate=ORDER_PROFIT_STEP_RATE, max_order=ORDER_MAX_COUNT,
                               pos_type=ORDER_POS_TYPE, pos_side=ORDER_POS_SIDE.name)
    morder.set_pending(order)
    return await place_order(order, cli)
