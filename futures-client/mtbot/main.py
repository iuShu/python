import asyncio
import logging
import random

from logger import log
from mtbot.data import channel
from mtbot.initiator import initiate
from mtbot.ma import strategy
from mtbot.pain import pain
from mtbot.tracer import trace
from mtbot.confirm import confirm


async def main():
    tasks = [
        asyncio.create_task(channel()),
        asyncio.create_task(pain()),
        asyncio.create_task(strategy()),
        # asyncio.create_task(initiate()),
        # asyncio.create_task(trace()),
        # asyncio.create_task(confirm()),
    ]
    await asyncio.wait(fs=tasks)


if __name__ == '__main__':
    log.setLevel(logging.INFO)
    asyncio.run(main())
