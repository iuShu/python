import asyncio
import random

import aiohttp

sample_url = 'https://img-home.csdnimg.cn/images/20201124032511.png'


async def simple():
    session = aiohttp.ClientSession()
    async with session.get(url=sample_url) as resp:
        print(resp.status)
    await session.close()
    await asyncio.sleep(.1)


class AioClient:

    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def request(self, url: str):
        print('request')
        async with self.session.get(url=url) as resp:
            print('response')
            return resp.status

    async def close(self):
        print('closing session')
        await self.session.close()
        await asyncio.sleep(.1)     # waiting for the session to close


async def instance():
    inst = AioClient()
    ret = await inst.request(url=sample_url)
    print('return', ret)
    await asyncio.sleep(1)
    await inst.close()


async def daemon(live: int):
    print('daemon start')
    while live:
        print(random.randint(10000, 100000))
        live -= 1
        await asyncio.sleep(.5)
    print('daemon end')


if __name__ == '__main__':
    asyncio.run(simple())
