import time
from tasklist import tasks as all_tasks
from airtest.core.api import init_device
from multiprocessing import Process


class Simulator(Process):

    def __init__(self, idx, name, handle, hwnd, serialno, sync, _indicator, _pause, _stop):
        super().__init__(daemon=True)
        self.idx = idx
        self.name = name
        self.handle = handle
        self.hwnd = hwnd

        self.sync = sync
        self._indicator = _indicator
        self._pause = _pause
        self._stop = _stop

        self.dev = init_device(uuid=serialno)
        self.serialno = serialno
        self.preheating()

        self.tasks = [t for t in all_tasks().values()]
        self.total = len(self.tasks)
        self.account = ''
        self.energy = 0
        self.level = 0
        self.arena_counter = 0

    def preheating(self):
        self.dev.snapshot()

    def snapshot(self):
        return self.dev.snapshot()

    def click(self, pos):
        self.dev.touch(pos)

    def run(self) -> None:
        while True:
            time.sleep(.2)

            if self._stop.is_set():
                self._indicator[self.idx] = 1
                self._stop.wait()
            self._pause.wait()

            idc = self._indicator[self.idx]
            if proceed(idc):
                task = self.tasks[idc - 1]
                if idc + 1 > self.total + 1:
                    self._stop.set()
                else:
                    self._indicator[self.idx] = idc + 1
            else:
                task = self.tasks[idc - 1]
                self._stop.set()
            task(self)


def proceed(idc: int) -> bool:
    return idc > 0


def next_task(idc: int, limit: int) -> int:
    if idc + 1 > limit + 1:
        return 1
    return idc + 1


if __name__ == '__main__':
    pass
