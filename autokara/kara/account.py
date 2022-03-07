
from config import config


class AccountManager(object):

    def __init__(self):
        self.idx = 1
        self.conf = config.instance()

    def obtain(self):
        acc = self.conf.get('account', f'kara.account.{self.idx}')
        if acc:
            self.idx += 1
            return acc.split('  ')


SINGLETON = AccountManager()


def instance():
    return SINGLETON
