import logging
import os
import sys
from logging import FileHandler, Formatter, Filter


class CustomHandler(FileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=False, errors=None):
        FileHandler.__init__(self, filename, mode, encoding, delay, errors)
        self._stdout = sys.stdout
        self.formatter = Formatter(fmt='%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] %(message)s')

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

log = logging.root
log.setLevel(logging.DEBUG)
log.addFilter(Filter('root'))
log.addHandler(CustomHandler(filename=log_file))


if __name__ == '__main__':
    log.debug('debug')
    log.info('info')
    log.warning('warn')
    log.fatal('fatal')
    try:
        p = 3 / 0
    except Exception:
        log.error('div', exc_info=True)
