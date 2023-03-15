import asyncio
import logging
from asyncio import run, wait, create_task

# import sys as system
# system.path.append('/opt/trading/okx-swap')   # for prod

from src.config import sys, trade, watch
from src.client import OkxPublicClient
from src.listener import InstListener
from src.indicator.indicator import EmaIndicator
from src.notifier import notifier

public = OkxPublicClient(sys('ws_public_url'))
update_config_interval = 5.0
inst_listeners = dict()

S_STOP = -1
S_NORMAL = 0
S_FINISH_STOP = 1


async def tasks():
    if sys('stop'):
        return

    for k, v in trade().items():
        if v['stop']:
            continue

        args = [k, v['inst_id'], v['inst_type']]
        indicator = EmaIndicator(*args)
        listener = InstListener(*args, indicator=indicator)
        inst_listeners[k] = listener
        public.register(listener)
        public.register(indicator)

    if not len(inst_listeners):
        logging.error("no listener")
        raise SystemExit(1)

    logging.info('startup with %d listeners' % len(inst_listeners))

    t = [
        create_task(daemon()),
        create_task(public.connect()),
    ]
    await wait(t)


async def daemon():
    while True:
        await asyncio.sleep(update_config_interval)
        await watch()
        for k, v in trade().items():
            lsn = inst_listeners.get(k)
            if not lsn:
                continue

            logging.debug('%s %s %s %s' % (v['stop'], lsn.inst(), lsn.is_stop(), lsn.is_finish_stop()))
            vs = v['stop']
            if not lsn.is_stop():
                if vs == S_STOP:
                    lsn.stop()
                elif vs == S_FINISH_STOP:
                    lsn.finish_stop(True)
                if v['strategy']:
                    lsn.switch_strategy(v['strategy'])

        if sys('stop') == S_STOP:
            public.stop()
            logging.info('program stop')
            notifier.sys_exit()
            break
        elif sys('stop') == S_FINISH_STOP:
            public.finish_stop()
            logging.warning("program state set to <finish_stop> and exit conf watching")
            break


if __name__ == '__main__':
    run(tasks())
    # print('here')

    # first = 1
    # print([first * pow(2, i) for i in range(0, 6)])

    pass
