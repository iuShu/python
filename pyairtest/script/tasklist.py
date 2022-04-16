import time

import constants
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
    # TODO get account
    sml.click(pos('email.input'))
    sml.type('ctrl+A')
    sml.type('account')
    cooldown()
    sml.click(pos('password.input'))
    sml.type('ctrl+A')
    sml.type('password')
    sml.click(pos('login.button'))
    cooldown('login.wait')

    times = conf.getint('kara', 'login.match')
    ret = sml.wait(t_main, timeout=times)
    if not ret:
        sml.back_last(0)     # switch account


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
    cooldown('role.open')
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
        sml.stop()
        return

    if not sml.desired:
        if sml.desired != get_scene(sml.level):
            sml.back_last(3)
            return
        sml.desired = None
        return              # to next task

    max_level = sml.sync(sml.level)
    if not max_level:
        sml.stop()          # sync failed
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
    ready = sml.sync(1)
    if not ready:
        sml.stop()          # sync failed
        return

    sml.click(scene_pos)    # start match
    pass


def logout(sml):
    pass


def cooldown(key: str = 'one.second', seconds: int = 0):
    if seconds:
        time.sleep(seconds)
    else:
        time.sleep(conf.getint(key + '.cooldown') / 1000)


def pos(key: str) -> tuple:
    return conf.getpos('kara', key + '.pos')
