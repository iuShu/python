import asyncio
import datetime
import json
import time

from logger import log
from asyncio.exceptions import TimeoutError

import websockets
from websockets.exceptions import ConnectionClosedError

from mtbot.okx.consts import *

_subscribers = []
_subscribe = dict()
_unsubscribe = dict()
_subscribed = dict()
_shutdown_signal = []


async def connect():
    while True:
        try:
            async with websockets.connect(WSS_PUBLIC_URL) as ws:
                log.info('websocket connected to %s', WSS_PUBLIC_URL)
                while not _shutdown_signal:
                    try:
                        await handle_channel(ws)
                        res = await asyncio.wait_for(ws.recv(), timeout=30)
                        log.debug('<< %s', res)
                    except ConnectionClosedError:
                        log.warning('IncompleteReadError caused this error, try re-connect')
                        break
                    except TimeoutError:
                        log.warning('CancelledError caused a timeout error, try continue')
                        continue
                    except Exception:
                        log.error('recv error', exc_info=True)
                        if await ping(ws):
                            log.warning('occurred error but ping ok, continue')
                            continue
                        break

                    try:
                        await dispatching(res)
                    except Exception:
                        log.error('dispatching process error, continue', exc_info=True)
                        continue
                if not _shutdown_signal:
                    log.error('subscribing error, reconnecting...')
                    _subscribe.update(_subscribed)
                    _subscribed.clear()
                else:
                    log.info('shutdown subscriber program')
                    await ws.close()
                    break
        except Exception:
            log.error('disconnected, try reconnecting...', exc_info=True)
            _subscribe.update(_subscribed)
            _subscribed.clear()


async def handle_channel(ws):
    if _subscribe:
        params = {'op': 'subscribe', 'args': _subscribe.popitem()[1]}
        text = json.dumps(params)
        log.debug('>> %s', text)
        await ws.send(text)
    if _unsubscribe:
        params = {'op': 'unsubscribe', 'args': _unsubscribe.popitem()[1]}
        text = json.dumps(params)
        log.debug('>> %s', text)
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
            key = channel_key(channel, inst_id)
            _subscribed[key] = [{'channel': channel, 'instId': inst_id}]
            log.info('subscribed: %s', [v for v in _subscribed.values()])
        elif event == 'unsubscribe':
            channel, inst_id = arg['channel'], arg['instId']
            key = channel_key(channel, inst_id)
            _subscribed.pop(key)
            log.info('subscribed: %s', [v for v in _subscribed.values()])
        else:
            log.warning('unknown event %s', event)
    elif 'data' in res:
        await handle_recv(res)
    else:
        log.warning('unknown response data %s', res)


async def handle_recv(resp):
    try:
        for s in _subscribers:
            await s.on_data(resp)
    except Exception:
        log.error('handle recv error', exc_info=True)


async def ping(ws):
    try:
        await ws.send('ping')
        resp = await ws.recv()
        if resp == 'pong':
            log.info('ping %s', resp)
            return True
        return False
    except Exception:
        return False


def local_time():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def register(subscriber):
    if not hasattr(subscriber, 'on_data'):
        raise TypeError('only accept class contained on_data method')
    if subscriber:
        _subscribers.append(subscriber)


def startup():
    # _shutdown_signal.clear()
    # add_channel('tickers', INST_BTC_USDT_SWAP)
    # add_channel('candle1m', INST_BTC_USDT_SWAP)
    # asyncio.run(connect())
    raise NotImplementedError('deprecated method')


def shutdown():
    _shutdown_signal.append('shutdown')


def add_channel(channel: str, inst_id: str):
    key = channel_key(channel, inst_id)
    if key in _subscribe or key in _subscribed:
        return None

    info = [{'channel': channel, 'instId': inst_id}]
    _subscribe[key] = info
    return info


def remove_channel(channel: str, inst_id: str):
    key = channel_key(channel, inst_id)
    if key in _unsubscribe or key not in _subscribed:
        return None

    info = [{'channel': channel, 'instId': inst_id}]
    _unsubscribe[key] = info
    return info


def channel_key(channel: str, inst_id: str):
    return hash(channel + inst_id)


if __name__ == '__main__':
    # startup()
    # lt = time.localtime(1640966400000 / 1000)
    lt = time.localtime(1653235200000 / 1000)
    # lt = time.localtime(1661269740000 / 1000)
    print(time.asctime(lt))
