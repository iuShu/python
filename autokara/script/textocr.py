import subprocess
import threading

import cv2 as cv
import numpy as np

from script import utils
from config import config
from subprocess import PIPE

OCR_EXE_PATH = config.instance().get('kara', 'tesseract.path')

sinfo = subprocess.STARTUPINFO()
sinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
sinfo.wShowWindow = subprocess.SW_HIDE


def roi_rect(img):
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    rect_kernel = cv.getStructuringElement(cv.MORPH_RECT, (9, 3))
    thresh = cv.threshold(gray, 200, 255, cv.THRESH_BINARY)[1]
    grad_x = cv.Sobel(thresh, ddepth=cv.CV_32F, dx=1, dy=0, ksize=-1)
    grad_x = np.absolute(grad_x)
    (miv, mxv) = (np.min(grad_x), np.max(grad_x))
    grad_x = (255 * ((grad_x - miv) / (mxv - miv)))
    grad_x = grad_x.astype('uint8')
    grad_x = cv.morphologyEx(grad_x, cv.MORPH_CLOSE, rect_kernel)
    thresh = cv.threshold(grad_x, 120, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)[1]
    cts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    roi = []
    for c in cts[0]:
        x, y, w, h = cv.boundingRect(c)
        if w > 20 and w / h > 2:
            roi.append((x, y, w, h))
    rf = roi[0]
    area = gray[rf[1]-5:rf[1]+rf[3]+5, rf[0]:rf[0]+rf[2]]
    return area


def text_recognize(img) -> str:
    area = roi_rect(img)
    return do_recognize(area)


def do_recognize(img) -> str:
    img = cv.resize(img, None, fx=2, fy=2, interpolation=cv.INTER_AREA)
    thn = threading.currentThread().name
    cv.imwrite(f'../resources/temp/ocr-{thn}.png', img)
    root = utils.project_root()
    cmd = f'{OCR_EXE_PATH}tesseract {root}resources\\temp\\ocr-{thn}.png stdout'
    prc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, startupinfo=sinfo)
    out, err = prc.communicate()
    if prc.returncode == 0:
        return out.decode().strip()
    raise RuntimeError('tesseract recognize error')


def practice():
    cap = cv.imread('../resources/cap/cap-1.png')
    apw = cv.imread('../resources/atv_power.png')
    lt, br = utils.matches(cap, apw)
    roi = cap[lt[1]:br[1], lt[0]:br[0]]
    pw = text_recognize(roi)
    print('activity power:', pw)


if __name__ == '__main__':
    # image = cv.imread('../resources/atv_power.png')
    # image = cv.imread('../resources/atv_power2.png')
    # print(text_recognize(image))

    practice()




