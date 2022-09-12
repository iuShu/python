import asyncio
from statistics import mean
from asyncio import Queue

from src.base import log, ValueHolder, repo
from src.config import conf
from src.okx import stream
from src.okx import client
from src.okx.consts import BAR_15M, BAR_30M
from .setting import *

AVAILABLE_MA_DURATIONS = [5, 10, 15, 20, 30, 60, 100, 150, 200, 365]
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

        dr = data_repo()
        for d in data:
            dr.insert(0, d)
        dr.pop(-1)        # remove incomplete latest data
        await log.info('prepared %d candle data' % len(dr))
    except Exception:
        await log.error('prepare candle error', exc_info=True)
    finally:
        await cli.close()


async def feed(data):
    ts = int(data[0])
    dr = data_repo()
    if TS.value == 0 and dr:
        last_ts = int(dr[-1][0])
        interval = BAR_INTERVAL[CANDLE_BAR_TYPE]
        if ((ts - last_ts) / 1000) != interval:
            dr.clear()    # discard old data
            await log.info('discard prepared data %d %d' % (ts, last_ts))

    if TS.value != 0 and ts > TS.value:
        dr.append(TICK.value)
        if len(dr) > STRATEGY_MAX_REPO_SIZE:
            dr.pop(0)
        # await log.info('strategy collect %d' % len(REPO))

    TS.value = ts
    TICK.value = data


async def satisfy(px: float) -> bool:
    dr = data_repo()
    if len(dr) < STRATEGY_MA_DURATION:
        return False

    pxs = [float(r[4]) for r in dr[-STRATEGY_MA_DURATION:]]
    avg = mean(pxs)
    # await log.info('px=%f ma=%f' % (px, avg))
    if ORDER_POS_SIDE.is_loss(avg, px):
        await log.info('satisfied px=%f ma=%f' % (px, avg))
        return True
    return False


def data_repo() -> list:
    r = repo.get(key_strategy_repo)
    if not r:
        r = []
        repo[key_strategy_repo] = r
    return r


def current_data() -> tuple:
    dr = data_repo()
    if len(dr) < STRATEGY_MA_DURATION:
        return STRATEGY_MA_DURATION, -1
    return STRATEGY_MA_DURATION, mean([float(r[4]) for r in dr[-STRATEGY_MA_DURATION:]])
