import sys

import win32api
import win32con
import win32gui

from config import config
from kara.instance import KaraInstance
from kara.simulator import Simulator
from kara.utils import message, execmd

SML_PATH = config.instance().get('kara', 'simulator.path')


class Karastar(object):

    def __init__(self):
        self.sml_list = []
        self.adb_devs = []
        self.instances = []
        self.init_env()
        self.init_adb()
        self.init_sml()
        self.init_layout()

    def init_env(self):
        lines = execmd(SML_PATH + 'ldconsole list2')
        if not lines or lines[0].strip().endswith('-1,-1'):
            message('Simulator not running')
            sys.exit()

        for line in lines:
            info = line.strip().split(',')
            if not info[-1] == '-1':
                self.sml_list.append(info)

    def init_adb(self):
        lines = execmd(SML_PATH + 'adb devices')
        if not lines:
            message('Adb.exe or device connection error')
            sys.exit()

        for line in lines:
            if len(line) > 1 and 'attached' not in line:
                self.adb_devs.append(line.split('device')[0].replace('\t', ''))

    def init_sml(self):
        if len(self.sml_list) != len(self.adb_devs):
            message('init error')
            execmd(SML_PATH + 'adb kill-server')
            sys.exit()

        for i in range(len(self.sml_list)):
            info = self.sml_list[i][:-3]
            dev = self.adb_devs[i]
            sml = Simulator(*info, dev)
            ki = KaraInstance(sml)
            self.instances.append(ki)

    def init_layout(self):
        if not self.instances:
            message('no available instance')
            return

        sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        print('screen', sw, sh)
        rnum = config.instance().getint('kara', 'instance.row.num')
        cnum = config.instance().getint('kara', 'instance.col.num')
        dw = config.instance().getint('kara', 'simulator.default.width')
        dh = config.instance().getint('kara', 'simulator.default.height')
        # xadd, yadd = dw, dh
        # if sw < (rnum * dw) - 100:
        #     xadd = 50
        # if sh < (cnum * dh) - 30:
        #     yadd = 50

        fx, fy = 0, 0
        # if xadd == 50:
        #     for i in self.instances:
        #         handle = i.sml.handle
        #         win32gui.SetWindowPos(handle, win32con.HWND_DESKTOP, fx, fy, dw, dh, win32con.SWP_SHOWWINDOW)
        #         fx += xadd
        #         fy += yadd
        #     return

        # idx = 0
        # while fx < sw:
        #     while fy < sh:
        #         handle = self.instances[idx].sml.handle
        #         win32gui.SetWindowPos(handle, win32con.HWND_DESKTOP, fx, fy, dw, dh, win32con.SWP_SHOWWINDOW)
        #         idx += 1
        #         fy += yadd
        #     fx += xadd
        #     fy = 0

        idx = 0
        for i in range(rnum):
            for j in range(cnum):
                if idx >= len(self.instances):
                    break
                handle = self.instances[idx].sml.handle
                win32gui.SetWindowPos(handle, win32con.HWND_DESKTOP, fx, fy, dw, dh, win32con.SWP_SHOWWINDOW)
                fx += dw
                idx += 1
            fy += dh
            fx = 0

    def run(self):
        print(self.instances)
        for i in self.instances:
            i.start()
        for i in self.instances:
            i.join()
        message('All instance finished')


if __name__ == '__main__':
    ks = Karastar()
    ks.run()
