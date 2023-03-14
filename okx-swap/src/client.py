import asyncio
import json
import logging
import aiohttp
from aiohttp.http_websocket import WSMsgType
from asyncio.exceptions import CancelledError, TimeoutError
from listener import Listener
from src.config import sys, trade
from src.notifier import notifier


MSG_CLOSE_TYPES = [WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED]
NOTIFY_INTERVAL = 5


class _OkxWsClient:

    def __init__(self, url):
        self._url = url
        self._heartbeat_interval = sys('heartbeat_interval')
        self._read_timeout = sys('read_timeout')
        self.listeners = set()

        self.ws = None
        self._running = False
        self._available = False

        self._finish_stop = False

    async def connect(self):
        session = aiohttp.ClientSession()
        interrupted, reconnect_time, self._running = False, 1, True
        while self._running:
            async with session.ws_connect(url=self._url, timeout=self._read_timeout, heartbeat=self._heartbeat_interval, autoping=True, verify_ssl=False) as ws:
                try:
                    logging.info(f'client connected to {self._url}')
                    self.ws = ws
                    if reconnect_time > 1:
                        await self.on_reconnect()
                    await self.after_connected()
                    interrupted, self._available = False, True

                    while self._running:
                        msg = await ws.receive(timeout=self._read_timeout)
                        if msg.type in MSG_CLOSE_TYPES:
                            logging.warning(f'recv close msg, {msg}')
                            interrupted, self._available = True, False
                            break
                        elif msg.type != WSMsgType.TEXT:
                            logging.warning(f'unknown msg {msg}')
                        else:
                            await self.dispatch(json.loads(msg.data))

                        stop = 0
                        for lsn in self.listeners:
                            if lsn.is_stop():
                                stop += 1
                            elif self._finish_stop:
                                lsn.finish_stop()
                        # logging.debug('sys %s %s' % (stop, len(self.listeners)))
                        if stop == len(self.listeners):
                            self.stop()
                except (CancelledError, TimeoutError) as e:
                    logging.error('client interrupted due to %s' % type(e))
                    interrupted, self._available = True, False
                except Exception:
                    logging.error('client eventloop unknown error, exit', exc_info=True)
                    self.stop()

            if interrupted:
                logging.warning(f'client try {reconnect_time} reconnect')
                reconnect_time += 1
                await self.on_interrupted()
            else:
                await ws.close()
                await session.close()
                logging.info('client shutdown')
                raise SystemExit(1)

    async def after_connected(self):
        pass

    async def on_interrupted(self):
        pass

    async def on_reconnect(self):
        pass

    async def dispatch(self, data: dict):
        pass

    def is_running(self):
        return self._running

    def is_available(self):
        return self._available

    def finish_stop(self):
        self._finish_stop = True

    def stop(self):
        self._available, self._running = False, False

    def register(self, listener: Listener):
        listener.owner(self)
        listener.prepare()
        self.listeners.add(listener)

    def send(self, msg: dict):
        asyncio.create_task(self.ws.send_json(msg))

    def check(self):
        return self._available and self._running and self.ws


class OkxPublicClient(_OkxWsClient):

    subscribing = dict()
    subscribed = dict()

    async def after_connected(self):
        await self.subscribe()

    async def on_interrupted(self):
        notifier.ws_interrupt('ws public client interrupted')

    async def on_reconnect(self):
        notifier.ws_reconnect('ws public client reconnected')

    async def dispatch(self, data: dict):
        data['from'] = 'public'
        for listener in self.listeners:
            if not listener.is_stop() and listener.consumable(data):
                await listener.consume(data)

    async def subscribe(self):
        channels, deduplicate = [], set()
        for listener in self.listeners:
            if (hash(listener.inst_id() + listener.channel())) not in deduplicate:
                channels.append({'instId': listener.inst_id(), 'channel': listener.channel()})
                deduplicate.add(hash(listener.inst_id() + listener.channel()))
        packet = {'op': 'subscribe', 'args': channels}
        self.send(packet)

        self.subscribing.clear()
        self.subscribed.clear()
        for channel in channels:
            self.subscribing[hash(channel['instId'] + channel['channel'])] = channel
            logging.info('subscribing channels %s %s' % (channel['instId'], channel['channel']))
        await self.confirm_subscribe()

    async def confirm_subscribe(self):
        max_loop = 16
        while len(self.subscribing) != len(self.subscribed) and max_loop:
            msg = await self.ws.receive_json(timeout=self._read_timeout)
            evt = msg['event'] if 'event' in msg else ''
            if evt == 'subscribe':
                arg = msg['arg']
                key = hash(arg['instId'] + arg['channel'])
                channel = self.subscribing[key]
                if not channel:
                    logging.error('recv unsubscribe channel ' + channel)
                    raise SystemExit(1)
                self.subscribed[key] = channel
                logging.info('subscribed channel %s %s' % tuple(channel.values()))
            max_loop -= 1

        if len(self.subscribing) != len(self.subscribed):
            logging.error('channel not fully subscribed')
            raise SystemExit(1)


# class OkxPrivateClient(OkxPublicClient):
#
#     async def after_connected(self):
#         await self.login()
#         await self.subscribe()
#
#     async def on_interrupted(self):
#         notifier.ws_interrupt('ws private client interrupted')
#
#     async def on_reconnect(self):
#         notifier.ws_interrupt('ws private client reconnected')
#
#     async def dispatch(self, data: dict):
#         data['from'] = 'private'
#         for listener in self.listeners:
#             if listener.consumable(data):
#                 await listener.consume(data)
#
#     async def login(self):
#         pass
#
#     async def subscribe(self):
#         channels = []
#         for listener in self.listeners:
#             channels.append({'instId': listener.inst_id(), 'channel': 'orders'})
#         packet = {'op': 'subscribe', 'args': channels}
#         self.send(packet)
#
#         self.subscribing.clear()
#         self.subscribed.clear()
#         for channel in channels:
#             self.subscribing[hash(channel['instId'] + channel['channel'])] = channel
#         await self.confirm_subscribe()


if __name__ == '__main__':
    pass
