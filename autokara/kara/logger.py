import os.path
import queue
import threading
import time

from kara.utils import localtime

LOG_DIR = '../logs/'


class KaraLogger(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = queue.Queue()
        self.file = f'{LOG_DIR}{int(time.time())}.log'
        self.init_dir()

    @staticmethod
    def init_dir():
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

    def log(self, txt: str):
        thn = threading.currentThread().name
        self.queue.put(LogMessage(thn, txt))

    def run(self) -> None:
        while True:
            msg = self.queue.get()
            if msg:
                with open(self.file, 'a') as f:
                    f.writelines((msg.serial()))


class LogMessage(object):

    def __init__(self, desc: str, txt: str):
        self.localtime = localtime()
        self.desc = desc
        self.txt = txt

    def serial(self) -> str:
        return f'{self.localtime} [{self.desc}] {self.txt}\n'


if __name__ == '__main__':
    print(localtime())

