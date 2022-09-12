import asyncio
from asyncio import Queue
from src.base import log
from src.config import conf
from src.okx import client, private as pstream
from src.okx.consts import STATE_FILLED, ALGO_STATE_EFFECTIVE
from . import morder, opertaions as opr
from .setting import EXCHANGE, INST_ID, INST_TYPE


async def algo():
    config = conf(EXCHANGE)
    await pstream.account(config)
    pipe: Queue = await pstream.subscribe('orders-algo', INST_ID, INST_TYPE)
    cli = await client.create(config, test=True)

    while not pstream.started():
        await asyncio.sleep(.5)

    await log.info('algo start')
    while pstream.running():
        msg = await pipe.get()
        try:
            if pstream.close_signal(msg):
                break
            data = msg[0]
            await log.info('algo recv %s' % data)
            await confirm_deal(data, cli)
        except Exception:
            await log.error('algo error', exc_info=True)
        finally:
            pipe.task_done()
    await cli.close()
    await log.info('algo stop')


async def confirm_deal(data: dict, cli: client.AioClient):
    ord_id, algo_id, state = data['ordId'], data['algoId'], data['state']
    order = morder.order()
    if state != ALGO_STATE_EFFECTIVE or not order:
        return
    if order.algo_id != algo_id:
        return
    await opr.close_pending(cli)
    await ensure_deal(cli)


async def ensure_deal(cli: client.AioClient):
    order = morder.order()
    if not order or order.state != STATE_FILLED:
        return

    info = await cli.get_order_info(inst_id=INST_ID, ord_id=order.ord_id)
    state, pnl = info['state'], int(info['pnl'])
    if state != STATE_FILLED:
        return

    if pnl > 0:
        await log.info('algo order=%d WON %f !!!' % (order.index(), pnl))
    elif pnl < 0:
        await log.warning('algo loss %f at order=%d' % (pnl, order.index()))
    else:
        await log.warning('unexpected data order=%d pnl=%d' % (order.index(), pnl))
        return
    morder.set_order(None)

    await log.warning('round end, go to next')
    # raise SystemExit(1)
