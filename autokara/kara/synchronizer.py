import threading
import time
from kara.karaexception import KaraException
from kara.utils import pos

lock = threading.Lock()
CANCEL_POS = pos('arena.match.cancel.button')


class Synchronizer(object):

    def __init__(self, member: int):
        self.member = member
        self.ev_senator = [0 for _ in range(member)]
        self.lv_senator = [0 for _ in range(member)]
        self.elv_barrier = threading.Barrier(member)

        self.scene_check = [False for _ in range(member)]
        self.scene_barrier = threading.Barrier(member)

        self.barrier = threading.Barrier(member)
        self.matched_timestamp = 0

        self.coordinators = [None for _ in range(member)]

        self.matched_senator = [False for _ in range(member)]
        self.surrender_barrier = None

        self.reset_senator = [False for _ in range(member)]

    def join(self, idx: int, ev: int, lv: int) -> tuple:
        self.ev_senator[idx] = ev
        self.lv_senator[idx] = lv
        try:
            self.elv_barrier.wait()
        except threading.BrokenBarrierError:
            raise KaraException('abort error')
        mev, mlv = max(self.ev_senator), max(self.lv_senator)
        self.elv_barrier.reset()
        return mev, mlv

    def same_scene(self, idx: int, check: bool) -> bool:
        self.scene_check[idx] = check
        try:
            self.scene_barrier.wait()
        except threading.BrokenBarrierError:
            raise KaraException('abort error')
        v = False in self.scene_check
        self.scene_barrier.reset()
        return not v

    def coordinate(self, sml):
        self.coordinators[sml.idx] = sml

    def cancel_all(self):
        for sml in self.coordinators:
            sml.click(CANCEL_POS)
        self.matched_timestamp = 999
        self.matched_timestamp = 998

    def ready_match(self):
        try:
            self.barrier.wait()
        except threading.BrokenBarrierError:
            raise KaraException('abort error')

    def match_collision(self, matched: bool) -> float:
        if not matched:
            if self.matched_timestamp != 0:
                return time.time() - self.matched_timestamp
            return 0.0

        # matched
        lock.acquire()
        try:
            if self.matched_timestamp == 0:
                self.matched_timestamp = time.time()
            return 0.0
        finally:
            lock.release()

    def simple_collision(self, matched: bool) -> float:
        if not matched:
            if self.matched_timestamp != 0:
                return time.time() - self.matched_timestamp
        elif self.matched_timestamp == 0:
            self.matched_timestamp = time.time()
        return 0.0

    def wait_times_diff(self, wait_times: int, matched: bool) -> int:
        if not matched:
            if self.matched_timestamp != 0:
                return self.matched_timestamp - wait_times
        elif self.matched_timestamp == 0:
            self.matched_timestamp = wait_times
        return 0

    def end_match(self, idx: int):
        self.reset_senator[idx] = True
        if False in self.reset_senator:
            return

        # reset
        self.barrier.reset()
        self.matched_timestamp = 0
        self.reset_senator = [False for _ in range(len(self.reset_senator))]

    def report_matched(self, idx: int):
        self.matched_senator[idx] = True

    def ready_surrender(self):
        if not self.surrender_barrier:
            mb_size = self.matched_senator.count(True)
            if mb_size < 1:
                raise KaraException('ready surrender sync error with size ' + str(mb_size))
            self.surrender_barrier = threading.Barrier(mb_size)

        try:
            self.surrender_barrier.wait()
        except threading.BrokenBarrierError:
            raise KaraException('abort error')

    def end_surrender(self):
        if self.surrender_barrier:
            self.surrender_barrier.reset()
        self.matched_senator = [False for _ in range(self.member)]

    def stop(self):
        self.elv_barrier.abort()
        self.scene_barrier.abort()
        self.barrier.abort()
        if self.surrender_barrier:
            self.surrender_barrier.abort()


def test():
    pass


if __name__ == '__main__':
    # s = [False for _ in range(4)]
    # s[0] = True
    test()

