import traceback

from config.api_config import db_conf
import pymysql

DEFAULT_DB_TYPE = 'mysql'
COLUMN_CACHE = dict()


def connect(db_type=DEFAULT_DB_TYPE):
    try:
        info = db_conf(db_type)
        return pymysql.connect(**info)
    except Exception:
        traceback.print_exc()


def table_columns(table: str):
    cols = COLUMN_CACHE.get(table)
    if cols:
        return cols

    info = db_conf(DEFAULT_DB_TYPE)
    rows = query('select column_name, data_type, column_key from information_schema.columns '
                 'where table_schema=%s and table_name=%s', args=(info['database'], table,))
    if not rows:
        raise RuntimeError('can not found columns for table ' + table)

    if type(rows[0]) is not tuple:
        cols = [rows]
    else:
        cols = [row for row in rows]
    COLUMN_CACHE[table] = cols
    return cols


def columns_name(table: str, with_id=False) -> list:
    cols = table_columns(table)
    if with_id:
        return [col[0] for col in cols]
    return [col[0] for col in cols if col[2] != 'PRI']


def query(sql: str, args=None):
    conn = connect()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, args)
        return cursor.fetchall()
    except Exception:
        return None
    finally:
        conn.close()


def insert(table: str, col_values: tuple, new_id=False):
    conn = connect()
    try:
        cols = columns_name(table)
        columns = ','.join(cols)
        placeholder = ','.join(['%s' for i in range(len(cols))])
        sql = f'insert into {table}({columns}) values({placeholder});'
        cursor = conn.cursor()
        er = cursor.execute(sql, args=col_values)
        if er == 1:
            conn.commit()
        else:
            conn.rollback()
        return cursor.lastrowid if new_id else er
    except Exception:
        conn.rollback()
        traceback.print_exc()
    finally:
        conn.close()


def insert_batch(table: str, col_values: tuple):
    conn = connect()
    try:
        cols = columns_name(table)
        columns = ','.join(cols)
        placeholder = ','.join(['%s' for i in range(len(cols))])
        sql = f'insert into {table}({columns}) values({placeholder});'
        cursor = conn.cursor()
        er = cursor.executemany(sql, args=col_values)
        if er == len(col_values):
            conn.commit()
        else:
            conn.rollback()
        return er
    except Exception:
        conn.rollback()
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':

    # print(table_columns('swap_btc_usdt_candle1m'))
    # print(columns_name('swap_btc_usdt_candle1m'))

    # query('select * from swap_btc_usdt_candle1m')

    values = ('100.001', '300.003', '200.001', '200.002', '18888.898981', '123123100.544001')
    vals = tuple([values for i in range(50)])
    # print(insert('swap_btc_usdt_candle1m', values))
    print(insert_batch('swap_btc_usdt_candle1m', vals))
