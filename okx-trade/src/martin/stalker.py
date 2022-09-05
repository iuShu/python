import asyncio

from src.base import log
from src.config import conf
from src.okx import stream, client
from src.okx.consts import STATE_FILLED
from . import morder
from .opertaions import place_order, place_algo, add_margin_balance
from .setting import EXCHANGE


async def stalk():
    cli = await client.create(conf(EXCHANGE), test=True)
    while not stream.started():
        await asyncio.sleep(.5)

    await log.info('stalker start')
    while stream.running():
        try:
            await place_algo(cli)
            await add_margin_balance(cli)
            await place_next(cli)
            await asyncio.sleep(.3)
        except Exception:
            await log.error('stalk error', exc_info=True)
        finally:
            pass
    await cli.close()
    await log.info('stalker stop')


async def place_next(cli: client.AioClient):
    order = morder.order()
    if not order or order.state != STATE_FILLED:
        return
    if order.next and order.next.ord_id:
        return

    nxt = order.create_next()
    await log.info('place next at px=%f pos=%d for order=%d' % (nxt.px, nxt.pos, order.index()))
    await place_order(nxt, cli)
