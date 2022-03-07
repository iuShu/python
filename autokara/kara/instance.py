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

    def run(self):
        try:
            self.sml.match_click(KARA_ICON)
            cooldown('apk.startup')

            while True:
                self.sml.match_click(EMADDR)
                cooldown('email.panel')
                acc = self.get_acc()
                if not acc:
                    message(self.sml.name + ' finished due to no more account')
                    break
                if not self.login(acc):
                    break

                self.checkin()
                self.recognize_power()

                # arena battle
                print('power', self.power)
                time.sleep(5)

                self.logout()
        except Exception as e:
            message(threading.currentThread().name + ' exited with error ' + e.__str__())
        else:
            message(threading.currentThread().name + ' finished at ' + localtime())

    def get_acc(self) -> tuple:
        lock.acquire()
        try:
            return self.acm.obtain()
        finally:
            lock.release()

    def login(self, acc):
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
        return True

    def checkin(self):
        self.sml.click(pos('quest.button'))
        cooldown('panel.open')
        self.sml.click(pos('quest.checkin'))
        cooldown('minor')
        self.sml.click(pos('quest.close'))
        cooldown('panel.quit')

    def recognize_power(self):
        lt, rb = pos('power.left.top'), pos('power.right.bottom')
        roi = self.sml.capture()[lt[1]:rb[1], lt[0]:rb[0]]
        txt = textocr.text_recognize(roi)
        if not txt or len(txt) > 5:
            return

        available = int(txt.split('/')[0])
        if available >= 1:
            self.power = available

    def logout(self):
        self.sml.click(pos('setting.button'))
        cooldown('panel.open')
        self.sml.click(pos('logout.button'))
