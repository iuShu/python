import numpy as np
import cv2 as cv
from script.utils import show, center
from tools import scene_stack, text
from search import find_role


def scene(img=None):
    # img = cv.imread('../resources/path/cap-10.png')
    show(img)
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    low = np.array([62, 0, 0])
    high = np.array([93, 255, 188])
    mask = cv.inRange(hsv, low, high)
    res = cv.bitwise_and(img, img, mask=mask)
    show(res)
    return res


def dilate(img=None):
    prc = scene(img)
    gray = cv.cvtColor(prc, cv.COLOR_BGR2GRAY)
    tpv, kernel = 2, 1
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2 * kernel + 1, 2 * kernel + 1))
    res = cv.dilate(gray, kernel, None, None, tpv)
    show(res)
    return res


def contours(img=None):
    monsters = set()
    try:
        ori = img.copy()
        prc = dilate(img)
        th = 53
        canny = cv.Canny(prc, th, th * 2)
        cts, hrc = cv.findContours(canny, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        for c in cts:
            x, y, w, h = cv.boundingRect(c)
            if x > 860 and y < 75:
                continue
            if 40 < w <= 53 and 39 < h < 44:
                print(w, h)
                monsters.add(((x, y), (x+w, y+h)))
                cv.rectangle(ori, (x, y), (x+w, y+h), (0, 0, 255), 1)
        show(ori)
    finally:
        return monsters


def closest(img):
    # pos = np.array(((454, 244), (508, 309)), dtype=np.uint16)
    # img = cv.imread('../resources/path/cap-10.png')
    monsters = contours(img)
    if not len(monsters):
        print('no monster')
        return

    pos = find_role(img)
    if np.any(np.array(pos) == -1):
        print('can not find role')
        return

    ct = center(pos)
    mid, mp = 0, None
    for m in monsters:
        c = center(m)
        dst = int(np.linalg.norm(ct - c))
        cv.rectangle(img, m[0], m[1], (0, 0, 255), 2)
        text(img, dst, m[0])
        if not mid or mid > dst:
            mid = dst
            mp = m
    cv.rectangle(img, pos[0], pos[1], (0, 255, 255), 2)
    cv.rectangle(img, mp[0], mp[1], (255, 0, 255), 2)
    show(img)


def batch():
    for s in scene_stack():
        contours(s[0])
        # closest(s[0])


if __name__ == '__main__':
    # scene()
    # dilate()
    # contours()
    batch()

