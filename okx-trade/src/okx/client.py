import asyncio
import json

import aiohttp
from . import consts
from . import utils
from src.base import log, ValueHolder

singleton = ValueHolder()
APIKEY = ValueHolder()
SECRETKEY = ValueHolder()
PASSPHRASE = ValueHolder()
TEST = ValueHolder(False)


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
                    resp = await resp.json()
                    datas = await utils.valid_resp(resp)
                    return datas
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
                    resp = await resp.json()
                    datas = await utils.valid_resp(resp)
                    return datas
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

    @staticmethod
    def create_order(inst_id: str, td_mode: str, side: str, ord_type: str, sz: str, ccy='', cl_ord_id='', tag='',
                     pos_side='', px='', reduce_only='', tgt_ccy='', ban_amend='') -> dict:
        params = {'instId': inst_id, 'tdMode': td_mode, 'side': side, 'ordType': ord_type, 'sz': sz}
        if ccy:
            params['ccy'] = ccy
        if cl_ord_id:
            params['clOrdId'] = cl_ord_id
        if tag:
            params['tag'] = tag
        if pos_side:
            params['posSide'] = pos_side
        if px:
            if ord_type == consts.ORDER_TYPE_MARKET:
                raise ValueError('price param not available at market-price order')
            params['px'] = str(px)
        if reduce_only:
            params['reduceOnly'] = reduce_only
        if tgt_ccy:
            params['tgtCcy'] = tgt_ccy
        if ban_amend:
            params['banAmend'] = ban_amend
        return params

    async def place_order(self, order: dict):
        if not order:
            raise ValueError('order can not be NONE')
        return await self.post(consts.PLACE_ORDER, order)

    async def cancel_order(self, inst_id: str, ord_id='', cl_ord_id=''):
        if not ord_id and not cl_ord_id:
            raise ValueError('Either parameter ordId or clOrdId is required')
        params = {'instId': inst_id, 'ordId': ord_id, 'clOrdId': cl_ord_id}
        return await self.post(consts.CANCEL_ORDER, params)

    async def get_order_info(self, inst_id: str, ord_id='', cl_ord_id=''):
        if not ord_id and not cl_ord_id:
            raise ValueError('Either parameter ordId or clOrdId is required')
        params = {'instId': inst_id, 'ordId': ord_id, 'clOrdId': cl_ord_id}
        return await self.get(consts.GET_ORDER_INFO, params)

    @staticmethod
    def create_algo_oco(inst_id: str, td_mode: str, algo_type: str, side: str, sz: str,
                        tp_tri_px: str, sl_tri_px: str, tp_tri_px_type=consts.PRICE_TYPE_LAST, sl_tri_px_type=consts.PRICE_TYPE_LAST,
                        tp_ord_px='-1', sl_ord_px='-1', pos_side='', ccy='', tag='', tgt_ccy='', reduce_only=''):
        # -1 market price (default)
        params = {'instId': inst_id, 'tdMode': td_mode, 'ordType': algo_type, 'side': side, 'sz': sz,
                  'tpTriggerPx': tp_tri_px, 'tpTriggerPxType': tp_tri_px_type, 'tpOrdPx': tp_ord_px,
                  'slTriggerPx': sl_tri_px, 'slTriggerPxType': sl_tri_px_type, 'slOrdPx': sl_ord_px}
        if pos_side:
            params['posSide'] = pos_side
        if ccy:
            params['ccy'] = ccy
        if tag:
            params['tag'] = tag
        if tgt_ccy:
            params['tgtCcy'] = tgt_ccy
        if reduce_only:
            params['reduceOnly'] = reduce_only
        return params

    async def place_algo_oco(self, algo_order):
        if not algo_order:
            raise ValueError('algo order can not be NONE')
        return await self.post(consts.PLACE_ALGO_ORDER, algo_order)

    async def cancel_algo_oco(self, inst_id: str, algo_ids: list):
        if not algo_ids:
            raise ValueError('must provide at less one algoId')
        params = []
        for algo in algo_ids:
            params.append({'instId': inst_id, 'algoId': algo})
        return await self.post(consts.CANCEL_ALGO_ORDER, params)

    async def margin_balance(self, inst_id: str, pos_side: str, _type: str, amt: str, ccy='', auto='', loan_trans=''):
        params = {'instId': inst_id, 'posSide': pos_side, 'type': _type, 'amt': amt}
        if ccy:
            params['ccy'] = ccy
        if auto:
            params['auto'] = auto
        if loan_trans:
            params['loanTrans'] = loan_trans
        return await self.post(consts.MARGIN_BALANCE, params)


async def client() -> AioClient:
    if not singleton.value:
        if not APIKEY.value or not SECRETKEY.value or not PASSPHRASE.value:
            raise ValueError('initializing aio client requires config items')
        singleton.value = await create(APIKEY.value, SECRETKEY.value, PASSPHRASE.value, TEST.value)
    return singleton.value


async def create(apikey: str, secretkey: str, passphrase: str, test=False) -> AioClient:
    return AioClient(apikey, secretkey, passphrase, test)
