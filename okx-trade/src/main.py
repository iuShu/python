import random
import asyncio
import aiodemo
from config import conf

from okx import stream, client, private
from okx.consts import INST_BTC_USDT_SWAP
from base import log

from martin.strategy import strategy
from martin.initiator import initiate
from martin.stalker import stalk
from martin.confirm import confirm
from martin.checker import check


async def daemon(live: int):
    await log.info('daemon start')
    while live:
        await log.info(random.randint(10000, 100000))
        live -= 1
        await asyncio.sleep(.5)
    # await stream.close()
    await log.info('daemon end')


# async def use_case():
#     client: aiodemo.AioClient = await aiodemo.singleton()
#     resp = await client.request(url=aiodemo.sample_url)
#     print('>', resp)
#     await client.close()


async def candles():    # test
    cli: client.AioClient = await client.create(conf('okx'), test=True)
    datas = await cli.get_candles(inst_id=INST_BTC_USDT_SWAP, limit=4)
    if not datas:
        return
    await log.info(datas)
    await cli.close()


async def wss_public():
    await stream.connect()


async def wss_private():
    await private.connect()


async def main():
    async_tasks = [
        # asyncio.create_task(daemon(100)),
        # asyncio.create_task(use_case()),
        # asyncio.create_task(candles()),
        asyncio.create_task(wss_public()),
        asyncio.create_task(wss_private()),
        asyncio.create_task(strategy()),
        asyncio.create_task(initiate()),
        asyncio.create_task(stalk()),
        asyncio.create_task(confirm()),
        asyncio.create_task(check()),
    ]
    await asyncio.wait(async_tasks)


if __name__ == '__main__':
    asyncio.run(main())
