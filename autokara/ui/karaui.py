import tkinter as tk
from tkinter import ttk, Tk, PhotoImage

from kara.game import Karastar
from kara.utils import message


class KaraUi(object):

    def __init__(self):
        self.root = None
        self.table = None
        self.karastar = None
        self.init_panel()
        self.child = None

    def init_panel(self):
        root = Tk()
        root.title('Kara Assistant')
        root.geometry('420x340+800+200')
        root.resizable(width=False, height=False)

        icon_start = PhotoImage(file='../resources/ui/start.png', name='start')
        icon_end = PhotoImage(file='../resources/ui/end.png', name='end')
        icon_istart = PhotoImage(file='../resources/ui/istart.png', name='istart')
        icon_ipause = PhotoImage(file='../resources/ui/ipause.png', name='ipause')
        icon_iend = PhotoImage(file='../resources/ui/iend.png', name='iend')

        menu = tk.Menu(root)
        m_option = tk.Menu(menu, tearoff=0)
        m_help = tk.Menu(menu, tearoff=0)
        m_option.add_command(label='init', command=self.m_init)
        m_option.add_separator()
        m_option.add_command(label='exit', command=self.win_exit)
        m_help.add_command(label='usage', command=self.usage)
        m_help.add_command(label='about', command=self.about)
        menu.add_cascade(label='Option', menu=m_option)
        menu.add_cascade(label='Help', menu=m_help)
        root.config(menu=menu)

        padx = 10
        btn = ttk.Button(root, text='start', compound=tk.LEFT, image='start')
        btn['state'] = tk.DISABLED
        btn.bind('<Button-1>', self.on_click)
        btn.place(x=padx, y=10)

        sep = ttk.Separator(root, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=10, pady=45)

        label_acc = ttk.Label(root, text='next acc | none')
        label_acc.place(x=padx, y=58)
        btn_list = ttk.Button(root, text='show all')
        btn_list.place(x=326, y=55)

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
        print('close')
        if self.karastar:
            [i.end() for i in self.karastar.instances]
        self.root.destroy()

    def m_init(self):
        for i in self.table.get_children():
            self.table.delete(i)

        ks = self.create_karastar()
        if not ks:
            return

        self.karastar = ks
        instances = ks.instances
        for i in range(len(instances)):
            inst = instances[i]
            rid = self.table.insert('', tk.END, values=[inst.sml.name, 'ready', '', 'init'])
            inst.bind_ui(rid, self.root)
        self.root.children['!button']['state'] = tk.NORMAL

    @staticmethod
    def create_karastar() -> Karastar:
        try:
            return Karastar()
        except Exception as e:
            message(e.__str__())

    def usage(self):
        child_wnd = tk.Toplevel(self.root)
        child_wnd.title('Usage of Karastar Assistant')
        x, y = self.root.winfo_x(), self.root.winfo_y()
        child_wnd.geometry(f'390x300+{x + 50}+{y + 50}')

        ttk.Label(child_wnd, text='首次使用').place(x=10, y=10)
        ttk.Label(child_wnd, text='1. 设置模拟器分辨率为 960 x 540').place(x=20, y=35)
        ttk.Label(child_wnd, text='2. 收起模拟器右侧工具栏').place(x=20, y=60)
        ttk.Label(child_wnd, text='3. 安装 Karastar 并打开设置好应用权限').place(x=20, y=85)
        ttk.Label(child_wnd, text='4. 使用多开工具复制此模拟器').place(x=20, y=110)
        ttk.Label(child_wnd, text='5. 修改 kara.properties 文件中模拟器安装路径 simulator.path').place(x=20, y=135)
        ttk.Label(child_wnd, text='6. 修改 kara.properties 文件中识别工具安装路径 tesseract.path').place(x=20, y=160)
        ttk.Label(child_wnd, text='正式使用').place(x=10, y=185)
        ttk.Label(child_wnd, text='1. Option -> init').place(x=20, y=210)
        ttk.Label(child_wnd, text='2. Start').place(x=20, y=235)

    def about(self):
        print('about')

    def on_click(self, event: tk.Event):
        btn = event.widget
        state = str(btn['state'])
        if state == tk.DISABLED:
            return

        btn['state'] = tk.DISABLED
        if btn['text'] == 'start':
            self.m_init()
            [i.start() for i in self.karastar.instances]
            btn['image'] = 'end'
            btn['text'] = 'end'
        else:
            [i.end() for i in self.karastar.instances]
            btn['image'] = 'start'
            btn['text'] = 'start'
        btn['state'] = tk.NORMAL


if __name__ == '__main__':
    kui = KaraUi()
