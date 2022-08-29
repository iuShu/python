import random
import asyncio
import aiodemo
from config import conf

from okx.client import client, AioClient
from okx.consts import INST_BTC_USDT_SWAP
from okx.utils import check_resp
from base import log


async def daemon(live: int):
    print('daemon start')
    while live:
        print(random.randint(10000, 100000))
        live -= 1
        await asyncio.sleep(.5)
    print('daemon end')


async def use_case():
    client: aiodemo.AioClient = await aiodemo.singleton()
    resp = await client.request(url=aiodemo.sample_url)
    print('>', resp)
    await client.close()


async def candles():    # test
    c = conf('okx')
    cli: AioClient = await client(c['apikey'], c['secretkey'], c['passphrase'], test=True)
    resp = await cli.get_candles(inst_id=INST_BTC_USDT_SWAP, limit=4)
    data = check_resp(resp, True)
    if not data:
        await log.error('error request candle with %s', resp)
        return
    print('>', data)
    # await log.info(data)
    await cli.close()


async def main():
    async_tasks = [
        asyncio.create_task(daemon(10)),
        # asyncio.create_task(use_case()),
        asyncio.create_task(candles()),
    ]
    await asyncio.wait(async_tasks)


if __name__ == '__main__':
    asyncio.run(main())
