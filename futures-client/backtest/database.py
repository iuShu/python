import traceback

from config.api_config import db_conf
import pymysql
from pymysql.connections import Connection

DEFAULT_DB_TYPE = 'mysql'
COLUMN_CACHE = dict()


class Conn:

    def __init__(self, conn: Connection):
        self._conn = conn
        self._active = True
        self._finish = True

    def cursor(self, cursor=None):
        if not self._active:
            raise RuntimeError('connection has been closed')
        self._finish = False
        return self._conn.cursor(cursor)

    def commit(self):
        if not self._active:
            raise RuntimeError('connection has been closed')
        self._conn.commit()
        self._finish = True

    def rollback(self):
        if not self._active:
            raise RuntimeError('connection has been closed')
        self._conn.rollback()
        self._finish = True

    def close(self):
        if self._active:
            self._conn.close()
            self._active = False

    def ping(self, reconnect: bool):
        if self._active:
            self._conn.ping(reconnect)


def connect(db_type=DEFAULT_DB_TYPE) -> Conn:
    try:
        info = db_conf(db_type)
        return Conn(pymysql.connect(**info))
    except Exception:
        traceback.print_exc()


DEF_CONN = connect()


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
    conn = DEF_CONN
    try:
        try:
            cursor = conn.cursor()
            cursor.execute(sql, args)
            return cursor.fetchall()
        except Exception:
            conn.ping(True)
    except Exception:
        traceback.print_exc()
        return None


def insert(table: str, col_values: tuple, new_id=False):
    conn = DEF_CONN
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


def insert_batch(table: str, col_values: tuple):
    conn = DEF_CONN
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
        return -1


if __name__ == '__main__':

    # print(table_columns('swap_btc_usdt_candle1m'))
    # print(columns_name('swap_btc_usdt_candle1m'))

    row = query('select * from swap_btc_usdt_candle1m limit 2')
    print(row)

    # values = ('100.001', '300.003', '200.001', '200.002', '18888.898981', '123123100.544001')
    # vals = tuple([values for i in range(50)])
    # print(insert('swap_btc_usdt_candle1m', values))
    # print(insert_batch('swap_btc_usdt_candle1m', vals))
