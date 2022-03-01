import cv2 as cv
import numpy as np
import pytesseract

from script import utils


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


def text_recognize(img):
    area = roi_rect(img)
    area = cv.resize(area, None, fx=2, fy=2, interpolation=cv.INTER_AREA)
    text = pytesseract.image_to_string(area)
    return text


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
