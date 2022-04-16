from os.path import dirname, realpath, normpath
from airtest.core.cv import Template

root_dir = dirname(realpath(__file__))
res_dir = normpath(root_dir + '/resources')
temp_dir = normpath(res_dir + '/temp')
gui_dir = normpath(res_dir + '/gui')
template_dir = normpath(res_dir + '/template')
airadb_dir = normpath(root_dir + '/airadb')

ico_kara = normpath(gui_dir + '/kara.png')
ico_start = normpath(gui_dir + '/start.png')
ico_end = normpath(gui_dir + '/end.png')
ico_istart = normpath(gui_dir + '/istart.png')
ico_iend = normpath(gui_dir + '/iend.png')
ico_ipause = normpath(gui_dir + '/ipause.png')

tesseract_sample = normpath(template_dir + '/tesseract_sample.png')
capture_file = normpath(temp_dir + '/capture.png')

log_file = ''
elv_file = ''

max_task_num = 31

t_kara = Template('resources/template/kara.png')
t_email = Template('resources/template/emaddr.png')
t_main = Template('resources/template/main_flag.png')
t_bf = Template('resources/template/battlefield_ready.png')
t_close = Template('resources/template/close.png')


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


def get_scene(lv: int, ev: int = 0):
    if ev > 0:
        for i in ARENA_ADVANCED:
            if ev <= i:
                return ARENA_ADVANCED[i]
    else:
        for i in ARENA_GENERAL:
            if lv <= i:
                return ARENA_GENERAL[i]
