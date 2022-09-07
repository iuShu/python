import json

import aiohttp
from asyncio.queues import Queue
from src.config import notify_conf
from src.base import repo, log
from src.okx import stream
from src.martin.setting import NOTIFY_NAME, KEY_NOTIFY_MSG

'''
    send message format
    {
        'op': str,
        'mid': number,
        'data': obj
    }
    
    receive message format
    {
        'code': 200,
        'msg': '',
        'mid': number,
        'data': obj
    }
'''
id_pool = [0, 0]
pending_idx = 0
confirm_idx = 1
op_login = 'login'
op_notify = 'notify'


async def service():
    session = aiohttp.ClientSession()
    pipe: Queue = queue()
    conf = notify_conf(NOTIFY_NAME)
    interrupted, times = False, 0
    while True:
        async with session.ws_connect(url=ws_url(conf), heartbeat=15.0) as ws:
            await login(ws, conf['secret'])
            while stream.running():
                await send(ws, pipe)
                await receive(ws)
            await ws.close()
        if not interrupted:
            break
        await log.warning('service interrupted %d, reconnecting...' % times)
    await log.info('service has been closed')


async def login(ws, secret: str) -> bool:
    await ws.send_json(_wrap_msg(op_login, secret))
    resp = await ws.receive_json()
    if confirm_receive(resp):
        return True
    await log.error('service login failed by %s' % json.dumps(resp))
    return False


async def send(ws, pipe: Queue):
    pending = []
    while not pipe.empty():
        pending.append(pipe.get_nowait())
    if not pending:
        return
    await ws.send_json(_wrap_msg(op_notify, pending))


async def receive(ws):
    resp = await ws.receive_json(timeout=1)
    if not confirm_receive(resp):
        return
    if 'op' in resp:
        await operate(resp)


async def operate(resp: dict):
    pass


def _wrap_msg(operation: str, data) -> dict:
    return {
        'op': operation,
        'mid': msg_id(),
        'data': data
    }


def msg_id() -> int:
    id_pool[pending_idx] += 1
    return id_pool[pending_idx]


async def confirm_receive(resp: dict):
    if 'op' in resp:
        return resp
    if 'code' not in resp or 'mid' not in resp or resp['code'] != 200:
        await log.error('service received %s' % json.dumps(resp))
        return None

    mid, prev = resp['mid'], id_pool[confirm_idx]
    if mid != (prev + 1):
        await log.warning('non-confirmed message %s when recv %s' % ([i for i in range(prev+1, mid)], mid))
    id_pool[confirm_idx] = mid      # non-strict mode: ignore non-confirmed message
    return resp


def queue() -> Queue:
    queue: Queue = repo.get(KEY_NOTIFY_MSG)
    if queue is None:
        queue = Queue()
        repo[KEY_NOTIFY_MSG] = queue
    return queue


def ws_url(conf):
    return 'ws://%s:%s/%s' % (conf['host'], conf['port'], conf['path'])


if __name__ == '__main__':
    pass
