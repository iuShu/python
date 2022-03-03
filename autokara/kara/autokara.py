"""
    close the right tools bar of thunder simulator
    set the simulator's resolution to 960 x 540
    open kara to allow the device permissions of the simulator
    copy 3 simulator after above steps are finished
"""

import time

from constants import *
from kara import utils
from kara.utils import cooldown
from kara.simulator import Simulator
from kara.account import AccountManager
from kara.dungeon import Dungeon, Kara
from config import config


def startup():
    sml = Simulator(TITLE)
    acm = AccountManager()

    sml.match_click(KARA_ICON)
    sml.match_click(EMADDR)
    sml.match(READY)

    acc = acm.obtain()
    if not acc:
        return
    login(sml, acc)

    checkin(sml)

    power = avt_power(sml)
    if power:
        roles = main_role(sml)
        role = Kara(roles)
        d = Dungeon(sml, power, role)
        d.start()

    logout(sml)


def login(sml: Simulator, acc):
    # click email input bar
    sml.cpress('lcontrol,a')
    sml.press('delete')
    sml.typing(acc[0])
    sml.press('return')
    cooldown('account.input')
    # click password input bar
    sml.cpress('lcontrol,a')
    sml.press('delete')
    sml.typing(acc[1])
    sml.press('return')
    cooldown('account.input')
    # click login button
    sml.match(MAIN)


def checkin(sml: Simulator):
    # click quest button
    cooldown('quest.panel')
    # click checkin button
    cooldown('quest.panel')
    # click close button
    cooldown('panel.quick')
    pass


def main_role(sml: Simulator):
    #   click team button
    tlt, trb = sml.match(TEAM_STAR, th=5)
    blt, brb = sml.match(TEAM_EDIT, blur=False, th=5)
    area = sml.capture()[trb[1]:blt[1], trb[0]:blt[0]]
    h, w, d = area.shape
    area = area[4:h - 10, 2:w // 3 - 10, :]
    c = utils.grab_cut(area, (1, 1, area.shape[1], area.shape[0]))
    if not c:
        raise RuntimeError('can not found the main kara in team panel')
    #   click back button to exit team panel
    cooldown('panel.quit')
    return c, cv.flip(c, 1)


def avt_power(sml: Simulator):
    lt, rb = sml.match(ATV_POWER)
    roi = sml.capture()[lt[1]:rb[1], lt[0]:rb[0]]
    # text = textocr.text_recognize(roi)
    # if len(text) > 5:
    #     return 0

    # available = int(text.split('/')[0])
    # if available < 1:
    #     return 0
    # return available
    return 0


def logout(sml: Simulator):
    # click setting button
    # click logout button
    pass


if __name__ == '__main__':
    startup()
