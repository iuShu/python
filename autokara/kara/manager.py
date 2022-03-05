import os
import time

import win32api
import win32con

import kara.simulator
import script.utils
from config import config
from simulator import Simulator


class Manager(object):

    def __init__(self):
        self.idx = 0
        self.wnds = []
        self.sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.devs = device_list()

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


def device_list():
    sml_path = config.instance().get('kara', 'simulator.path')
    prc = os.popen(f'{sml_path}adb devices')
    devices = []
    for line in prc.readlines():
        if len(line) > 1 and 'attached' not in line:
            devices.append(line.split('device')[0].replace('\t', ''))
    prc.close()
    return devices


if __name__ == '__main__':
    m = Manager()
    s = m.create()
    pass
