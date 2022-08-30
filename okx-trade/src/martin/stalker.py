import asyncio
from asyncio import Queue
from src.base import log
from src.okx import stream
from src.okx.consts import STATE_FILLED
from .opertaions import place_order, place_algo, add_margin_balance
from .morder import MartinOrder, ORDER, PENDING
from .setting import INST_ID


async def stalk():
    await log.info('stalk start')

    while not stream.started():
        await asyncio.sleep(.5)

    while stream.running():
        try:
            await place_algo()
            await add_margin_balance()
            await place_next()
            await asyncio.sleep(.3)
        except Exception:
            await log.error('stalk error', exc_info=True)
        finally:
            pass


async def place_next():
    if not ORDER.value:
        return

    order: MartinOrder = ORDER.value
    if order.state != STATE_FILLED or order.next.ord_id:
        return

    nxt = order.create_next()
    await place_order(nxt)
