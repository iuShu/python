import threading
import time
import tkinter
from tkinter import Tk, ttk, PhotoImage


class KaraWindow(object):

    def __init__(self):
        self.root = None
        self.devs = []
        self.init_window()

    def init_window(self):
        root = Tk()
        root.title('Kara Assistant')
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h, xp, yadd = 352, 386, 10, 10
        x, y = sw // 2 - (sw // 3) - (w // 4), sh // 3
        root.geometry(f'{w}x{h}+{x}+{y}')
        root.resizable(width=False, height=True)

        # icon_kara = PhotoImage(file='../resources/ui/assistant.png')
        icon_start = PhotoImage(file='../resources/ui/start.png', name='start')
        icon_end = PhotoImage(file='../resources/ui/end.png', name='end')
        icon_istart = PhotoImage(file='../resources/ui/istart.png', name='istart')
        icon_ipause = PhotoImage(file='../resources/ui/ipause.png', name='ipause')
        icon_iend = PhotoImage(file='../resources/ui/iend.png', name='iend')

        btn = ttk.Button(root, text='Start', compound=tkinter.LEFT, image='start')
        btn.bind('<Button-1>', self.on_start)
        bw, bh = btn.winfo_reqwidth(), btn.winfo_reqheight()
        btn.place(x=w // 2 - (bw // 2), y=yadd)

        ny = yadd * 2 + bh
        label = ttk.Label(root, text='Emulator: ' + str(len(self.devs)))
        label.place(x=xp, y=ny)

        ny += label.winfo_reqheight()
        lb = tkinter.Listbox(root, height=5, selectmode=tkinter.BROWSE, listvariable=tkinter.StringVar())
        lb.place(x=xp, y=ny)
        lb.config(width=47, height=17)
        lb['state'] = tkinter.DISABLED

        self.root = root
        root.mainloop()

    def create_devices(self):
        master = self.root.children['!listbox']
        for i in range(6):
            widgets = toolbar(master, i)
            print('create', i)
            time.sleep(.2)

    def on_start(self, event: tkinter.Event):
        btn = event.widget
        txt, state = btn['text'], str(btn['state'])
        btn['state'] = tkinter.DISABLED

        def on_event():
            time.sleep(1)
            if txt == 'Start' and state == tkinter.NORMAL:
                btn['text'] = 'End'
                btn['image'] = 'end'
                btn['state'] = 'normal'
                # create_toolbar(btn)
                self.create_devices()
            elif txt == 'End' and state == tkinter.NORMAL:
                btn['text'] = 'Start'
                btn['image'] = 'start'
                btn['state'] = 'normal'

        run_task(on_event)


def toolbar(master, idx):
    sml = ttk.Label(master, text='simulator-' + str(idx), width=44, anchor='w', padding=4)
    desc = ttk.Label(master, text='matching READY ', width=19, anchor='e', padding=3, background='#e6e6e7')
    bstart = ttk.Button(master, compound=tkinter.CENTER, image='istart', width=2)
    bpause = ttk.Button(master, compound=tkinter.CENTER, image='ipause', width=2)
    bend = ttk.Button(master, compound=tkinter.CENTER, image='iend', width=2)
    # bstart['state'] = tkinter.DISABLED
    bpause['state'] = tkinter.DISABLED
    bend['state'] = tkinter.DISABLED
    nx, ny = 3, idx * 27 + idx * 6 + 6
    sml.place(x=nx, y=ny)
    desc.place(x=nx + 103, y=ny)
    bstart.place(x=nx + 103 + desc.winfo_reqwidth(), y=ny)
    bpause.place(x=nx + 103 + desc.winfo_reqwidth() + bstart.winfo_reqwidth(), y=ny)
    bend.place(x=nx + 103 + desc.winfo_reqwidth() + bstart.winfo_reqwidth() + bpause.winfo_reqwidth(), y=ny)
    return sml, desc, bstart, bpause, bend


def run_task(func):
    t = threading.Thread(target=func)
    t.start()


if __name__ == '__main__':
    # first()
    # second()
    kw = KaraWindow()


