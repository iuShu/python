import json

import aiohttp

from logger import log
from mtbot.okx.consts import *
from mtbot.okx.utils import get_timestamp, sign, get_header, pre_hash, parse_params_to_str


class AioClient:

    def __init__(self, apikey: str, secretkey: str, passphrase: str, test=False):
        self._session = aiohttp.ClientSession()
        self._apikey = apikey
        self._secret = secretkey
        self._passphrase = passphrase
        self._test = test

    async def _get(self, path: str, params=None):
        path = path + parse_params_to_str(params)
        url = API_URL + path
        timestamp = get_timestamp()
        signature = sign(pre_hash(timestamp, GET, path, ''), self._secret)
        headers = get_header(self._apikey, signature, timestamp, self._passphrase)
        if self._test:
            headers['x-simulated-trading'] = '1'
        async with self._session.get(url=url, headers=headers) as resp:
            return await self._response(resp)

    async def _post(self, path: str, params=None):
        url = API_URL + path
        timestamp = get_timestamp()
        signature = sign(pre_hash(timestamp, POST, path, json.dumps(params)), self._secret)
        headers = get_header(self._apikey, signature, timestamp, self._passphrase)
        if self._test:
            headers['x-simulated-trading'] = '1'
        async with self._session.post(url=url, headers=headers, data=params) as resp:
            return await self._response(resp)

    @staticmethod
    async def _response(resp):
        if not str(resp.status).startswith('2'):
            log.error('Response %d', resp.status)
            return None

        try:
            ret = await resp.json()
            log.info('ret', ret)
            return ret
        except Exception:
            log.error('Invalid response content', exc_info=True)

    async def close(self):
        await self._session.close()

    async def get_candles(self, inst_id: str, bar='', before='', after='', limit='', history=False):
        params = {'instId': inst_id}
        if bar:
            params['bar'] = bar
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        path = MARKET_CANDLE_HISTORY if history else MARKET_CANDLE
        return await self._get(path, params=params)
