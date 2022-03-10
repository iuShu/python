import threading
import time

import numpy as np

from kara.constants import *
from kara.simulator import Simulator
from kara.utils import cooldown, message, pos, localtime
from kara import account
from script import textocr

lock = threading.Lock()


class KaraInstance(threading.Thread):

    def __init__(self, sml: Simulator):
        threading.Thread.__init__(self, name='instance-' + sml.name)
        self.power = 0
        self.sml = sml
        self.acm = account.instance()
        self.step = 0

    def forward(self):
        self.step += 1

    def run(self):
        thr_name = threading.currentThread().name
        try:
            self.forward()
            self.sml.match_click(KARA_ICON)
            self.forward()
            cooldown('apk.startup')

            while True:
                self.forward()
                self.sml.match_click(EMADDR)
                cooldown('email.panel')
                self.forward()
                acc = self.get_acc()
                if not acc:
                    message(self.sml.name + ' finished due to no more account')
                    break

                if not self.login(acc):
                    break

                self.checkin()

                self.arena()

                print('power', self.power)

                self.logout()
        except Exception as e:
            message(f'{thr_name} exited with error {e.__str__()} at {STEPS[self.step]}')
        else:
            message(thr_name + ' finished at ' + localtime())

    def get_acc(self) -> tuple:
        lock.acquire()
        try:
            return self.acm.obtain()
        finally:
            lock.release()

    def login(self, acc):
        self.forward()
        self.sml.click(pos('email.input'))
        time.sleep(.2)
        self.sml.cpress('lcontrol,a')
        self.sml.press('delete')
        self.sml.typing(acc[0])
        self.sml.press('return')
        cooldown('account.input')
        self.sml.click(pos('password.input'))
        time.sleep(.2)
        self.sml.cpress('lcontrol,a')
        self.sml.press('delete')
        self.sml.typing(acc[1])
        self.sml.press('return')
        cooldown('account.input')
        self.sml.click(pos('login.button'))
        lt, rb = self.sml.match(MAIN)
        if np.any(lt is None):
            message('login failure with account ' + acc[0])
            return False
        self.forward()
        return True

    def checkin(self):
        self.forward()
        self.sml.click(pos('quest.button'))
        cooldown('panel.open')
        self.sml.click(pos('quest.checkin'))
        cooldown('minor')
        self.sml.click(pos('quest.close'))
        cooldown('panel.quit')

    def recognize_power(self):
        self.forward()
        lt, rb = pos('power.left.top'), pos('power.right.bottom')
        roi = self.sml.capture()[lt[1]:rb[1], lt[0]:rb[0]]
        txt = textocr.text_recognize(roi)
        if not txt or len(txt) > 5:
            return

        available = int(txt.split('/')[0])
        if available >= 1:
            self.power = available

    def arena(self):
        self.forward()

        pass

    def logout(self):
        self.forward()
        self.sml.click(pos('setting.button'))
        cooldown('panel.open')
        self.sml.click(pos('logout.button'))


if __name__ == '__main__':
    lv = 1
    for j in range(25):
        for i in GENERAL.keys():
            if lv <= i:
                print(lv, i, GENERAL[i])
                break
        lv += 1
