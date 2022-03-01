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

