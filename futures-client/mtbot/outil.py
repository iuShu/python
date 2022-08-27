from logger import log
from mtbot.okx.utils import check_resp
from mtbot.data import CLIENT, ValueHolder
from mtbot.mo import MartinOrder, PENDING, ORDER
from mtbot.setting import INST_ID, STATE_LIVE, STATE_FILLED, ALGO_TYPE_OCO, MARGIN_BALANCE_ADD

confirm_failed = ValueHolder(0)
place_algo_failed = ValueHolder(0)
extra_margin_failed = ValueHolder(0)


async def place_order(order: MartinOrder) -> bool:
    created = CLIENT.create_order(inst_id=INST_ID, td_mode=order.pos_type, side=order.open_type,
                                  pos_side=order.pos_side, ord_type=order.ord_type, sz=str(order.pos), px=order.px)
    resp = await CLIENT.place_order(created)
    data = check_resp(resp)
    if not data:
        log.error('place order-%d failed with %s', order.index(), resp)
        return False

    order.ord_id = data['ordId']
    order.state = STATE_LIVE
    PENDING.value = order
    log.info('placed order-%d with pos-%d', order.index(), order.pos)
    return True


async def confirm_order() -> bool:
    order: MartinOrder = PENDING.value
    if not order:
        return False

    resp = await CLIENT.get_order_info(inst_id=INST_ID, ord_id=order.ord_id)
    data = check_resp(resp)
    if not data:
        log.error('confirm order-%d info failed with %s', order.index(), resp)
        confirm_failed.value += 1
        return False

    state = data['state']
    if state != STATE_FILLED:
        log.debug('confirm order-%d at %s', order.index(), state)
        return False

    order.state = state
    order.px = float(data['fillPx'])
    order.ctime = data['cTime']
    order.utime = data['uTime']
    ORDER.value = order
    PENDING.value = None
    log.info('confirm order-%d at px-%f', order.index(), order.px)
    return True


async def place_algo() -> bool:
    order: MartinOrder = ORDER.value
    if not order or order.state != STATE_FILLED:
        return False

    if order.prev:
        resp = await CLIENT.cancel_algo_oco(inst_id=INST_ID, algo_ids=[order.prev.algo_id])
        data = check_resp(resp)
        if not data:
            log.error('cancel prev algo-%d failed with %s', order.prev.index(), resp)
            return False
        log.info('cancel prev algo-%d success', order.prev.index())

    tpx = str(order.profit_price())
    spx = str(order.stop_loss_price())
    full_pos = str(order.full_pos())
    algo = CLIENT.create_algo_oco(inst_id=INST_ID, td_mode=order.pos_type, algo_type=ALGO_TYPE_OCO, sz=full_pos,
                                  side=order.close_type, tp_tri_px=tpx, sl_tri_px=spx, pos_side=order.pos_side)
    log.info('place algo-%d at tp-%s sl-%s fp-%s', order.index(), tpx, spx, full_pos)
    resp = CLIENT.place_algo_oco(algo)
    data = check_resp(resp)
    if not data:
        log.error('place algo-%d failed with %s', order.index(), resp)
        place_algo_failed.value += 1
        return False
    log.info('place algo-%d success', order.index())
    return True


async def add_margin_balance() -> bool:
    order: MartinOrder = ORDER.value
    if not order or order.state != STATE_FILLED:
        return False

    extra = order.extra_margin_balance()
    if not extra:
        log.info('enough margin balance')
        return True

    resp = CLIENT.margin_balance(inst_id=INST_ID, pos_side=order.pos_side, _type=MARGIN_BALANCE_ADD, amt=str(extra))
    data = check_resp(resp)
    if not data:
        log.error('add margin-%d %f failed with %s', order.index(), extra, resp)
        extra_margin_failed.value += 1
        return False
    log.info('add margin-%d %f success', order.index(), extra)
    return True
