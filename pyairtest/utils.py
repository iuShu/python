import numpy as np
import win32api
import win32con
import cv2 as cv
import subprocess


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


def try_do(task):
    try:
        task()
    except Exception:
        pass
