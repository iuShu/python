import time

from aiohttp import web, WSMsgType, WSMessage
from aiohttp.web_request import Request

routes = web.RouteTableDef()
channels = []


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
    channels.append(ws)
    async for msg in ws:
        msg: WSMessage = msg
        if msg.type == WSMsgType.TEXT:
            resp = {
                'code': 200,
                'msg': 'success',
                'data': 'recv ' + msg.data
            }
            await ws.send_json(resp)
            if msg.data == 'wss-close':
                await ws.close()
    print('wss connection closed')
    return ws


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=5889)
