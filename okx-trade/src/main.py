import random
import asyncio
import aiodemo
from config import conf

from okx import stream
from okx import client
from okx.consts import INST_BTC_USDT_SWAP
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
    cli: client.AioClient = await client.create(conf('okx'), test=True)
    datas = await cli.get_candles(inst_id=INST_BTC_USDT_SWAP, limit=4)
    if not datas:
        return
    await log.info(datas)
    await cli.close()


async def wss():
    await stream.connect()


async def main():
    async_tasks = [
        asyncio.create_task(daemon(20)),
        # asyncio.create_task(use_case()),
        # asyncio.create_task(candles()),
        asyncio.create_task(wss()),
        asyncio.create_task(strategy()),
    ]
    await asyncio.wait(async_tasks)


if __name__ == '__main__':
    asyncio.run(main())
