import time
import traceback

import numpy as np
from constants import max_task_num

from script.tasklist import tasks as all_tasks
from airtest.core.api import init_device
from airtest.core.cv import Template
from multiprocessing import Process

EXECUTE_INTERVAL = .2
FIND_TIMEOUT = 20
FIND_INTERVAL = .5


class Simulator(Process):

    def __init__(self, idx, name, handle, hwnd, serialno,
                 indicator, not_pause, not_stop, _sync_action, _sync_data, _acc_queue, log_queue):
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
        self._acc_queue = _acc_queue        # Manager.Queue
        self.log_queue = log_queue          # Manager.Queue
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
            self.log('device prepared')
            return
        raise RuntimeError(self.name, self.pid, 'init device error')

    def snapshot(self) -> np.ndarray:
        return self.dev.screen_proxy.snapshot()

    def click(self, pos: tuple):
        self.dev.touch(pos)

    def match(self, template: Template) -> tuple:
        ret = template._cv_match(self.snapshot())
        if ret:
            rec = ret['rectangle']
            return rec[0], rec[2]
        return ()

    def wait(self, template: Template, timeout=FIND_TIMEOUT, interval=FIND_INTERVAL) -> tuple:
        self.log('finding', template.filename)
        start_time = time.time()
        while self.is_running():
            rec = self.match(template)
            if rec:
                self.log('found', template.filename, 'cost', time.time() - start_time)
                return rec

            if (time.time() - start_time) > timeout:
                self.log('cannot found', template.filename)
                return ()
            time.sleep(interval)

    def obtain_account(self) -> tuple:
        if self._acc_queue.empty():
            return ()
        acc = self._acc_queue.get_nowait()
        return acc if acc else ()

    def set_indicator(self, task_serial):
        self.indicator[self.idx] = task_serial

    def task_name(self, progress: int = 0) -> str:
        return self.tasks_name[progress if progress else self.progress]

    def is_running(self) -> bool:
        return self.not_stop.is_set()

    def log(self, *args):
        joined = ' '.join(tuple(map(str, args)))
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = f'[{now}] {self.pid} {self.name} {joined}\n'
        self.log_queue.put_nowait(msg)
        print(msg)

    def stop(self):     # stop all processes
        self.not_stop.clear()
        self.not_pause.set()
        self._sync_action.reset()
        self._sync_data[self.idx] = 0
        self.reset_pvp_sync()
        self.log('stop at progress', self.task_name())

    def reset(self):
        self.progress = 0
        self.indicator[self.idx] = 0
        self.desired = None
        self.account = ''
        self.energy = 0
        self.level = 0
        self.arena_counter = 0

    def forward(self, num: int = 1):
        fore_progress = self.progress + num
        if fore_progress >= self.total:
            self.stop()
            return

        task_serial = self.indicator[self.idx]
        if not has_task(fore_progress, task_serial):
            self.stop()
            return

        steps = num - 1
        self.log('fore to progress', self.task_name(self.progress + num))
        self.progress += steps

    def backward(self, num: int = 1):
        prev_progress = self.progress - num
        if prev_progress < 0:
            self.stop()
            return

        task_serial = self.indicator[self.idx]
        if not has_task(prev_progress, task_serial):
            self.stop()
            return

        steps = num + 1
        self.log('back to progress', self.task_name(self.progress - num))
        if self.progress < steps:
            self.progress = -1
        else:
            self.progress -= steps

    def execute(self, task) -> bool:
        try:
            task(self)
            return True
        except Exception:
            self.log('execute task error:', traceback.format_exc())
            return False

    def sync_action(self) -> bool:
        try:
            self._sync_action.wait()
            self._sync_action.reset()
            return True
        except Exception:
            self.log(self.name, self.idx, 'sync action failed at', self.task_name(), '\n', traceback.format_exc())
            self.not_stop.clear()
            return False

    def sync_data(self, val: int) -> int:
        self._sync_data[self.idx] = val
        self.log('sync with value', val)
        try:
            self._sync_action.wait()
            max_val = max(self._sync_data)
            self._sync_data[self.idx] = 0
            self._sync_action.reset()
            return max_val
        except Exception:
            self.log('sync data failed at', self.task_name(), '\n', traceback.format_exc())
            self.not_stop.clear()
            return -1

    def pvp_sync(self, val: int, matched: bool) -> int:
        data = self._sync_data[-1]
        if matched and data == 0:
            self._sync_data[-1] = val
            return 0
        elif data != 0:
            return val - data
        return 0

    def reset_pvp_sync(self):
        self._sync_data[-1] = 0

    def run(self) -> None:
        self.log('start')
        self.prepare()
        while True:
            if not self.is_running():
                self.reset()
                self.not_stop.wait()        # wait if stop

            self.not_pause.wait()           # wait if pause
            if not self.is_running():       # prevent recover from pause
                continue

            task_serial = self.indicator[self.idx]
            if has_task(self.progress, task_serial):
                task = self.tasks[self.progress]
                if not self.execute(task):
                    self.not_stop.clear()
                    continue

            if self.progress >= self.total - 1:
                self.log('finished round')
                self.stop()

            self.progress += 1
            time.sleep(EXECUTE_INTERVAL)


def has_task(index: int, task_serial: int) -> bool:
    """
        task serial value
            full task:      0b1111 1110 0000 ... ... 0000 0000
            single task:    0b0010 0000 0000 ... ... 0000 0000
            partial task:   0b0111 0000 0000 ... ... 0000 0000
    """
    serial = bin(task_serial)[2:]
    if len(serial) != max_task_num:
        serial = ''.join(['0' for _ in range(max_task_num - len(serial))]) + serial
    return serial[index] == '1'


if __name__ == '__main__':
    pass
