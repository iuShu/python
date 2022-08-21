from logger import log
from okx.v5.account import Account
from okx.v5.utils import check_resp
from martin.mto import MartinOrder


def place_order(client: Account, order: MartinOrder, ord_type: str):
    o = client.create_order(inst_id=order.inst_id, td_mode=order.pos_type, side=order.open_side(),
                            ord_type=ord_type, sz=str(order.pos), pos_side=order.pos_side)
    res = client.place_order(o)
    data = check_resp(res)
    if not data:
        log.error('place order error %s', res)
        return None
    return data


def cancel_order(client: Account, order: MartinOrder):
    pass


def cancel_algo(client: Account, algo_ids: list):
    pass


def close_pos(client: Account):
    pass

