import time

from backtest.database import insert_batch
from config.api_config import conf, db_conf
from okx.v5.account import Account
from okx.v5.consts import INST_BTC_USDT_SWAP, BAR_1M
from okx.v5.utils import check_resp


def client():
    c = conf('okx')
    return Account(api_key=c['apikey'], api_secret_key=c['secretkey'], passphrase=c['passphrase'], test=True)


def gather():
    cli = client()
    ts = ''
    while True:
        res = cli.get_candles(inst_id=INST_BTC_USDT_SWAP, bar=BAR_1M, after=ts, history=True, limit=100)
        data = check_resp(res, True)
        if not data:
            print('no data after', ts)
            break

        ts = data[-1][0]
        td = []
        for d in data:
            lt = time.localtime(int(d[0]) / 1000)
            d[0] = time.strftime('%Y-%m-%d %H:%M:%S', lt)
            td.append(tuple(d))
        vals = tuple(td)
        er = insert_batch('swap_btc_usdt_candle1m', col_values=vals)
        if er != len(vals):
            print('insert failed after', data[-1][0])
            break
        print('request data after', data[-1][0])


if __name__ == '__main__':
    gather()
