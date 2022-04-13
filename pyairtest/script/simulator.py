import time
from script.tasklist import tasks as all_tasks
from airtest.core.api import init_device
from multiprocessing import Process


class Simulator(Process):

    def __init__(self, idx, name, handle, hwnd, serialno, sync, _indicator, _not_pause, _not_stop):
        super().__init__(daemon=True)
        self.idx = idx
        self.name = name
        self.handle = int(handle)
        self.hwnd = int(hwnd)

        self.sync = sync                # Manager.Array
        self._indicator = _indicator    # Manager.Array
        self._not_pause = _not_pause    # Manager.Event
        self._not_stop = _not_stop      # Manager.Event
        self.progress = 0

        self.dev = init_device(uuid=serialno)   # TODO serialize inside the Process
        self.serialno = serialno

        self.tasks = [t for t in all_tasks().values()]
        self.total = len(self.tasks)
        self.account = ''
        self.energy = 0
        self.level = 0
        self.arena_counter = 0

        self.preheating()

    def preheating(self):
        self.dev.snapshot()

    def snapshot(self):
        return self.dev.snapshot()

    def click(self, pos):
        self.dev.touch(pos)

    def set_indicator(self, progress):
        self._indicator[self.idx] = progress

    def fallback(self, step=1):
        self.progress -= step

    def run(self) -> None:
        print(self.name, self.pid, 'start')
        while True:
            if not self._not_stop.is_set():
                print(self.name, 'stop')
                self.progress = 0
                self.set_indicator(0)
                self._not_stop.wait()       # wait if stop

            print(self.name, self._not_pause.is_set())
            self._not_pause.wait()          # wait if pause

            indicator = self._indicator[self.idx]
            if has_task(self.progress, indicator):
                task = self.tasks[self.progress]
                task(self)
                time.sleep(.2)

            self.progress += 1
            if self.progress > self.total:
                print(self.name, 'finished round')
                self.progress = 0
                self.set_indicator(0)
                self._not_stop.clear()


def has_task(index: int, indicator: int) -> bool:
    """
        indicator value
            full task:      0b1111 1110 0000 ... ... 0000 0000
            single task:    0b0010 0000 0000 ... ... 0000 0000
            partial task:   0b0111 0000 0000 ... ... 0000 0000
    """
    serial = bin(indicator)[2:]
    return serial[index] == '1'


if __name__ == '__main__':
    pass
