import functools
import random
import time

import cv2 as cv
import numpy as np
import win32con
import win32gui
from PIL import Image, ImageGrab

import utils

CHECK_TIME = 120
WIN_WIDTH = 960
WIN_HEIGHT = 576


def cooldown(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        time.sleep(random.randint(0, 8) / 10)
        return func(*args, **kw)
    return wrapper


class WinControl(object):

    def __init__(self, title):
        self.title = title
        self.handle = win32gui.FindWindow(0, title)
        self.x, self.y, self.w, self.h = win32gui.GetWindowRect(self.handle)
        self.cap = None
        self.fix_pos()

    def fix_pos(self):
        x, y, w, h = win32gui.GetWindowRect(self.handle)
        # print(x, y, w, h)
        win32gui.SetWindowPos(self.handle, win32con.HWND_DESKTOP, 0, 0, WIN_WIDTH, WIN_HEIGHT, win32con.SWP_SHOWWINDOW)

    def capture(self):
        win32gui.SetForegroundWindow(self.handle)
        cap = ImageGrab.grab((self.x, self.y, self.w, self.h))
        # cap = cap.resize((1600, 900), Image.ANTIALIAS)
        self.cap = cv.cvtColor(np.asarray(cap), cv.COLOR_RGB2BGR)
        return self.cap

    def matches(self, template, gaussian=True):
        self.capture()
        return utils.matches(self.cap, template, gaussian)

    @cooldown
    def click(self, point, after=0):
        utils.left_click(self.handle, np.array(point, dtype=np.uint16), self.x, self.y)
        if after:
            time.sleep(after)

    @cooldown
    def rand_click(self, left_top, bottom_right):
        utils.random_click(self.handle, left_top, bottom_right, self.x, self.y)

    def match_randclk(self, template, gaussian=True):
        self.match_action(template, lambda wc, lt, br: self.rand_click(lt, br), gaussian)

    def match_action(self, template, action, gaussian=True):
        idx = 0
        while idx < CHECK_TIME:
            lt, br = self.matches(template, gaussian)
            if not np.min(lt == utils.NOT_MATCHED):
                action(self, lt, br)
                return
            time.sleep(.5)
            idx += 1
        raise RuntimeError('not match the template')

    def check_condition(self, twait, template, action, next_action):
        idx = 0
        # elc = (int((self.x + self.w) * .5), int((self.y + self.h) * .78))
        while idx < 66:
            # time.sleep(twait)
            # action.left_click(handle, int((xo + ww) * .5), int((yo + wh) * .78))
            # action.left_click(handle, *elc)
            action(self)
            time.sleep(twait)
            lt, br = self.matches(template)
            if not np.min(lt == utils.NOT_MATCHED):
                # account(handle, lt, br)
                next_action(self, lt, br)
                return
            idx += 1
        raise RuntimeError('condition check failure')

    def save_capture(self, name):
        self.capture()
        cv.imshow(f'{name}', self.cap)
        cv.waitKey(0)
        cv.imwrite(f'../resources/{name}.png', self.cap)

    def save_area(self, name):
        self.capture()
        cap = self.cap
        lt, br = (190, 488), (268, 552)
        # cv.rectangle(cap, lt, br, (0, 0, 255), 2)
        cap = cap[lt[1]:br[1], lt[0]:br[0]]
        cv.imshow(f'{name}', cap)
        cv.waitKey(0)
        # cv.imwrite(f'../resources/{name}.png', cap)


if __name__ == '__main__':
    winctrl = WinControl('雷电模拟器')
    # print(winctrl.handle)
    # lt, br = winctrl.matches(cv.imread('../resources/dungeon.png'))
    # utils.show_match(winctrl.cap, lt, br)
    # winctrl.save_capture('setting-panel')
    # winctrl.save_area('quest')

    # point = (135, 140)
    # utils.show_point(winctrl.capture(), point)
