import sys

import kara.action
from config import config
from kara.simulator import Simulator
from kara.instance import KaraInstance
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
            sys.exit()

        for i in range(len(self.sml_list)):
            info = self.sml_list[i][:-3]
            dev = self.adb_devs[i]
            sml = Simulator(*info, dev)
            ki = KaraInstance(sml)
            self.instances.append(ki)

    def run(self):
        print(self.instances)
        if not self.instances:
            message('no available instance')
            return

        for i in self.instances:
            i.start()
        for i in self.instances:
            i.join()
        message('All instance finished')


if __name__ == '__main__':
    ks = Karastar()
    ks.run()

