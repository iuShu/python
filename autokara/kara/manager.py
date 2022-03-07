import os
import time

import win32api
import win32con

from config import config
from simulator import Simulator


class Manager(object):

    def __init__(self):
        self.init_adb()
        self.idx = 0
        self.wnds = []
        self.sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.devs = self.device_list()

    def create(self) -> Simulator:
        simulator = Simulator('雷电模拟器', self.idx, self.devs[self.idx])
        self.wnds.append(simulator)
        self.idx += 1
        return simulator

    def alloc_pos(self):
        num = config.instance().getint('kara', 'window.number')
        wn = num // 2
        ew = self.sw // wn
        eh = self.sh // wn
        print(ew, eh)
        pass

    @staticmethod
    def init_adb():
        sml_path = config.instance().get('kara', 'simulator.path')

        prc = os.popen(sml_path + 'ldconsole list2')
        txt = prc.read().strip()
        if txt.endswith('-1,-1'):
            raise RuntimeError('simulator not running')
        prc.close()

        prc = os.popen('TASKLIST /FI "IMAGENAME eq adb.exe"')
        if len(prc.readlines()) > 2:
            return

        start = time.time()
        # os.system(sml_path + 'adb kill-server')
        os.system(sml_path + 'adb devices')
        print('init adb cost', time.time() - start)

    @staticmethod
    def device_list() -> list:
        sml_path = config.instance().get('kara', 'simulator.path')
        prc = os.popen(sml_path + 'adb devices')
        devices = []
        for line in prc.readlines():
            if len(line) > 1 and 'attached' not in line:
                devices.append(line.split('device')[0].replace('\t', ''))
        prc.close()
        return devices


if __name__ == '__main__':
    m = Manager()
    # s = m.create()
    print(m.devs)
