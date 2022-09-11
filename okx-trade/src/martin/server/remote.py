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


async def reacting():
    session = aiohttp.ClientSession()
    conf = notify_conf(NOTIFY_NAME)
    interrupted, times = False, 0

    while not stream.started():
        await asyncio.sleep(.5)

    await log.info('remote start')
    while True:
        # async with session.ws_connect(url=ws_url(conf), heartbeat=10.0) as ws:
        async with session.ws_connect(url='ws://localhost:5889/ws', autoping=True, receive_timeout=3.0) as ws:
            await init(ws, conf['secret'])
            while stream.running():
                if not await recv(ws):
                    interrupted = True
                    times += 1
                    break
            await ws.close()
        if not interrupted:
            break
        await log.warning('remote interrupted %d, reconnecting...' % times)
    await log.info('remote has been closed')


async def init(ws, secret: str):
    msg = await ws.receive()
    resp = json.loads(msg.data)
    cid = resp['data']
    await log.info('remote got cid %d' % cid)

    packet = {
        'op': NOTIFY_OP_LOGIN,
        'cid': cid,
        'mid': 1,
        'data': secret
    }
    await ws.send_json(packet)
    msg = await ws.receive()
    resp = json.loads(msg.data)
    if resp.get('code') == 200 and resp.get('mid') == 1:
        await log.info('remote login ok')
    else:
        await log.error('remote login failed by %s' % json.dumps(resp))
        raise SystemExit(1)

    packet['op'] = NOTIFY_OP_SUBSCRIBE
    packet['mid'] = 2
    packet['data'] = NOTIFY_OP_OPERATE
    await ws.send_json(packet)
    msg = await ws.receive()
    resp = json.loads(msg)
    if resp.get('code') == 200 and resp.get('mid') == 2:
        await log.info('remote subscribe ok')
    else:
        await log.error('remote subscribe failed by %s' % json.dumps(resp))
        raise SystemExit(1)


async def recv(ws) -> bool:
    msg = await ws.receive()
    print('remote recv', msg)
    if msg.type == WSMsgType.CLOSE or msg.type == WSMsgType.CLOSED:
        await log.warning('received close signal %s' % msg.type)
        return False
    elif msg.type != WSMsgType.TEXT:
        await log.warning('unknown msg type %s %s' % (msg.type, msg.data))
        return True

    resp = json.loads(msg.data)
    if 'op' not in resp or resp['op'] != NOTIFY_OP_OPERATE or resp['data'] != NOTIFY_CLOSE_SIGNAL:
        return True
    await log.warning('recv close signal')
    raise SystemExit(1)


def ws_url(conf):
    return 'ws://%s:%s/%s' % (conf['host'], conf['port'], conf['path'])


if __name__ == '__main__':
    asyncio.run(reacting())
