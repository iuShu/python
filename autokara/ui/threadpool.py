import queue
import threading
import time


class ThreadPool(threading.Thread):

    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num
        self.pool = []
        self.tasks = queue.Queue()
        self.init_pool()
        self.stop = False

    def init_pool(self):
        for i in range(self.num):
            pt = PoolThread(self, f'tpool-{i}')
            pt.setDaemon(daemonic=True)
            pt.start()
            self.pool.append(pt)

    def stop(self):
        self.stop = True

    def exec(self, task) -> None:
        self.tasks.put(task)

    def run(self) -> None:
        while not self.stop:
            time.sleep(5)


class PoolThread(threading.Thread):

    def __init__(self, pool: ThreadPool, name: str):
        threading.Thread.__init__(self, name=name)
        self.pool = pool

    def run(self):
        while True:
            task = self.pool.tasks.get(block=True)
            if task:
                task()


def create(num: int) -> ThreadPool:
    pool = ThreadPool(num)
    pool.start()
    return pool


if __name__ == '__main__':
    pass



