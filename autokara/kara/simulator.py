import random
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
        return utils.wincap(self.hwnd)
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


def multi_test():
    from kara.synchronizer import Synchronizer
    time.sleep(2)

    def task(sml: Simulator, sync: Synchronizer):
        collect_pos, fold_pos, cancel_pos = (130, 112), (655, 304), (410, 116)
        clt, crb = (246, 85), (295, 135)
        slt, srb = (106, 86), (155, 134)
        thn = threading.currentThread().name
        file_manager = cv.imread('../resources/area/cancel.png')
        start_flag = cv.imread('../resources/area/match_start.png')
        matched = sync.wait_times_diff
        start_times, wait_times, cd, endurance = 60, 60, 500 / 1000, 200 / 1000
        sml.click(collect_pos)
        time.sleep(.8)

        sync.ready_match()

        sml.click(fold_pos)
        while start_times > 0:
            lt, rb = s.tmatch(start_flag)
            if np.all(lt == slt) and np.all(rb == srb):
                break
            start_times -= 1

        while matched(wait_times, False) < 3 and wait_times > 0:
            lt, rb = sml.tmatch(file_manager)
            if np.all(lt != clt) or np.all(rb != crb):
                matched(wait_times, True)
                print(thn, 'entered', wait_times, start_times)
                return
            wait_times -= 1

        sml.click(cancel_pos)
        time.sleep(cd)
        print(thn, 'cancel', wait_times, start_times, sync.matched_timestamp)

    def match_ok(sml: Simulator, brr: threading.Barrier):
        time.sleep(2)
        brr.wait()
        sml.click((130, 112))
        time.sleep(2)

    sml_list = [Simulator(0, 'ld1', 197390, 132088, ''),
                Simulator(1, 'ld2', 525280, 132078, ''),
                Simulator(2, 'ld3', 458952, 525256, ''),
                Simulator(3, 'ld4', 721198, 525890, '')]
    syn = Synchronizer(len(sml_list))
    barrier = threading.Barrier(3)
    for e in sml_list:
        threading.Thread(target=task, args=[e, syn]).start()

    ci = random.randint(0, 3)
    for e in range(4):
        if e == ci:
            continue
        threading.Thread(target=match_ok, args=[sml_list[e], barrier]).start()


if __name__ == '__main__':
    s = Simulator(0, 'ld1', 197390, 132088, '127.0.0.1:5554')
    # cap = s.capture()
    # roi = cap[81:137, 103:158]
    # cv.imwrite('../resources/area/roi.png', roi)
    # s.match_click(cv.imread('../resources/area/roi.png'))
    # lt, rb = s.tmatch(cv.imread('../resources/area/roi.png'))
    # print(utils.rect_center(lt, rb))
    # img = s.capture()
    # roi = img[234:275, 93:190]
    # cv.imwrite('../resources/area/roi.png', roi)
    # cap = s.capture()
    # cv.imshow('img', cap)
    # cv.waitKey(0)

    # multi_test()

    from utils import tmatch
    # img = cv.imread('../resources/temp/capture.png')
    # tpl = cv.imread('../resources/cancel.png')
    # lt, rb = (106, 86), (155, 134)
    # img = img[lt[1]:rb[1], lt[0]:rb[0]]
    # lt, rb = tmatch(img, tpl)
    # cv.rectangle(img, lt, rb, (0, 0, 255), 1)
    # cv.imshow('img', img)
    # cv.waitKey(0)
    # print(lt, rb)

    pass
