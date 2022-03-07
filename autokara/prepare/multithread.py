import threading


STOP = -1
INIT = 1
START = 2
RUNNING = 3
PAUSE = 4


class Mmg(object):

    def __init__(self):
        self.repo = []
        self.state = INIT

    def create(self):
        sml = Sml()
        self.repo.append(sml)
        return sml

    def start(self):
        if self.state >= START:
            return

        for e in self.repo:
            e.start()

    def pause(self):
        if self.state != RUNNING:
            return
        pass


class Sml(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self) -> None:
        pass
