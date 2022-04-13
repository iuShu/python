from os.path import dirname, realpath, normpath

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
