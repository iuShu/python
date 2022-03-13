import threading
import time

import cv2 as cv
import numpy as np

import kara.utils
import script.textocr
from kara.simulator import Simulator


TPL = cv.imread('../resources/area/roi.png')


class Synchronizer(object):

    def __init__(self):
        pass


class Slave(threading.Thread):

    def __init__(self, sml: Simulator, sid: int, barrier: threading.Barrier):
        threading.Thread.__init__(self)
        self.sml = sml
        self.sid = sid
        self.barrier = barrier
        self.trigger = 0

    def run(self) -> None:
        rlt, rrb = (103, 81), (158, 137)
        # p = np.array((130, 109))
        p2 = (390, 210)

        while True:
            lt, rb = self.sml.tmatch(TPL)
            if np.all(lt == rlt) and np.all(rb == rrb):
                self.barrier.wait()
                break
        print(1)
        while True:
            lt, rb = self.sml.tmatch(TPL)
            if np.all(lt != rlt) or np.all(rb != rrb):
                self.sml.click(p2)
            time.sleep(.02)

        # time.sleep(.2)
        # while True:
        #     if self.match('cancel button'):
        #         continue

        pass


def test():
    batch = 4
    barrier = threading.Barrier(batch)
    sml = [Simulator(0, 'ld1', 393894, 132428, 'emulator-5554'), Simulator(1, 'ld2', 853248, 591158, '127.0.0.1:5557'),
           Simulator(0, 'ld3', 459946, 2229310, '127.0.0.1:5559'), Simulator(0, 'ld4', 66960, 66976, '127.0.0.1:5561')]
    slaves = []
    for i in range(batch):
        s = Slave(sml[i], i * 100, barrier)
        slaves.append(s)
        s.start()
    for i in slaves:
        i.join()


if __name__ == '__main__':
    # test()
    # ev1 = img[lt[1]:rb[1], lt[0]:rb[0]]

    # 576, 962
    img = cv.imread('../resources/arena/match.png')
    lt, rb = kara.utils.pos('arena.match.cancel.lt'), kara.utils.pos('arena.match.cancel.rb')
    print(lt, rb)
    # img = img[lt[1]:rb[1], lt[0]:rb[0]]
    # img = img[:, :1530, :]
    # img = cv.resize(img, (962, 576))
    tpl = cv.imread('../resources/cancel.png')
    print(kara.utils.tmatch(img, tpl))
    # cv.imshow('img', img)
    # cv.waitKey(0)
    # cv.imwrite('../resources/cancel.png', img)

