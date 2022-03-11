import time
import tkinter
from tkinter import Tk, ttk, PhotoImage

from kara import game, instance
from ui import threadpool


class KaraWindow(object):

    def __init__(self):
        self.karastar = game.Karastar()
        self.root = None
        self.widgets = dict()
        self.wset = set()
        self.executor = threadpool.create(len(self.karastar.instances) + 2)
        self.init_window()

    def init_window(self):
        root = Tk()
        root.title('Karastar Assistant')
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = 352, 388
        x, y = sw // 2 - (sw // 3) - (w // 4), sh // 3
        root.geometry(f'{w}x{h}+{x}+{y}')
        root.resizable(width=False, height=True)

        # icon_kara = PhotoImage(file='../resources/ui/assistant.png', name='asst')
        icon_start = PhotoImage(file='../resources/ui/start.png', name='start')
        icon_end = PhotoImage(file='../resources/ui/end.png', name='end')
        icon_istart = PhotoImage(file='../resources/ui/istart.png', name='istart')
        icon_ipause = PhotoImage(file='../resources/ui/ipause.png', name='ipause')
        icon_iend = PhotoImage(file='../resources/ui/iend.png', name='iend')

        btn = ttk.Button(root, text='Start', compound=tkinter.LEFT, image='start')
        btn.bind('<Button-1>', self.on_control)
        bw, bh = btn.winfo_reqwidth(), btn.winfo_reqheight()
        btn.place(x=w // 2 - (bw // 2), y=10)

        ny = 20 + bh
        label = ttk.Label(root, text='Emulator: ' + str(len(self.karastar.instances)))
        label.place(x=10, y=ny)

        ny += label.winfo_reqheight()
        lb = tkinter.Listbox(root, height=5, selectmode=tkinter.BROWSE, listvariable=tkinter.StringVar())
        lb.place(x=10, y=ny)
        lb.config(width=47, height=17)
        lb['state'] = tkinter.DISABLED
        lb.bind('<Visibility>', self.create_devices)

        root.protocol('WM_DELETE_WINDOW', self.close)
        self.root = root
        root.mainloop()

    def close(self):
        self.executor.stop()
        [i.end() for i in self.karastar.instances]
        self.root.destroy()

    def create_devices(self, event: tkinter.Event):
        master = event.widget
        instances = self.karastar.instances

        def do_create():
            for i in range(len(instances)):
                widgets = toolbar(master, i, instances[i].sml.name, self.toolbar_command)
                obj = KaraWidget(self, instances[i], widgets)
                self.wset.add(obj)
                for w in widgets:
                    self.widgets[w] = obj
                print('create', i)
                time.sleep(.1)
        self.executor.exec(do_create)

    def on_control(self, event: tkinter.Event):
        btn = event.widget
        txt, state = btn['text'], str(btn['state'])
        btn['state'] = tkinter.DISABLED

        def on_event():
            if txt == 'Start' and state == tkinter.NORMAL:
                [w.start() for w in self.wset]
                btn['text'] = 'End'
                btn['image'] = 'end'
                btn['state'] = 'normal'
            elif txt == 'End' and state == tkinter.NORMAL:
                [w.end() for w in self.wset]
                btn['text'] = 'Start'
                btn['image'] = 'start'
                btn['state'] = 'normal'
        self.executor.exec(on_event)

    def toolbar_command(self, event):
        self.widgets[event.widget].on_event(event.widget)


class KaraWidget(object):

    def __init__(self, kwd: KaraWindow, inst: instance.KaraInstance, widgets: tuple):
        self.kwd = kwd
        self.wname = widgets[0]
        self.wdesc = widgets[1]
        self.wstart = widgets[2]
        self.wpause = widgets[3]
        self.wend = widgets[4]
        self.inst = inst
        self.started = False

    def on_event(self, widget: tkinter.Widget):
        if widget['state'] == tkinter.DISABLED:
            return

        if widget.winfo_name() == self.wstart.winfo_name():
            self.start()
        elif widget.winfo_name() == self.wpause.winfo_name():
            self.pause()
        elif widget.winfo_name() == self.wend.winfo_name():
            self.end()

    def start(self):
        if self.started:
            ki, idx = instance.KaraInstance(self.inst.sml), 0
            instances = self.kwd.karastar.instances
            for i in range(len(instances)):
                if instances[i] is self.inst:
                    idx = i
                    break
            self.kwd.karastar.instances[idx] = ki
            self.inst = ki

        if self.inst.is_alive():
            self.inst.resume()
        else:
            self.inst.desc_widget = self.wdesc
            self.inst.start()
            self.started = True

        self.wstart['state'] = tkinter.DISABLED
        self.wpause['state'] = tkinter.NORMAL
        self.wend['state'] = tkinter.NORMAL

    def pause(self):
        self.inst.pause()
        self.wstart['state'] = tkinter.NORMAL
        self.wpause['state'] = tkinter.DISABLED
        self.wend['state'] = tkinter.NORMAL

    def end(self):
        self.inst.end()
        self.wstart['state'] = tkinter.NORMAL
        self.wpause['state'] = tkinter.DISABLED
        self.wend['state'] = tkinter.DISABLED


def toolbar(master, idx, name, command):
    name = ttk.Label(master, text=name, width=44, anchor='w', padding=4)
    desc = ttk.Label(master, text='ready', width=19, anchor='e', padding=3, background='#e6e6e7')
    bstart = ttk.Button(master, compound=tkinter.CENTER, image='istart', width=2)
    bpause = ttk.Button(master, compound=tkinter.CENTER, image='ipause', width=2)
    bend = ttk.Button(master, compound=tkinter.CENTER, image='iend', width=2)
    # bstart['state'] = tkinter.DISABLED
    bpause['state'] = tkinter.DISABLED
    bend['state'] = tkinter.DISABLED
    bstart.bind('<Button-1>', command)
    bpause.bind('<Button-1>', command)
    bend.bind('<Button-1>', command)
    nx, ny = 3, idx * 27 + idx * 6 + 6
    name.place(x=nx, y=ny)
    desc.place(x=nx + 103, y=ny)
    bstart.place(x=nx + 103 + desc.winfo_reqwidth(), y=ny)
    bpause.place(x=nx + 103 + desc.winfo_reqwidth() + bstart.winfo_reqwidth(), y=ny)
    bend.place(x=nx + 103 + desc.winfo_reqwidth() + bstart.winfo_reqwidth() + bpause.winfo_reqwidth(), y=ny)
    return name, desc, bstart, bpause, bend


if __name__ == '__main__':
    # first()
    # second()
    kw = KaraWindow()


