import time

import cv2 as cv
import numpy as np

import script.dungeon
from script import action, textocr, dungeon
from script.utils import *
from script.WinControl import WinControl

TITLE = '雷电模拟器'
KARA_ICON = cv.imread("../resources/kara.png")
EMADDR = cv.imread("../resources/emaddr.png")
READY = cv.imread('../resources/ready.png')
MAIN = cv.imread('../resources/main_flag.png')
SETTING = cv.imread('../resources/setting.png')
LOGOUT = cv.imread('../resources/logout.png')
QUEST = cv.imread('../resources/quest.png')
CHECKIN = cv.imread('../resources/checkin.png')
CLOSE = cv.imread('../resources/close.png')
BACK = cv.imread('../resources/back.png')
ATV_POWER = cv.imread('../resources/atv_power.png')
DUNGEON = cv.imread('../resources/dungeon.png')
TEAM = cv.imread('../resources/team/team-btn.png')
TEAM_STAR = cv.imread('../resources/team/team-star.png')
TEAM_EDIT = cv.imread('../resources/team/team-edit.png')
LEVEL = cv.imread('../resources/dungeon/level_text.png')
MONSTER = cv.imread('../resources/dungeon/monster.png')
ROUND = cv.imread('../resources/fight/round.png')


def workflow():
    # open kara
    winctrl = WinControl(TITLE)
    winctrl.match_randclk(KARA_ICON)
    winctrl.match_randclk(EMADDR)

    # input account
    winctrl.match_action(READY, lambda wc, lp, rp: account(wc, lp, rp))

    # checkin daily quest
    winctrl.match_action(MAIN, lambda wc, lp, rp: daily_checkin(wc))

    # check power
    power = enough_power(winctrl)
    print('check power', power)
    if not power:
        log_out(winctrl)
        return

    # recognize main kara
    roles = reg_role(winctrl)
    start_dungeon(winctrl, roles)


def open_kara(wc: WinControl):
    wc.match_randclk(KARA_ICON)
    wc.match_randclk(EMADDR)

    wc.match_action(READY, lambda wct, lp, rp: account(wct, lp, rp))


def account(wc: WinControl, lt, br):
    action.lang_pref(wc.handle, 'en')
    offset = np.array((wc.x, wc.y))
    left_point = lt[0] + int((br[0] - lt[0]) * .5)
    ecp = (left_point, lt[1] + int((br[1] - lt[1]) * .3))
    pcp = (left_point, lt[1] + int((br[1] - lt[1]) * .85))
    lcp = (left_point, lt[1] + int((br[1] - lt[1]) * 1.2))

    action.left_click(wc.handle, *np.add(ecp, offset))
    time.sleep(.4)
    action.press_kb('{sltAll}{backspace}' + 'hentonwu128@outlook.com' + '{enter}')
    time.sleep(.4)
    action.left_click(wc.handle, *np.add(pcp, offset))
    time.sleep(.4)
    action.press_kb('{sltAll}{backspace}' + '58CSM@karastar' + '{enter}')
    action.left_click(wc.handle, *np.add(lcp, offset))


def daily_checkin(wc: WinControl):
    wc.click((220, 500), 1)
    # wc.match_randclk(QUEST)
    # wc.match_randclk(CHECKIN)
    # wc.match_randclk(CLOSE, gaussian=False)
    wc.click((866, 90))

    # cap = wc.capture()
    # img = cap[cap.shape[0]//4*3:, :cap.shape[1]//3]
    # show(img)
    # lt, rb = matches(img, cv.imread('../resources/quest2.png'))
    # show_match(img, lt, rb)


def enough_power(wc: WinControl):
    cap = wc.capture()
    lt, br = matches(cap, ATV_POWER)
    roi = cap[lt[1]:br[1], lt[0]:br[0]]
    text = textocr.text_recognize(roi)
    if len(text) > 5:
        return 0

    available = int(text.split('/')[0])
    if available < 1:
        return 0
    return available


def reg_role(wc: WinControl):
    wc.match_randclk(TEAM, gaussian=False)
    time.sleep(1)
    cap = wc.capture()
    lt, br = matches(cap, TEAM_STAR, threshold=5)
    top = br
    lt, br = matches(cap, TEAM_EDIT, gaussian=False, threshold=5)
    bottom = lt
    area = cap[top[1]:bottom[1], top[0]:bottom[0]]
    h, w, d = area.shape
    area = area[4:h - 10, 2:w // 3 - 10, :]
    c = grab_cut(area, (1, 1, area.shape[1], area.shape[0]))
    if not c:
        raise RuntimeError('can not found main kara in team panel')
    wc.match_randclk(BACK)
    return c, cv.flip(c, 1)


def start_dungeon(wc: WinControl, roles):
    wc.match_randclk(DUNGEON)
    wc.match_randclk(LEVEL)
    wc.match_action(BACK, lambda wc, lp, rp: print('Entered Dungeon'))

    discover(wc, roles)

    wc.match_randclk(BACK)
    wc.match_action(MAIN, lambda wc, lp, rp: print('Back to Main'))
    if enough_power(wc):
        start_dungeon(wc, roles)
    else:
        log_out(wc)


def discover(wc: WinControl, roles):
    dg = dungeon.Dungeon()
    while True:
        monsters = MONSTER, cv.flip(MONSTER, 1)
        cap = wc.capture()
        lt, rb = match_all(cap, monsters)
        if not np.any(np.array(lt) == -1):
            wc.click(np.add(lt, np.divide(np.subtract(rb, lt), (2, 2))))
            fight(wc)
            return

        lt, br = match_all(cap, roles)
        nears, graph = reg_scene(cap, (lt, br))
        g = dungeon.Grids(graph)
        dg.forward(g)
        nxt = dg.next_step()
        if not nxt:  # exit and re-enter
            return

        print(nears[nxt[0], nxt[1]])
        wc.rand_click(*nears[nxt[0], nxt[1]])
        time.sleep(1.5)  # moving


def find_monster(wc: WinControl):
    # wc.match_action()
    pass


def fight(wc: WinControl):
    wc.match_action(ROUND, lambda wc, lt, br: print('Start Fight'))
    pass


def log_out(wc: WinControl):
    wc.match_randclk(SETTING)
    wc.match_randclk(LOGOUT)


if __name__ == '__main__':
    # workflow()
    wc = WinControl('雷电模拟器')
    # open_kara(wc)
    # account(wc)
    # daily_checkin(wc)
    # print(enough_power(wc))
    # reg_role(wc)
    # start_dungeon(wc)
    log_out(wc)
    # fight(wc)

