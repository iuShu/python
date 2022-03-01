import random

import cv2 as cv
import numpy as np

from script import action

RED = (0, 0, 255)
GOOD_THRESHOLD = 8
SIFT = cv.SIFT_create()
FLANN = cv.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
NOT_MATCHED = np.array((-1, -1))

ROI_WIDTH = 4
ROI_HEIGHT = 2
GROUND_THRESHOLD = 7000
ROLE = 1
SEARCHED = 5
WALL = 99
GRID_HEIGHT = 5
GRID_WIDTH = 9
CENTER_GRID = np.array((2, 4))


def matches(screen, template, gray=True, gaussian=True, threshold=GOOD_THRESHOLD):
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

    print('good: ', len(good), len(good) >= threshold)
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
            return NOT_MATCHED, NOT_MATCHED
    except cv.error:
        return NOT_MATCHED, NOT_MATCHED


def match_all(screen, templates, gaussian=True, threshold=GOOD_THRESHOLD):
    for t in templates:
        lt, rb = matches(screen, t, gaussian, threshold)
        if not np.any(lt == -1):
            return lt, rb
    return NOT_MATCHED


def left_click(handle, point, xo=0, yo=0):
    p = np.add(point, np.array((xo, yo)))
    action.left_click(handle, *p)


def random_point(lt, rb, xo=0, yo=0):
    cx = (rb[0] - lt[0]) / 2
    cy = (rb[1] - lt[1]) / 2
    rand = random.randint(0, 8)
    return int(xo + cx + lt[0] + rand), int(yo + cy + lt[1] + rand)


def random_click(handle, lt, br, xo=0, yo=0):
    point = random_point(lt, br, xo, yo)
    action.left_click(handle, *point)


def center(point):
    if not isinstance(point, np.ndarray):
        point = np.array(point)
    return np.add(point[0], (point[1] - point[0]) // 2)


def roi_area_more(pos):
    rw, rh = pos[1][0] - pos[0][0], pos[1][1] - pos[0][1]
    lt = pos[0][0] - rw * ROI_WIDTH, pos[0][1] - rh * ROI_HEIGHT
    rb = pos[1][0] + rw * ROI_WIDTH, pos[1][1] + rh * ROI_HEIGHT
    grids = []
    y = lt[1]
    while y < rb[1]:
        x = lt[0]
        while x < rb[0]:
            grids.append(((x, y), (x + rw, y + rh)))
            x += rw
        y += rh
    return grids


def filter_ground(img):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    upper = np.array([186, 133, 90])
    lower = np.array([128, 39, 12])
    mask = cv.inRange(hsv, lower, upper)
    res = cv.bitwise_and(img, img, mask=mask)
    # show(res)
    return res


def reg_scene(cap, pos):
    nears = roi_area_more(pos)
    filtered = filter_ground(cap)
    grounds = []
    for lt, rb in nears:
        grid = filtered[lt[1]:rb[1], lt[0]:rb[0]]
        if np.count_nonzero(grid) > GROUND_THRESHOLD:
            grounds.append(0)
        else:
            grounds.append(WALL)
    return np.array(nears).reshape((GRID_HEIGHT, GRID_WIDTH, 2, 2)), np.array(grounds).reshape(
        (GRID_HEIGHT, GRID_WIDTH))


def show(img, title='img'):
    cv.imshow(title, img)
    cv.waitKey(0)


def show_match(capture, lt, br):
    cv.rectangle(capture, lt, br, (0, 0, 255), 2)
    cv.imshow('img', capture)
    cv.waitKey(0)


def show_point(capture, point):
    cv.rectangle(capture, point, np.add(point, 2), RED, 2)
    cv.imshow('img', capture)
    cv.waitKey(0)


def grab_cut(img, rect):
    mask = np.zeros(img.shape[:2], np.uint8)
    bgm = np.zeros((1, 65), np.float64)
    fgm = np.zeros((1, 65), np.float64)

    # rect = (0, 0, 109, 109)
    cv.grabCut(img, mask, rect, bgm, fgm, 5, cv.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    return img * mask2[:, :, np.newaxis]
