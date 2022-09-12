import asyncio
import json

import aiohttp
from aiohttp.web_ws import WSMsgType
from asyncio.queues import Queue
from src.config import notify_conf
from src.base import repo, log
from src.okx import stream
from src.martin.setting import *

'''
    send message format
    {
        'op': str,
        'cid': int
        'mid': int,
        'data': obj
    }

    receive message format
    {
        'op': str,
        'mid': int,
        'code': int,
        'msg': str,
        'data': obj
    }
'''
id_pool = [0, 0, 0]
pending_idx = 0
confirm_idx = 1
client_idx = 2


async def notifying():
    session = aiohttp.ClientSession()
    pipe: Queue = pending_queue()
    conf = notify_conf(NOTIFY_NAME)
    interrupted, times = False, 0

    while not stream.started():
        await asyncio.sleep(.5)

    await log.info('notify start')
    while True:
        async with session.ws_connect(url=ws_url(conf), autoping=True) as ws:
            await init(ws, conf['secret'])
            while stream.running():
                await send(ws, pipe)
                if not await recv(ws):
                    interrupted = True
                    times += 1
                    break
            await ws.close()
        if not interrupted:
            break
        id_pool[pending_idx] = 0
        id_pool[confirm_idx] = 0
        await log.warning('service interrupted %d, reconnecting...' % times)
    await log.info('service has been closed')


async def init(ws, secret: str):
    msg = await ws.receive()
    resp = json.loads(msg.data)
    id_pool[client_idx] = resp['data']
    await log.info('notify got cid %d' % resp['data'])

    await ws.send_json(_wrap_msg(NOTIFY_OP_LOGIN, secret))
    msg = await ws.receive()
    resp = json.loads(msg.data)
    if await confirm_receive(resp):
        await log.info('notify login ok')
    else:
        await log.error('notify login failed by %s' % json.dumps(resp))


async def send(ws, pipe: Queue):
    pending = await pipe.get()
    await log.info('send %s %s' % (pending, ws.closed))
    await ws.send_json(_wrap_msg(NOTIFY_OP_NOTIFY, {'topic': NOTIFY_OP_NOTIFY, 'msg': pending}))


async def recv(ws) -> bool:
    msg = await ws.receive()
    if msg.type == WSMsgType.CLOSE or msg.type == WSMsgType.CLOSED:
        await log.warning('received close signal %s' % msg.type)
        return False
    elif msg.type != WSMsgType.TEXT:
        await log.warning('unknown msg type %s %s' % (msg.type, msg.data))
        return True

    resp = json.loads(msg.data)
    return await confirm_receive(resp)


def _wrap_msg(operation: str, data) -> dict:
    return {
        'op': operation,
        'cid': id_pool[client_idx],
        'mid': msg_id(),
        'data': data
    }


def msg_id() -> int:
    id_pool[pending_idx] += 1
    return id_pool[pending_idx]


async def confirm_receive(resp: dict) -> bool:
    if 'op' not in resp or 'code' not in resp or 'mid' not in resp or resp['code'] != 200:
        await log.error('service received %s' % json.dumps(resp))
        return False

    mid, confirm = resp['mid'], id_pool[confirm_idx]
    if mid != (confirm + 1):
        await log.warning('non-confirmed message %s when recv %s' % ([i for i in range(confirm, mid)], mid))
    id_pool[confirm_idx] = mid      # non-strict mode: ignore non-confirmed message
    return True


def pending_queue() -> Queue:
    q: Queue = repo.get(KEY_NOTIFY_MSG)
    if q is None:
        q = Queue()
        repo[KEY_NOTIFY_MSG] = q
    return q


def ws_url(conf):
    return 'ws://%s:%s/%s' % (conf['host'], conf['port'], conf['path'])


def notify(msg):
    q = pending_queue()
    q.put_nowait(msg)


if __name__ == '__main__':
    asyncio.run(notifying())
    pass
