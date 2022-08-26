import logging
import os
import sys
from logging import FileHandler, Formatter, Filter
from logging.handlers import QueueHandler, QueueListener
import queue


class CustomHandler(FileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=False, errors=None):
        FileHandler.__init__(self, filename, mode, encoding, delay, errors)
        self._stdout = sys.stdout
        self.formatter = Formatter(fmt='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')

    def emit(self, record: logging.LogRecord) -> None:
        if record.name == 'websockets.client':
            return
        try:
            msg = self.format(record)
            self._stdout.write(msg + self.terminator)
            if record.levelno > logging.DEBUG:
                self.stream.write(msg + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)


log_dir = os.path.dirname(__file__)
log_file = os.path.join(log_dir, 'app.log')

queue = queue.Queue()
log = logging.root
log.setLevel(logging.DEBUG)
log.addFilter(Filter('root'))
log.addHandler(QueueHandler(queue))
QueueListener(queue, CustomHandler(filename=log_file), respect_handler_level=True).start()

if __name__ == '__main__':
    log.debug('debug')
    log.info('info')
    log.warning('warn')
    log.fatal('fatal')
    try:
        p = 3 / 0
    except Exception:
        log.error('div', exc_info=True)
