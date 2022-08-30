import asyncio
from statistics import mean
from asyncio import Queue

from src.base import log, ValueHolder, peak
from src.config import conf
from src.okx import stream
from src.okx.streams import pipes
from src.okx import client
from src.okx.consts import BAR_15M, BAR_30M
from .setting import *

AVAILABLE_MA_DURATIONS = [5, 10, 15, 20, 30, 60, 100, 150, 200, 365]
REPO = []
TS = ValueHolder()
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
    await log.info('strategy prepare')
    await prepare()

    while not stream.started():
        await asyncio.sleep(.5)

    await log.info('strategy start %s' % pipe)
    while stream.running():
        await log.info('strategy check %s' % pipe)
        candle = await pipe.get()
        try:
            print('strategy tick len', len(candle))
            await feed(candle[0])
        except Exception:
            await log.error('strategy error', exc_info=True)
        finally:
            pipe.task_done()
    await log.info('strategy end')


async def prepare():
    await log.info('prepare start')
    cli = await client.create(conf(EXCHANGE), test=True)
    try:
        await log.info('prepare get candle start')
        data = await cli.get_candles(inst_id=INST_ID, bar=CANDLE_BAR_TYPE, limit=str(STRATEGY_MA_DURATION + 5))
        await log.info('prepare get candle end')
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

    if not TS.value:
        last_ts = int(REPO[-1][0])
        interval = BAR_INTERVAL[CANDLE_BAR_TYPE]
        if ((ts - last_ts) / 1000) != interval:
            REPO.clear()    # discard old data
    elif ts > TS.value:
        REPO.append(TICK.value)
        if len(REPO) > STRATEGY_MAX_REPO_SIZE:
            REPO.pop(0)

    TS.value = ts
    TICK.value = data


async def satisfy(px: float) -> bool:
    if len(REPO) < STRATEGY_MA_DURATION:
        return False

    pxs = [float(r[4]) for r in REPO[-STRATEGY_MA_DURATION:]]
    avg = mean(pxs)
    await log.debug('%f %f %s', px, avg, pxs)
    if ORDER_POS_SIDE.is_profit(avg, px):
        await log.info('%f %f', px, avg)
        return True
    return False
