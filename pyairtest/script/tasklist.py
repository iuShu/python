import time

from airtest.core.android import Android


def tasks():
    # return {
    #     'open_kara': open_kara,
    #     'login': login,
    #     'recognize_energy': recognize_energy,
    #     'recognize_level': recognize_level,
    #     'pvp_match': pvp_match,
    #     'logout': logout,
    # }
    fake = dict()
    for i in range(10):
        fake[f'switch-{i}'] = open_kara
    return fake


def open_kara(sml):
    dev: Android = sml.dev
    dev.touch((133, 111))
    time.sleep(2)
    dev.touch((667, 243))


def login(sml):
    pass


def recognize_energy(sml):
    pass


def recognize_level(sml):
    pass


def pvp_match(sml):
    pass


def logout(sml):
    pass
