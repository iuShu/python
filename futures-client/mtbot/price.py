from asyncio import Queue

from logger import log
from mtbot.data import PIPES, STARTED, TICKERS


async def price():
    while not STARTED:
        pass

    log.info('trace start')
    pipe: Queue = PIPES.get(TICKERS)
    
