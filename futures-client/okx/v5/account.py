from .client import Client
from .consts import *


class Account(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, first=False):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, test, first)

    def get_account_config(self):
        return self._request_without_params(GET, ACCOUNT_CONFIG)

    def get_leverage(self, inst_id='', mgn_mode=''):
        params = {'instId': inst_id, 'mgnMode': mgn_mode}
        return self._request_with_params(GET, ACCOUNT_LEVERAGE, params)

    def set_leverage(self, lever: str, mgn_mode: str, inst_id='', ccy='', pos_side=''):
        params = {'lever': lever, 'mgnMode': mgn_mode}
        if not inst_id and not ccy:
            raise ValueError('Either parameter instId or ccy is required')
        if inst_id:
            params['instId'] = inst_id
        if ccy:
            params['ccy'] = ccy
        if pos_side:
            params['posSide'] = pos_side
        return self._request_with_params(POST, ACCOUNT_SET_LEVERAGE, params)

    def get_asset_balance(self, ccy=''):
        if ccy:
            return self._request_with_params(GET, ASSET_BALANCE, {'ccy': ccy})
        return self._request_without_params(GET, ASSET_BALANCE)

    def get_account_balance(self, ccy=''):
        if ccy:
            return self._request_with_params(GET, ACCOUNT_BALANCE, {'ccy': ccy})
        return self._request_without_params(GET, ACCOUNT_BALANCE)

    def get_order_info(self, inst_id: str, ord_id='', cl_ord_id=''):
        if not ord_id and not cl_ord_id:
            raise ValueError('Either parameter ordId or clOrdId is required')
        params = {'instId': inst_id, 'ordId': ord_id, 'clOrdId': cl_ord_id}
        return self._request_with_params(GET, GET_ORDER_INFO, params)

    def get_pending_order(self, inst_type='', uly='', inst_id='', ord_type='', state='', before='', after='', limit=''):
        params = {}
        if ord_type:
            params['ordType'] = ord_type
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if inst_type:
            params['instType'] = inst_type
        if state:
            params['state'] = state
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        if params:
            return self._request_with_params(GET, GET_PENDING_ORDER, params)
        return self._request_without_params(GET, GET_PENDING_ORDER)

    def get_order_history(self, inst_type: str, uly='', inst_id='', ord_type='', state='', category='', before='',
                          after='', limit='', archive=False):
        params = {'instType': inst_type}
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if ord_type:
            params['ordType'] = ord_type
        if state:
            params['state'] = state
        if category:
            params['category'] = category
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        if archive:
            return self._request_with_params(GET, GET_ORDER_HISTORY_ARCHIVE, params=params)
        return self._request_with_params(GET, GET_ORDER_HISTORY, params=params)

    def get_order_detail(self, ord_id='', uly='', inst_id='', inst_type='', before='', after='', begin='', end='',
                         limit='', archive=False):
        params = {}
        if ord_id:
            params['ordId'] = ord_id
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if inst_type:
            params['instType'] = inst_type
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if begin:
            params['begin'] = begin
        if end:
            params['end'] = end
        if limit:
            params['limit'] = limit
        path = GET_ORDER_DETAILS_ARCHIVE if archive else GET_ORDER_DETAILS
        if params:
            return self._request_with_params(GET, path, params)
        return self._request_without_params(GET, path)

    def get_order_detail_archive(self, inst_type: str, ord_id='', uly='', inst_id='', before='', after='',
                                 begin='', end='', limit=''):
        return self.get_order_detail(ord_id, uly, inst_id, inst_type, before, after, begin, end, limit, archive=True)

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
            if ord_type not in [ORDER_TYPE_LIMIT, ORDER_TYPE_POST_ONLY, ORDER_TYPE_FOK, ORDER_TYPE_IOC]:
                raise ValueError('price param not available')
            params['px'] = px
        if reduce_only:
            params['reduceOnly'] = reduce_only
        if tgt_ccy:
            params['tgtCcy'] = tgt_ccy
        if ban_amend:
            params['banAmend'] = ban_amend
        return params

    def place_order(self, order: dict):
        if not order:
            raise ValueError('order can not be NONE')
        return self._request_with_params(POST, PLACE_ORDER, order)

    def place_batch_order(self, orders: list):
        return self._request_with_params(POST, PLACE_BATCH_ORDERS, orders)

    def cancel_order(self, inst_id: str, ord_id='', cl_ord_id=''):
        if not ord_id and not cl_ord_id:
            raise ValueError('Either parameter ordId or clOrdId is required')
        params = {'instId': inst_id, 'ordId': ord_id, 'clOrdId': cl_ord_id}
        return self._request_with_params(POST, CANCEL_ORDER, params)

    def cancel_batch_order(self, cancels: list):
        if not cancels:
            raise ValueError('orders is null')
        return self._request_with_params(POST, CANCEL_ORDER, cancels)

    def close_position(self, inst_id: str, mgn_mode: str, pos_side='', ccy='', auto_cancel=False):
        """
        close all pos at market price
        """
        params = {'instId': inst_id, 'mgnMode': mgn_mode}
        if pos_side:
            params['posSide'] = pos_side
        if ccy:
            params['ccy'] = ccy
        if auto_cancel:
            params['autoCxl'] = 'true'
        return self._request_with_params(POST, CLOSE_POSITION, params)

    def get_algo_order_pending(self, algo_type: str, inst_type='', inst_id='', algo_id='', before='', after='', limit=''):
        params = {'ordType': algo_type}
        if inst_type:
            params['instType'] = inst_type
        if inst_id:
            params['instId'] = inst_id
        if algo_id:
            params['algoId'] = algo_id
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, ALGO_ORDER_PENDING, params)

    def get_algo_order_history(self, algo_type: str, algo_id='', state='', inst_type='', inst_id='',
                               before='', after='', limit=''):
        params = {'ordType': algo_type}
        if not algo_id and not state:
            raise ValueError('Either parameter state or algoId is required')
        if algo_id and state:
            raise ValueError('Only require one of the algoId or state')
        if inst_type:
            params['instType'] = inst_type
        if inst_id:
            params['instId'] = inst_id
        if algo_id:
            params['algoId'] = algo_id
        if state:
            params['state'] = state
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, ALGO_ORDER_HISTORY, params)

    @staticmethod
    def create_algo_oco(inst_id: str, td_mode: str, algo_type: str, side: str, sz: str,
                        tp_tri_px: str, sl_tri_px: str, tp_tri_px_type=PRICE_TYPE_LAST, sl_tri_px_type=PRICE_TYPE_LAST,
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

    def place_algo_oco(self, algo_order):
        if not algo_order:
            raise ValueError('algo order can not be NONE')
        return self._request_with_params(POST, PLACE_ALGO_ORDER, algo_order)

    def cancel_algo_oco(self, inst_id: str, algo_ids: list):
        if not algo_ids:
            raise ValueError('must provide at less one algoId')
        params = []
        for algo in algo_ids:
            params.append({'instId': inst_id, 'algoId': algo})
        return self._request_with_params(POST, CANCEL_ALGO_ORDER, params)

    def get_candles(self, inst_id: str, bar=BAR_15M, before='', after='', limit=''):
        params = {'instId': inst_id}
        if bar:
            params['bar'] = bar
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, MARKET_CANDLE, params)

    def market_ticker(self, inst_id: str):
        return self._request_with_params(GET, MARKET_TICKER, {'instId': inst_id})

    def margin_balance(self, inst_id: str, pos_side: str, _type: str, amt: str, ccy='', auto='', loan_trans=''):
        params = {'instId': inst_id, 'posSide': pos_side, 'type': _type, 'amt': amt}
        if ccy:
            params['ccy'] = ccy
        if auto:
            params['auto'] = auto
        if loan_trans:
            params['loanTrans'] = loan_trans
        return self._request_with_params(POST, MARGIN_BALANCE, params)
