from PIL import Image
import os
import subprocess
import time

import cv2
import numpy as np

import script.utils


def adb_capture():
    start = time.time()
    cmd = 'G:\\application\\simulator\\LDPlayer4\\adb -s 127.0.0.1:5555 shell screencap -p'
    pro = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pro.communicate()
    print(len(out))
    if pro.returncode > 0:
        raise RuntimeError('unknown error during fetching capture image')

    out = out.replace(b'\r\n', b'\n')
    print(len(out))
    # with open('../resources/area/cap.png', 'wb') as f:
    #     f.write(out)
    # re = cv2.imread('../resources/area/cap.png')
    # print(re.shape)
    met = np.frombuffer(out, dtype=np.uint8)
    img = cv2.imdecode(met, cv2.IMREAD_COLOR)
    print(img.shape)
    # img = Image.frombytes(mode='RGB', size=(540, 960), data=out)
    # img.show()
    print('cost', time.time() - start)
    script.utils.show(img)


def device_list():
    prc = os.popen('G:\\application\\simulator\\LDPlayer4\\adb devices')
    devices = []
    for line in prc.readlines():
        if len(line) > 1 and 'attached' not in line:
            devices.append(line.split('device')[0].replace('\t', ''))
    prc.close()
    print(devices)
    return devices


if __name__ == '__main__':
    adb_capture()
    # device_list()
