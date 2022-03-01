import sys

import numpy as np
import cv2
from ctypes import windll
from ctypes.wintypes import HWND

import pytesseract
import win32api
import win32gui


def test():
    print('Hello PyCharm')
    for i in range(10):
        print(i)


def nptest():
    v = np.array([1,2,3])
    # print(np.eye(3, 3))
    # print(np.shape(np.full((3,2), 5, dtype=np.float64)))
    print(np.reshape(v, (3, 1)))


def cvtest():
    img = cv2.imread('../resources/kara.png')
    # cv2.imshow("kara.png", img)
    # cv2.waitKey()
    print(type(img))
    print(img.shape)
    print(img.size)
    print(img.dtype)
    print(img.item(10,10,2))


def img_draw():
    black = np.zeros((512,512,3), np.uint8)
    cv2.line(black, (0,0), (511,511), (0,0,255), 5)
    cv2.rectangle(black, (324,100), (500,228), (0,255,0), 3)
    cv2.circle(black, (447,63), 63, (255,0,0), 2)
    cv2.ellipse(black, (256, 256), (100, 50), 0, 0, 180, 255, -1)
    cv2.putText(black, 'OpenCV', (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow("black", black)
    cv2.waitKey()


def tesseract_demo():
    from PIL import Image
    txt = pytesseract.image_to_string(Image.open('../resources/atv_power.png'))
    print(txt)


if __name__ == '__main__':
    # test()
    # nptest()
    # cvtest()
    # img_draw()
    tesseract_demo()
