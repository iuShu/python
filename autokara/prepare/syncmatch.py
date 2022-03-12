import random
import threading
import time


class Synchronizer(object):

    def __init__(self):
        pass


class Slave(threading.Thread):

    def __init__(self, sid: int, barrier: threading.Barrier):
        threading.Thread.__init__(self)
        self.sid = sid
        self.barrier = barrier

    def run(self) -> None:
        if not self.check_power():
            return

        self.barrier.wait()

        self.click('arena level')

        while True:
            if self.match('cancel button'):
                continue

        pass

    def check_power(self) -> bool:
        pass

    def click(self, pos: str):
        pass

    def match(self, img: str) -> bool:
        pass


def test():
    batch = 4
    barrier = threading.Barrier(batch)
    slaves = []
    for i in range(batch):
        s = Slave(i * 100, barrier)
        slaves.append(s)
        s.start()
    for i in slaves:
        i.join()


if __name__ == '__main__':
    test()
