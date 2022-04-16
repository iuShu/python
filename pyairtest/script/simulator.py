import time

import numpy as np

from script.tasklist import tasks as all_tasks
from airtest.core.api import init_device
from airtest.core.cv import Template
from multiprocessing import Process

EXECUTE_INTERVAL = .2
FIND_TIMEOUT = 20
FIND_INTERVAL = .5
SYNC_ACTION_TIMEOUT = 1800
SYNC_DATA_TIMEOUT = 3600


class Simulator(Process):

    def __init__(self, idx, name, handle, hwnd, serialno,
                 indicator, not_pause, not_stop, _sync_action, _sync_data):
        super().__init__(daemon=True)
        self.idx = idx
        self.name = name
        self.handle = int(handle)
        self.hwnd = int(hwnd)

        self.dev = None
        self.serialno = serialno

        self.indicator = indicator          # Manager.Array
        self.not_pause = not_pause          # Manager.Event
        self.not_stop = not_stop            # Manager.Event
        self._sync_action = _sync_action    # Barrier
        self._sync_data = _sync_data        # Manager.Array
        self.desired = None

        self.progress = 0
        self.tasks_name = [n for n in all_tasks().keys()]
        self.tasks = [t for t in all_tasks().values()]
        self.total = len(self.tasks)
        self.account = ''
        self.energy = 0
        self.level = 0
        self.arena_counter = 0

    def prepare(self):
        self.dev = init_device(uuid=self.serialno)
        if self.dev:
            self.dev.snapshot()     # preheating
            print(self.name, self.pid, 'device prepared')
            return
        raise RuntimeError(self.name, self.pid, 'init device error')

    def snapshot(self) -> np.ndarray:
        return self.dev.screen_proxy.snapshot()

    def match(self, template: Template) -> tuple:
        match_pos = template.match_in(self.snapshot())
        if match_pos:
            return match_pos
        return ()

    def click(self, pos: tuple):
        self.dev.touch(pos)

    def wait(self, template: Template, timeout=FIND_TIMEOUT, interval=FIND_INTERVAL) -> tuple:
        print(self.name, self.pid, 'finding', template)
        start_time = time.time()
        while self.not_stop.is_set():
            screen = self.snapshot()
            match_pos = template.match_in(screen)
            if match_pos:
                print(self.name, self.pid, 'found', template, 'cost', time.time() - start_time)
                return match_pos

            if (time.time() - start_time) > timeout:
                print(self.name, self.pid, 'cannot found', template)
                return ()
            time.sleep(interval)

    def typing(self, keys: str):
        pass

    def set_indicator(self, task_serial):
        self.indicator[self.idx] = task_serial

    def task_name(self, progress: int = 0) -> str:
        return self.tasks_name[progress if progress else self.progress]

    def stop(self):
        # TODO what if a task invoke barrier.wait() after the process stopped
        self.not_stop.clear()
        self.not_pause.set()
        self._sync_action.abort()
        self._sync_data[self.idx] = 0
        print(self.name, self.pid, 'stop at progress', self.task_name())

    def reset(self):
        self.progress = 0
        self.indicator[self.idx] = 0
        self.desired = None
        self.account = ''
        self.energy = 0
        self.level = 0
        self.arena_counter = 0

    def back_last(self, num: int = 1):
        prev_progress = self.progress - num
        if prev_progress < 0:
            self.stop()
            return

        task_serial = self.indicator[self.idx]
        if not has_task(prev_progress, task_serial):
            self.stop()
            return

        steps = num + 1
        print(self.name, self.pid, 'back to progress', self.task_name(self.progress - num))
        if self.progress < steps:
            self.progress = -1
        else:
            self.progress -= steps

    def execute(self, task) -> bool:
        try:
            task(self)
            return True
        except Exception as ex:
            print(self.name, 'execute task error:', ex.__str__)
            return False

    def sync_action(self) -> bool:
        try:
            self._sync_action.wait()
            self._sync_action.reset()
            return True
        except Exception:
            print(self.name, self.idx, 'sync action failed at', self.task_name())
            return False

    def sync_data(self, val: int) -> int:
        self._sync_data[self.idx] = val
        print(self.name, self.pid, 'sync with value', val)
        try:
            self._sync_action.wait()
            max_val = max(self._sync_data[self.idx])
            self._sync_data[self.idx] = 0
            self._sync_action.reset()
            return max_val
        except Exception:
            print(self.name, self.pid, 'sync data failed at', self.task_name())
            return -1

    def run(self) -> None:
        print(self.name, self.pid, 'start')
        self.prepare()
        while True:
            if not self.not_stop.is_set():
                self.reset()
                self.not_stop.wait()        # wait if stop

            print(self.name, self.not_pause.is_set())
            self.not_pause.wait()           # wait if pause
            if not self.not_stop.is_set():  # prevent recover from pause
                continue                    # release pause and stop

            task_serial = self.indicator[self.idx]
            if has_task(self.progress, task_serial):
                task = self.tasks[self.progress]
                if not self.execute(task):
                    break

            self.progress += 1
            if self.progress > self.total:
                print(self.name, 'finished round')
                self.stop()

            time.sleep(EXECUTE_INTERVAL)


def has_task(index: int, task_serial: int) -> bool:
    """
        task serial value
            full task:      0b1111 1110 0000 ... ... 0000 0000
            single task:    0b0010 0000 0000 ... ... 0000 0000
            partial task:   0b0111 0000 0000 ... ... 0000 0000
    """
    serial = bin(task_serial)[2:]
    return serial[index] == '1'


if __name__ == '__main__':
    pass
