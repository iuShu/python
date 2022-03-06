import subprocess
import time
from subprocess import PIPE

import cv2 as cv
import numpy as np
import win32con
import win32gui

import kara.account
from config import config
from kara import action, utils, autokara

CAPTURE_PATH = config.instance().get('kara', 'capture.path')
CAPTURE_NAME = config.instance().get('kara', 'capture.file.name')
CAPTURE_WAIT_TIME = config.instance().getint('kara', 'capture.wait.time') / 1000
SIMULATOR_PATH = config.instance().get('kara', 'simulator.path')
S_CAPTURE_PATH = config.instance().get('kara', 'simulator.capture.path')

WAIT_TIMES = config.instance().getint('kara', 'simulator.wait.times')


class Simulator(object):

    def __init__(self, name, idx, dev):
        self.idx = idx
        self.dev = dev
        self.name = name
        self.handle = win32gui.FindWindow(0, self.name)
        if not self.handle:
            raise NameError(f'can not found window {name}')
        self.hwnd = win32gui.GetWindow(self.handle, win32con.GW_CHILD)
        self.adb = f'{SIMULATOR_PATH}adb -s {dev} shell '
        print(self.handle, self.hwnd)

    def capture(self) -> np.ndarray:
        prc = subprocess.Popen(self.adb + 'screencap -p', stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = prc.communicate()
        if prc.returncode > 0:
            raise RuntimeError('unknown error during fetching capture image')
        prc.kill()
        out = out.replace(b'\r\n', b'\n')
        met = np.frombuffer(out, dtype=np.uint8)
        return cv.imdecode(met, cv.IMREAD_COLOR)

    def click(self, p):
        action.click(self.hwnd, tuple(p))

    def press(self, key: str):
        action.press(self.hwnd, key)

    def cpress(self, keys: str):
        action.cpress(self.hwnd, keys)

    def typing(self, txt: str):
        action.typing(self.hwnd, txt)

    def match(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        wt = WAIT_TIMES if wait else 1
        while wt > 0:
            cap = self.capture()
            lt, rb = utils.match(cap, template, gray, blur, th)
            if np.any(lt is not None):
                print('match at', wt)
                return lt, rb
            print('not match at', str(wt))
            utils.cooldown('simulator.match')
            wt -= 1
        return None, None

    def match_click(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        lt, rb = self.match(template, gray, blur, th, wait)
        if np.any(lt is None):
            raise LookupError('can not match the template')
        self.click(utils.rect_center(lt, rb))


if __name__ == '__main__':
    s = Simulator('雷电模拟器', 0, 'emulator-5554')
    # cv.imwrite('../resources/area/cap.png', s.capture())
    # acm = kara.account.AccountManager()
    # autokara.login(s, acm.obtain())
    # autokara.checkin(s)
    # autokara.avt_power(s)
