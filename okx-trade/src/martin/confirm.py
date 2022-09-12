import asyncio
from asyncio import Queue
from src.base import log
from src.config import conf
from src.okx import private as pstream
from src.okx.consts import STATE_FILLED, STATE_LIVE
from . import morder
from .setting import EXCHANGE, INST_ID, INST_TYPE


async def confirm():
    config = conf(EXCHANGE)
    await pstream.account(config)
    pipe: Queue = await pstream.subscribe('orders', INST_ID, INST_TYPE)

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
            await confirm_filled(data)
        except Exception:
            await log.error('confirm error', exc_info=True)
        finally:
            pipe.task_done()
    await log.info('confirm stop')


async def confirm_filled(data: dict):
    ord_id, state = data['ordId'], data['state']
    pending = morder.pending()
    # await log.info('confirm %s %s %s %s' % (ord_id, state, state == STATE_FILLED, pending))
    if state == STATE_LIVE:
        pending.ord_id = ord_id
        pending.state = state
        await log.info('confirm placed order=%d' % pending.index())
        return

    if state != STATE_FILLED or not pending or pending.ord_id != ord_id:
        return
    pending.state = state
    pending.px = float(data['fillPx'])
    pending.ctime = data['cTime']
    pending.utime = data['uTime']
    morder.set_order(pending)
    morder.set_pending(None)
    await log.info('confirm order=%d filled at px=%f' % (pending.index(), pending.px))
