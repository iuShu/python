import random
import time
from multiprocessing import Process, Array


def mock_task(idx, arr):
    time.sleep(random.randint(0, 5))
    arr[idx] = 1
    print(idx, 'sync')


def multithread():
    pass


def multipro():
    core = 4
    arr = Array('b', core)
    pl = []
    for i in range(core):
        pro = Process(target=mock_task, args=(i, arr))
        pl.append(pro)
        pro.start()

    for p in pl:
        p.join()
    print('test end', [i for i in arr])


if __name__ == '__main__':
    # multithread()
    multipro()
