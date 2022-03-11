import threading

from config import config

lock = threading.Lock()


class AccountManager(object):

    def __init__(self):
        self.idx = 1
        self.conf = config.instance()

    def obtain(self):
        lock.acquire()
        try:
            acc = self.conf.get('account', f'kara.account.{self.idx}')
            if acc:
                self.idx += 1
                return acc.split('  ')
        finally:
            lock.release()


SINGLETON = AccountManager()


def instance():
    return SINGLETON
