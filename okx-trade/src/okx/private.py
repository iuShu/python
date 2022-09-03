import asyncio
import time

import aiohttp
from json import loads
from asyncio.queues import Queue
from aiohttp.http_websocket import WSMsgType
from src.base import log, repo
from .consts import WSS_PRIVATE_URL, GET, WSS_REQUEST_PATH
from .utils import pre_hash, sign

key_started = 'private-started'
key_running = 'private-running'
key_pipes = 'private-pipes'
key_pending = 'private-pending'
key_subscribe = 'private-subscribe'
key_subscribed = 'private-subscribed'
key_account = 'private-ws-account'

MAX_WAITING_MSG = 100
CLOSE_SIGNAL = 'private-stream-close'


async def connect():
    session = aiohttp.ClientSession()
    await log.info('websocket private start')
    interrupted, times = False, 0
    while True:
        async with session.ws_connect(url=WSS_PRIVATE_URL, autoclose=False, autoping=False) as ws:
            await log.info('websocket private connected')
            await login(ws)
            repo[key_started] = True
            repo[key_running] = True
            while running():
                await send(ws)
                if not await dispatch(ws):
                    interrupted = True
                    times += 1
                    break
            await ws.close()

        if not interrupted:
            break
        await log.warning('websocket private interrupted %d, reconnecting...' % times)
        subscribes, subscribed = var(key_subscribe, dict()), var(key_subscribed, dict())
        item = subscribed.popitem()
        while item:
            subscribes[item[0]] = item[1]
            item = subscribed.popitem() if subscribed else None
        interrupted = False

    await close()
    await session.close()
    await log.info('websocket private has been closed')


async def login(ws):
    acc = var(key_account, dict())
    for i in range(10):
        if acc:
            break
        await asyncio.sleep(.5)
    if not acc:
        await log.fatal('account not found, exit')
        raise SystemExit(1)

    packet = _login_json(acc)
    await ws.send_json(packet)
    # await log.info('send login params %s' % packet)
    msg = await ws.receive()
    if msg.type != WSMsgType.TEXT:
        await log.error('unknown msg type %s %s' % (msg.type, msg.data))
        raise SystemExit(1)

    json = loads(msg.data)
    event = json.get('event')
    if event == 'login':
        await log.info('login ok')
        return

    await log.error('login failed by %s' % json)
    raise SystemExit(1)


async def send(ws):
    subscribes = var(key_subscribe, dict())
    if not subscribes:
        return

    pending = var(key_pending, dict())
    item = subscribes.popitem()
    while item:
        await ws.send_json(item[1])
        pending[item[0]] = item[1]
        item = subscribes.popitem() if subscribes else None


async def dispatch(ws) -> bool:
    msg = await ws.receive()
    if msg.type == WSMsgType.CLOSE or msg.type == WSMsgType.CLOSED:
        await log.warning('received close signal %s' % msg.type)
        return False
    elif msg.type != WSMsgType.TEXT:
        await log.warning('unknown msg type %s %s' % (msg.type, msg.data))
        return True

    json = loads(msg.data)
    if 'data' in json:
        arg, pipes = json['arg'], var(key_pipes, dict())
        queues = pipes.get(_key(arg['channel'], arg['instId']))
        if not queues:
            await log.warning('no subscriber at %s %s' % (arg['channel'], arg['instId']))
        else:
            for queue in queues:
                if queue.qsize() > MAX_WAITING_MSG:
                    queue.get_nowait()      # discard old msg
                queue.put_nowait(json['data'])
    elif 'event' in json:
        event = json['event']
        if event == 'error':
            await log.error('event error by %s' % json)
        else:
            arg, pending, subscribed = json['arg'], var(key_pending, dict()), var(key_subscribed, dict())
            if event == 'subscribe':
                key = _key(arg['channel'], arg['instId'])
                subscribed[key] = pending.pop(key)
                await log.info('subscribed %s %s' % (arg['channel'], arg['instId']))
            elif event == 'login':
                await log.info('login ok')
    else:
        await log.warning('received unknown data %s' % json)
    return True


async def account(acc: dict):
    var(key_account, dict()).update(acc)


async def subscribe(channel: str, inst_id: str, inst_type='') -> Queue:
    key = _key(channel, inst_id)
    queue = Queue()

    pipes, subscribes = var(key_pipes, dict()), var(key_subscribe, dict())
    queues: list = pipes.get(key)
    if queues:
        queues.append(queue)
    else:
        pipes[key] = [queue]
    subscribes[key] = _subscribe_json(channel, inst_id, inst_type)
    return queue


async def close():
    repo[key_running] = False
    pipes = var(key_pipes, dict())
    if not pipes:
        return
    for queues in pipes.values():
        for queue in queues:
            queue.put_nowait(CLOSE_SIGNAL)


def close_signal(msg: str) -> bool:
    return type(msg) == str and msg == CLOSE_SIGNAL


def var(key: str, default_val):
    v = repo.get(key)
    if v is None:
        v = default_val
        repo[key] = v
    return v


def running() -> bool:
    return repo.get(key_running) is True


def started() -> bool:
    return repo.get(key_started) is True


def _key(channel: str, inst_id: str):
    return hash(channel + inst_id)


def _login_json(acc: dict):
    ts = str(int(time.time()))
    signature = sign(pre_hash(ts, GET, WSS_REQUEST_PATH, ''), acc['secretkey'])
    arg = {
        'apiKey': acc['apikey'],
        'passphrase': acc['passphrase'],
        'timestamp': ts,
        'sign': signature.decode('utf-8')
    }
    return {'op': 'login', 'args': [arg]}


def _subscribe_json(channel: str, inst_id: str, inst_type: str):
    arg = {'channel': channel, 'instId': inst_id}
    if inst_type:
        arg['instType'] = inst_type
    return {'op': 'subscribe', 'args': [arg]}
