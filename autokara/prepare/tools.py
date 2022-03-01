import os
import time

import cv2 as cv
import numpy as np

from script import utils

DILATE_IMG = cv.imread('../resources/dungeon/sample.png')
ERODE_IMG = cv.imread('../resources/cap/cap-4.png')

TB_NAME = 'kara trackbar'
KN_NAME = 'kara kernel'
WIN_NAME = 'kara demo window'
KERNEL = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))


def collect_img():
    path = 'G:\\application\\karastar\\assets\\assets\\games\\native\\'
    directory = os.listdir(path)
    img = []
    for d in directory:
        files = os.listdir(path + d)
        for f in files:
            if not f.endswith('png'):
                continue
            img.append(path + d + '\\' + f)

    nr = 'G:\\temp\\game\\'
    if not os.path.exists(nr):
        os.mkdir(nr)

    idx = 0
    for i in img:
        cp = f'{nr}img-{idx}.png'
        os.system(f'copy {i} {cp}')
        idx += 1


def on_dilate(arg):
    gray = cv.cvtColor(DILATE_IMG, cv.COLOR_BGR2GRAY)
    tpv = cv.getTrackbarPos(TB_NAME, WIN_NAME)
    knv = cv.getTrackbarPos(KN_NAME, WIN_NAME)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2 * knv + 1, 2 * knv + 1))
    img = cv.dilate(gray, kernel, None, None, tpv)
    cv.imshow(WIN_NAME, img)


def dilation():
    cv.namedWindow(WIN_NAME)
    cv.createTrackbar(TB_NAME, WIN_NAME, 3, 10, on_dilate)
    cv.createTrackbar(KN_NAME, WIN_NAME, 1, 5, on_dilate)
    on_dilate(0)
    cv.waitKey(0)


def on_erode(arg):
    # gray = cv.cvtColor(ERODE_IMG, cv.COLOR_BGR2GRAY)
    erosion_size = cv.getTrackbarPos(TB_NAME, WIN_NAME)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2 * erosion_size + 1, 2 * erosion_size + 1),
                                      (erosion_size, erosion_size))

    erosion_dst = cv.erode(ERODE_IMG, kernel)
    cv.imshow(WIN_NAME, erosion_dst)


def erosion():
    cv.namedWindow(WIN_NAME)
    cv.createTrackbar(TB_NAME, WIN_NAME, 0, 21, on_erode)
    on_erode(0)
    cv.waitKey(0)


CANNY_IMG = cv.imread('../resources/path/cap-10.png')


def on_canny(val):
    low = cv.getTrackbarPos('thresh low:', 'canny indicator')
    high = cv.getTrackbarPos('thresh high:', 'canny indicator')
    width = cv.getTrackbarPos('Contours width:', 'canny indicator')
    # canny = cv.Canny(CANNY_IMG, threshold, threshold * 2)
    canny = cv.Canny(CANNY_IMG, low, high)
    cts, hrc = cv.findContours(canny, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    if width:
        cp = CANNY_IMG.copy()
        for i in cts:
            x, y, w, h = cv.boundingRect(i)
            if w < width:
                cv.rectangle(cp, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv.imshow('canny indicator', cp)
    else:
        drawing = np.zeros((canny.shape[0], canny.shape[1], 3), dtype=np.uint8)
        for i in range(len(cts)):
            cv.drawContours(drawing, cts, i, (0, 0, 255), 2, cv.LINE_4, hierarchy=hrc)
        cv.imshow('canny indicator', drawing)


def contours():
    cv.namedWindow('canny indicator')
    cv.createTrackbar('thresh low:', 'canny indicator', 100, 255, on_canny)
    cv.createTrackbar('thresh high:', 'canny indicator', 100, 255, on_canny)
    cv.createTrackbar('Contours width:', 'canny indicator', 0, 255, on_canny)
    on_canny(0)
    cv.waitKey(0)


SELECTOR = 'image area selector'
TL_X = 'Top Left X'
TL_Y = 'Top Left Y'
BR_X = 'Bottom Right X'
BR_Y = 'Bottom Right Y'
SAVE = 'Save'
IMAGE = '../resources/path/cap-10.png'


def draw_rect(arg):
    tlx = cv.getTrackbarPos(TL_X, SELECTOR)
    tly = cv.getTrackbarPos(TL_Y, SELECTOR)
    brx = cv.getTrackbarPos(BR_X, SELECTOR)
    bry = cv.getTrackbarPos(BR_Y, SELECTOR)
    img = cv.imread(IMAGE)
    cv.imshow(SELECTOR, cv.rectangle(img, (tlx, tly), (brx, bry), (0, 0, 255), 2))


def save_area(arg):
    btn = cv.getTrackbarPos(SAVE, SELECTOR)
    if not btn:
        return

    now = int(time.time())
    tlx = cv.getTrackbarPos(TL_X, SELECTOR)
    tly = cv.getTrackbarPos(TL_Y, SELECTOR)
    brx = cv.getTrackbarPos(BR_X, SELECTOR)
    bry = cv.getTrackbarPos(BR_Y, SELECTOR)
    img = cv.imread(IMAGE)
    area = img[tly:bry, tlx:brx]
    cv.imwrite(f'../resources/area/{now}.png', area)


def select_area():
    img = cv.imread(IMAGE)
    cv.namedWindow(SELECTOR)
    cv.createTrackbar(TL_X, SELECTOR, 0, img.shape[1], draw_rect)
    cv.createTrackbar(TL_Y, SELECTOR, 0, img.shape[0], draw_rect)
    cv.createTrackbar(BR_X, SELECTOR, 0, img.shape[1], draw_rect)
    cv.createTrackbar(BR_Y, SELECTOR, 0, img.shape[0], draw_rect)
    cv.createTrackbar(SAVE, SELECTOR, 0, 1, save_area)
    draw_rect(0)
    cv.waitKey(0)


def grabcut():
    cap = cv.imread(IMAGE)
    mask = np.zeros(cap.shape[:2], np.uint8)
    bgm = np.zeros((1, 65), np.float64)
    fgm = np.zeros((1, 65), np.float64)
    rect = (203, 171, 336, 301)
    cv.grabCut(cap, mask, rect, bgm, fgm, 1, cv.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    img = cap * mask2[:, :, np.newaxis]
    utils.show(img)


def pick(val):
    lh = cv.getTrackbarPos('low hue', 'hsv picker')
    ls = cv.getTrackbarPos('low sat', 'hsv picker')
    lv = cv.getTrackbarPos('low val', 'hsv picker')
    hh = cv.getTrackbarPos('high hue', 'hsv picker')
    hs = cv.getTrackbarPos('high sat', 'hsv picker')
    hv = cv.getTrackbarPos('high val', 'hsv picker')
    print(lh, ls, lv, hh, hs, hv)
    lower_green = np.array([lh, ls, lv])
    upper_green = np.array([hh, hs, hv])
    img = cv.imread('../resources/path/cap-10.png')
    # img = cv.resize(img, None, fx=.5, fy=.5, interpolation=cv.INTER_AREA)
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, lower_green, upper_green)
    res = cv.bitwise_and(img, img, mask=mask)
    cv.imshow('hsv picker', res)


def hsv_picker():
    cv.namedWindow('hsv picker', 0)
    # cv.resizeWindow('hsv picker', 900, 570)
    lh = cv.createTrackbar('low hue', 'hsv picker', 0, 255, pick)
    ls = cv.createTrackbar('low sat', 'hsv picker', 0, 255, pick)
    lv = cv.createTrackbar('low val', 'hsv picker', 0, 255, pick)
    hh = cv.createTrackbar('high hue', 'hsv picker', 0, 255, pick)
    hs = cv.createTrackbar('high sat', 'hsv picker', 0, 255, pick)
    hv = cv.createTrackbar('high val', 'hsv picker', 0, 255, pick)
    pick(0)
    cv.waitKey(0)


THRESH_WIN = 'thresh window'
THRESH_LOW = 'thresh low'
THRESH_HIGH = 'thresh high'
THRESH_TYPE = 'thresh type'
THRESH_TYPES = dict()
THRESH_IMG = cv.imread('../resources/area/dilate.png', 0)


def on_thresh(val):
    miv = cv.getTrackbarPos(THRESH_LOW, THRESH_WIN)
    mav = cv.getTrackbarPos(THRESH_HIGH, THRESH_WIN)
    t = cv.getTrackbarPos(THRESH_TYPE, THRESH_WIN)
    cp = THRESH_IMG.copy()
    th = cv.threshold(cp, miv, mav, t)[1]
    cv.imshow(THRESH_WIN, th)


def thresh():
    for i in dir(cv):
        if i.startswith('THRESH'):
            THRESH_TYPES[getattr(cv, i)] = i

    cv.namedWindow(THRESH_WIN)
    cv.createTrackbar(THRESH_LOW, THRESH_WIN, 0, 255, on_thresh)
    cv.createTrackbar(THRESH_HIGH, THRESH_WIN, 0, 255, on_thresh)
    cv.createTrackbar(THRESH_TYPE, THRESH_WIN, 0, 16, on_thresh)
    on_thresh(0)
    cv.waitKey(0)


def scene_stack():
    d = '../resources/path'
    stack = []
    idx = 1
    for e in os.listdir(d):
        p = f'{d}/cap-{idx}.png'
        stack.append((cv.imread(p, cv.COLOR_BGR2GRAY), p))
        idx += 1
    return stack


def text(img, txt, p, color=(0, 255, 255), scale=.5):
    cv.putText(img, str(txt), org=np.subtract(p, (0, 5)), fontFace=cv.FONT_ITALIC, fontScale=scale,
               color=color, lineType=1)


if __name__ == '__main__':
    select_area()
    # contours()
    # dilation()
    # hsv_picker()
    # thresh()


