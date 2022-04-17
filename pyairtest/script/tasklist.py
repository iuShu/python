import time

import win
import utils
import textocr

from airtest.core.android import Android
from script.config import conf
from constants import *


def tasks() -> dict:
    return {
        'open_kara': open_kara,
        'login': login,
        'recognize_energy': recognize_energy,
        'recognize_level': recognize_level,
        'sync_level': sync_level,
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
    match_pos = sml.match(t_kara)
    if not match_pos:
        sml.back_last()     # fire stop
        return

    sml.click(match_pos)
    cooldown('apk.startup')

    times = conf.getint('kara', 'startup.match')
    for _ in range(times):
        sml.click(pos('email.button'))
        cooldown('half.second')
        if sml.match(t_close):
            break


def login(sml):
    acc = sml.obtain_account()
    if not acc:
        sml.not_stop.clear()
        return

    sml.click(pos('email.input'))
    win.cpress(sml.hwnd, 'lcontrol,a')
    win.press(sml.hwnd, 'delete')
    win.typing(sml.hwnd, acc[0])
    cooldown()
    sml.click(pos('password.input'))
    win.cpress(sml.hwnd, 'lcontrol,a')
    win.press(sml.hwnd, 'delete')
    win.typing(sml.hwnd, acc[1])
    cooldown()
    sml.click(pos('login.button'))
    cooldown('login.wait')

    times = conf.getint('kara', 'login.loading.times')
    ret = sml.wait(t_main, timeout=times)
    if not ret:
        sml.back_last(0)     # log in failed, switch account


def recognize_energy(sml):
    screen = sml.snapshot()
    elt, erb = pos('energy.lt'), pos('energy.rb')
    roi = screen[elt[1]:erb[1], elt[0]:erb[0]]
    try:
        reg = textocr.recognize(roi)
        energy = int(reg.removesuffix('20'))
        if energy < 1:
            sml.back_last()  # back to log in
        else:
            sml.energy = energy
    except Exception:
        print(sml.name, sml.pid, 'energy recognize error')
        sml.back_last()


def recognize_level(sml):
    sml.click(pos('role.button'))
    cooldown('panel.open')
    screen = sml.snapshot()
    llt, lrb = pos('role.lv.lt'), pos('role.lv.rb')
    try:
        roi = screen[llt[1]:lrb[1], llt[0]:lrb[0]]
        level = int(textocr.recognize(roi))
        sml.level = level
        sml.click(pos('back'))
        cooldown()
    except Exception:
        print(sml.name, sml.pid, 'level recognize error')
        sml.back_last(2)    # back to log in


def sync_level(sml):
    if sml.level == 0:
        sml.not_stop.clear()    # prevent single task
        return

    if not sml.desired:
        if sml.desired != get_scene(sml.level):
            sml.back_last(3)
            return
        sml.desired = None
        return              # to next task

    max_level = sml.sync_data(sml.level)
    if not max_level:       # sync failed
        return

    if sml.level == max_level:
        return              # to next task

    scene, self_scene = get_scene(max_level), get_scene(sml.level)
    if scene != self_scene:
        sml.desired = scene
        sml.back_last(3)    # back to log in
        return


def pvp_match(sml):
    cooldown()
    sml.click(pos('arena.button'))
    cooldown()
    sml.wait(t_bf)
    cooldown()

    scene_pos = conf.getpos('kara', get_scene(sml.level))
    slt = pos('arena.match.start.lt')
    clt = pos('arena.match.cancel.lt')
    cancel_pos = pos('arena.match.cancel.button')
    match_counter = 1
    max_try = conf.getint('kara', 'arena.match.try.times')
    ready = sml.sync_action()
    if not ready:           # sync failed
        return

    sml.click(scene_pos)    # start match
    sml.reset_pvp_sync()    # reset
    cooldown(seconds=.4)
    while sml.is_running():
        screen = sml.snapshot()
        lt, rb = utils.tmatch(screen, t_who)
        if lt[0] != slt[0] or lt[1] != slt[1]:
            break
        cooldown(seconds=.1)

    while sml.is_running() and max_try > sml.pvp_sync(match_counter, False):
        screen = sml.snapshot()
        lt, rb = utils.tmatch(screen, t_cancel)
        if lt[0] != clt[0] or lt[1] != clt[1]:
            sml.pvp_sync(match_counter, True)
            _battle(sml)
            return
        match_counter += 1

    sml.click(cancel_pos)
    cooldown(seconds=.5)
    sml.click(cancel_pos)
    cooldown(seconds=.5)
    while sml.is_running():
        if sml.match(t_bf):
            print(sml.name, sml.pid, 'cancel ok')
            sml.click(pos('back'))
            cooldown()
            sml.back_last(0)    # re-enter arena
            return
        elif sml.match(t_squirrel):
            print(sml.name, sml.pid, 'cancel failed')
            _battle(sml)
            return
        cooldown(seconds=.5)


def _battle(sml):   # not in the task list, pvp_match() inner only
    print(sml.name, sml.pid, 'pvp loading')
    times = conf.getint('kara', 'battle.loading.times')
    sml.wait(t_squirrel, timeout=times)
    print(sml.name, sml.pid, 'start battle')
    sml.click(pos('arena.battle.setting'))
    cooldown()
    sml.click(pos('arena.battle.surrender'))
    cooldown()
    print(sml.name, sml.pid, 'surrender')
    sml.back_last(0)


def logout(sml):
    if not sml.match(t_main):
        print(sml.name, sml.pid, 'not in home page')
        return

    sml.click(pos('setting.button'))
    cooldown('panel.open')
    sml.click(pos('logout.button'))
    sml.back_last(5)    # back to log in


def cooldown(key: str = 'one.second', seconds: float = 0):
    if seconds:
        time.sleep(seconds)
    else:
        time.sleep(conf.getint(key + '.cooldown') / 1000)


def pos(key: str) -> tuple:
    return conf.getpos('kara', key + '.pos')
