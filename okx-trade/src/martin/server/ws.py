import json
import time
import traceback

from aiohttp import web, WSMsgType, WSMessage
from aiohttp.web_request import Request
from src.martin.setting import *

'''
    send message format
    {
        'op': str,
        'cid': int
        'mid': int,
        'data': obj
    }

    receive message format
    {
        'op': str,
        'mid': int,
        'code': int,
        'msg': str,
        'data': obj
    }
'''
routes = web.RouteTableDef()
id_pool = [0]

logins = dict()
channels = {
    NOTIFY_OP_NOTIFY: [],
    NOTIFY_OP_OPERATE: [],
}

code_200 = 200
msg_200 = 'success'
code_400 = 400
msg_400 = 'illegal data format'
code_401 = 401
msg_401 = 'please login first'
code_402 = 402
msg_402 = 'wrong login passphrase'
code_404 = 404
msg_404 = 'no such channel'
code_415 = 415
msg_415 = 'not allow empty data'


@routes.get('/')
async def hello(request: Request):
    resp = {
        'code': 200,
        'msg': 'success',
        'data': 'hello ' + str(int(time.time()))
    }
    return web.json_response(data=resp)


@routes.get('/ws')
async def handle_req(request: Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await ws.send_json(_wrap_resp(op='init', data=client_id()))
    async for msg in ws:
        msg: WSMessage = msg
        if msg.type == WSMsgType.TEXT:
            data = validate(msg)
            # print('recv', data)
            if not data:
                await ws.send_json(_wrap_resp(op='', code=code_400, msg=msg_400))
                continue
            if data.get('op') == NOTIFY_OP_OPERATE and data.get('data') == NOTIFY_CLOSE_SIGNAL:
                await ws.send_json(_wrap_resp(op=NOTIFY_OP_OPERATE, mid=data['mid']))
                await ws.close()
                break
            await handle_recv(ws, data)
    # print('ws connection closed')
    return ws


def validate(msg: WSMessage):
    try:
        packet = json.loads(msg.data)
        for key in ['op', 'cid', 'mid', 'data']:
            if key not in packet:
                return None
        return packet
    except Exception:
        traceback.print_exc()


async def handle_recv(ws, data: dict):
    await login(data, ws)
    await subscribe(data, ws)
    await notify(data, ws)


async def login(data: dict, ws):
    if data['op'] != NOTIFY_OP_LOGIN:
        return
    if data['data'] != NOTIFY_SERVICE_SECRET:
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_LOGIN, mid=data['mid'], code=code_402, msg=msg_402))
    else:
        logins[data['cid']] = 1
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_LOGIN, mid=data['mid'], msg='login success'))


async def subscribe(data: dict, ws):
    if data['op'] != NOTIFY_OP_SUBSCRIBE:
        return
    if not _is_login(data):
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_SUBSCRIBE, mid=data['mid'], code=code_401, msg=msg_401))
    elif data['data'] not in channels:
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_SUBSCRIBE, mid=data['mid'], code=code_404, msg=msg_404))
    else:
        channels[data['data']].append(ws)
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_SUBSCRIBE, mid=data['mid'], msg='subscribe success'))


async def notify(data: dict, ws):
    if data['op'] != NOTIFY_OP_NOTIFY:
        return
    if not _is_login(data):
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_NOTIFY, mid=data['mid'], code=code_401, msg=msg_401))
    elif not data['data']:
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_NOTIFY, mid=data['mid'], code=code_415, msg=msg_415))
    else:
        msg = data['data']
        if type(msg) != dict or 'topic' not in msg or 'msg' not in msg:
            await ws.send_json(_wrap_resp(op=NOTIFY_OP_NOTIFY, mid=data['mid'], code=code_400, msg=msg_400))
            return
        subscribers: list = channels[msg['topic']]
        for each in subscribers:
            channel: web.WebSocketResponse = each
            if channel.closed:
                subscribers.remove(channel)
                continue
            await channel.send_json(_wrap_resp(op=NOTIFY_OP_NOTIFY, data=json.dumps(msg)))
        await ws.send_json(_wrap_resp(op=NOTIFY_OP_NOTIFY, mid=data['mid']))


def client_id() -> int:
    id_pool[0] += 1
    return id_pool[0]


def _is_login(data) -> bool:
    return data and data['cid'] in logins


def _wrap_resp(op: str, mid=0, code=code_200, msg=msg_200, data=None) -> dict:
    return {
        'op': op,
        'code': code,
        'msg': msg,
        'mid': mid,
        'data': data if data else ''
    }


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=5889)
