import subprocess
import threading
import time
from subprocess import PIPE

import cv2 as cv
import numpy as np
import win32con
import win32gui
import win32ui

from config import config
from kara import action, utils
from PIL import ImageGrab

WAIT_TIMES = config.instance().getint('kara', 'simulator.wait.times')
SIMULATOR_PATH = config.instance().get('kara', 'simulator.path')


class Simulator(object):

    def __init__(self, idx, name, handle, hwnd, dev):
        self.idx = int(idx)
        self.dev = dev
        self.name = name
        self.handle = int(handle)
        self.hwnd = int(hwnd)
        self.adb = f'{SIMULATOR_PATH}adb -s {dev} shell '
        self.f_stop = False

    def stop(self):
        self.f_stop = True

    def capture(self) -> np.ndarray:
        # return utils.adbcap(self.adb)
        return utils.wincap(self.hwnd)[:, :, :3]
        # return utils.pilcap(self.hwnd)

    def click(self, p):
        action.click(self.hwnd, tuple(p))

    def press(self, key: str):
        action.press(self.hwnd, key)

    def cpress(self, keys: str):
        action.cpress(self.hwnd, keys)

    def typing(self, txt: str):
        action.typing(self.hwnd, txt)

    def tmatch(self, template: np.ndarray):
        h, w, d = template.shape
        res = cv.matchTemplate(self.capture(), template, cv.TM_CCOEFF)
        miv, mav, mil, lt = cv.minMaxLoc(res)
        rb = (lt[0] + w, lt[1] + h)
        return np.array(lt), np.array(rb)

    def match(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        wt = WAIT_TIMES if wait else 1
        thn = threading.currentThread().name
        while wt > 0 and not self.f_stop:
            lt, rb = utils.match(self.capture(), template, gray, blur, th)
            if np.any(lt is not None):
                print(thn, 'match at', wt)
                return lt, rb
            print(thn, 'mismatch at', wt)
            utils.cooldown('simulator.match')
            wt -= 1
        return None, None

    def match_click(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        lt, rb = self.match(template, gray, blur, th, wait)
        if np.any(lt is None):
            raise LookupError('can not match the template')
        self.click(utils.rect_center(lt, rb))


if __name__ == '__main__':
    s = Simulator(0, '雷电模拟器', 15270726, 5309338, '127.0.0.1:5554')
    # cap = s.capture()
    # roi = cap[81:137, 103:158]
    # cv.imwrite('../resources/area/roi.png', roi)
    # s.match_click(cv.imread('../resources/area/roi.png'))
    # lt, rb = s.tmatch(cv.imread('../resources/area/roi.png'))
    # print(utils.rect_center(lt, rb))
    # img = s.capture()
    # roi = img[234:275, 93:190]
    # cv.imwrite('../resources/area/roi.png', roi)
    cap = s.capture()
    cv.imshow('img', cap)
    cv.waitKey(0)
    pass
