import random
import threading
import time

import cv2 as cv
import numpy as np

import kara.utils
from config import config
from kara.synchronizer import Synchronizer
from kara.simulator import Simulator


class SyncTest(threading.Thread):

    def __init__(self, sml: Simulator, syn: Synchronizer):
        threading.Thread.__init__(self)
        self.sml = sml
        self.syn = syn

    def run(self) -> None:
        matched = self.syn.match_collision
        wait_times = config.instance().getint('kara', 'arena.match.wait.time')
        match_collision_endurance = config.instance().getint('kara', 'arena.match.collision.endurance') / 1000
        scene_pos, clt, crb, cancel_pos = (128, 108), (236, 116), (285, 167), (256, 136)
        cancel_img = cv.imread('../resources/area/cancel.png')
        cd = config.instance().getint('kara', 'arena.startup.cooldown') / 1000
        # clt, crb = np.array(clt), np.array(crb)

        self.syn.ready_match()

        self.sml.click(scene_pos)
        time.sleep(cd)

        while matched(False) < match_collision_endurance and wait_times > 0:
            lt, rb = self.sml.tmatch(cancel_img)
            if np.all(lt != clt) or np.all(rb != crb):  # matched
                matched(True)
                self.syn.finished(self.sml.idx)
                print(self.sml.name + ' matched at', wait_times)
                time.sleep(random.randint(1, 3))
                print(self.sml.name + ' surrendered')
                return
            wait_times -= 1

        print(self.sml.name + ' missed at', wait_times)
        self.sml.click(cancel_pos)
        self.syn.finished(self.sml.idx)


def test():
    batch = 4
    sync = Synchronizer(batch)
    sml = [Simulator(0, 'ld1', 10225640, 9700794, ''),
           Simulator(1, 'ld2', 7995654, 7734554, ''),
           Simulator(2, 'ld3', 9176544, 7539042, ''),
           Simulator(3, 'ld4', 2820204, 9896436, '')]

    time.sleep(3)

    for i in range(batch):
        t = SyncTest(sml[i], sync)
        t.start()

    time.sleep(2)
    click_matched(sml, batch-1)


def click_matched(sml: list, batch=1):
    matched_pos = (779, 288)
    matched_barrier = threading.Barrier(batch)

    def execute(s: Simulator, barrier: threading.Barrier):
        barrier.wait()
        s.click(matched_pos)

    for i in range(batch):
        t = threading.Thread(target=execute, args=[sml[i], matched_barrier])
        t.start()


def simple():
    time.sleep(3)
    sml = [Simulator(0, 'ld1', 10225640, 9700794, ''),
           Simulator(1, 'ld2', 7995654, 7734554, ''),
           Simulator(2, 'ld3', 9176544, 7539042, ''),
           Simulator(3, 'ld4', 2820204, 9896436, '')]
    tpl = cv.imread('../resources/area/cancel.png')
    cl, cr = (236, 116), (285, 167)
    for s in sml:
        s.click((128, 108))

    time.sleep(2)

    for _ in range(10):
        for s in sml:
            l, r = s.tmatch(tpl)
            if np.all(l != cl) or np.all(r != cr):
                print(s.name, 'x')
            # else:
            #     print(s.name, 'matched')
            #     s.click((779, 288))

    for s in sml:
        s.click((779, 288))


if __name__ == '__main__':
    # 576, 962

    test()
    # simple()

    pass

