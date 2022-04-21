import numpy as np
import win32api
import win32con
import cv2 as cv
import subprocess

lower_val = np.array([119, 0, 0])
upper_val = np.array([255, 72, 255])


def error(msg: str):
    raise RuntimeError(msg)


def execmd(cmd: str) -> str:
    try:
        gbk_bytes = subprocess.check_output(cmd, shell=True)
        return gbk_bytes.decode('gbk')
    except Exception:
        pass


def message(msg, title='Karastar Assistant Tips'):
    win32api.MessageBox(0, msg, title, win32con.MB_OK | win32con.MB_ICONINFORMATION)


def tmatch(screen: np.ndarray, template: np.ndarray) -> tuple:
    h, w, d = template.shape
    res = cv.matchTemplate(screen, template, cv.TM_CCOEFF)
    miv, mav, mil, mal = cv.minMaxLoc(res)
    return mal, (mal[0] + w, mal[1] + h)


def show(img, title='snapshot'):
    cv.imshow(title, img)
    cv.waitKey(0)


def hsv_filter(img: np.ndarray) -> np.ndarray:
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, lower_val, upper_val)
    return cv.bitwise_and(img, img, mask=mask)


def only_numeric(txt: str) -> str:
    flt = filter(lambda s: s.isnumeric(), txt)
    return ''.join([f for f in flt])


def try_do(task):
    try:
        task()
    except Exception:
        pass
