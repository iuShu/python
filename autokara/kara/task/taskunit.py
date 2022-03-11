
class TaskUnit(object):

    def __init__(self, func, inst):
        self.func = func
        self.inst = inst

    def exec(self):
        self.func(self.inst)


def create(func, inst):
    return TaskUnit(func, inst)


