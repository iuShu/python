import asyncio
import base64
import hmac
import logging
import time

import aiohttp

from src.config import ntf


class Notifier:

    def ws_interrupt(self, text: str):
        pass

    def ws_reconnect(self, text: str):
        pass

    def order_error(self, text: str):
        pass

    def order_filled(self, text: str):
        pass

    def order_closed(self, text: str):
        pass

    def trade_stop(self, text: str):
        pass

    def undercost(self, balance: float, cost: float, inst_id: str):
        pass

    def sys_exit(self):
        pass


class DingtalkNotifier(Notifier):

    _webhook = ntf('dingtalk')['webhook']
    _secret = ntf('dingtalk')['secret']
    _rate_limited = ntf('dingtalk')['rate_limited']
    _limited_duration = ntf('dingtalk')['limited_duration']     # sec

    _queue = []
    _pending = []
    _order = 0
    _drainer = None

    def ws_interrupt(self, text: str):
        msg = f'**Client Interrupt**\n----\n{text}\n\n----\n{self.ts2format()}'
        self._send('Client Interrupt', msg)

    def ws_reconnect(self, text: str):
        msg = f'**Client Reconnect**\n----\n{text}\n\n----\n{self.ts2format()}'
        self._send('Client Reconnect', msg)

    def order_error(self, text: str):
        msg = f'**Order Error**\n----\n{text}\n\n----\n{self.ts2format()}'
        self._send('Order Error', msg)

    def order_filled(self, text: str):
        msg = f'**Order Fill**\n----\n{text}\n\n----\n{self.ts2format()}'
        self._send('Order Fill', msg)

    def order_closed(self, text: str):
        msg = f'**Order Close**\n----\n{text}\n\n----\n{self.ts2format()}'
        self._send('Order Close', msg)

    def trade_stop(self, text: str):
        msg = f'**Trade Stop**\n----\n{text}\n\n----\n{self.ts2format()}'
        self._send('Trade Stop', msg)

    def undercost(self, balance: float, cost: float, inst_id: str):
        msg = f'**Undercost**\n----\n\nnot enough cost for trading\n{inst_id}\nbln={balance}, cost={cost}\n\n----\n{self.ts2format()}'
        self._send('Undercost', msg)

    def sys_exit(self):
        msg = '**System Exit**\n----\n\nsystem exit, be aware of orders in running/pending\n\n----\n' + self.ts2format()
        self._send('System Exit', msg)

    def _send(self, title: str, msg: str):
        if ntf('mute_all'):
            return

        logging.info('notify %s' % title)
        packet = {'msgtype': 'markdown', 'markdown': {'title': title, 'text': msg}}
        if not self._rate_limit(packet):
            self._order += 1
            packet['markdown']['text'] = packet['markdown']['text'] + f' [{self._order}]'
            asyncio.create_task(self._async_send(packet))

    def _rate_limit(self, packet: dict) -> bool:
        if len(self._queue) < self._rate_limited:
            self._queue.append([int(time.time()), packet])
            if len(self._queue) > self._rate_limited:
                self._queue.pop()
            return False

        if len(self._queue) >= self._rate_limited:
            earliest, current = self._queue[0][0], int(time.time())
            if current - earliest > self._limited_duration:
                self._queue.append([int(time.time()), packet])
                if len(self._queue) > self._rate_limited:
                    self._queue.pop()
                return False
            else:
                self._pending.append(packet)
                if not self._drainer:
                    self._drainer = asyncio.create_task(self._drain_msg())
                return True
        return True

    async def _async_send(self, packet: dict):
        ts = time.time() * 1000
        sign = self.signature(f'{ts}\n{self._secret}', self._secret)
        url = f'{self._webhook}&timestamp={ts}&sign={sign}'
        async with aiohttp.ClientSession() as session:
            await session.post(url=url, data=packet)

    async def _drain_msg(self):
        while True:
            text = []
            while self._pending:
                packet = self._pending.pop()
                text.append(packet['markdown']['text'])
            self._send('Combined Messages', '\n----\n'.join(text))
            await asyncio.sleep(2.0)

    @staticmethod
    def ts2format() -> str:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))

    @staticmethod
    def signature(message, secret) -> bytes:
        mac = hmac.new(bytes(secret, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)


_notifier_mapping = {
    'windows': None,
    'dingtalk': DingtalkNotifier(),
    'wechat': None,
    'telegram': None,
}


class NotifierContext(Notifier):

    _notifiers = []

    def __init__(self):
        available = ntf('available')
        if available:
            for n in available:
                self._notifiers.append(_notifier_mapping[n])
        self._notifiers.append(Notifier())  # default

    def ws_interrupt(self, text: str):
        for n in self._notifiers:
            n.ws_interrupt(text)

    def ws_reconnect(self, text: str):
        for n in self._notifiers:
            n.ws_reconnect(text)

    def order_error(self, text: str):
        for n in self._notifiers:
            n.order_error(text)

    def order_filled(self, text: str):
        for n in self._notifiers:
            n.order_filled(text)

    def order_closed(self, text: str):
        for n in self._notifiers:
            n.order_closed(text)

    def trade_stop(self, text: str):
        for n in self._notifiers:
            n.trade_stop(text)

    def undercost(self, balance: float, cost: float, inst_id: str):
        for n in self._notifiers:
            n.undercost(balance, cost, inst_id)

    def sys_exit(self):
        for n in self._notifiers:
            n.sys_exit()


notifier = NotifierContext()

