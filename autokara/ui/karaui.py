from tkinter import ttk, Tk, PhotoImage
import tkinter as tk


class KaraUi(object):

    def __init__(self):
        pass


def test():
    root = Tk()
    root.title('Kara Assistant')
    root.geometry('400x400')
    root.resizable(width=False, height=True)

    icon_start = PhotoImage(file='../resources/ui/start.png', name='start')
    icon_end = PhotoImage(file='../resources/ui/end.png', name='end')
    icon_istart = PhotoImage(file='../resources/ui/istart.png', name='istart')
    icon_ipause = PhotoImage(file='../resources/ui/ipause.png', name='ipause')
    icon_iend = PhotoImage(file='../resources/ui/iend.png', name='iend')

    padx = 10
    btn = ttk.Button(root, text='start', compound=tk.LEFT, image='start')
    btn.place(x=padx, y=10)

    sep = ttk.Separator(root, orient=tk.HORIZONTAL)
    sep.pack(fill=tk.X, pady=45)

    label_acc = ttk.Label(root, text='account: hentonwuq@outlook.com')
    label_acc.place(x=padx, y=58)
    btn_list = ttk.Button(root, text='show all')
    btn_list.place(x=308, y=55)

    sep = ttk.Separator(root, orient=tk.HORIZONTAL)
    sep.pack(fill=tk.X)

    label_sml = ttk.Label(root, text='lb-1')

    root.mainloop()


if __name__ == '__main__':
    test()
