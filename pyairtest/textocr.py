import subprocess
import cv2 as cv
from tutorial import tesseract_root, tesseract_temp
from subprocess import PIPE

sinfo = subprocess.STARTUPINFO()
sinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
sinfo.wShowWindow = subprocess.SW_HIDE


def recognize(img) -> str:
    img = cv.resize(img, None, fx=2, fy=2, interpolation=cv.INTER_AREA)
    cv.imwrite(f'{tesseract_temp}', img)
    cmd = f'{tesseract_root} {tesseract_temp} stdout outputbase digits'
    prc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, startupinfo=sinfo)
    out, err = prc.communicate()
    if prc.returncode == 0:
        return out.decode().strip()
    raise RuntimeError('tesseract recognize error while execute ' + cmd)
