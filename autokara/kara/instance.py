import queue
import threading

from kara import account
from kara.karaexception import KaraException
from kara.simulator import Simulator
from kara.task.tasklist import tasklist
from kara.utils import cooldown, message


class KaraInstance(threading.Thread):

    def __init__(self, sml: Simulator):
        threading.Thread.__init__(self, name='inst-' + sml.name)
        self.sml = sml
        self.acm = account.instance()
        self.tasks = queue.Queue()
        self.task = None
        self.power = 0
        self.acc = None
        self.f_pause = False
        self.f_end = False
        self.desc_widget = None

    def run(self):
        th_name = threading.currentThread().name
        tasklist(self)
        try:
            while not self.f_end:
                if not self.f_pause:
                    self.task = self.tasks.get(block=True)
                    if self.task:
                        self.task.exec()
                else:
                    cooldown('instance.pause')
        except KaraException as ke:
            message(f'{th_name} exited with error: {ke.msg}')
        except Exception as e:
            message(f'{th_name} exited with error: {e.__str__()}')
        print(th_name, 'finished')

    def desc(self, txt: str):
        if txt:
            self.desc_widget['text'] = self.sml.name + txt

    def resume(self):
        self.f_pause = False

    def pause(self):
        self.f_pause = True

    def end(self):
        self.sml.stop()
        self.f_end = True

    def obtain_account(self):
        self.acc = self.acm.obtain()
        return self.acc

    def check_power(self):
        return self.power > 0


if __name__ == '__main__':
    pass
