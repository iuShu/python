import os.path

from kara.task.taskunit import create
from kara.karaexception import KaraException
from kara.utils import cooldown, pos, ltime
from kara.constants import *
from config import config
from script import textocr
from tkinter.messagebox import askyesno

import time
import numpy as np


def tasks() -> dict:
    total = [
        open_kara,
        login,
        karapower
    ]

    temp = dict()
    for i in total:
        temp[i.__name__] = i
    return temp


def tasklist(inst):
    queue = inst.tasks
    for v in tasks().values():
        queue.put(create(v, inst))


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
    inst.log('using account ' + acc[0])
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
        raise KaraException('login failure')

    inst.desc('login ok')


def checkin(inst):
    inst.desc('checkin ...')
    s = inst.sml
    s.click(pos('quest.button'))
    cooldown('panel.open')
    s.match(CHECKIN)
    s.click(pos('quest.checkin'))
    cooldown('minor')
    s.click(pos('quest.close'))
    cooldown('panel.quit')


def karapower(inst):
    inst.desc('recognize kara power')
    cooldown('panel.open')
    s = inst.sml
    lt, rb = pos('power.left.top'), pos('power.right.bottom')
    roi = s.capture()[lt[1]:rb[1], lt[0]:rb[0]]
    txt = textocr.text_recognize(roi)
    inst.desc(f'power = {txt}')
    cooldown('panel.quit')
    if txt and '/' in txt:
        available = int(txt.split('/')[0])
        if available > 0:
            inst.power = available
            inst.arena_offset = True
            inst.tasks.put(create(arena_prepare, inst))
            return
    inst.tasks.put(create(logout, inst))


def arena_prepare(inst):
    s = inst.sml
    inst.desc('enter arena')
    s.click(pos('arena.button'))
    cooldown('arena.panel.open')
    if inst.arena_offset:
        s.click(pos('team.quit'))
        cooldown('panel.quit')
        s.click(pos('arena.button'))
        cooldown('arena.panel.open')
        inst.arena_offset = False

    inst.desc('recognizing ev lv')
    img, ti, ei, li = s.capture(), [], [], []
    lt, rb = np.array(pos('arena.kara.lt')), np.array(pos('arena.kara.rb'))
    xadd, yadd = pos('arena.kara.inc')
    for _ in range(3):
        tlt = lt
        ei.append(img[lt[1]:rb[1], lt[0]:rb[0]])
        lt, rb = lt + (0, yadd), rb + (0, yadd)
        trb = rb
        li.append(img[lt[1]:rb[1], lt[0]:rb[0]])
        ti.append(img[tlt[1]:trb[1], tlt[0]:trb[0]])
        lt, rb = lt + (xadd, -yadd), rb + (xadd, -yadd)

    roi = np.hstack(ti)
    if not os.path.exists(ELV_PATH):
        os.makedirs(ELV_PATH)
    cv.imwrite(f'{ELV_PATH}{s.name}-{ltime()}.png', roi)

    mxe, mxl = 0, 0
    for e in ei:
        txt = textocr.do_recognize(cv.cvtColor(e, cv.COLOR_BGR2GRAY))
        if not txt:
            inst.desc('recognizing ev error')
            return
        num = int(txt.split(':')[1].strip())
        if mxe == 0 or mxe < num:
            mxe = num

    for i in li:
        txt = textocr.do_recognize(cv.cvtColor(i, cv.COLOR_BGR2GRAY))
        if not txt:
            inst.desc('recognizing lv error')
            return
        num = int(txt.split(':')[1].strip())
        if mxl == 0 or mxl < num:
            mxl = num

    inst.desc(f'ev {mxe} and lv {mxl}')
    max_ev, max_lv = inst.sync.join(inst.sml.idx, mxe, mxl)
    max_scene, scene = get_scene(max_ev, max_lv), get_scene(mxe, mxl)
    inst.desc(f'self {scene} / max {max_scene}')

    if inst.flow_confirm and not askyesno(title='Task confirm', message='Are you sure to continue the task ?'):
        inst.desc('task flow abort cause client confirmed')
        return

    if max_scene == scene:
        if inst.sync.same_scene(inst.sml.idx, True):
            inst.arena_scene = max_scene
            inst.tasks.put(create(arena, inst))
        else:
            inst.tasks.put(create(arena_prepare, inst))
    else:
        inst.sync.same_scene(inst.sml.idx, False)
        inst.desc(f'mismatch: {mxe}/{mxl} {max_ev}/{max_lv}')
        s.click(pos('team.quit'))
        cooldown('panel.quit')
        inst.tasks.put(create(logout, inst))


def arena(inst):
    # prepare
    s = inst.sml
    scene_pos, cancel_pos = pos(inst.arena_scene), pos('arena.match.cancel.button')

    clt, crb = pos('arena.match.cancel.lt'), pos('arena.match.cancel.rb')
    slt = pos('arena.match.start.lt')
    wait_times = config.instance().getint('kara', 'arena.match.wait.time')
    wait_times_endurance = config.instance().getint('kara', 'arena.match.wait.endurance')
    match_check_times = config.instance().getint('kara', 'arena.match.check.times')
    matched = inst.sync.wait_times_diff
    inst.desc('pvp match ready')

    inst.sync.coordinate(inst.sml)
    inst.sync.ready_match()

    # matching
    s.click(scene_pos)
    while not inst.f_end and match_check_times > 0:
        lt, rb = s.tmatch(MATCH_START)
        if np.all(lt == slt):
            break
        match_check_times -= 1
    if match_check_times < 1:
        inst.desc('can not start match')
        inst.sync.cancel_all()
        inst.sync.end_match(inst.sml.idx)
        inst.tasks.put(create(arena_prepare, inst))
        return

    while not inst.f_end and matched(wait_times, False) < wait_times_endurance and wait_times > 0:
        lt, rb = s.tmatch(CANCEL)
        if np.all(lt != clt) or np.all(rb != crb):  # matched
            matched(wait_times, True)
            # print('matched', lt, rb, ' times', wait_times)
            inst.desc('matched')
            inst.sync.report_matched(inst.sml.idx)
            inst.sync.end_match(inst.sml.idx)
            cooldown('arena.match.loading')
            inst.tasks.put(create(battle, inst))
            return
        wait_times -= 1

    # match failed
    # print('wait_times', wait_times)
    inst.sync.end_match(inst.sml.idx)
    s.click(cancel_pos)
    s.click(cancel_pos)
    cooldown('panel.quit')
    s.click(pos('team.quit'))
    cooldown('panel.quit')

    lt, rb = s.match(MAIN, wait=10)
    if np.any(lt is None):  # cancel match failed
        inst.desc('cancel failed, enter battle')
        inst.tasks.put(create(battle, inst))
    else:   # cancel match success
        inst.desc('cancel ok')
        inst.tasks.put(create(arena_prepare, inst))


def battle(inst):
    inst.desc('pvp loading')
    inst.power -= 1
    s = inst.sml
    lt, rb = s.match(ARENA_SQUIRREL, blur=False)
    if np.any(lt is None):
        raise KaraException('error status at pvp battle')

    inst.desc('entered pvp battle')
    s.click(pos('arena.battle.setting'))
    cooldown('panel.quit')

    inst.desc('surrender')
    inst.sync.ready_surrender()
    s.click(pos('arena.battle.surrender'))
    inst.sync.end_surrender()
    cooldown('panel.quit')

    if inst.check_power():
        inst.desc('next pvp match')
        inst.tasks.put(create(arena_prepare, inst))
    else:
        inst.desc('no power, logout')
        inst.tasks.put(create(logout, inst))


def logout(inst):
    s = inst.sml
    inst.desc('logout ...')
    s.click(pos('setting.button'))
    cooldown('panel.open')
    s.click(pos('logout.button'))
    cooldown('panel.quit')

    queue = inst.tasks
    queue.put(create(login, inst))
    queue.put(create(karapower, inst))
