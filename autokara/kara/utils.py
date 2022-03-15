import os
import subprocess
import time
from ctypes import windll
from PIL import ImageGrab
from subprocess import PIPE

import cv2 as cv
import numpy as np
import win32api
import win32con
import win32gui
import win32ui

from config import config

windll.user32.SetProcessDPIAware()
RED = (0, 0, 255)
GOOD_THRESHOLD = 8
SIFT = cv.SIFT_create()
FLANN = cv.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))


def adbcap(adb_cmd):
    prc = subprocess.Popen(adb_cmd + 'screencap -p', stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = prc.communicate()
    if prc.returncode > 0:
        raise RuntimeError('unknown error during fetching capture image')
    prc.kill()
    out = out.replace(b'\r\n', b'\n')
    met = np.frombuffer(out, dtype=np.uint8)
    return cv.imdecode(met, cv.IMREAD_COLOR)


def wincap(handle):
    x, y, x2, y2 = win32gui.GetWindowRect(handle)
    w, h = x2 - x, y2 - y

    wdc = win32gui.GetWindowDC(handle)
    hdc = win32ui.CreateDCFromHandle(wdc)
    cdc = hdc.CreateCompatibleDC()

    sbm = win32ui.CreateBitmap()
    sbm.CreateCompatibleBitmap(hdc, w, h)
    cdc.SelectObject(sbm)
    cdc.BitBlt((0, 0), (w, h), hdc, (0, 0), win32con.SRCCOPY)
    # bmpinfo = sbm.GetInfo()
    bmpstr = sbm.GetBitmapBits(True)

    # im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    # im.show()
    img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((h, w, 4))
    cv.cvtColor(img, cv.COLOR_RGBA2BGR)
    # cv.imshow('img', img)
    # cv.waitKey(0)

    win32gui.DeleteObject(sbm.GetHandle())
    cdc.DeleteDC()
    hdc.DeleteDC()
    win32gui.ReleaseDC(handle, wdc)

    return img


def pilcap(handle):
    x, y, x2, y2 = win32gui.GetWindowRect(handle)
    cap = ImageGrab.grab((x, y, x2, y2))
    img = cv.cvtColor(np.array(cap), cv.COLOR_RGB2BGR)
    return img


def tmatch(screen, template):
    h, w, d = template.shape
    res = cv.matchTemplate(screen, template, cv.TM_CCOEFF)
    miv, mav, mil, mal = cv.minMaxLoc(res)
    lt, rb = mal, (mal[0] + w, mal[1] + h)
    # cv.rectangle(screen, lt, rb, 255, 2)
    # cv.imshow('img', screen)
    # cv.waitKey(0)
    return lt, rb


def match(screen, template, gray=True, gaussian=True, threshold=GOOD_THRESHOLD):
    try:
        if gray:
            screen = cv.cvtColor(screen, cv.COLOR_BGR2GRAY)
            template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        if gaussian:
            screen = cv.GaussianBlur(screen, (5, 5), 0)
            template = cv.GaussianBlur(template, (5, 5), 0)
        kp1, des1 = SIFT.detectAndCompute(template, None)
        kp2, des2 = SIFT.detectAndCompute(screen, None)

        good = []
        for m, n in FLANN.knnMatch(des1, des2, k=2):
            if m.distance < 0.7 * n.distance:
                good.append(m)

        # print('good: ', len(good), len(good) >= threshold)
        if len(good) >= threshold:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            m, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
            h, w = template.shape[0], template.shape[1]
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv.perspectiveTransform(pts, m)
            dst = np.int32(dst)
            # screen = cv.polylines(screen, [dst], True, (255, 0, 0), 3, cv.LINE_AA)
            # cv.imshow('img', screen)
            # cv.waitKey(0)
            return dst[0, 0], dst[2, 0]
        else:
            # print('Not found enough matches')
            return None, None
    except cv.error:
        print('Error occur during template matching')
        # script.utils.show(screen, title='screen')
        # script.utils.show(template, title='template')
        return None, None


def grab_cut(img, rect) -> np.ndarray:
    mask = np.zeros(img.shape[:2], np.uint8)
    bgm = np.zeros((1, 65), np.float64)
    fgm = np.zeros((1, 65), np.float64)

    # rect = (0, 0, 109, 109)
    cv.grabCut(img, mask, rect, bgm, fgm, 5, cv.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    return img * mask2[:, :, np.newaxis]


def show(img: np.ndarray, title='Screen Image'):
    cv.imshow(title, img)
    cv.waitKey(0)


def cooldown(cfk: str):
    time.sleep(config.instance().getint('kara', cfk + '.cooldown') / 1000)


def pos(cfk: str) -> tuple:
    return tuple(map(int, config.instance().get('kara', cfk + '.pos')))


def rect_center(lt, rb) -> np.ndarray:
    if not isinstance(lt, np.ndarray):
        lt, rb = np.array(lt), np.array(rb)
    return np.add(lt, np.array(np.array(rb - lt) // 2))


def message(msg, title='Karastar Assistant Tips'):
    win32api.MessageBox(0, msg, title, win32con.MB_OK | win32con.MB_ICONINFORMATION)


def execmd(cmd) -> list:
    try:
        prc = os.popen(cmd)
        lines = prc.readlines()
        prc.close()
        return lines
    except Exception:
        return []


def localtime() -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
