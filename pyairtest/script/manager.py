import win32gui
import win32con
from airtest.core.android import Android
from airtest.core.android.adb import ADB
from script.config import conf
from script.simulator import Simulator
from utils import execmd, error

manager_adb = ADB()


def initialize() -> list:
    ld_cmd = conf.get('kara', 'simulator.path') + 'ldconsole list2'
    ret = execmd(ld_cmd)
    if not ret:
        raise RuntimeError('execute ldconsole command error')

    lines = [e for e in filter(lambda x: len(x) > 1 and x.split(',')[4] == '1', ret.split('\n'))]
    devs = manager_adb.devices(state="device")
    if len(devs) != len(lines):
        error('simulator devices info mismatched')

    try:
        simulators = []
        for i in range(len(devs)):
            info = lines[i].split(',')
            simulator = Simulator(*info[:4], devs[i][0])
            simulators.append(simulator)
        _layout(simulators)
        return simulators
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

    ww = conf.getint('kara', 'window.width')
    wh = conf.getint('kara', 'window.height')
    for simulator in simulators:
        dev: Android = simulator.dev
        resolution = dev.get_current_resolution()
        if ww != resolution[0] or wh != resolution[1]:
            error('please confirm collapse the rightside toolbar and change resolution to 960 x 540')


def cleanup():
    manager_adb.kill_server()


if __name__ == '__main__':

    pass
