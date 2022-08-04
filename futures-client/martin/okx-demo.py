import inspect

from config.api_config import conf
from okx.v5.account import Account
from okx.v5.consts import *


def pre():
    json = conf('okx')
    account = Account(api_key=json['apikey'], api_secret_key=json['secretkey'], passphrase=json['passphrase'], test=True)

    # balance = account.get_account_balance('USDT')
    # print(balance)

    orders = account.get_order_history(INST_TYPE_SWAP)
    print(orders)

    # detail = account.get_order_detail()
    # print(detail)


if __name__ == '__main__':
    pre()
