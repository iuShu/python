from airtest.core.api import init_device
from multiprocessing import Process


class Simulator(Process):

    def __init__(self, idx, name, handle, hwnd, serialno):
        super().__init__(daemon=True)
        self.id = idx
        self.name = name
        self.handle = handle
        self.hwnd = hwnd
        self.dev = init_device(uuid=serialno)
        self.serialno = serialno
        self.preheating()

    def preheating(self):
        self.dev.snapshot()

    def snapshot(self):
        return self.dev.snapshot()

    def click(self, pos):
        self.dev.touch(pos)

    def run(self) -> None:
        pass

    def cleanup(self):
        self.dev.adb.kill_server()


if __name__ == '__main__':
    pass

