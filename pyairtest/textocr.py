import os
import subprocess
import cv2 as cv
from constants import temp_dir
from script.config import conf
from subprocess import PIPE

sinfo = subprocess.STARTUPINFO()
sinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
sinfo.wShowWindow = subprocess.SW_HIDE

tesseract_root = conf.get('kara', 'tesseract.path')


def recognize(img) -> str:
    img = cv.resize(img, None, fx=2, fy=2, interpolation=cv.INTER_AREA)
    tesseract_temp = os.path.normpath(temp_dir + f'/ocr-{os.getpid()}.png')
    cv.imwrite(f'{tesseract_temp}', img)
    cmd = f'{tesseract_root}tesseract {tesseract_temp} stdout outputbase digits'
    prc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, startupinfo=sinfo)
    out, err = prc.communicate()
    if prc.returncode == 0:
        return out.decode().strip()
    raise RuntimeError('tesseract recognize error while execute ' + cmd)
