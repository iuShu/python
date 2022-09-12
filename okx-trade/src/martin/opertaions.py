from src.base import log
from src.okx.client import AioClient
from src.okx.consts import STATE_LIVE, STATE_FILLED, ALGO_TYPE_OCO, MARGIN_BALANCE_ADD
from . import morder
from .setting import INST_ID


async def place_order(order: morder.MartinOrder, client: AioClient) -> bool:
    created = client.create_order(inst_id=INST_ID, td_mode=order.pos_type, side=order.open_type,
                                  pos_side=order.pos_side, ord_type=order.ord_type, sz=str(order.pos), px=order.px)
    datas = await client.place_order(created)
    if datas:
        await log.info('placed order=%d with pos=%d at px=%s' % (order.index(), order.pos, order.px))
        return True


async def place_algo(client: AioClient) -> bool:
    order = morder.order()
    if not order or order.state != STATE_FILLED or order.algo_id:
        return False

    prev: morder.MartinOrder = order.prev
    if prev and prev.algo_id:
        datas = await client.cancel_algo_oco(inst_id=INST_ID, algo_ids=[prev.algo_id])
        if not datas:
            await log.error('cancel prev algo=%d failed' % prev.index())
        else:
            prev.algo_id = None
            await log.info('cancel prev algo=%d success' % prev.index())

    tpx = str(order.profit_price())
    spx = str(order.stop_loss_price())
    full_pos = str(order.full_pos())
    algo = client.create_algo_oco(inst_id=INST_ID, td_mode=order.pos_type, algo_type=ALGO_TYPE_OCO, sz=full_pos,
                                  side=order.close_type, tp_tri_px=tpx, sl_tri_px=spx, pos_side=order.pos_side)
    await log.info('place algo=%d at tp=%s sl=%s fp=%s' % (order.index(), tpx, spx, full_pos))
    datas = await client.place_algo_oco(algo)
    if not datas:
        return False

    order.algo_id = datas[0]['algoId']
    await log.info('place algo=%d success' % order.index())
    return True


async def add_margin_balance(client: AioClient) -> bool:
    order = morder.order()
    if not order or order.state != STATE_FILLED or order.extra_margin != 0:
        return False

    extra = order.extra_margin_balance()
    if not extra:
        order.extra_margin = -1
        await log.info('order=%d has enough margin balance' % order.index())
        return True

    datas = await client.margin_balance(inst_id=INST_ID, pos_side=order.pos_side, _type=MARGIN_BALANCE_ADD, amt=str(extra))
    if not datas:
        return False

    order.extra_margin = extra
    await log.info('order=%d added %f margin' % (order.index(), extra))
    return True


async def close_pending(cli: AioClient):
    pending = morder.pending()
    if not pending or pending.state != STATE_LIVE:
        return

    datas = await cli.cancel_order(INST_ID, ord_id=pending.ord_id)
    if not datas:
        await log.warning('pending order=%d at px=%f fp=%d has been filled unexpectedly'
                          % (pending.index(), pending.px, pending.full_pos()))
        pending.as_first_order()
        return
    morder.set_pending(None)
    await log.info('cancel pending order=%d at px=%f' % (pending.index(), pending.px))


async def close_all_position(client: AioClient):
    order = morder.order()
    if not order or order.state != STATE_FILLED or not order.algo_id:
        return

    datas = await client.close_position(inst_id=INST_ID, mgn_mode=order.pos_type,
                                        pos_side=order.pos_side, auto_cancel=True)
    if datas:
        return True
