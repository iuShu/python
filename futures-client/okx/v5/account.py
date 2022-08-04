from .client import Client
from .consts import *


class Account(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, first=False):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, test, first)

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
            raise ValueError('ordId and clOrdId must provided one of them')
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

    def get_order_detail_archive(self, inst_type: str, ord_id='', uly='', inst_id='', before='', after='', begin='',
                                 end='', limit=''):
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
            raise ValueError('order is null')
        return self._request_with_params(POST, PLACE_ORDER, order)

    def place_batch_order(self, orders: list):
        return self._request_with_params(POST, PLACE_BATCH_ORDERS, orders)

    def cancel_order(self, inst_id: str, ord_id='', cl_ord_id=''):
        if not ord_id and not cl_ord_id:
            raise ValueError('ordId and clOrdId must provided one of them')
        params = {'instId': inst_id, 'ordId': ord_id, 'clOrdId': cl_ord_id}
        return self._request_with_params(POST, CANCEL_ORDER, params)

    def cancel_batch_order(self, cancels: list):
        if not cancels:
            raise ValueError('orders is null')
        return self._request_with_params(POST, CANCEL_ORDER, cancels)
