import aiohttp
from json import loads
from asyncio.queues import Queue
from src.base import ValueHolder, log
from .consts import WSS_PUBLIC_URL

_STARTED = ValueHolder(False)
_RUNNING = ValueHolder(False)
_PIPES = dict()
_PENDING = dict()
_SUBSCRIBE = dict()


async def connect():
    session = aiohttp.ClientSession()
    await log.info('websocket start')
    async with session.ws_connect(url=WSS_PUBLIC_URL, autoclose=False, autoping=False) as ws:
        _STARTED.value = True
        _RUNNING.value = True
        while _RUNNING.value:
            await send(ws)
            await dispatch(ws)
    await session.close()
    await log.info('websocket has been closed of %s', WSS_PUBLIC_URL)


async def subscribe(channel: str, inst_id: str, inst_type='') -> Queue:
    key = _key(channel, inst_id)
    queue = Queue()
    if key in _PIPES:
        _PIPES.get(key).append(queue)
    else:
        _PIPES[key] = [queue]
    _SUBSCRIBE[key] = _subscribe_json(channel, inst_id, inst_type)
    return queue


async def close():
    _RUNNING.value = False


async def send(ws):
    if not _SUBSCRIBE:
        return

    item = _SUBSCRIBE.popitem()
    while item:
        await ws.send_json(item[1])
        _PENDING[item[0]] = item[1]
        item = _SUBSCRIBE.popitem()


async def dispatch(ws):
    # json = await ws.receive_json()
    msg = await ws.receive()
    await log.info(type(msg), msg.type, msg.data)
    json = loads(msg.data)
    if 'data' in json:
        arg = json['arg']
        queues = _PIPES.get(_key(arg['channel'], arg['instId']))
        if not queues:
            await log.warning('no subscriber at %s %s', arg['channel'], arg['instId'])
        else:
            for queue in queues:
                queue.put_nowait(json['data'])
    elif 'event' in json:
        event = json['event']
        if event == 'error':
            await log.error('event error by %s', json)
        else:
            arg = json['arg']
            if event == 'subscribe':
                _PENDING.pop(_key(arg['channel'], arg['instId']))
                await log.info('subscribed %s %s', arg['channel'], arg['instId'])
    else:
        await log.warning('received unknown data %s', json)


def running() -> bool:
    return _RUNNING.value


def started() -> bool:
    return _STARTED.value


def _key(channel: str, inst_id: str):
    return hash(channel + inst_id)


def _subscribe_json(channel: str, inst_id: str, inst_type: str):
    arg = {'channel': channel, 'instId': inst_id}
    if inst_type:
        arg['instType'] = inst_type
    return {'op': 'subscribe', 'args': [arg]}
