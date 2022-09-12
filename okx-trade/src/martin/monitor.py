import asyncio
from asyncio import Queue
from src.base import log
from src.config import conf
from src.okx import stream, client
from . import morder, opertaions as opr
from .setting import EXCHANGE, INST_ID, ORDER_POS_SIDE

# TODO store history data to determine whether it should regardless algo order and close all position manually
_REPO = []
MAX_STORE = 20
JUDGE_FACTOR = 5


async def monitoring():
    cli = await client.create(conf(EXCHANGE), test=True)
    pipe: Queue = await stream.subscribe('tickers', INST_ID)
    await log.info('monitor start')

    while not stream.started():
        await asyncio.sleep(.5)

    while stream.running():
        tick = await pipe.get()
        try:
            if stream.close_signal(tick):
                break
            if not morder.order():
                continue

            data = tick[0]
            _REPO.append(float(data['last']))
            if len(_REPO) > MAX_STORE:
                _REPO.pop(0)

            tp_px = morder.order().profit_price()
            for each in _REPO[-JUDGE_FACTOR:]:
                if not ORDER_POS_SIDE.is_profit(tp_px, each):
                    return

            await log.info('manually close by %f %s' % (tp_px, _REPO[-JUDGE_FACTOR:]))
            ret = await opr.close_all_position(cli)
            if ret:
                await log.info('close all pos at %s' % _REPO[-1])
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
