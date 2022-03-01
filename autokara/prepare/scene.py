import os

import numpy as np
import cv2 as cv
from tools import scene_stack, text
from script.utils import show, center
from search import find_role


def scene(img=None):
    # img = cv.imread('../resources/path/cap-10.png')
    show(img)
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    low = np.array([32, 82, 0])
    high = np.array([62, 202, 195])
    mask = cv.inRange(hsv, low, high)
    res = cv.bitwise_and(img, img, mask=mask)
    # show(res)
    return res


def ground(img=None):
    img = cv.imread('../resources/path/cap-10.png')
    s = scene(img)
    low = np.array([123, 39, 0])
    high = np.array([150, 129, 91])
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, low, high)
    res = cv.bitwise_and(img, img, mask=mask)
    show(res)
    gray = cv.cvtColor(res, cv.COLOR_BGR2GRAY)
    tpv, kernel = 2, 1
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2 * kernel + 1, 2 * kernel + 1))
    dlt = cv.dilate(gray, kernel, None, None, tpv)
    # show(dlt)
    ths = cv.threshold(dlt, 0, 255, cv.THRESH_BINARY_INV)[1]
    show(ths)
    prc = cv.bitwise_and(img, img, mask=ths)
    show(prc)


def dilate(img=None):
    prc = scene(img)
    gray = cv.cvtColor(prc, cv.COLOR_BGR2GRAY)
    tpv, kernel = 2, 1
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (2 * kernel + 1, 2 * kernel + 1))
    res = cv.dilate(gray, kernel, None, None, tpv)
    # show(res)
    return res


def line():
    img = cv.imread('../resources/path/cap-10.png')
    prc = dilate(img)
    res = cv.threshold(prc, 0, 255, cv.THRESH_BINARY_INV)[1]
    edges = cv.Canny(res, 51, 113)
    show(edges)
    lines = cv.HoughLinesP(edges, 3, np.pi / 180, threshold=60, minLineLength=5, maxLineGap=10)
    pale = np.zeros(img.shape)
    for points in lines:
        x1, y1, x2, y2 = points[0]
        dx, dy = abs(x1 - x2), abs(y1 - y2)
        if dx > 30 or dy > 30:
            cv.line(pale, (x1, y1), (x2, y2), (0, 255, 255), 2)
    show(pale)


def thresh(img=None):
    # img = cv.imread('../resources/path/cap-1.png')
    res = dilate(img)
    res = cv.threshold(res, 0, 255, cv.THRESH_BINARY_INV)[1]
    # show(res)
    prc = cv.bitwise_and(img, img, mask=res)
    # show(prc)
    return res, prc


PREV_DIRECTION = 0


def search(img=None, pdir=0):
    # img = cv.imread('../resources/path/cap-16.png')
    thr, bwa = thresh(img)
    role = find_role(bwa)
    if np.any(np.array(role) == -1):
        print('can not find role')
        return

    c = center(role)
    genesis = c - 10, c + 10
    avl = spread(thr, genesis, pdir)
    nxt = None
    for i in range(len(avl)):
        e = avl[i]
        if i == len(avl)-1:
            cv.rectangle(bwa, e[0], e[1], (0, 0, 255), 2)
            nxt = e
        else:
            cv.rectangle(bwa, e[0], e[1], 255, 1)
    cv.line(bwa, c, center(nxt), (0, 255, 255), thickness=1)
    show(bwa)
    return calc_direction(c, center(nxt))


def spread(thr, grid, pdir, threshold=350):
    stack = [grid]
    reached = set()
    avl = []
    idx = 0
    while len(stack):
        cur = stack.pop()
        i = 0 if not len(stack) else len(stack)
        for n in neighbors(cur, thr.shape, pdir):
            if np.any(n is None):
                continue
            if np.all(n == -1):     # reach border
                return avl
            tp = tuple(map(tuple, n))
            if tp in reached:
                continue
            if cv.countNonZero(thr[n[0][1]:n[1][1], n[0][0]:n[1][0]]) < threshold:
                continue
            stack.insert(i, n)
            reached.add(tp)
            avl.append(tp)
            cv.rectangle(thr, tp[0], tp[1], (0, 0, 0), 1)
            text(thr, idx, np.add(tp[0], (0, 16)), color=(0, 0, 0), scale=.3)
            show(thr)
            idx += 1
    return avl


OUT_OF_BORDER = np.array(((-1, -1), (-1, -1)))
FORBIDDEN = np.array((((0, 0), (180, 304)), ((180, 0), (566, 134)), ((774, 0), (1000, 134))))


def neighbors(grid, limit, pdir):
    if pdir == 0:
        return [up(grid), left(grid), right(grid, limit), down(grid, limit)]
    elif pdir == 1:
        return [down(grid, limit), left(grid), right(grid, limit), up(grid)]
    elif pdir == 2:
        return [up(grid), down(grid, limit), left(grid), right(grid, limit)]
    elif pdir == 3:
        return [up(grid), down(grid, limit), right(grid, limit), left(grid)]


def up(p):
    p = np.subtract(p, (0, 20))
    if p[0][1] >= 36 and not in_forbidden(p):
        return p
    return OUT_OF_BORDER


def down(p, limit):
    p = np.add(p, (0, 20))
    if p[1][1] <= limit[0] and not in_forbidden(p):
        return p
    return OUT_OF_BORDER


def left(p):
    p = np.subtract(p, (20, 0))
    if p[0][0] >= 0 and not in_forbidden(p):
        return p
    return OUT_OF_BORDER


def right(p, limit):
    p = np.add(p, (20, 0))
    if p[1][0] <= limit[1] - 36 and not in_forbidden(p):
        return p
    return OUT_OF_BORDER


def in_forbidden(p):
    for f in FORBIDDEN:
        if f[0][0] <= p[0][0] < f[1][0]:
            if f[0][1] <= p[0][1] < f[1][1]:
                return True
    return False


def calc_direction(p1, p2):
    angle = int(np.rad2deg(np.arctan2(p2[1] - p1[1], p2[0] - p1[0])))
    print('angle', angle)
    if -135 <= angle < -45:
        return 0    # up
    elif 45 <= angle < 135:
        return 1    # down
    elif 135 <= angle <= 180 or -180 <= angle < -135:
        return 2    # left
    elif -45 <= angle < 45:
        return 3    # right


def batch():
    pdir = 0
    for img in scene_stack():
        print('process in', img[1])
        # dilate(img[0])
        # thresh(img[0])
        pdir = search(img[0], pdir)
        print('prev', pdir)


if __name__ == '__main__':
    # scene()
    # ground()
    # dilate()
    # line()
    # thresh()
    # search()
    batch()


