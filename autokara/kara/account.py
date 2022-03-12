import threading

from config import config

lock = threading.Lock()


class AccountManager(object):

    def __init__(self):
        self.idx = 1
        self.conf = config.instance()
        self.next = self.peek(self.idx)[0]

    def obtain(self) -> tuple:
        lock.acquire()
        try:
            acc = self.conf.get('account', f'kara.account.{self.idx}')
            if acc:
                self.idx += 1
                self.next = self.peek(self.idx)[0]
                return acc.split('  ')
        finally:
            lock.release()

    def peek(self, idx):
        acc = self.conf.get('account', f'kara.account.{idx}')
        return acc.split('  ') if acc else ('none', 'none')


SINGLETON = AccountManager()


def instance():
    return SINGLETON
