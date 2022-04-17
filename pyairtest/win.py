import string
import time
import win32con
import win32gui
import win32api
from ctypes import windll

WinMessage = windll.user32.SendMessageW
# WinMessage = windll.user32.PostMessageW
VkKeyScanA = windll.user32.VkKeyScanA
MapVirtualKeyW = windll.user32.MapVirtualKeyW

CLICK_DURATION = .04
KEYBOARD_DURATION = .08

EXTENDED = '~!@#$%^&*()_+{}|:"<>?'
VkCode = {
    "back":  0x08,
    "tab":  0x09,
    "return":  0x0D,
    "shift":  0x10,
    "control":  0x11,
    "menu":  0x12,
    "pause":  0x13,
    "capital":  0x14,
    "escape":  0x1B,
    "space":  0x20,
    "end":  0x23,
    "home":  0x24,
    "left":  0x25,
    "up":  0x26,
    "right":  0x27,
    "down":  0x28,
    "print":  0x2A,
    "snapshot":  0x2C,
    "insert":  0x2D,
    "delete":  0x2E,
    "lwin":  0x5B,
    "rwin":  0x5C,
    "numpad0":  0x60,
    "numpad1":  0x61,
    "numpad2":  0x62,
    "numpad3":  0x63,
    "numpad4":  0x64,
    "numpad5":  0x65,
    "numpad6":  0x66,
    "numpad7":  0x67,
    "numpad8":  0x68,
    "numpad9":  0x69,
    "multiply":  0x6A,
    "add":  0x6B,
    "separator":  0x6C,
    "subtract":  0x6D,
    "decimal":  0x6E,
    "divide":  0x6F,
    "f1":  0x70,
    "f2":  0x71,
    "f3":  0x72,
    "f4":  0x73,
    "f5":  0x74,
    "f6":  0x75,
    "f7":  0x76,
    "f8":  0x77,
    "f9":  0x78,
    "f10":  0x79,
    "f11":  0x7A,
    "f12":  0x7B,
    "numlock":  0x90,
    "scroll":  0x91,
    "lshift":  0xA0,
    "rshift":  0xA1,
    "lcontrol":  0xA2,
    "rcontrol":  0xA3,
    "lmenu":  0xA4,
    "rmenu":  0XA5
}


def get_virtual_keycode(key: str):
    if len(key) == 1 and key in string.printable:
        return VkKeyScanA(ord(key)) & 0xff
    else:
        return VkCode[key]


def press(hwnd, key: str):
    vk_code = get_virtual_keycode(key)
    scan_code = MapVirtualKeyW(vk_code, 0)
    shift = key in string.ascii_uppercase, key in EXTENDED
    if True in shift:
        WinMessage(hwnd, win32con.WM_KEYDOWN, 160, 19529729)
    WinMessage(hwnd, win32con.WM_KEYDOWN, vk_code, (scan_code << 16) | 1)
    time.sleep(KEYBOARD_DURATION)
    if True in shift:
        WinMessage(hwnd, win32con.WM_KEYUP, 160, 3240755201)
    WinMessage(hwnd, win32con.WM_KEYUP, vk_code, (scan_code << 16) | 0XC0000001)


def cpress(hwnd, ckey: str):
    keys = ckey.split(',')
    reverse = []
    for k in keys:
        vk_code = get_virtual_keycode(k)
        scan_code = MapVirtualKeyW(vk_code, 0)
        reverse.insert(0, (vk_code, scan_code))
        WinMessage(hwnd, win32con.WM_KEYDOWN, vk_code, (scan_code << 16) | 1)
    time.sleep(KEYBOARD_DURATION)
    for r in reverse:
        WinMessage(hwnd, win32con.WM_KEYUP, r[0], (r[1] << 16) | 0XC0000001)


def click(hwnd, p: tuple):
    x, y, w, h = win32gui.GetWindowRect(hwnd)
    spos = win32gui.ScreenToClient(hwnd, (p[0] + x, p[1] + y))
    wpos = win32api.MAKELONG(spos[0], spos[1])
    WinMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, wpos)
    time.sleep(CLICK_DURATION)
    WinMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, wpos)


def typing(hwnd, txt: str):
    for t in txt:
        press(hwnd, t)

