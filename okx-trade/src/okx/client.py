import asyncio
import json

import aiohttp
from . import consts
from . import utils
from src.base import log, ValueHolder

singleton = ValueHolder()


class AioClient:

    def __init__(self, apikey: str, secretkey: str, passphrase: str, test=False):
        self.session = aiohttp.ClientSession()
        self.apikey = apikey
        self.secretkey = secretkey
        self.passphrase = passphrase
        self.test = test

    async def get(self, path: str, params=None):
        url = consts.API_URL + path + utils.parse_params_to_str(params)
        timestamp = utils.get_timestamp()
        signature = utils.sign(utils.pre_hash(timestamp, consts.GET, path, ''), self.secretkey)
        headers = utils.get_header(self.apikey, signature.decode('utf-8'), timestamp, self.passphrase)
        if self.test:
            headers['x-simulated-trading'] = '1'
        async with self.session.get(url=url, headers=headers) as resp:
            if not str(resp.status).startswith('2'):
                await log.error('Get status %d', resp.status)
            else:
                try:
                    return await resp.json()
                except Exception:
                    await log.error('Invalid response content', exc_info=True)

    async def post(self, path: str, params=None):
        url = consts.API_URL + path
        timestamp = utils.get_timestamp()
        signature = utils.sign(utils.pre_hash(timestamp, consts.POST, path, json.dumps(params)), self.secretkey)
        headers = utils.get_header(self.apikey, signature.decode('utf-8'), timestamp, self.passphrase)
        if self.test:
            headers['x-simulated-trading'] = '1'
        async with self.session.post(url=url, headers=headers, data=params) as resp:
            if not str(resp.status).startswith('2'):
                await log.error('Post status %d', resp.status)
            else:
                try:
                    return await resp.json()
                except Exception:
                    await log.error('Invalid response content', exc_info=True)

    async def close(self):
        await self.session.close()
        await asyncio.sleep(.1)     # waiting for the session to close

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
        path = consts.MARKET_CANDLE_HISTORY if history else consts.MARKET_CANDLE
        return await self.get(path, params=params)


async def client(apikey='', secretkey='', passphrase='', test=False):
    if not singleton.value:
        if not apikey or not secretkey or not passphrase:
            raise ValueError('initializing aio client requires config items')
        singleton.value = await create(apikey, secretkey, passphrase, test)
    return singleton.value


async def create(apikey: str, secretkey: str, passphrase: str, test=False):
    return AioClient(apikey, secretkey, passphrase, test)
