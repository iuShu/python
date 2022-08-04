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

    def get_order_history(self, inst_type: str, uly='', inst_id='', ord_type='', state='', category='', before='', after='', limit=''):
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
        return self._request_with_params(GET, GET_ORDER_HISTORY, params=params)

    def get_order_history_archive(self, inst_type: str, uly='', inst_id='', ord_type='', state='', category='', before='', after='', limit=''):
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
        return self._request_with_params(GET, GET_ORDER_HISTORY_ARCHIVE, params=params)

    def get_order_detail(self, order_id='', uly='', inst_id='', inst_type='', before='', after='', begin='', end='', limit=''):
        """
        last 3 days
        """
        params = {}
        if order_id:
            params['ordId'] = order_id
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
        if params:
            return self._request_with_params(GET, GET_ORDER_DETAILS, params)
        return self._request_without_params(GET, GET_ORDER_DETAILS)

