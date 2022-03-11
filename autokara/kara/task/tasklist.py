import random

from kara.task.taskunit import create
from kara.karaexception import KaraException
from kara.utils import cooldown, pos
from kara.constants import *
from script import textocr

import time
import numpy as np


def tasklist(inst):
    queue = inst.tasks
    queue.put(create(open_kara, inst))
    queue.put(create(login, inst))      # logout()
    queue.put(create(checkin, inst))
    queue.put(create(karapower, inst))
    # queue.put(create(logout, inst))


def open_kara(inst):
    s = inst.sml
    inst.desc('find app icon')
    s.match_click(KARA_ICON)
    inst.desc('app launching')
    cooldown('apk.startup')
    s.match(EMADDR)


def login(inst):
    s = inst.sml
    inst.desc('find email button')
    s.match_click(EMADDR)
    cooldown('email.panel')
    inst.desc('obtain account')
    acc = inst.obtain_account()
    if not acc:
        raise KaraException('no more account')

    inst.desc('login ...')
    s.click(pos('email.input'))
    time.sleep(.2)
    s.cpress('lcontrol,a')
    s.press('delete')
    s.typing(acc[0])
    s.press('return')
    cooldown('account.input')
    s.click(pos('password.input'))
    time.sleep(.2)
    s.cpress('lcontrol,a')
    s.press('delete')
    s.typing(acc[1])
    s.press('return')
    cooldown('account.input')
    s.click(pos('login.button'))
    lt, rb = s.match(MAIN)
    if np.any(lt is None):
        raise KaraException('login failure with account ' + acc[0])

    inst.desc('login ok')


def checkin(inst):
    print(inst.sml.name, inst.desc_widget.winfo_name())
    inst.desc('checkin ...')
    s = inst.sml
    s.click(pos('quest.button'))
    cooldown('panel.open')
    s.click(pos('quest.checkin'))
    cooldown('minor')
    s.click(pos('quest.close'))
    cooldown('panel.quit')


def karapower(inst):
    inst.desc('recognize kara power')
    s = inst.sml
    lt, rb = pos('power.left.top'), pos('power.right.bottom')
    roi = s.capture()[lt[1]:rb[1], lt[0]:rb[0]]
    txt = textocr.text_recognize(roi)
    print('reg', txt)
    if not txt or '/' not in txt:
        return

    available = int(txt.split('/')[0])
    if available > 0:
        inst.power = available


def arena(inst):
    # if not inst.check_power():
    #     raise KaraException('not enough kara power')

    pass


def logout(inst):
    s = inst.sml
    inst.desc('logout ...')
    s.click(pos('setting.button'))
    cooldown('panel.open')
    s.click(pos('logout.button'))

    queue = inst.tasks
    queue.put(create(login, inst))
    queue.put(create(checkin, inst))
    queue.put(create(karapower, inst))
    queue.put(create(logout, inst))
