import random
import time

import cv2 as cv
import numpy as np

import script.utils
from script.utils import *


def rand_cards(img=None):
    img = cv.imread('../resources/cap/cap-9.png')
    w, h = img.shape[1], img.shape[0]
    x, y = 80, h - h // 6
    cards = []
    while x < (w - 150):
        x += 35
        cards.append((x, y))
    for i in random.sample(range(0, 19), 19):
        cv.circle(img, cards[i], 3, 255, thickness=-1)
        show(img)


def buttons():
    img = cv.imread('../resources/cap/cap-5.png')
    # start = cv.imread('../resources/fight/start.png')
    # lt, br = matches(img, start, gaussian=False)
    # cv.circle(img, script.utils.center((lt, br)), 3, 255, thickness=-1)
    # show_match(img, lt, br)
    setting = (793, 72)
    start = (770, 365)
    speedup = (804, 406)
    show_point(img, setting)
    show_point(img, start)
    show_point(img, speedup)


def rounds(img=None):
    img = cv.imread('../resources/cap/cap-9.png')
    start = cv.imread('../resources/fight/start.png')
    lt, br = matches(img, start, gaussian=False)
    print(lt, br)
    show_match(img, lt, br)


def victory(img=None):
    img = cv.imread('../resources/cap/cap-11.png')
    vct = cv.imread('../resources/fight/victory.png')
    lt, br = matches(img, vct)
    print(lt, br)
    show_match(img, lt, br)


def fight():
    start = cv.imread('../resources/fight/start.png')
    vct = cv.imread('../resources/fight/victory.png')
    """
    wc.match_action(start, lambda wct, lt, br: wc.click(speedup))
    while True:
        # check healthy
        lt, br = matches(cap, start)
        if np.any(np.array(lt) == -1):
            lt, br = matches(cap, vct)
            if np.any(np.array(lt) == -1):
                break
            time.sleep(.5)
            continue
            
        rand_cards(cap)
        wc.click(start)
        time.sleep(5)
    
    wc.click(center)
    time.sleep(.5)
    wc.click(center)
    """


if __name__ == '__main__':
    # rand_cards()
    # buttons()
    # rounds()
    victory()

