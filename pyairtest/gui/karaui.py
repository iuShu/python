import os
import tkinter as tk
from tkinter.messagebox import askyesno
from tkinter import ttk, Tk, PhotoImage

import cv2 as cv
import textocr
from constants import *
from gui.multicombox import Combopicker
from script.config import conf
from script.tasklist import tasks
from script import manager
from utils import message, show, try_do

# from kara.logger import LOG_DIR


class KaraUi(object):

    def __init__(self):
        self.root = None
        self.table = None

        self.simulators = []
        self._indicator = None
        self._not_pause = None
        self._not_stop = None

        self.tasks = tasks()
        self.flow_confirm = True
        self.init_panel()
        self.child = None
        self.capture_wnd = None

    def init_panel(self):
        root = Tk()
        root.title('Kara Assistant')
        root.geometry('420x340+800+200')
        root.resizable(width=False, height=False)
        root.iconphoto(True, PhotoImage(file=ico_kara))

        icon_start = PhotoImage(file=ico_start, name='start')
        icon_end = PhotoImage(file=ico_end, name='end')
        icon_istart = PhotoImage(file=ico_istart, name='istart')
        icon_ipause = PhotoImage(file=ico_ipause, name='ipause')
        icon_iend = PhotoImage(file=ico_iend, name='iend')

        menu = tk.Menu(root)
        m_option = tk.Menu(menu, tearoff=0)
        m_config = tk.Menu(m_option, tearoff=0)
        m_help = tk.Menu(menu, tearoff=0)
        m_option.add_command(label='init', command=self.m_init)
        m_option.add_command(label='capture', command=self.m_capture)
        m_option.add_cascade(label='config', menu=m_config)
        m_option.add_command(label='log dir', command=self.m_logger)
        m_option.add_command(label='elv dir', command=self.m_elv)
        bv = tk.BooleanVar(value=True)
        m_option.add_checkbutton(label='task confirm', variable=bv, command=lambda: self.m_match_confirm(bv))
        m_config.add_command(label='kara', command=lambda: self.m_config('kara'))
        m_config.add_command(label='account', command=lambda: self.m_config('account'))
        m_option.add_separator()
        m_option.add_command(label='exit', command=self.win_exit)
        m_help.add_command(label='usage', command=self.usage)
        m_help.add_command(label='about', command=self.about)
        menu.add_cascade(label='Option', menu=m_option)
        menu.add_cascade(label='Help', menu=m_help)
        root.config(menu=menu)

        padx = 10
        frame = ttk.Frame(root, padding=10)
        frame.place(x=0, y=0)

        btn = ttk.Button(frame, text='start', compound=tk.LEFT, image='start', width=8)
        btn['state'] = tk.DISABLED
        btn.bind('<Button-1>', self.start_end)
        btn.pack(side=tk.LEFT)

        btn = ttk.Button(frame, text='pause', compound=tk.LEFT, image='ipause', width=8)
        btn['state'] = tk.DISABLED
        btn.bind('<Button-1>', self.pause_resume)
        btn.pack(side=tk.LEFT, padx=5)

        print(self.tasks.keys())
        picker = Combopicker(frame, values=self.tasks.keys())
        picker.select_all()
        picker.pack(side=tk.LEFT, padx=0)

        sep = ttk.Separator(root, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=10, pady=45)

        label_acc = ttk.Label(root, text='next acc | none')
        label_acc.place(x=padx, y=58)
        btn_list = ttk.Button(root, text='show all')
        btn_list.bind('<Button-1>', self.show_all_account)
        btn_list.place(x=325, y=55)

        tree = ttk.Treeview(root, show='headings')
        tree["columns"] = ("name", "progress", "account", "state")
        tree.column("name", width=70, anchor=tk.W)
        tree.column("progress", width=200, anchor=tk.CENTER)
        tree.column("account", width=80, anchor=tk.W)
        tree.column("state", width=50, anchor=tk.CENTER)
        tree.heading("name", text='name')
        tree.heading("progress", text="progress")
        tree.heading("account", text="acc")
        tree.heading("state", text="state")
        tree.place(x=padx, y=100)

        root.protocol('WM_DELETE_WINDOW', self.win_exit)
        self.root = root
        self.table = tree
        root.mainloop()

    def win_exit(self):
        # [s.cleanup() for s in self.simulators]
        # manager.cleanup()
        try_do(lambda: self.capture_wnd.destroy())
        self.root.destroy()

    def m_init(self):
        if self.simulators:
            message('already initialized')
            return

        # for i in self.table.get_children():
        #     self.table.delete(i)
        try:
            self.switch_local_adb()
            simulators, i, np, ns = manager.initialize()
        except RuntimeError as re:
            message(re.__str__())
            return

        serial = self.current_task_serial()
        for simulator in simulators:
            self._indicator[simulator.idx] = serial     # assign task serial
            rid = self.table.insert('', tk.END, values=[simulator.name, 'ready', '', 'init'])
            # simulator.add_tasks(func)
            # inst.bind_ui(rid, self.root)

        self._indicator = i
        self._not_stop = ns
        self._not_pause = np
        self.simulators = simulators

        btn_start_end = self.root.children['!frame'].children['!button']
        btn_start_end['state'] = tk.NORMAL

    def m_capture(self):
        if not self.simulators:
            self.m_init()
        if not self.simulators:
            return

        first = self.simulators[0]
        show(first.snapshot())

    @staticmethod
    def m_logger():
        # path = os.path.abspath(LOG_DIR)
        # if not os.path.exists(path):
        #     os.makedirs(path)
        # os.startfile(path)
        pass

    @staticmethod
    def m_elv():
        # path = os.path.abspath(ELV_PATH)
        # if not os.path.exists(path):
        #     os.makedirs(path)
        # os.startfile(path)
        pass

    def m_match_confirm(self, bv: tk.BooleanVar):
        self.flow_confirm = bv.get()

    def m_config(self, file: str):
        child_wnd = tk.Toplevel(self.root)
        child_wnd.title('kara.properties')
        x, y = self.root.winfo_x(), self.root.winfo_y()
        child_wnd.geometry(f'412x436+{x + 50}+{y + 30}')
        child_wnd.resizable(width=False, height=False)

        tips = ttk.Label(child_wnd, text='Double click to modify')
        tips.place(x=10, y=10)

        tree = ttk.Treeview(child_wnd, show='headings', height=15)
        tree["columns"] = ("key", "value")
        tree.column("key", width=170, anchor=tk.W)
        tree.column("value", width=220, anchor=tk.CENTER)
        tree.heading("key", text='key')
        tree.heading("value", text="value")
        tree.bind('<Double-1>', lambda e: self.config_modify(e, tree, key_input, val_input))
        tree.place(x=10, y=35)

        props = conf.getall(file)
        for k in props:
            v = props[k] if not isinstance(props[k], list) else ','.join(props[k])
            tree.insert('', tk.END, values=[k, v])

        key_input = ttk.Entry(child_wnd, width=24, textvariable=tk.StringVar(child_wnd, value='abc'))
        val_input = ttk.Entry(child_wnd, width=29)
        btn_save = ttk.Button(child_wnd, text='save', width=8)
        btn_delete = ttk.Button(child_wnd, text='delete', width=8)
        btn_cancel = ttk.Button(child_wnd, text='cancel', width=8)
        btn_save.bind('<Button-1>', lambda e: self.config_control(2, child_wnd, file, key_input, val_input))
        btn_delete.bind('<Button-1>', lambda e: self.config_control(1, child_wnd, file, key_input, val_input))
        btn_cancel.bind('<Button-1>', lambda e: self.config_control(0, child_wnd, file, key_input, val_input))
        key_input.place(x=10, y=370)
        val_input.place(x=193, y=370)
        btn_save.place(x=194, y=400)
        btn_delete.place(x=265, y=400)
        btn_cancel.place(x=336, y=400)

    def usage(self):
        child_wnd = tk.Toplevel(self.root)
        child_wnd.title('Usage of Karastar Assistant')
        x, y = self.root.winfo_x(), self.root.winfo_y()
        child_wnd.geometry(f'410x320+{x + 50}+{y + 30}')
        child_wnd.resizable(width=False, height=False)

        ttk.Label(child_wnd, text='首次配置').place(x=10, y=10)
        ttk.Label(child_wnd, text='1. 设置模拟器分辨率为 960 x 540').place(x=20, y=35)
        ttk.Label(child_wnd, text='2. 收起模拟器右侧工具栏').place(x=20, y=60)
        ttk.Label(child_wnd, text='3. 安装 Karastar 打开允许相关设备权限').place(x=20, y=85)
        ttk.Label(child_wnd, text='4. 使用多开工具复制此模拟器').place(x=20, y=110)
        ttk.Label(child_wnd, text='5. Option/config/kara 配置模拟器安装路径 simulator.path').place(x=20, y=135)
        ttk.Label(child_wnd, text='6. Option/config/kara 配置识别工具安装路径 tesseract.path').place(x=20, y=160)
        ttk.Label(child_wnd, text='7. Option/config/account 配置账号').place(x=20, y=185)
        ttk.Label(child_wnd, text='正式使用').place(x=10, y=210)
        ttk.Label(child_wnd, text='1. Option/init 初始化并排列模拟器').place(x=20, y=235)
        ttk.Label(child_wnd, text='2. Option/capture 测试截图功能').place(x=20, y=260)
        ttk.Label(child_wnd, text='3. Start 启动辅助').place(x=20, y=285)

    def about(self):
        message('To be continued ...')

    def show_all_account(self, event):
        props = conf.getall('account')
        child_wnd = tk.Toplevel(self.root)
        child_wnd.title('Karastar Account List')
        h, x, y = 30, self.root.winfo_x(), self.root.winfo_y()
        h += (len(props.keys()) * 25 + 6)
        child_wnd.geometry(f'390x{h}+{x + 50}+{y + 30}')
        child_wnd.resizable(width=False, height=False)

        x, y, yadd = 10, 10, 25
        for i in range(len(props.keys())):
            acc = props.get(f'kara.account.{i+1}').split('  ')
            ttk.Label(child_wnd, text=f'{i+1}    {acc[0]}  {acc[1]}').place(x=x, y=y)
            y += yadd

    def start_end(self, event: tk.Event):
        btn = event.widget
        state = str(btn['state'])
        if state != tk.NORMAL:
            return

        btn['state'] = tk.DISABLED
        btn_pause_end = self.root.children['!frame'].children['!button2']
        if btn['text'] == 'start':
            self.start_process()
            btn['image'] = 'end'
            btn['text'] = 'end'
            btn_pause_end['state'] = tk.NORMAL
        else:
            self.stop_process()
            btn['image'] = 'start'
            btn['text'] = 'start'
            btn_pause_end['image'] = 'ipause'
            btn_pause_end['text'] = 'pause'
            btn_pause_end['state'] = tk.DISABLED
        btn['state'] = tk.NORMAL

    def pause_resume(self, event: tk.Event):
        btn = event.widget
        state = str(btn['state'])
        if state != tk.NORMAL:
            return

        btn['state'] = tk.DISABLED
        if btn['text'] == 'pause':
            self.resume_process()
            btn['image'] = 'start'
            btn['text'] = 'resume'
        else:
            self.pause_process()
            btn['image'] = 'ipause'
            btn['text'] = 'pause'
        btn['state'] = tk.NORMAL

    def config_modify(self, event: tk.Event, table: ttk.Treeview, ki: ttk.Entry, vi: ttk.Entry):
        rid = event.widget.selection()[0]
        row = table.item(rid)
        key, val = row['values'][0], row['values'][1]
        ki.delete(0, tk.END)
        vi.delete(0, tk.END)
        ki.insert(0, key)
        vi.insert(0, val)

        master, buttons = event.widget.master, []
        for k in master.children.keys():
            if 'button' in k:
                buttons.append(k)

        prev_mode, mode = 'normal', 'normal'
        if len(buttons) == 4:
            prev_mode = 'tesseract'
        elif len(buttons) == 5:
            prev_mode = 'position'
        if 'pos' in key and ',' in val:
            mode = 'position'
        elif 'tesseract' in key:
            mode = 'tesseract'

        if prev_mode != mode:
            [master.children[buttons[i]].destroy() for i in range(3, len(buttons))]

        if mode == 'position':
            btn_click = ttk.Button(master, text='click', width=8)
            btn_click.bind('<Button-1>', lambda e: self.click_test(vi))
            btn_click.place(x=10, y=400)
            btn_capture = ttk.Button(master, text='capture', width=8)
            btn_capture.bind('<Button-1>', lambda e: self.capture_pos(e, vi))
            btn_capture.place(x=80, y=400)
        elif mode == 'tesseract':
            btn_click = ttk.Button(master, text='test', width=8)
            btn_click.bind('<Button-1>', self.tesseract_test)
            btn_click.place(x=10, y=400)

    def config_control(self, tag: int, wnd: tk.Toplevel, file: str, ki: ttk.Entry, vi: ttk.Entry):
        if tag == 0:
            ki.delete(0, tk.END)
            vi.delete(0, tk.END)
            return

        delete = tag == 1
        key, val = ki.get(), vi.get()
        if not key or (not delete and not val):
            return

        if file == 'account' and '  ' not in val:
            val = val.replace(' ', '  ')

        if delete and not askyesno('Confirm delete account', 'Are you sure to delete this account ?'):
            return

        if conf.update(file, key, val, delete):
            wnd.destroy()
            self.m_config(file)
            message(key + ' updated successful')
        else:
            message(ki.get() + ' update fail, occurred unknown error')

    def click_test(self, vi: ttk.Entry):
        val = vi.get()
        if not val:
            return

        pos = tuple(map(int, val.split(',')))
        if not self.simulators:
            self.m_init()
        if self.simulators:
            self.simulators[0].click(pos)

    @staticmethod
    def tesseract_test(event: tk.Event):
        res = ''
        try:
            res = textocr.recognize(cv.imread(tesseract_sample))
            if res == '05:59:55':
                message('tesseract ok')
        except Exception:
            message('error occurred during tesseract testing', res)

    def capture_pos(self, event: tk.Event, vi: ttk.Entry):
        val = vi.get()
        if not val:
            return

        pos = tuple(map(int, val.split(',')))
        if not self.simulators:
            self.m_init()
        if not self.simulators:
            return

        master = event.widget.master
        child_wnd = tk.Toplevel(master)
        child_wnd.title('Screenshot')
        x, y = self.root.winfo_x(), self.root.winfo_y()
        child_wnd.geometry(f'984x600+{x - 300}+{y - 100}')
        child_wnd.resizable(width=False, height=False)

        cap = self.simulators[0].snapshot()
        cv.circle(cap, pos, 3, (0, 255, 255), thickness=-1)
        cv.imwrite(capture_file, cap)
        capture = PhotoImage(master=child_wnd, file=capture_file, name='capture')

        tips = ttk.Label(child_wnd, text='Click the following photo to collect the mouse position')
        pl = ttk.Label(child_wnd, text=' x, y | ')
        pos = ttk.Label(child_wnd, text=f'{pos[0]}, {pos[1]}')
        btn = ttk.Button(child_wnd, text='copy')
        btn.bind('<Button-1>', lambda e: self.copy_pos(e, pos))
        tips.place(x=10, y=12)
        pl.place(x=782, y=10)
        pos.place(x=820, y=11)
        btn.place(x=885, y=7)

        cap = ttk.Label(child_wnd, image=capture, compound=tk.CENTER)
        cap.bind('<Button-1>', lambda e: self.cursor_pos(e, pos))
        cap.place(x=10, y=44)

        child_wnd.mainloop()

    @staticmethod
    def cursor_pos(event: tk.Event, label: ttk.Label):
        label['text'] = f'{event.x}, {event.y}'

    def copy_pos(self, event: tk.Event, label: ttk.Label):
        pos = label['text'].replace(' ', '')
        self.root.clipboard_clear()
        self.root.clipboard_append(string=pos)
        message('copy position successful')

    def current_task_serial(self) -> int:
        picker = self.root.children['!frame'].children['!combopicker']
        serial = []
        task_names = list(self.tasks.keys())
        if not picker.current_value:    # default
            [serial.append('1') for _ in range(len(self.tasks))]
            [serial.append('0') for _ in range(max_task_num - len(self.tasks))]
        else:   # custom task serial
            selected = picker.current_value.split(',')
            for each in task_names:
                serial.append('1' if each in selected else '0')
        return int('0b' + ''.join(serial), base=2)

    @staticmethod
    def switch_local_adb():
        if not os.path.exists(airadb_dir):
            return

        from airtest.core.android.constant import DEFAULT_ADB_PATH
        simulator_path = conf.get('kara', 'simulator.path')
        DEFAULT_ADB_PATH['Windows'] = os.path.normpath(simulator_path + 'airadb/adb.exe')
        message('switch adb to ' + DEFAULT_ADB_PATH['Windows'])

    def start_process(self):
        # num = len(self.simulators)
        # status = [sml.is_alive() for sml in self.simulators]
        # if status.count(False) == num:
        #     [sml.start() for sml in self.simulators]
        # elif status.count(True) != num:
        #     self.abnormal_state()
        def not_alive_func():
            [sml.start() for sml in self.simulators]

        def alive_func():
            message('process already start')

        self.operate_process(not_alive_func, alive_func)

    def resume_process(self):
        # num = len(self.simulators)
        # status = [sml.is_alive() for sml in self.simulators]
        # if status.count(False) == num:
        #     message('please start process first')
        # elif status.count(True) == num:
        #     if not self._not_pause.is_set():
        #         self._not_pause.set()
        # else:
        #     self.abnormal_state()
        def not_alive_func():
            message('please start process first')

        def alive_func():
            if not self._not_pause.is_set():
                self._not_pause.set()

        self.operate_process(not_alive_func, alive_func)

    def stop_process(self):
        # num = len(self.simulators)
        # status = [sml.is_alive() for sml in self.simulators]
        # if status.count(False) == num:
        #     message('please start process first')
        # elif status.count(True) == num:
        #     if self._not_stop.is_set():
        #         self._not_stop.clear()
        # else:
        #     self.abnormal_state()
        def not_alive_func():
            message('please start process first')

        def alive_func():
            if self._not_stop.is_set():
                self._not_stop.clear()

        self.operate_process(not_alive_func, alive_func)

    def pause_process(self):
        # num = len(self.simulators)
        # status = [sml.is_alive() for sml in self.simulators]
        # if status.count(False) == num:
        #     message('please start process first')
        # elif status.count(True) == num:
        #     if self._not_pause.is_set():
        #         self._not_pause.clear()
        # else:
        #     self.abnormal_state()
        def not_alive_func():
            message('please start process first')

        def alive_func():
            if self._not_pause.is_set():
                self._not_pause.clear()

        self.operate_process(not_alive_func, alive_func)

    def operate_process(self, not_alive_func, alive_func):
        num = len(self.simulators)
        status = [sml.is_alive() for sml in self.simulators]
        if status.count(False) == num:
            not_alive_func()
        elif status.count(True) == num:
            alive_func()
        else:
            self.abnormal_state()

    @staticmethod
    def abnormal_state():
        err = 'abnormal process state, please restart the program'
        message(err)
        raise RuntimeError(err)


if __name__ == '__main__':
    kui = KaraUi()
