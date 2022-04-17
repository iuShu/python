from multiprocessing import Manager, Barrier
import win32gui
import win32con
from airtest.core.android.adb import ADB
from script.config import conf
from script.simulator import Simulator
from utils import execmd, error

manager_adb = None


def initialize() -> tuple:
    ld_cmd = conf.get('kara', 'simulator.path') + 'ldconsole list2'
    ret = execmd(ld_cmd)
    if not ret:
        error('execute ldconsole command error')

    lines = [e for e in filter(lambda x: len(x) > 1 and x.split(',')[4] == '1', ret.split('\n'))]
    if not lines:
        error('no available simulator')

    global manager_adb
    manager_adb = ADB() if not manager_adb else manager_adb
    devs = manager_adb.devices(state="device")
    num = len(devs)
    if len(devs) != len(lines):
        error('simulator devices info mismatched')

    try:
        simulators = []
        mng = Manager()
        indicator = mng.Array('i', [0] * num)
        not_pause = mng.Event()
        not_stop = mng.Event()
        not_pause.set()
        _sync_action = Barrier(parties=num)
        _sync_data = mng.Array('i', [0] * (num + 1))
        _acc_queue = _accounts(mng)
        log_queue = mng.Queue()
        args = [-1, '', -1, -1, '', indicator, not_pause, not_stop, _sync_action, _sync_data, _acc_queue, log_queue]
        for i in range(len(devs)):
            info = lines[i].split(',')
            args[0] = i
            args[1:4] = info[1:4]
            args[4] = devs[i][0]
            simulator = Simulator(*args)
            simulator.start()
            simulators.append(simulator)
        _layout(simulators)
        return simulators, indicator, not_pause, not_stop, log_queue
    except RuntimeError:
        error('initialize simulator error')


def _layout(simulators: list):
    # sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    # sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    rnum = conf.getint('kara', 'instance.row.num')
    cnum = conf.getint('kara', 'instance.col.num')
    dw = conf.getint('kara', 'simulator.default.width')
    dh = conf.getint('kara', 'simulator.default.height')
    idx, fx, fy, total = 0, 0, 0, len(simulators)
    for r in range(rnum):
        for c in range(cnum):
            if idx >= total:
                break

            handle = simulators[idx].handle
            win32gui.SetWindowPos(handle, win32con.HWND_DESKTOP, fx, fy, dw, dh, win32con.SWP_SHOWWINDOW)
            win32gui.SendMessage(handle, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
            fx += dw
            idx += 1
        fy += dh
        fx = 0


def _accounts(mng):
    idx = 1
    queue = mng.Queue()
    while True:
        account = conf.get('account', f'kara.account.{idx}')
        if not account:
            return queue
        arr = account.replace('  ', ' ').split(' ')
        queue.put(arr)
        idx += 1


if __name__ == '__main__':
    initialize()
    pass
