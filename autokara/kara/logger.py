import os.path
import queue
import random
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
        batch = []
        while True:
            msg = self.get_nowait()
            if msg:
                batch.append(msg.serial())

                for _ in range(39):
                    msg = self.get_nowait()
                    if not msg:
                        break
                    batch.append(msg.serial())

                with open(self.file, 'a') as f:
                    f.writelines(batch)
                batch.clear()

            time.sleep(1)

    def get_nowait(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None


class LogMessage(object):

    def __init__(self, desc: str, txt: str):
        self.localtime = localtime()
        self.desc = desc
        self.txt = txt

    def serial(self) -> str:
        return f'{self.localtime} [{self.desc}] {self.txt}\n'


def performance():
    logger = KaraLogger()
    logger.start()

    def generate(lg: KaraLogger):
        for i in range(4):
            for _ in range(30):
                lg.log(str(random.randint(0, 100000)))
                time.sleep(.05)
            time.sleep(3)
        print(threading.currentThread().name, 'end')
        pass

    for _ in range(4):
        threading.Thread(target=generate, args=[logger]).start()


if __name__ == '__main__':
    performance()

