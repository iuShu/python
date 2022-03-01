import cv2 as cv
import numpy as np
import pytesseract
from script.utils import show
from script.textocr import text_recognize


def scene():
    img = cv.imread('../resources/path/cap-10.png')
    lower_green = np.array([0, 0, 225])
    upper_green = np.array([60, 182, 255])
    img = cv.imread('../resources/path/cap-3.png')
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, lower_green, upper_green)
    res = cv.bitwise_and(img, img, mask=mask)
    show(res)


def healthy():
    img = cv.imread('../resources/path/cap-10.png')
    roi = img[188:210, 133:180]
    show(roi)
    roi = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
    th = cv.threshold(roi, 168, 255, cv.THRESH_BINARY)[1]
    show(th)
    txt = pytesseract.image_to_string(th)
    print('healthy', txt)


if __name__ == '__main__':
    # scene()
    healthy()

