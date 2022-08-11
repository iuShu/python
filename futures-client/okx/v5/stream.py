import asyncio
import datetime
import json
import traceback

import websockets
from okx.v5.consts import *
from okx.v5.utils import log
from okx.v5.subscriber import Subscriber


_subscribers = []
_subscribe = dict()
_unsubscribe = dict()
_subscribed = dict()
_shutdown_signal = []


async def connect():
    for i in range(5):
        try:
            async with websockets.connect(WSS_PUBLIC_URL) as ws:
                log.info('websocket connected to %s', WSS_PUBLIC_URL)
                while not _shutdown_signal:
                    try:
                        await handle_channel(ws)
                        res = await asyncio.wait_for(ws.recv(), timeout=30)
                        log.info('<< %s', res)
                    except Exception:
                        traceback.print_exc()
                        if await ping(ws):
                            log.warning('occurred error but ping ok, continue')
                            continue
                        break

                    try:
                        await dispatching(res)
                    except Exception:
                        traceback.print_exc()
                        log.error('dispatching process error, continue')
                        continue
                if not _shutdown_signal:
                    log.error('subscribing error, %d reconnecting...', i+1)
                else:
                    log.info('shutdown subscriber program at %d', i+1)
                    ws.close()
                    break
        except Exception:
            traceback.print_exc()
            log.error('disconnected, %d try reconnecting...', i+1)
            _subscribe.update(_subscribed)
            _subscribed.clear()


async def handle_channel(ws):
    if _subscribe:
        params = {'op': 'subscribe', 'args': _subscribe.popitem()[1]}
        text = json.dumps(params)
        log.info('>> %s', text)
        await ws.send(text)
    if _unsubscribe:
        params = {'op': 'unsubscribe', 'args': _unsubscribe.popitem()[1]}
        text = json.dumps(params)
        log.info('>> %s', text)
        await ws.send(text)


async def dispatching(res):
    res = json.loads(res)
    if 'event' in res:
        event = res['event']
        if event == 'error':
            log.error('%d %s', res['code'], res['msg'])
            return

        arg = res['arg']
        if event == 'subscribe':
            channel, inst_id = arg['channel'], arg['instId']
            key = _channel_key(channel, inst_id)
            _subscribed[key] = [{'channel': channel, 'instId': inst_id}]
            log.info('subscribed: %s', [k for k in _subscribed.keys()])
        elif event == 'unsubscribe':
            channel, inst_id = arg['channel'], arg['instId']
            key = _channel_key(channel, inst_id)
            _subscribed.pop(key)
            log.info('subscribed: %s', [k for k in _subscribed.keys()])
        else:
            log.warning('unknown event %s', event)
    elif 'data' in res:
        await handle_recv(res)
    else:
        log.warning('unknown response data %s', res)


async def handle_recv(resp):
    try:
        for s in _subscribers:
            s.on_data(resp)
    except Exception:
        traceback.print_exc()


async def ping(ws):
    try:
        await ws.send('ping')
        resp = await ws.recv()
        log.info('reconnected', resp)
        return True
    except Exception:
        return False


def local_time():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def register(subscriber: Subscriber):
    if not issubclass(type(subscriber), Subscriber):
        raise TypeError('accept Subscriber class or subclass only')
    if subscriber:
        _subscribers.append(subscriber)


def startup():
    _shutdown_signal.clear()
    # add_channel('tickers', INST_BTC_USDT_SWAP)
    add_channel('candle1m', INST_BTC_USDT_SWAP)
    asyncio.run(connect())


def shutdown():
    _shutdown_signal.append('shutdown')


def add_channel(channel: str, inst_id: str):
    key = _channel_key(channel, inst_id)
    if key in _subscribe or key in _subscribed:
        return None

    info = [{'channel': channel, 'instId': inst_id}]
    _subscribe[key] = info
    return info


def remove_channel(channel: str, inst_id: str):
    key = _channel_key(channel, inst_id)
    if key in _unsubscribe or key not in _subscribed:
        return None

    info = [{'channel': channel, 'instId': inst_id}]
    _unsubscribe[key] = info
    return info


def _channel_key(channel: str, inst_id: str):
    return hash(channel + inst_id)


if __name__ == '__main__':
    startup()

