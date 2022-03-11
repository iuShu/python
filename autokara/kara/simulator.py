import subprocess
import threading
from subprocess import PIPE

import cv2 as cv
import numpy as np

import script.utils
from config import config
from kara import action, utils, account

WAIT_TIMES = config.instance().getint('kara', 'simulator.wait.times')
SIMULATOR_PATH = config.instance().get('kara', 'simulator.path')


class Simulator(object):

    def __init__(self, idx, name, handle, hwnd, dev):
        self.idx = idx
        self.dev = dev
        self.name = name
        self.handle = int(handle)
        self.hwnd = int(hwnd)
        self.adb = f'{SIMULATOR_PATH}adb -s {dev} shell '
        self.f_stop = False

    def stop(self):
        self.f_stop = True

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
        thn = threading.currentThread().name
        while wt > 0 and not self.f_stop:
            cap = self.capture()
            lt, rb = utils.match(cap, template, gray, blur, th)
            if np.any(lt is not None):
                print(thn, 'match at', wt)
                return lt, rb
            # print(thn, 'mismatch at', wt)
            utils.cooldown('simulator.match')
            wt -= 1
        return None, None

    def match_click(self, template: np.ndarray, gray=True, blur=True, th=utils.GOOD_THRESHOLD, wait=True):
        lt, rb = self.match(template, gray, blur, th, wait)
        if np.any(lt is None):
            raise LookupError('can not match the template')
        self.click(utils.rect_center(lt, rb))


if __name__ == '__main__':
    # s = Simulator('雷电模拟器', 0, '127.0.0.1:5555')
    # cv.imwrite('../resources/area/cap.png', s.capture())
    pass
