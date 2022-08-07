import asyncio
import time
import traceback

from config.api_config import conf
from okx.v5.account import Account
from okx.v5.handler import Handler
from okx.v5.utils import log
from okx.v5.consts import *
from okx.v5 import stream

from core.price import LastPrice
from core.position import Isolated
from core.side import ShortSide
from core.fee import MakerFee
from core.utils import Computable
from martin.morder import MartinOrder


TRACE_MAX_TIMES = 30
TRACE_INTERVAL = 1
FOLLOW_GAP = 10.0


class MartinBot(Handler):

    def __init__(self, inst_id=INST_BTC_USDT_SWAP, test=True):
        channel = TICKERS_BTC_USDT_SWAP[0]
        Handler.__init__(self, channel['channel'], channel['instId'])
        self._inst_id = inst_id
        self._test_net = test
        self._client = self._init_client()
        self._mo = None
        self._algos = []
        self._event_loop = None

    def event_loop(self, event_loop=None):
        if not event_loop:
            return self._event_loop
        self._event_loop = event_loop
        return self

    def _handle(self, data):
        print(data)
        px = self._latest_px(data)

        try:
            if self._mo:
                self._follow(px)
            else:
                self._place_order(px)
        except Exception:
            traceback.print_exc()
            log.fatal('handle error, shutdown bot')
            self.shutdown()

    def _follow(self, px):
        px = Computable(float(px))
        spx = Computable(self._mo.stop_loss().stop_price())
        if spx - px <= FOLLOW_GAP:          # !!! short side
            nxt = self._mo.create_next()
            if not nxt:                     # reached end
                return
            self._mo = nxt
            nro = self._convert_order(nxt)
            self._place_order(nro)
            return

        # trace take profit order
        res = self._client.get_order_history(inst_type=INST_TYPE_SWAP, inst_id=self._inst_id, state=STATE_FILLED, limit=10)
        history = self._check_resp(res, 'trace take profit order')
        last_order = history[0]
        pnl, px, state = last_order['pnl'], last_order['px'], last_order['state']
        if pnl != '0' and px and state == STATE_FILLED:
            self._close_all()
            # self._mo = None         # next round
            # self._cancel_algos()    # next round
            self.shutdown()         # developing test

    def _place_order(self, px):
        mo = create_morder(px)
        order = self._convert_order(mo)
        if not order:
            log.warning('No order to be placed')
            return

        res = self._client.place_order(order)
        d = self._check_resp(res, 'place order')
        if not d:
            return

        ord_id = d['ordId']
        mo.state(STATE_LIVE)
        mo.ord_id(ord_id)
        self._mo = mo
        log.info('placed order %s', ord_id)
        if self._trace_order() and self._place_algo():
            log.info('order %s filled and algo placed', ord_id)
            return

        res = self._client.cancel_order(self._inst_id, ord_id=ord_id)
        self._check_resp(res, 'cancel order')
        log.warning('cancel order %s', ord_id)
        self._cancel_algos()
        self._mo = None
        self.shutdown()
        log.info('shutdown bot')
        log.warning('Please check the previous filled order!')

    def _trace_order(self) -> bool:
        try:
            ord_id = self._mo.ord_id()
            for i in range(TRACE_MAX_TIMES):
                info = self._client.get_order_info(inst_id=self._inst_id, ord_id=ord_id)
                if info['code'] != '0':
                    log.error('%d trace request error: %s', i, info['msg'])
                    raise RuntimeError('trace order error ' + ord_id)
                order = info['data'][0]
                state = order['state']
                log.info('%d trace order %s state %s', i, ord_id, state)
                if state == STATE_FILLED:
                    return True
                elif state == STATE_PARTIALLY_FILLED or state == STATE_LIVE:
                    time.sleep(TRACE_INTERVAL)
                    continue
                else:
                    log.warning('%d trace order %s have been canceled', i, ord_id)
                    return False
            return False
        except Exception:
            traceback.print_exc()
            return False

    def _place_algo(self) -> bool:
        pos = self._mo.position()
        tp, sl = self._mo.take_profit(), self._mo.stop_loss()
        algo = self._client.create_algo_oco(inst_id=self._inst_id, td_mode=pos.pos_type(), algo_type=ALGO_TYPE_OCO,
                                            side=SIDE_BUY, sz=str(pos.pos()),
                                            tp_tri_px=str(tp.stop_price()), sl_tri_px=str(sl.stop_price()))
        res = self._client.place_algo_oco(algo)
        data = self._check_resp(res, 'place algo')
        if data:
            self._algos.append(data['algoId'])
            return True
        return False

    def _cancel_algos(self):
        if not self._algos:
            return
        res = self._client.cancel_algo_oco(self._inst_id, self._algos)
        self._check_resp(res, 'cancel algo orders')
        self._algos.clear()

    def _close_all(self):
        pos = self._mo.position()
        res = self._client.close_position(inst_id=self._inst_id, mgn_mode=pos.pos_type(), pos_side=self._mo.side().side())
        self._check_resp(res, 'close position')

    def _init_client(self):
        json = conf('okx')
        account = Account(api_key=json['apikey'], api_secret_key=json['secretkey'], passphrase=json['passphrase'],
                          test=self._test_net)
        return account

    def _convert_order(self, mo: MartinOrder) -> dict:
        return self._client.create_order(inst_id=self._inst_id, td_mode=mo.position().pos_type(), side=SIDE_SELL,
                                         ord_type=ORDER_TYPE_LIMIT, sz=str(mo.position().pos()),
                                         pos_side=mo.side().side(), px=str(mo.start_price()))

    def shutdown(self):
        if self._event_loop:
            self._event_loop.close()

    @staticmethod
    def _latest_px(data):
        ts, px = 0, .0
        for d in data:
            t = int(d['ts'])
            if not px or t > ts:
                px = d['last']
                ts = t
        return px

    @staticmethod
    def _check_resp(res: dict, topic: str) -> dict:
        if res['code'] != '0':
            log.error('%s resp error %s', topic, res)
            return {}
        data = res['data']
        d = data[0]
        if 'sCode' in d and d['sCode'] != '0':
            log.error('%s error %s', topic, data)
            return {}
        return d


def create_morder(price) -> MartinOrder:
    p = LastPrice(float(price))
    sd = ShortSide()
    pos = Isolated(.1, p, 100)
    mf = MakerFee(.0005)

    mo = MartinOrder()
    mo.start_price(p).position(pos).side(sd).open_fee(mf).close_fee(mf)
    mo.step_rate(.004).profit_step_rate(.0002)
    mo.open_order()
    return mo


def run():
    bot = MartinBot()
    stream.register(bot)
    loop = stream.startup()
    bot.event_loop(loop)


if __name__ == '__main__':
    run()
