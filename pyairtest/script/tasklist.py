import time
import traceback

import utils
import win
import textocr

from airtest.core.android import Android
from script.config import conf
from constants import *
from utils import only_numeric, tmatch


def tasks() -> dict:
    return {
        'open_kara': open_kara,
        'login': login,
        'recognize_energy': recognize_energy,
        'recognize_level': recognize_level,
        'pvp_match': pvp_match,
        'logout': logout,
    }
    # return fake_tasks()


# test only
def fake_tasks() -> dict:
    def func(sml):
        dev: Android = sml.dev
        dev.touch((133, 111))
        time.sleep(2)
        dev.touch((667, 243))

    fake = dict()
    for i in range(10):
        fake[f'switch-{i}'] = func
    return fake


def open_kara(sml):
    rec = sml.match(t_kara)
    if not rec:
        sml.backward()     # fire stop
        sml.log('cannot found kara app')
        return

    sml.click(center(rec))
    sml.log('app loading')
    cooldown('apk.startup')
    times = conf.getint('kara', 'startup.match.times')
    for _ in range(times):
        sml.click(pos('email.button'))
        cooldown(seconds=.5)
        if sml.match(t_close):
            break


def login(sml):
    if not sml.match(t_close):      # for single execute
        sml.click(pos('email.button'))
        cooldown()

    sml.log('obtain account')
    acc = sml.obtain_account()
    if not acc:
        sml.log('no account, stop all')
        sml.not_stop.clear()
        return

    sml.log('account', acc[0])
    sml.click(pos('email.input'))
    cooldown()
    win.cpress(sml.hwnd, 'lcontrol,a')
    win.press(sml.hwnd, 'delete')
    win.typing(sml.hwnd, acc[0])
    win.press(sml.hwnd, 'return')
    cooldown()
    sml.click(pos('password.input'))
    cooldown()
    win.cpress(sml.hwnd, 'lcontrol,a')
    win.press(sml.hwnd, 'delete')
    win.typing(sml.hwnd, acc[1])
    win.press(sml.hwnd, 'return')
    cooldown()
    sml.click(pos('login.button'))
    sml.log('login')
    cooldown('login.wait')

    times = conf.getint('kara', 'login.loading.times')
    ret = sml.wait(t_main, timeout=times)
    if not ret:
        sml.log('login failed')
        sml.backward(0)     # login failed, switch account


def recognize_energy(sml):
    sml.log('recognize energy')
    screen = sml.snapshot()
    elt, erb = pos('energy.lt'), pos('energy.rb')
    roi = screen[elt[1]:erb[1], elt[0]:erb[0]]
    try:
        hsv = utils.hsv_filter(roi)
        reg = textocr.recognize(hsv)
        numeric = only_numeric(reg)
        energy = int(numeric[:numeric.rfind('20')])
        sml.log('energy', energy)
        if energy < 1:
            sml.forward(3)      # logout and re-login
        else:
            sml.energy = energy
    except Exception as e:
        sml.log('energy recognize error', e.__str__())
        sml.forward(3)          # logout and re-login


def recognize_level(sml):
    sml.log('recognize level')
    sml.click(pos('role.button'))
    sml.wait(t_role)
    sml.log('entered role panel')
    screen = sml.snapshot()
    llt, lrb = pos('role.lv.lt'), pos('role.lv.rb')
    try:
        roi = screen[llt[1]:lrb[1], llt[0]:lrb[0]]
        reg = textocr.recognize(roi)
        level = int(only_numeric(reg))
        sml.log('level', level)
        sml.level = level
        sml.click(pos('back'))
        _sync_level(sml)
        cooldown()
    except Exception as e:
        sml.log('level recognize error', e.__str__())
        sml.forward(2)


def _sync_level(sml):
    if sml.desired:
        sml.log('desired', sml.desired)
        if sml.desired != get_scene(sml.level):
            sml.backward(2)
            return
        sml.desired = None
        return              # to next task

    max_level = sml.sync_data(sml.level)
    if not max_level:       # sync failed
        return

    sml.log('max level', max_level)
    if sml.level == max_level:
        return              # to next task

    scene, self_scene = get_scene(max_level), get_scene(sml.level)
    if scene != self_scene:
        sml.desired = scene
        sml.forward(2)      # logout and re-login
        return


def pvp_match(sml):
    sml.log('energy', sml.energy, ', pvp counter', sml.arena_counter)
    if sml.energy < 1 or sml.arena_counter >= 10:
        sml.log('can not join pvp')
        sml.forward(1)      # to log out
        return

    sml.log('enter arena')
    sml.click(pos('arena.button'))
    sml.wait(t_bf)
    cooldown()

    scene_pos = pos(get_scene(sml.level))
    slt = pos('arena.match.start.lt')
    clt = pos('arena.match.cancel.lt')
    cancel_pos = pos('arena.match.cancel.button')
    match_counter = 1
    max_try = conf.getint('kara', 'arena.match.try.times')

    sml.log('pvp match ready')
    ready = sml.sync_action()
    if not ready:           # sync failed
        return

    sml.click(scene_pos)    # start match
    sml.reset_pvp_sync()    # reset
    cooldown(seconds=.4)
    while sml.is_running():
        lt, rb = tmatch(sml.snapshot(), t_who)
        if lt[0] != slt[0] or lt[1] != slt[1]:
            break
        cooldown(seconds=.1)

    while sml.is_running() and max_try > sml.pvp_sync(match_counter, False):
        lt, rb = tmatch(sml.snapshot(), t_cancel)
        if lt[0] != clt[0] or lt[1] != clt[1]:
            sml.pvp_sync(match_counter, True)
            sml.log('matched at', match_counter)
            _battle(sml)
            return
        match_counter += 1

    sml.click(cancel_pos)
    cooldown(seconds=.3)
    sml.click(cancel_pos)
    sml.log('try cancel at', match_counter)
    cooldown()
    while sml.is_running():
        if sml.match(t_bf):
            sml.log('cancel ok')
            sml.click(pos('back'))
            cooldown()
            sml.backward(0)     # re-enter arena
            return
        elif sml.match(t_squirrel):
            sml.log('cancel failed')
            _battle(sml)
            return
        cooldown(seconds=.5)


def _battle(sml):
    sml.log('pvp loading')
    sml.arena_counter += 1
    sml.energy -= 1
    times = conf.getint('kara', 'battle.loading.times')
    sml.wait(t_squirrel, timeout=times)
    sml.log('start battle')
    sml.click(pos('arena.battle.setting'))
    cooldown()
    sml.click(pos('arena.battle.surrender'))
    cooldown()
    sml.log('surrendered')
    sml.backward(0)             # re-enter arena


def logout(sml):
    if not sml.match(t_main):
        sml.log('logout failed: not in home page')
        return

    sml.click(pos('setting.button'))
    cooldown('panel.open')
    sml.click(pos('logout.button'))
    sml.log('log out')
    sml.backward(5)    # back to log in


def cooldown(key: str = 'one.second', seconds: float = 0):
    if seconds:
        time.sleep(seconds)
    else:
        time.sleep(conf.getint('kara', key + '.cooldown') / 1000)


def pos(key: str) -> tuple:
    return conf.getpos('kara', key + '.pos')


def center(rec) -> tuple:
    lt, rb = rec[0], rec[1]
    x = lt[0] + ((rb[0]-lt[0])//2)
    y = lt[1] + ((rb[1]-lt[1])//2)
    return x, y

