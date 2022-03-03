import time

import numpy as np
import win32con
import win32gui
from PIL import ImageGrab

import script.utils
from kara import action, utils
from config import config

WAIT_TIME = config.instance().getint('kara', 'simulator.wait.time')


class Simulator(object):

    def __init__(self, name):
        self.name = name
        self.handle = win32gui.FindWindow(0, self.name)
        if not self.handle:
            raise NameError(f'can not found window {name}')
        self.hwnd = win32gui.GetWindow(self.handle, win32con.GW_CHILD)

    def capture(self):
        win32gui.SetForegroundWindow(self.handle)
        x, y, w, h = win32gui.GetWindowRect(self.handle)
        return ImageGrab.grab((x, y, w, h))

    def click(self, p):
        action.click(self.hwnd, p)

    def press(self, key: str):
        action.press(self.hwnd, key)

    def cpress(self, keys: str):
        action.cpress(self.hwnd, keys)

    def typing(self, txt: str):
        action.typing(self.hwnd, txt)

    def match(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        wt = WAIT_TIME if wait else 1
        while wt > 0:
            cap = self.capture()
            lt, rb = utils.match(cap, template, gray, blur, th)
            if lt:
                return lt, rb
            time.sleep(config.instance().getint('kara', 'simulator.match.cooldown') / 1000)
            wt -= 1
        return None, None

    def match_click(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        lt, rb = self.match(template, gray, blur, th, wait)
        if not lt:
            raise LookupError('can not match the template')
        self.click(utils.rect_center(lt, rb))


if __name__ == '__main__':
    s = Simulator('雷电模拟器')
    # s.click(())
    # s.typing('hentonwu128@outlook.com')
    # s.press('return')
    s.cpress('lcontrol,a')
    s.press('delete')



