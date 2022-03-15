import threading
import time

lock = threading.Lock()


class Synchronizer(object):

    def __init__(self, member: int):
        self.ev_senator = [0 for _ in range(member)]
        self.lv_senator = [0 for _ in range(member)]
        self.elv_barrier = threading.Barrier(member)

        self.scene_check = [False for _ in range(member)]
        self.scene_barrier = threading.Barrier(member)

        self.barrier = threading.Barrier(member)
        self.matched_timestamp = 0

        self.reset_senator = [False for _ in range(member)]

    def join(self, idx: int, ev: int, lv: int) -> tuple:
        self.ev_senator[idx] = ev
        self.lv_senator[idx] = lv
        self.elv_barrier.wait()
        mev, mlv = max(self.ev_senator), max(self.lv_senator)
        self.elv_barrier.reset()
        return mev, mlv

    def same_scene(self, idx: int, check: bool) -> bool:
        self.scene_check[idx] = check
        self.scene_barrier.wait()
        v = False in self.scene_check
        self.scene_barrier.reset()
        return not v

    def ready_match(self):
        self.barrier.wait()

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

    def finished(self, idx: int):
        self.reset_senator[idx] = True
        if False in self.reset_senator:
            return

        # reset
        self.barrier.reset()
        self.matched_timestamp = 0
        self.reset_senator = [False for _ in range(len(self.reset_senator))]


def test():
    pass


if __name__ == '__main__':
    # s = [False for _ in range(4)]
    # s[0] = True
    test()

