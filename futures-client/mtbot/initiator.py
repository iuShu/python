import asyncio
from asyncio import Queue

from logger import log
from mtbot.data import PIPES, STARTED, RUNNING, TICKERS, close
from mtbot.ma import satisfy
from mtbot.mo import MartinOrder, ORDER, PENDING
from mtbot.outil import place_order
from mtbot.setting import *


async def initiate():
    while not STARTED.value:
        pass

    waiting = False
    queues: list = PIPES.get(TICKERS)
    pipe = Queue()
    queues.append(pipe)
    log.info('init start')
    while RUNNING.value:
        if not waiting and ORDER.value:
            queues.remove(pipe)
            waiting = True
            log.info('init waiting')
        if waiting and not ORDER.value:
            queues.append(pipe)
            waiting = False
            log.info('init wakeup')
        if ORDER.value:
            await asyncio.sleep(1)
            continue

        tick = await pipe.get()
        try:
            if ORDER.value or PENDING.value:
                continue

            data = tick[0]
            px = float(data['last'])
            satisfied = await satisfy(px)
            if not satisfied:
                continue

            placed = await place_first()
            if not placed:
                log.fatal('placed first failed')
                close()
                break
            waiting = True
        except Exception:
            log.error('init error', exc_info=True)
        finally:
            pipe.task_done()
    log.info('init end')


async def place_first() -> bool:
    order = MartinOrder(pos=ORDER_START_POS, follow_rate=ORDER_FOLLOW_RATE, profit_step_rate=ORDER_PROFIT_STEP_RATE,
                        max_order=ORDER_MAX_COUNT, pos_type=ORDER_POS_TYPE, pos_side=ORDER_POS_SIDE.name)
    return await place_order(order)
