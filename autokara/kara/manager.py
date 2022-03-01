from simulator import Simulator
from config.config import instance
import win32api
import win32con


class Manager(object):

    def __init__(self):
        self.idx = 0
        self.list = []
        self.sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.conf = instance()

    def manage(self, s: Simulator):
        self.list.append(s)

    def alloc_pos(self):
        num = self.conf.getint('kara', 'window.number')
        wn = num // 2
        ew = self.sw // wn
        eh = self.sh // wn
        print(ew, eh)
        pass


if __name__ == '__main__':
    m = Manager()
    m.alloc_pos()
