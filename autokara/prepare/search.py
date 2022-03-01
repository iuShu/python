import os
from queue import Queue

import numpy as np
import cv2 as cv

import script.dungeon
from script.utils import *

BLUR_VAL = (3, 3)
WALL_THRESHOLD = 1500
GROUND_THRESHOLD = 7000

ROI_WIDTH = 4
ROI_HEIGHT = 2


def find_role(img=None):
    # cap = cv.imread('../resources/home.png')
    # btn = cv.imread('../resources/team-btn.png')
    # lt, br = match(cap, btn, blur=False)
    # draw_match(cap, lt, br)

    team = cv.imread('../resources/team/team-panel.png')
    star = cv.imread('../resources/team/team-star.png')
    edit = cv.imread('../resources/team/team-edit.png')
    lt, br = matches(team, star, threshold=5)
    top = br
    lt, br = matches(team, edit, gaussian=False, threshold=5)
    bottom = lt
    area = team[top[1]:bottom[1], top[0]:bottom[0]]
    h, w, d = area.shape
    area = area[4:h - 10, 2:w // 3 - 10, :]
    c = grab_cut(area, (1, 1, area.shape[1], area.shape[0]))
    vc = cv.flip(c, 1)
    # cv.imwrite('../resources/area/role.png', c)
    # show(c)
    # show(vc)
    # cap = cv.imread('../resources/dungeon/sample.png')
    cap = cv.imread('../resources/path/cap-2.png')
    if img is not None:
        cap = img
    lt, br = matches(cap, c, threshold=5)
    if np.any(lt == -1):
        lt, br = matches(cap, vc, threshold=5)
    # show_match(cap, lt, br)
    return lt, br


def roi_area(pos):
    rw, rh = pos[1][0] - pos[0][0], pos[1][1] - pos[0][1]
    up = np.subtract(pos[0], (0, rh)), np.subtract(pos[1], (0, rh))
    down = np.add(pos[0], (0, rh)), np.add(pos[1], (0, rh))
    left = np.subtract(pos[0], (rw, 0)), np.subtract(pos[1], (rw, 0))
    right = np.add(pos[0], (rw, 0)), np.add(pos[1], (rw, 0))
    return up, down, left, right


def roi_area_more(pos):
    rw, rh = pos[1][0] - pos[0][0], pos[1][1] - pos[0][1]
    lt = pos[0][0] - rw * ROI_WIDTH, pos[0][1] - rh * ROI_HEIGHT
    rb = pos[1][0] + rw * ROI_WIDTH, pos[1][1] + rh * ROI_HEIGHT
    grids = []
    y = lt[1]
    while y < rb[1]:
        x = lt[0]
        while x < rb[0]:
            grids.append(((x, y), (x + rw, y + rh)))
            x += rw
        y += rh
    return grids


def cut_area(img, lt, br):
    return img[lt[1]:br[1], lt[0]:br[0]]


def filter_nonwall(img):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    # lower_blue = np.array([110, 50, 50])
    # upper_blue = np.array([130, 255, 255])
    lower_green = np.array([31, 95, 28])
    upper_green = np.array([150, 255, 170])

    mask = cv.inRange(hsv, lower_green, upper_green)
    res = cv.bitwise_and(img, img, mask=mask)
    # show(res)
    return res


def reg_wall():
    pos = ((386, 214), (440, 266))
    cap = cv.imread('../resources/dungeon/sample.png')
    blur = cv.GaussianBlur(cap, BLUR_VAL, 0)
    # cv.rectangle(blur, pos[0], pos[1], (0, 0, 255), 2)

    # u, d, l, r = roi_area(pos)
    # cv.rectangle(blur, *u, (0, 255, 255), 2)
    # cv.rectangle(blur, *d, (0, 255, 255), 2)
    # cv.rectangle(blur, *l, (0, 255, 255), 2)
    # cv.rectangle(blur, *r, (0, 255, 255), 2)
    # show(blur)
    areas = [cut_area(blur, *i) for i in roi_area(pos)]
    # roi = cut_area(cap, *u)

    # b = np.full((roi.shape[1], roi.shape[0]), fill_value=0)
    # g = np.full((roi.shape[1], roi.shape[0]), fill_value=200)
    # r = np.full((roi.shape[1], roi.shape[0]), fill_value=0)
    # img = cv.merge((b, g, r))
    res = []
    for roi in areas:
        reg = filter_nonwall(roi)
        cnt = np.count_nonzero(reg)
        res.append(cnt > WALL_THRESHOLD)
    print(res)


def filter_ground(img):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    # lower = np.array([123, 39, 33])
    # upper = np.array([150, 101, 91])
    # lower = np.array([128, 47, 35])
    upper = np.array([186, 133, 90])
    lower = np.array([128, 39, 12])
    # upper = np.array([153, 88, 90])
    mask = cv.inRange(hsv, lower, upper)
    res = cv.bitwise_and(img, img, mask=mask)
    # show(res)
    return res


def reg_ground(img=None):
    # pos = ((379, 214), (433, 266))
    # cap = cv.imread('../resources/dungeon/sample.png')
    pos = find_role(img)
    cap = cv.imread('../resources/path/cap-2.png')
    if img is not None:
        cap = img
    # cap = cv.GaussianBlur(cap, BLUR_VAL, 0)
    nears = roi_area_more(pos)
    filtered = filter_ground(cap)
    grounds = []
    # show(filtered)
    for lt, rb in nears:
        cv.rectangle(cap, lt, rb, (0, 0, 255), 1)
        # reg = filter_ground(cut_area(cap, lt, rb))
        reg = cut_area(filtered, lt, rb)
        cnt = np.count_nonzero(reg)
        if cnt > GROUND_THRESHOLD:
            # cv.putText(cap, str(cnt), org=np.add(lt, (16, 32)), fontFace=cv.FONT_ITALIC, fontScale=.3,
            #            color=(0, 255, 255), lineType=1)
            grounds.append(True)
        else:
            grounds.append(False)
    show(cap)

    grids = np.array(nears).reshape((5, 9, 2, 2))
    grounds = np.array(grounds).reshape((5, 9))
    dis = bfs(grounds)
    go = None
    max_dis = 0
    for r in range(dis.shape[0]):
        for c in range(dis.shape[1]):
            if dis[r, c]:
                cv.putText(cap, str(dis[r, c]), org=np.add(grids[r, c][0], (16, 32)), fontFace=cv.FONT_ITALIC, fontScale=.3,
                           color=(0, 255, 255), lineType=1)
            if max_dis < dis[r, c]:
                max_dis = dis[r, c]
                go = (r, c)
    print(go, max_dis)
    lt, br = grids[go[0], go[1]]
    cv.rectangle(cap, lt, br, (255, 0, 0), 2)
    show(cap)


def detect_scenes():
    from script.utils import reg_scene
    path = '../resources/path'
    dg = script.dungeon.Dungeon()
    for i in range(1, len(os.listdir(path))):
        d = f'{path}/cap-{i}.png'
        if not os.path.exists(d):
            continue

        print('detect in', d)
        img = cv.imread(d)
        pos = find_role(img)
        if np.all(np.array(pos) == -1):
            print('can not match role in', d)
            break
        nears, grounds = reg_scene(img, pos)
        for n in nears:
            for p in n:
                cv.rectangle(img, p[0], p[1], (0, 255, 255), 2)

        grounds[2, 4] = ROLE
        cp = img.copy()
        for r in range(grounds.shape[0]):
            for c in range(grounds.shape[1]):
                cv.putText(cp, str(grounds[r, c]), org=np.add(nears[r, c][0], (16, 32)), fontFace=cv.FONT_ITALIC, fontScale=.3,
                           color=(255, 255, 0), lineType=1)
        show(cp)

        g = script.dungeon.Grids(grounds)
        dg.forward(g)
        nxt = dg.next_step()
        print('nxt', nxt)
        cv.rectangle(img, nears[nxt[0], nxt[1]][0], nears[nxt[0], nxt[1]][1], (220, 20, 120), 2)

        for r in range(grounds.shape[0]):
            for c in range(grounds.shape[1]):
                cv.putText(img, str(grounds[r, c]), org=np.add(nears[r, c][0], (16, 32)), fontFace=cv.FONT_ITALIC, fontScale=.3,
                           color=(255, 255, 0), lineType=1)
        show(img)


def full_wall():
    # pos = ((378, 214), (430, 266))
    pos = ((386, 214), (440, 266))
    cap = cv.imread('../resources/dungeon/sample.png')
    blur = cv.GaussianBlur(cap, BLUR_VAL, 0)

    nears = roi_area_more(pos)
    points = []
    flags = []
    for g in nears:
        area = blur[g[0][1]:g[1][1], g[0][0]:g[1][0]]
        cnt = np.count_nonzero(filter_nonwall(area))
        points.append(g)
        flags.append(cnt > WALL_THRESHOLD)

    for i, j in points:
        cv.rectangle(blur, i, j, (0, 0, 255), 2)
    for i in range(len(flags)):
        if flags[i]:
            cv.putText(blur, str('X'), org=np.add(points[i][0], (16, 38)), fontFace=cv.FONT_ITALIC, fontScale=1,
                       color=(0, 0, 255), lineType=4)
    show(blur)

    p = points[len(points) - 2]
    print('trap', p)
    show(cut_area(cap, p[0], p[1]))

    # pa = np.array(points).reshape((5, 9, 2, 2))
    fa = np.array(flags).reshape((5, 9))
    return fa


class Point(object):

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __hash__(self):
        return hash(self.row) + hash(self.col)

    def __str__(self):
        return f'P({self.row},{self.col})'


class Graph(object):

    def __init__(self, nparray: np.ndarray):
        self.graph = nparray

    def get(self, p: Point):
        return self.graph.item((p.row, p.col))

    def neighbors(self, p: Point):
        n = [None, None, None, None]
        if p.row - 1 >= 0 and self.get(Point(p.row - 1, p.col)):
            n[0] = Point(p.row - 1, p.col)
        if p.row + 1 <= self.graph.shape[0] - 1 and self.get(Point(p.row + 1, p.col)):
            n[1] = Point(p.row + 1, p.col)
        if p.col - 1 >= 0 and self.get(Point(p.row, p.col - 1)):
            n[2] = Point(p.row, p.col - 1)
        if p.col + 1 <= self.graph.shape[1] - 1 and self.get(Point(p.row, p.col + 1)):
            n[3] = Point(p.row, p.col + 1)
        return n


def bfs(g: np.ndarray):
    frontier = Queue()
    reached = set()
    cost = dict()

    graph = Graph(g)
    # graph = Graph(np.random.randint(10, 99, (5, 9), dtype=np.uint8))
    print(graph.graph)

    role = Point(2, 4)
    print(graph.get(role))

    frontier.put(role)
    reached.add(role)
    cost[role] = 0

    while not frontier.empty():
        cur = frontier.get()
        for p in graph.neighbors(cur):
            if p and p not in reached:
                frontier.put(p)
                reached.add(p)
                cost[p] = cost[cur] + 1

    cost_graph = np.zeros(graph.graph.shape, dtype=np.uint16)
    for e in cost:
        cost_graph.itemset((e.row, e.col), cost[e])
    print(cost_graph)
    return cost_graph


def moving_path():
    path = 'G:\\coding\\python\\workplace\\autokara\\resources\\path\\'
    for i in range(1, 34):
        p = f'{path}cap-{i}.png'
        if not os.path.exists(p):
            continue
        print('recognizing', p)
        img = cv.imread(p)
        reg_ground(img)


if __name__ == '__main__':
    # find_role()
    reg_ground()
    # moving_path()
    # detect_scenes()


