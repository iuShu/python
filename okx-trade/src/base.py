import asyncio
import sys
from os.path import dirname, split
from aiologger import Logger
from aiologger.levels import LogLevel
from aiologger.handlers.files import AsyncFileHandler
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.formatters.base import Formatter

PROJECT_NAME = split(dirname(dirname(__file__)))[1]
DEFAULT_ENCODING = 'utf-8'
DEFAULT_LOG_STYLE = '%(levelname)s %(asctime)s %(filename)s:%(lineno)d %(message)s'
DEFAULT_LOG_FILE = f'../{PROJECT_NAME}.log'


def init_aio_logger() -> Logger:
    formatter = Formatter(fmt=DEFAULT_LOG_STYLE)
    handler = AsyncFileHandler(filename=DEFAULT_LOG_FILE, encoding=DEFAULT_ENCODING)
    handler.formatter = formatter
    logger: Logger = Logger(name=PROJECT_NAME, level=LogLevel.INFO)
    logger.add_handler(handler)
    return logger


def init_aio_sys_logger() -> Logger:    # to be fixed
    return Logger.with_default_handlers()


log = init_aio_logger()
# log = init_aio_sys_logger()


async def test():
    await log.debug('111 debug')
    await log.info('222 info')
    await log.warning('333 warn')
    await log.error('444 error')
    await log.critical('555 critical')
    await log.critical('666 critical 不可以')


class ValueHolder:

    def __init__(self, value=None):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


start = ValueHolder(False)
running = ValueHolder(False)
pipes = dict()
pending = dict()
subscribe = dict()


if __name__ == '__main__':
    asyncio.run(test())
