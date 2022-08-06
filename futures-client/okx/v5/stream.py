import asyncio
import datetime
import json
import traceback
import logging

import websockets
from okx.v5.consts import *

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.DEBUG)
log = logging.getLogger()


async def subscribe_public(channels):
    for i in range(5):
        try:
            async with websockets.connect(WSS_PUBLIC_URL) as ws:
                params = {'op': 'subscribe', 'args': channels}
                text = json.dumps(params)
                log.info('>> %s', text)
                await ws.send(text)
                while True:
                    try:
                        res = await asyncio.wait_for(ws.recv(), timeout=25)
                        log.info('<< %s', res)
                        await subscribing(res)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        traceback.print_exc()
                        if await ping(ws):
                            log.warning('occurred error but ping ok, continue')
                            continue
                        log.error('reconnecting...')
                        break
                log.error('subscribing error, %d reconnecting...', i+1)
        except Exception:
            traceback.print_exc()
            log.error('disconnected, %d reconnecting...', i+1)


async def subscribing(res):
    res = json.loads(res)
    if 'event' in res:
        if res['event'] == 'error':
            log.error('%d %s', res['code'], res['msg'])
            return
        log.info('channels subscribed')
    elif 'data' in res:
        await handle_recv(res)
    else:
        log.warning('unknown response data')


async def handle_recv(res):
    data = res['data']
    for d in data:
        print(d)


async def ping(ws):
    try:
        await ws.send('ping')
        res = await ws.recv()
        print('reconnected', res)
        return True
    except Exception:
        return False


def local_time():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


if __name__ == '__main__':
    asyncio.run(subscribe_public(TICKERS_BTC_USDT_SWAP))

