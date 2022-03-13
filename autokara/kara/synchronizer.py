import queue
import threading

lock = threading.Lock()


class Synchronizer(object):

    def __init__(self, member: int):
        self.ev_senator = [0 for _ in range(member)]
        self.lv_senator = [0 for _ in range(member)]
        self.barrier = threading.Barrier(member)

    def join(self, idx: int, ev: int, lv: int):
        self.ev_senator[idx] = ev
        self.lv_senator[idx] = lv
        self.barrier.wait()
        mev, mlv = max(self.ev_senator), max(self.lv_senator)
        self.barrier.reset()
        return mev, mlv


if __name__ == '__main__':
    s = [0 for _ in range(4)]
    s[0] = 4
    s[2] = 3
    print(max(s))
