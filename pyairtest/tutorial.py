import time

import cv2 as cv
import numpy as np

import textocr
from airtest.core.api import *

t_kara = Template('resources/kara.png')
t_email = Template('resources/emaddr.png')
t_main = Template('resources/main_flag.png')
t_bf = Template('resources/battlefield_ready.png')
t_close = Template('resources/close.png')
tesseract_root = 'E:/application/tesseract/tesseract'
tesseract_temp = 'E:/tesseract_temp.png'


def screenshot():
    android = init_device('Android')
    screen = android.snapshot(filename=None, quality=ST.SNAPSHOT_QUALITY)
    cv.imshow('img', screen)
    cv.waitKey(0)


def check_energy():
    dev = init_device('Android')
    screen = dev.snapshot(filename=None, quality=ST.SNAPSHOT_QUALITY)
    lt, rb = (365, 16), (419, 40)   # energy area position
    roi = screen[lt[1]:rb[1], lt[0]:rb[0]]
    reg = textocr.recognize(roi)
    energy = reg.removesuffix('20')
    print(energy)


def max_level():
    dev = init_device('Android')
    screen = dev.snapshot(filename=None, quality=ST.SNAPSHOT_QUALITY)
    lt, rb = (258, 117), (300, 138)  # energy area position
    roi = screen[lt[1]:rb[1], lt[0]:rb[0]]
    level = textocr.recognize(roi)
    print(level)


def tmatch(screen: np.ndarray, template: np.ndarray):
    h, w, d = template.shape
    res = cv.matchTemplate(screen, template, cv.TM_CCOEFF)
    miv, mav, mil, mal = cv.minMaxLoc(res)
    return mal, (mal[0] + w, mal[1] + h)


def test():
    android = init_device('Android')
    touch(t_kara)       # open app
    sleep(4)

    while True:
        click((485, 455))
        sleep(1)
        if exists(t_close):
            break
    click((480, 220))
    sleep(.5)
    double_click((22, 27))
    keyevent('67')
    text('email')
    sleep(1)
    click((480, 290))
    sleep(.5)
    double_click((22, 27))
    keyevent('67')
    text('password')
    sleep(1)
    click((480, 335))   # login
    sleep(4)

    wait(t_main, interval=.5)

    click((580, 475))
    sleep(1)
    wait(t_bf, interval=.5)
    click((60, 50))     # back to main


def temp():
    mf = cv.imread('resources/main_flag.png')
    mlt = (106, 234)
    rp, bp = (85, 505), (60, 50)
    android = init_device('Android')
    android.screen_proxy.snapshot()     # prepare minicap
    print('ready')
    sleep(1)
    while True:
        screen = android.screen_proxy.snapshot()
        lt, rb = tmatch(screen, mf)
        if lt[0] != mlt[0] or lt[1] != mlt[1]:
            click(bp)
            print('click')
            sleep(.5)

    # TODO init multiple devices and thread working model


if __name__ == '__main__':
    # test()
    temp()
