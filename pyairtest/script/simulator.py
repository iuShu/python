import time
from script.tasklist import tasks as all_tasks
from airtest.core.api import init_device
from multiprocessing import Process


class Simulator(Process):

    def __init__(self, idx, name, handle, hwnd, serialno, sync, _indicator, _not_pause, _not_stop):
        super().__init__(daemon=True)
        self.idx = idx
        self.name = name
        self.handle = handle
        self.hwnd = hwnd

        self.sync = sync                        # Manager.Array
        self._indicator = _indicator            # Manager.Array
        self._not_pause = _not_pause            # Manager.Event
        self._not_stop = _not_stop              # Manager.Event

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

    def set_indicator(self, progress):
        self._indicator[self.idx] = progress

    def run(self) -> None:
        progress = 0
        while True:

            # TODO how to control the single or partial-loop task ?

            if not self._not_stop.is_set():     # stop
                progress = 0
                self.set_indicator(0)
                self._not_stop.wait()

            self._not_pause.wait()

            indicator = self._indicator[self.idx]
            if has_task(progress, indicator):
                task = self.tasks[progress]
                task(self)
                time.sleep(.2)

            progress += 1
            if progress > self.total:
                progress = 0
                self.set_indicator(0)
                self._not_stop.clear()


def has_task(index: int, indicator: int) -> bool:
    serial = bin(indicator)[2:]
    return serial[index] == '1'


if __name__ == '__main__':
    pass
