from kara.task.taskunit import create
from kara.karaexception import KaraException
from kara.utils import cooldown, pos
from kara.constants import *
from config import config
from script import textocr

import time
import numpy as np


def tasklist(inst):
    queue = inst.tasks
    queue.put(create(open_kara, inst))
    queue.put(create(login, inst))      # logout()
    queue.put(create(checkin, inst))
    queue.put(create(karapower, inst))
    # queue.put(create(arena, inst))
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
            inst.tasks.put(create(arena_prepare, inst))
            return
    inst.tasks.put(create(logout, inst))


def arena_prepare(inst):
    s = inst.sml
    inst.desc('enter arena')
    s.click(pos('arena.button'))
    cooldown('panel.open')

    inst.desc('recognizing ev lv')
    img, ei, li = s.capture(), [], []
    lt, rb = np.array(pos('arena.kara.lt')), np.array(pos('arena.kara.rb'))
    xadd, yadd = pos('arena.kara.inc')
    for _ in range(3):
        ei.append(img[lt[1]:rb[1], lt[0]:rb[0]])
        lt, rb = lt + (0, yadd), rb + (0, yadd)
        li.append(img[lt[1]:rb[1], lt[0]:rb[0]])
        lt, rb = lt + (xadd, -yadd), rb + (xadd, -yadd)

    mxe, mxl = 0, 0
    for e in ei:
        txt = textocr.do_recognize(e)
        if not txt:
            inst.desc('recognizing ev error')
            return
        num = int(txt.split(':')[1].strip())
        if mxe == 0 or mxe < num:
            mxe = num

    for i in li:
        txt = textocr.do_recognize(i)
        if not txt:
            inst.desc('recognizing lv error')
            return
        num = int(txt.split(':')[1].strip())
        if mxl == 0 or mxl < num:
            mxl = num

    inst.desc(f'ev {mxe} and lv {mxl}')
    max_ev, max_lv = inst.sync.join(inst.sml.idx, mxe, mxl)
    max_scene, scene = get_scene(max_ev, max_lv), get_scene(mxe, mxl)
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
    wait_times = config.instance().getint('kara', 'arena.match.wait.time')
    match_collision_endurance = config.instance().getint('kara', 'arena.match.collision.endurance') / 1000
    matched = inst.sync.match_collision
    cd = config.instance().getint('kara', 'arena.startup.cooldown') / 1000
    inst.desc('pvp match ready')

    inst.sync.ready_match()

    # matching
    s.click(scene_pos)
    time.sleep(cd)

    while matched(False) < match_collision_endurance and wait_times > 0:
        lt, rb = s.tmatch(CANCEL)
        if np.all(lt != clt) or np.all(rb != crb):  # matched
            matched(True)
            inst.desc('matched')
            inst.sync.finished(inst.sml.idx)
            inst.tasks.put(create(battle, inst))
            return
        wait_times -= 1

    # match failed
    inst.sync.finished(inst.sml.idx)
    s.click(cancel_pos)
    cooldown('panel.quit')
    s.click(pos('team.quit'))
    inst.tasks.put(create(arena_prepare, inst))


def battle(inst):
    inst.desc('entered pvp battle')
    s = inst.sml
    s.match(ARENA_SQUIRREL)
    s.click(pos('arena.battle.setting'))
    cooldown('minor')
    s.click(pos('arena.battle.surrender'))
    cooldown('panel.quit')
    inst.power -= 1
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
    queue.put(create(checkin, inst))
    queue.put(create(karapower, inst))
    # queue.put(create(logout, inst))
