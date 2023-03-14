import base64
import hmac
import json
import logging
from datetime import datetime

import requests

from src.config import sys, trade

action_set_lever = '/api/v5/account/set-leverage'
action_candles = '/api/v5/market/candles'
action_balance = '/api/v5/account/balance'
action_algo = '/api/v5/trade/order-algo'
action_close = '/api/v5/trade/close-position'

action_place_order = '/api/v5/trade/order'
action_place_orders = '/api/v5/trade/batch-orders'
action_order_detail = '/api/v5/trade/order'
action_order_history = '/api/v5/trade/orders-history'
action_cancel_order = '/api/v5/trade/cancel-order'
action_cancel_orders = '/api/v5/trade/cancel-batch-orders'


class RestApi:

    def __init__(self):
        self._host = sys('api_url')

    def _get(self, action: str, params=None):
        action += self.path_params(params)
        ts = self.timestamp()
        sign = self.signature(ts + 'GET' + action + '', sys('secret'))
        resp = requests.get(url=self._host + action, headers=self.headers(sign, ts))
        if not str(resp.status_code).startswith('2'):
            logging.warning(f'http get error at {self._host + action}, response with {resp.status_code} {resp.text}')
            return {}

        try:
            raw = resp.json()
            if raw.get('code') == '0':
                return raw['data']
            logging.error('http get error %s' % raw)
            return {}
        except Exception:
            logging.error('http get invalid response content', exc_info=True)

    def _post(self, action: str, params) -> dict:
        ts = self.timestamp()
        sign = self.signature(ts + 'POST' + action + json.dumps(params), sys('secret'))
        resp = requests.post(url=self._host + action, headers=self.headers(sign, ts), json=params)
        if not str(resp.status_code).startswith('2'):
            logging.warning(f'http post error at {self._host + action}, response with {resp.status_code} {resp.text}')
            return {}

        try:
            raw = resp.json()
            if raw.get('code') == '0':
                return raw['data']
            logging.error('http post error %s' % raw)
            return {}
        except Exception:
            logging.error('http post invalid response content', exc_info=True)

    def get_candle(self, inst_id: str, bar: str, before=0, after=0, limit=0) -> tuple:
        params = {'instId': inst_id, 'bar': bar}
        if before:
            params['before'] = str(before)
        if after:
            params['after'] = str(after)
        if limit:
            params['limit'] = limit
        return self._get(action_candles, params)

    def place_order(self, inst_id: str, td_mode: str, ord_type: str, side: str, pos_side: str, sz, px=.0) -> dict:
        params = {
            'instId': inst_id,
            'tdMode': td_mode,
            'ordType': ord_type,
            'side': side,
            'sz': str(sz)
        }
        if pos_side:
            params['posSide'] = pos_side
        if px:
            params['px'] = str(px)
        data = self._post(action_place_order, params)
        if data:
            if data[0]['sCode'] == '0' and len(data[0]['ordId']) > 0:
                return data[0]

        logging.error('place order error %s' % data)
        return {}

    def place_orders(self, inst_id: str, td_mode: str, ord_type: str, side: str, pos_side: str, sz: list, px=None) -> dict:
        body = []
        for i in range(0, len(sz)):
            params = {
                'instId': inst_id,
                'tdMode': td_mode,
                'ordType': ord_type,
                'side': side,
                'sz': str(sz[i])
            }
            if pos_side:
                params['posSide'] = pos_side
            if px:
                params['px'] = str(px[i])
            body.append(params)
        data = self._post(action_place_orders, body)
        if data:
            for each in data:
                if each['sCode'] != '0':
                    return {}
            return data

        logging.error('place batch orders error')
        return {}

    def order_detail(self, inst_id: str, ord_id: str) -> dict:
        params = {
            'instId': inst_id,
            'ordId': ord_id
        }
        data = self._get(action_order_detail, params)
        if data:
            return data[0]

        logging.error('get order detail error')
        return {}

    def last_filled_order(self, inst_id: str, inst_type: str) -> dict:
        params = {
            'instId': inst_id,
            'instType': inst_type,
            'state': 'filled',
            'limit': 1
        }
        data = self._get(action_order_history, params)
        if data:
            return data[0]

        logging.error('get order history error')
        return {}

    def cancel_order(self, inst_id: str, ord_id: str) -> bool:
        params = {
            'instId': inst_id,
            'ordId': ord_id
        }
        data = self._post(action_cancel_order, params)
        if data and data[0]['sCode'] == '0':
            return True

        logging.error('cancel order error')
        return False

    def cancel_orders(self, inst_id: str, ord_id: list) -> bool:
        body = [{'instId': inst_id, 'ordId': o} for o in ord_id]
        data = self._post(action_cancel_orders, body)
        if data:
            for each in data:
                if each['sCode'] != '0':
                    return False
            return True

        logging.error('cancel batch orders error')
        return False

    def place_algo(self, inst: str, inst_id: str, total_sz: float, side: str, pos_side: str, tp: float, sl: float) -> dict:
        params = {
            'instId': inst_id,
            'tdMode': trade(inst)['td_mode'],
            'posSide': pos_side,
            'side': side,
            'ordType': 'oco',
            'sz': total_sz,
            'tpTriggerPxType': 'last',
            'tpTriggerPx': str(tp),
            'tpOrdPx': '-1',
            'slTriggerPxType': 'last',
            'slTriggerPx': str(sl),
            'slOrdPx': '-1'
        }
        data = self._post(action_algo, params)
        if data and data[0]['sCode'] == '0':
            return data[0]

        logging.error('place algo error')
        return {}

    def cancel_algo(self, inst_id: str, algo_id: str) -> bool:
        params = {'instId': inst_id, 'algoId': algo_id}
        data = self._post(action_algo, [params])
        if data and data[0]['sCode'] == '0':
            return True

        logging.error('cancel algo error')
        return False

    def close_position(self, inst_id: str, td_mode: str, pos_side: str, auto_cancel=True) -> bool:
        params = {'instId': inst_id, 'mgnMode': td_mode, 'posSide': pos_side, 'autoCxl': auto_cancel}
        data = self._post(action_close, params)
        if data:
            return data[0]['instId'] == inst_id and data[0]['posSide'] == pos_side

        logging.error('close position error')
        return False

    def set_lever(self, inst_id: str, lever: int, mgn_mode: str, pos_side: str) -> bool:
        params = {
            'instId': inst_id,
            'lever': str(lever),
            'mgnMode': mgn_mode,
            'posSide': pos_side
        }
        data = self._post(action_set_lever, params)
        if data and data[0]['lever'] == str(lever):
            return True

        logging.error('%s set lever error' % inst_id)
        return False

    def get_balance(self, currency: str) -> float:
        params = {'ccy': currency}
        data = self._get(action_balance, params)
        if data:
            details = data[0]['details']
            if details:
                return details[0]['availEq']
        return 0.0

    @staticmethod
    def path_params(params: dict) -> str:
        if not params:
            return ''

        url = '?'
        for key, value in params.items():
            url = url + str(key) + '=' + str(value) + '&'
        return url[0:-1]

    @staticmethod
    def timestamp() -> str:
        now = datetime.utcnow()
        t = now.isoformat("T", "milliseconds")
        return t + "Z"

    @staticmethod
    def signature(message, secret) -> bytes:
        mac = hmac.new(bytes(secret, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)

    @staticmethod
    def headers(sign: bytes, timestamp: str) -> dict:
        header = dict()
        header['Content-Type'] = 'application/json'
        header['OK-ACCESS-KEY'] = sys('apikey')
        header['OK-ACCESS-SIGN'] = sign.decode(encoding='utf-8')
        header['OK-ACCESS-TIMESTAMP'] = timestamp
        header['OK-ACCESS-PASSPHRASE'] = sys('passphrase')
        if sys('env') == 'test':
            header['x-simulated-trading'] = '1'
        return header


api = RestApi()


if __name__ == '__main__':
    # last = '2023-02-21 17:45:00'
    # ts = int(time.mktime(time.strptime(last, '%Y-%m-%d %H:%M:%S')))
    #
    # candles = api.get_candle(inst_id='BTC-USDT-SWAP', bar='15m')
    # require = True
    # for c in candles:
    #     if c[0][:-3] == str(ts):
    #         require = False
    #     if require:
    #         t = int(c[0][:-3])
    #         ft = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
    #         print(ft, c)

    pass