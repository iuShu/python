import queue
import threading

from kara import account
from kara.karaexception import KaraException
from kara.simulator import Simulator
from kara.task.tasklist import tasklist
from kara.synchronizer import Synchronizer
from kara.utils import cooldown, message


class KaraInstance(threading.Thread):

    def __init__(self, sml: Simulator, sync: Synchronizer):
        threading.Thread.__init__(self, name='inst-' + sml.name)
        self.sml = sml
        self.acm = account.instance()
        self.tasks = queue.Queue()
        self.task = None
        self.sync = sync
        self.power = 0
        self.acc = None
        self.arena_scene = ''
        self.f_pause = False
        self.f_end = False
        self.ui_rid = None
        self.ui_root = None

    def run(self):
        self.ui_change('state', 'run')
        th_name = threading.currentThread().name
        tasklist(self)
        try:
            while not self.f_end:
                if not self.f_pause:
                    self.task = self.tasks.get(block=True, timeout=2)
                    if self.task:
                        self.task.exec()
                else:
                    cooldown('instance.pause')
        except KaraException or RuntimeError as ke:
            self.desc(ke.__str__())
            # message(f'{th_name} exited with error: {ke.msg}')
        except Exception as e:
            self.desc(e.__str__())
            message(f'{th_name} exited with error: {e.__str__()}')
        self.finish()

    def bind_ui(self, rid, root):
        self.ui_rid = rid
        self.ui_root = root
        self.ui_root.children['!label']['text'] = 'next acc | ' + self.acm.next

    def ui_change(self, col: str, val):
        table = self.ui_root.children['!treeview']
        table.set(self.ui_rid, col, val)

    def desc(self, txt: str):
        if txt:
            self.ui_change('progress', txt)

    def resume(self):
        self.f_pause = False

    def pause(self):
        self.f_pause = True

    def end(self):
        self.sml.stop()
        self.f_end = True

    def finish(self):
        print(threading.currentThread().name, 'finished')
        self.ui_change('state', 'end')
        table = self.ui_root.children['!treeview']
        for i in table.get_children():
            if table.item(i)['values'][3] != 'end':
                return
        btn = self.ui_root.children['!button']
        btn['image'] = 'start'
        btn['text'] = 'start'
        btn['state'] = 'normal'

    def obtain_account(self):
        self.acc = self.acm.obtain()

        desc = 'x' if not self.acc else self.acc[0]
        self.ui_change('account', desc)
        self.ui_root.children['!label']['text'] = 'next acc | ' + self.acm.next

        return self.acc

    def check_power(self):
        return self.power > 0


if __name__ == '__main__':
    pass
