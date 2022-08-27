import asyncio
from asyncio import Queue

from logger import log
from mtbot.data import PIPES, STARTED, RUNNING, TICKERS, close
from mtbot.mo import PENDING
from mtbot.setting import FAILURE_THRESHOLD_CONFIRM, FAILURE_THRESHOLD_PLACE_ALGO, FAILURE_THRESHOLD_EXTRA_MARGIN
from mtbot.outil import confirm_order, place_algo, add_margin_balance, \
    confirm_failed, place_algo_failed, extra_margin_failed


async def confirm():
    while not STARTED.value:
        pass

    waiting, done = False, False
    queues: list = PIPES.get(TICKERS)
    pipe = Queue()
    queues.append(pipe)
    log.info('confirm start')
    while RUNNING.value:
        if not waiting and done:
            queues.remove(pipe)
            waiting = True
            log.info('confirm waiting')
        if waiting and PENDING.value:
            queues.append(pipe)
            waiting = False
            done = False
            log.info('confirm wakeup')
        if waiting and done:
            await asyncio.sleep(1)
            continue

        await pipe.get()
        try:
            if await confirm_order():
                if await place_algo():
                    if await add_margin_balance():
                        done = True
        except Exception:
            log.error('confirm error', exc_info=True)
        finally:
            pipe.task_done()
            if (confirm_failed.value >= FAILURE_THRESHOLD_CONFIRM) or \
                    (place_algo_failed.value >= FAILURE_THRESHOLD_PLACE_ALGO) or \
                    (extra_margin_failed.value >= FAILURE_THRESHOLD_EXTRA_MARGIN):
                log.warning('too much failed')
                close()
                break
    log.info('confirm end')
