from statistics import mean
from asyncio import Queue
from src.base import log
from mtbot.data import PIPES, STARTED, RUNNING, CANDLE, CLIENT, ValueHolder, close
from .setting import *
from src.okx.utils import check_resp
from src.okx.consts import *

AVAILABLE_MA_DURATIONS = [5, 10, 15, 20, 30]
REPO = []
TS = ValueHolder()
TICK = ValueHolder()

BAR_INTERVAL = {
    BAR_1M: 60,
    BAR_15M: 60 * 15,
    BAR_30M: 60 * 30
}


async def strategy():
    while not STARTED.value:
        pass

    if STRATEGY_MA_DURATION not in AVAILABLE_MA_DURATIONS:
        await log.warning('unavailable MA duration setting')
        await close()
        return

    queues: list = PIPES.get(CANDLE)
    pipe = Queue()
    queues.append(pipe)
    await log.info('strategy start')
    await prepare()
    while RUNNING.value:
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
    await log.info('begin candle')
    async with CLIENT as client:
        resp = await client.get_candles(inst_id=INST_ID, bar=CANDLE_BAR_TYPE, limit=str(STRATEGY_MA_DURATION + 5))
    await log.info('end candle')
    data = check_resp(resp, True)
    if not data:
        await log.warning('request candle error %s', resp)
        return

    for d in data:
        REPO.insert(0, d)
    REPO.pop(-1)        # remove incomplete latest data
    await log.info('prepared %d candle data', len(REPO))


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
