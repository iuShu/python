import asyncio
from asyncio import Queue
from src.base import log, repo
from src.config import conf
from src.okx import stream, client
from . import morder, opertaions as opr
from .setting import EXCHANGE, INST_ID, ORDER_POS_SIDE, key_monitor_repo

# TODO store history data to determine whether it should regardless algo order and close all position manually
MAX_STORE = 20
JUDGE_FACTOR = 5


async def monitoring():
    pipe: Queue = await stream.subscribe('tickers', INST_ID)
    cli = await client.create(conf(EXCHANGE), test=True)

    while not stream.started():
        await asyncio.sleep(.5)

    await log.info('monitor start')
    while stream.running():
        tick = await pipe.get()
        try:
            if stream.close_signal(tick):
                break

            data, dr = tick[0], data_repo()
            dr.append(float(data['last']))
            if len(dr) > MAX_STORE:
                dr.pop(0)
            if not morder.order():
                continue

            tp_px = morder.order().profit_price()
            for each in dr[-JUDGE_FACTOR:]:
                if not ORDER_POS_SIDE.is_profit(tp_px, each):
                    return

            await log.info('manually close by %f %s' % (tp_px, dr[-JUDGE_FACTOR:]))
            ret = await opr.close_all_position(cli)
            if ret:
                await log.info('close all pos at %s' % dr[-1])
                morder.set_order(None)
                await opr.close_pending(cli)
                return
            await log.warning('close all pos failed')
        except Exception:
            await log.error('monitor error', exc_info=True)
        finally:
            pipe.task_done()
    await cli.close()
    await log.info('monitor stop')


def data_repo() -> list:
    r = repo.get(key_monitor_repo)
    if not r:
        r = []
        repo[key_monitor_repo] = r
    return r


def current_data() -> tuple:
    dr, order = data_repo(), morder.order()
    return order.profit_price() if order else -1, dr[-JUDGE_FACTOR:]
