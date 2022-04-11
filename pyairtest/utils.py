import win32api
import win32con
import cv2 as cv
import subprocess


def error(msg: str):
    raise RuntimeError(msg)


def execmd(cmd: str) -> str:
    gbk_bytes = subprocess.check_output(cmd, shell=True)
    return gbk_bytes.decode('gbk')


def message(msg, title='Karastar Assistant Tips'):
    win32api.MessageBox(0, msg, title, win32con.MB_OK | win32con.MB_ICONINFORMATION)


def show(img, title='snapshot'):
    cv.imshow(title, img)
    cv.waitKey(0)


def try_do(task):
    try:
        task()
    except Exception:
        pass
