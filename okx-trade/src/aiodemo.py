import asyncio
import random
import aiohttp
from base import ValueHolder

# sample_url = 'https://img-home.csdnimg.cn/images/20201124032511.png'
sample_url = 'https://github.com/iuShu'


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


# client = AioClient()
client = ValueHolder()


async def singleton():
    if not client.value:
        client.value = await create()
    return client.value


async def create():
    return AioClient()


if __name__ == '__main__':
    asyncio.run(simple())
