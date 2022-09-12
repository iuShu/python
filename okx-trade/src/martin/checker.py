import asyncio
import os

from src.base import log
from src.martin import morder
from src.martin import strategy, monitor


async def check():

    loc = os.path.join(os.path.dirname(__file__), '../../resources/debug.properties')
    last = 0
    await log.info('checker start')
    while True:
        modify = int(os.path.getmtime(loc))
        # await log.info('l=%d m=%d' % (last, modify))
        if 0 < last < modify:
            await update_prop(loc)
        last = modify
        await asyncio.sleep(2)
    # await log.info('checker stop')


async def update_prop(loc):
    prop = dict()
    with open(loc, 'r') as f:
        for line in f.readlines():
            kv = line.strip().replace(' ', '').split('=')
            prop[kv[0]] = int(kv[1])

    o, p = morder.order(), morder.pending()
    if prop['order.prev.check']:
        await log.info('[prev] order %s' % (o.prev if o else '-'))
    if prop['order.check']:
        await log.info('[now] order %s' % (o if o else '-'))
    if prop['order.next.check']:
        await log.info('[next] order %s' % (o.next if o else '-'))
    await log.info('[now] pending %s' % (p if p else '-'))
    await log.info('[strategy] MA%d %f' % strategy.current_data())
    await log.info('[monitor] %s %s' % monitor.current_data())

