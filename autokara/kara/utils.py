import sys
import time
from ctypes import windll, byref, c_ubyte, wintypes
from config import config

import cv2 as cv
import numpy as np
import win32con

windll.user32.SetProcessDPIAware()
RED = (0, 0, 255)
GOOD_THRESHOLD = 8
SIFT = cv.SIFT_create()
FLANN = cv.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))


def winCapture(handle):
    rect = wintypes.RECT()
    windll.user32.GetClientRect(handle, byref(rect))
    width, height = rect.right, rect.bottom

    dc = windll.user32.GetDC(handle)
    cdc = windll.gdi32.CreateCompatibleDC(dc)
    bitmap = windll.gdi32.CreateCompatibleBitmap(dc, width, height)
    windll.gdi32.SelectObject(cdc, bitmap)
    windll.gdi32.BitBlt(cdc, 0, 0, width, height, dc, 0, 0, win32con.SRCCOPY)

    total_bytes = width * height * 4
    buffer = bytearray(total_bytes)
    byte_array = c_ubyte * total_bytes
    windll.gdi32.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
    windll.gdi32.DeleteObject(bitmap)
    windll.gdi32.DeleteObject(cdc)
    windll.user32.ReleaseDC(handle, dc)
    return np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 4))


def capture2(handle):
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    screen = QApplication.primaryScreen()
    img = screen.grabWindow(handle).toImage()
    w, h, c = img.width(), img.height(), img.depth() // 8
    arr = img.bits().asstring(w * h * c)
    cap = np.fromstring(arr, dtype=np.uint8).reshape((h, w, c))
    return cap


def match(screen, template, gray=True, gaussian=True, threshold=GOOD_THRESHOLD):
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
    try:
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
        return None, None


def grab_cut(img, rect):
    mask = np.zeros(img.shape[:2], np.uint8)
    bgm = np.zeros((1, 65), np.float64)
    fgm = np.zeros((1, 65), np.float64)

    # rect = (0, 0, 109, 109)
    cv.grabCut(img, mask, rect, bgm, fgm, 5, cv.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    return img * mask2[:, :, np.newaxis]


def cooldown(cfk: str):
    time.sleep(config.instance().getint('kara', f'{cfk}.cooldown') / 1000)


def rect_center(lt, rb):
    lt, rb = np.array(lt), np.array(rb)
    return np.add(lt[0], (rb[1] - lt[0]) // 2)

