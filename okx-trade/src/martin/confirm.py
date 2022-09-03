import asyncio
from asyncio import Queue
from src.base import log
from src.config import conf
from src.okx import client, private as pstream
from src.okx.consts import STATE_FILLED
from .morder import MartinOrder, ORDER, PENDING
from .setting import EXCHANGE, INST_ID, INST_TYPE


async def confirm():
    config = conf(EXCHANGE)
    await pstream.account(config)
    pipe: Queue = await pstream.subscribe('orders', INST_ID, INST_TYPE)
    cli = await client.create(config, test=True)

    while not pstream.started():
        await asyncio.sleep(.5)

    await log.info('confirm start')
    while pstream.running():
        msg = await pipe.get()
        try:
            if pstream.close_signal(msg):
                break
            data = msg[0]
            await log.info('confirm recv %s' % data)
            await confirm_deal(data, cli)
            await confirm_filled(data)
        except Exception:
            await log.error('confirm error', exc_info=True)
        finally:
            pipe.task_done()
    await cli.close()
    await log.info('confirm stop')


async def confirm_deal(data: dict, cli: client.AioClient):
    ord_id, state, pnl = data['ordId'], data['state'], float(data['pnl'])
    if state != STATE_FILLED or not ORDER.value:
        return
    order: MartinOrder = ORDER.value
    if order.ord_id != ord_id:
        return

    if pnl > 0:
        await log.info('confirm order-%d WON %f !!!' % (order.index(), pnl))
    elif pnl < 0:
        await log.warning('confirm loss %f at order-%d' % (pnl, order.index()))
    else:
        return
    ORDER.value = None

    if not PENDING.value:
        return

    pending: MartinOrder = PENDING.value
    datas = await cli.cancel_order(INST_ID, ord_id=pending.ord_id)
    if not datas:
        await log.warning('pending order-%d at px-%f fp-%d suddenly filled'
                          % (pending.index(), pending.px, pending.full_pos()))
        pending.as_first_order()
        return
    await log.info('cancel pending order-%d at px-%f' % (pending.index(), pending.px))


async def confirm_filled(data: dict):
    ord_id, state = data['ordId'], data['state']
    if state != STATE_FILLED or not PENDING.value:
        return
    order: MartinOrder = PENDING.value
    if order.ord_id != ord_id:
        return

    order.state = state
    order.px = float(data['fillPx'])
    order.ctime = data['cTime']
    order.utime = data['uTime']
    ORDER.value = order
    PENDING.value = None
    await log.info('confirm order-%d at px-%f' % (order.index(), order.px))
