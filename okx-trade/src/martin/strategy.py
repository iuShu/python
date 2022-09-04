import asyncio
from statistics import mean
from asyncio import Queue

from src.base import log, ValueHolder
from src.config import conf
from src.okx import stream
from src.okx import client
from src.okx.consts import BAR_15M, BAR_30M
from .setting import *

AVAILABLE_MA_DURATIONS = [5, 10, 15, 20, 30, 60, 100, 150, 200, 365]
REPO = []
TS = ValueHolder(0)
TICK = ValueHolder()

BAR_INTERVAL = {
    BAR_1M: 60,
    BAR_15M: 60 * 15,
    BAR_30M: 60 * 30
}


async def strategy():
    if STRATEGY_MA_DURATION not in AVAILABLE_MA_DURATIONS:
        await log.warning('unavailable MA duration setting')
        raise SystemExit(1)

    pipe: Queue = await stream.subscribe('candle' + CANDLE_BAR_TYPE, INST_ID)
    cli = await client.create(conf(EXCHANGE), test=True)
    await log.info('strategy prepare')
    await prepare(cli)

    while not stream.started():
        await asyncio.sleep(.5)

    await log.info('strategy start')
    while stream.running():
        candle = await pipe.get()
        try:
            if stream.close_signal(candle):
                break
            await feed(candle[0])
        except Exception:
            await log.error('strategy error', exc_info=True)
        finally:
            pipe.task_done()
    await cli.close()
    await log.info('strategy stop')


async def prepare(cli: client.AioClient):
    try:
        data = await cli.get_candles(inst_id=INST_ID, bar=CANDLE_BAR_TYPE, limit=str(STRATEGY_MA_DURATION + 5))
        if not data:
            return

        for d in data:
            REPO.insert(0, d)
        REPO.pop(-1)        # remove incomplete latest data
        await log.info('prepared %d candle data' % len(REPO))
    except Exception:
        await log.error('prepare candle error', exc_info=True)
    finally:
        await cli.close()


async def feed(data):
    ts = int(data[0])

    if TS.value == 0 and REPO:
        last_ts = int(REPO[-1][0])
        interval = BAR_INTERVAL[CANDLE_BAR_TYPE]
        if ((ts - last_ts) / 1000) != interval:
            REPO.clear()    # discard old data

    if TS.value != 0 and ts > TS.value:
        REPO.append(TICK.value)
        if len(REPO) > STRATEGY_MAX_REPO_SIZE:
            REPO.pop(0)
        # await log.info('strategy collect %d' % len(REPO))

    TS.value = ts
    TICK.value = data


async def satisfy(px: float) -> bool:
    if len(REPO) < STRATEGY_MA_DURATION:
        return False

    pxs = [float(r[4]) for r in REPO[-STRATEGY_MA_DURATION:]]
    avg = mean(pxs)
    # await log.info('px=%f ma=%f' % (px, avg))
    if ORDER_POS_SIDE.is_profit(avg, px):
        await log.info('satisfied px=%f ma=%f' % (px, avg))
        return True
    return False
