import numpy as np
import cv2 as cv
from search import find_role
from script.utils import show


def scene():
    img = cv.imread('../resources/area/role.png')
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    th = cv.threshold(gray, 1, 255, cv.THRESH_BINARY_INV)[1]
    msk = cv.bitwise_not(img, img, mask=th)
    show(msk)

    hsv = cv.cvtColor(msk, cv.COLOR_BGR2HSV)
    show(hsv)
    h, s, v = cv.split(hsv)
    print(np.min(h))
    print(np.min(s))
    print(np.min(v))
    print(np.max(h))
    print(np.max(s))
    print(np.max(v))


def role():
    pass


if __name__ == '__main__':
    scene()



