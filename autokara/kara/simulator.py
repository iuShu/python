import win32api
import win32con
import win32gui
from PIL import ImageGrab


class Simulator(object):

    def __init__(self, name):
        self.name = name
        self.handle = win32gui.FindWindow(0, self.name)

    def capture(self):
        win32gui.SetForegroundWindow(self.handle)
        x, y, w, h = win32gui.GetWindowRect(self.handle)
        return ImageGrab.grab((x, y, w, h))

    def click(self, p):
        pass


def test():
    """
    see https://zhuanlan.zhihu.com/p/309664632
    """
    hwnd = win32gui.FindWindow(0, '雷电模拟器')
    child = win32gui.GetWindow(hwnd, win32con.GW_CHILD)
    # handle = win32gui.WindowFromPoint((100, 100))
    # print(hwnd, child, handle)
    raw = (130, 150)
    pos = win32gui.ScreenToClient(child, raw)
    wp = win32api.MAKELONG(pos[0], pos[1])
    # win32gui.SendMessage(child, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    win32gui.SendMessage(child, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, wp)
    win32gui.SendMessage(child, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, wp)


if __name__ == '__main__':
    test()
