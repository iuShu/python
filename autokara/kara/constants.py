import cv2 as cv


TITLE = '雷电模拟器'
KARA_ICON = cv.imread("../resources/kara.png")
EMADDR = cv.imread("../resources/emaddr.png")
READY = cv.imread('../resources/ready.png')
MAIN = cv.imread('../resources/main_flag.png')
CHECKIN = cv.imread('../resources/checkin.png')
ATV_POWER = cv.imread('../resources/atv_power.png')


ARENA_GENERAL = {
    10: 'arena.general.baby',
    15: 'arena.general.catch',
    20: 'arena.general.hunger',
    9999: 'arena.general.strike'
}

ARENA_ADVANCED = {
    10: 'arena.advanced.legend',
    9999: 'arena.advanced.extreme',
}
