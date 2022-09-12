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
    await opr.ensure_deal(cli)

