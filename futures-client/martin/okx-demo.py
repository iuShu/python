from config.api_config import conf
from okx.v5.account import Account
from okx.v5.consts import *


def train():
    json = conf('okx')
    account = Account(api_key=json['apikey'], api_secret_key=json['secretkey'], passphrase=json['passphrase'], test=True)

    # balance = account.get_account_balance('USDT')
    # print(balance)

    orders = account.get_order_history(inst_type=INST_TYPE_SWAP, inst_id=INST_BTC_USDT_SWAP, limit=5)
    print(orders)

    # detail = account.get_order_detail(inst_type=INST_TYPE_SWAP)
    # detail = account.get_order_detail_archive(inst_type=INST_TYPE_SWAP, ord_id='473073320380993536')
    # print(detail)

    # pending = account.get_pending_order()
    # print(pending)

    # info = account.get_order_info(inst_id='BTC-USDT-SWAP', ord_id='473073320380993536')
    # print(info)

    # algo_pending = account.get_algo_order_pending(algo_type=ALGO_TYPE_OCO, inst_type=INST_TYPE_SWAP)
    # print(algo_pending)

    # algo_history = account.get_algo_order_history(algo_type=ALGO_TYPE_OCO, inst_type=INST_TYPE_SWAP, state=ALGO_STATE_EFFECTIVE)
    # print(algo_history)

    # config = account.get_account_config()
    # print(config)

    # res = account.set_leverage(lever="100", mgn_mode=TD_MODE_ISOLATE, inst_id=INST_BTC_USDT_SWAP, pos_side=POS_SIDE_SHORT)
    # print(res)

    # leverage = account.get_leverage(inst_id=INST_BTC_USDT_SWAP, mgn_mode=TD_MODE_ISOLATE)
    # print(leverage)

    # swap_sell(account)  # short side

    # pending = account.get_pending_order(inst_type=INST_TYPE_SWAP, inst_id=INST_BTC_USDT_SWAP, ord_type=ORDER_TYPE_LIMIT)
    # print('pending', pending)

    # cancel = account.cancel_order(inst_id=INST_BTC_USDT_SWAP, ord_id='476175419176259584')
    # print(cancel)

    # ticker = account.market_ticker(INST_BTC_USDT_SWAP)
    # last_px = ticker['data'][0]['last']

    from strategy.simple import SimpleMAStrategy
    # candles = account.get_candles(INST_BTC_USDT_SWAP, bar='1m', limit=11)
    # print(candles)

    # stg = SimpleMAStrategy()
    # print(stg.can_execute(last_px, candles['data']))


def swap_sell(account):
    px = '23250.0'
    order = account.create_order(INST_BTC_USDT_SWAP, TD_MODE_ISOLATE, SIDE_SELL,
                                 ORDER_TYPE_LIMIT, sz='10', px=px, pos_side=POS_SIDE_SHORT)
    res = account.place_order(order)
    if res['code'] != '0':
        print('resp error', res)
        return

    data = res['data']
    for d in data:
        if d['sCode'] != '0':
            print('place order error', data)
            return

    print('place order success', data)
    pending = account.get_pending_order(inst_type=INST_TYPE_SWAP, inst_id=INST_BTC_USDT_SWAP, ord_type=ORDER_TYPE_LIMIT)
    print('pending', pending)


if __name__ == '__main__':
    train()
