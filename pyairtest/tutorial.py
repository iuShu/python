import threading
import time

import cv2 as cv
import numpy as np

import textocr
from airtest.core.api import *

t_kara = Template('resources/template/kara.png')
t_email = Template('resources/template/emaddr.png')
t_main = Template('resources/template/main_flag.png')
t_bf = Template('resources/template/battlefield_ready.png')
t_close = Template('resources/template/close.png')
tesseract_root = 'F:/wqt/application/tesseract/tesseract'
tesseract_temp = 'E:/wqt/tesseract_temp.png'
kara_app_name = 'com.chain.infinity'
emulator_path = 'F:/wqt/application/simulator/LDPlayer4.0/'


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


def performance():
    mf = cv.imread('resources/template/main_flag.png')
    mlt = (106, 234)
    rp, bp = (85, 505), (60, 50)
    android = init_device('Android')
    android.screen_proxy.snapshot()  # prepare minicap
    print('ready')
    sleep(1)
    while True:
        screen = android.screen_proxy.snapshot()
        lt, rb = tmatch(screen, mf)
        if lt[0] != mlt[0] or lt[1] != mlt[1]:
            click(bp)
            print('click')
            sleep(.5)


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
    from airtest.core.android.adb import ADB

    def emulator(serialno):
        thn = threading.current_thread().name
        android = init_device(uuid=serialno)
        print(thn, android.serialno, len(android.list_app()), android.adb.adb_path)
        print(android.get_current_resolution())
        print(android.get_render_resolution())

    devs = ADB().devices(state="device")
    for d in devs:
        thread = threading.Thread(target=emulator, args=[d[0]])
        thread.start()


def windows():
    # win = init_device('Windows')
    # ret = win.shell('dir')
    # print(ret.decode('gbk'))
    import subprocess
    cmd = f'{emulator_path}ldconsole list2'
    gbk_bytes: bytes = subprocess.check_output(cmd, shell=True)
    print(gbk_bytes.decode('gbk'))


if __name__ == '__main__':
    # test()
    temp()
    # windows()
