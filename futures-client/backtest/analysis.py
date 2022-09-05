from backtest.database import query
from backtest.index import ftime
from backtest.index.highest import Highest
from backtest.index.lowest import Lowest
from backtest.index.fluctuate_rate import FluctuateRate
from backtest.index.long_trend import LongTrend


table = 'swap_btc_usdt_candle1m'


def process():
    indexes = [Highest(), Lowest(), FluctuateRate(), LongTrend()]
    page, page_size = 1, 100
    while True:
        rows = query(f'select ts, open, high, low, close from {table} where id < 116000 '
                     f'order by ts limit {(page - 1) * page_size},{page_size}')
        page += 1
        if not rows:
            break
        for row in rows:
            [ind.feed(row) for ind in indexes]
        print('finished', len(rows), ftime(int(rows[-1][0].timestamp())))
        if len(rows) < page_size:
            break
    print()
    [print(ind) for ind in indexes]


if __name__ == '__main__':
    process()
