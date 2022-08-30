import random
import asyncio
import aiodemo
from config import conf

from okx import stream
from okx.client import client, AioClient, APIKEY, SECRETKEY, PASSPHRASE, TEST
from okx.consts import INST_BTC_USDT_SWAP
from okx.utils import check_resp
from base import log

from martin.strategy import strategy


async def daemon(live: int):
    await log.info('daemon start')
    while live:
        await log.info(random.randint(10000, 100000))
        live -= 1
        await asyncio.sleep(.5)
    # await stream.close()
    await log.info('daemon end')


async def use_case():
    client: aiodemo.AioClient = await aiodemo.singleton()
    resp = await client.request(url=aiodemo.sample_url)
    print('>', resp)
    await client.close()


async def candles():    # test
    cli: AioClient = await client()
    resp = await cli.get_candles(inst_id=INST_BTC_USDT_SWAP, limit=4)
    data = check_resp(resp, True)
    if not data:
        await log.error('error request candle with %s', resp)
        return
    print('>', data)
    # await log.info(data)
    await cli.close()


def init_client():
    c = conf('okx')
    APIKEY.value = c['apikey']
    SECRETKEY.value = c['secretkey']
    PASSPHRASE.value = c['passphrase']
    TEST.value = True


async def wss():
    await stream.connect()


async def main():
    init_client()
    async_tasks = [
        asyncio.create_task(daemon(30)),
        # asyncio.create_task(use_case()),
        # asyncio.create_task(candles()),
        asyncio.create_task(wss()),
        asyncio.create_task(strategy()),
    ]
    await asyncio.wait(async_tasks)


if __name__ == '__main__':
    asyncio.run(main())
