import random
from queue import Queue

import numpy as np

GRID_WIDTH = 9
GRID_HEIGHT = 5
CENTER_GRID = np.array((2, 4))

ROLE = 1
SEARCHED = 5
WALL = 99


class Grids(object):

    def __init__(self, g: np.ndarray):
        self.uid = random.random()
        self.graph = g
        self.role = find_role(g)
        self.footprints = []
        self.searched = []

    def reach(self, p):
        self.footprints.append(p)

    def search(self, p):
        self.searched.append(p)

    def rem_role(self):
        if self.graph.item(self.role) == ROLE:
            self.graph.itemset(self.role, SEARCHED)

    def neighbors(self, p):
        return [self.up(p), self.down(p), self.left(p), self.right(p)]

    def up(self, p):
        if p[0] - 1 >= 0:
            return p[0] - 1, p[1]

    def down(self, p):
        if p[0] + 1 <= self.graph.shape[0] - 1:
            return p[0] + 1, p[1]

    def left(self, p):
        if p[1] - 1 >= 0:
            return p[0], p[1] - 1

    def right(self, p):
        if p[1] + 1 <= self.graph.shape[1] - 1:
            return p[0], p[1] + 1

    def last(self):
        return self.footprints[len(self.footprints) - 1]


class Dungeon(object):

    def __init__(self):
        self.main = None    # the grid contained role: Grids.uid
        self.steps = []     # step's record: Grids.uid
        self.repo = dict()

    def forward(self, g: Grids):
        if self.steps:
            # self.merge_grids(g)
            pass
        else:
            g.searched.append(g.role)
            g.graph.itemset(g.role, SEARCHED)
        self.repo[g.uid] = g
        self.main = g.uid

    def merge_grids(self, new: Grids):
        g = self.repo[self.main]
        dis = np.subtract(CENTER_GRID, g.last())
        # dis = np.subtract(CENTER_GRID, (2, 1))
        olt = [0 if dis[0] > 0 else abs(dis[0]), 0 if dis[1] > 0 else abs(dis[1])]
        orb = np.subtract((GRID_HEIGHT, GRID_WIDTH), (abs(dis[0]), abs(dis[1])))
        orb = np.subtract(orb, (1, 1))
        orb = np.add(orb, np.array(olt))
        # print('old', olt, orb)
        nlt = np.add(olt, dis)
        nrb = np.add(orb, dis)
        # print('new', nlt, nrb)
        new.graph[nlt[0]:nrb[0]+1, nlt[1]:nrb[1]+1] = g.graph[olt[0]:orb[0]+1, olt[1]:orb[1]+1]
        # print(new.graph)
        for p in g.footprints:
            fp = np.add(p, dis)
            if np.all(np.greater(fp, (-1, -1))) and np.all(np.less(fp, (GRID_HEIGHT, GRID_WIDTH))):
                new.reach(fp)
        for p in g.searched:
            s = np.add(p, dis)
            if np.all(np.greater(s, (-1, -1))) and np.all(np.less(s, (GRID_HEIGHT, GRID_WIDTH))):
                new.search(s)

    def next_step(self):
        grids = self.repo[self.main]
        graph = grids.graph
        role = grids.role
        if not role:
            raise RuntimeError('can not found role in main grids')

        stack = grids.searched.copy()
        stack.insert(0, role)
        stack.insert(0, role)
        cur = role
        while True:
            prev = len(stack)
            nears = grids.neighbors(cur)
            for n in nears:
                if n is None:
                    break
                val = 0 if n is None else graph.item((n[0], n[1]))
                if n and val != WALL and val != SEARCHED:
                    stack.append(n)
                    grids.searched.append(n)
                    graph.itemset((n[0], n[1]), SEARCHED)
                    cur = n
                    break
            if len(stack) == prev:
                if None in nears:
                    break
                if len(stack):
                    cur = stack.pop()
                else:
                    return None     # no exit

        if not len(self.steps):
            grids.reach(role)
        grids.reach(cur)
        grids.rem_role()
        self.steps.append(grids.uid)
        return cur

    def backward(self):

        pass


def find_role(grids: np.ndarray):
    r = np.where(grids == ROLE)
    return r[0][0], r[1][0]


def generate():
    one = np.zeros((5, 9), dtype=np.uint8)
    [one.itemset((0, i), WALL) for i in range(5)]
    [one.itemset((0, 6 + i), WALL) for i in range(3)]
    [one.itemset((i, 0), WALL) for i in range(5)]
    [one.itemset((4, i), WALL) for i in range(5)]
    one.itemset((1, 4), WALL)
    one.itemset((2, 4), ROLE)
    one.itemset((1, 6), WALL)
    [one.itemset((3, 4 + i), WALL) for i in range(3)]
    [one.itemset((4, 6 + i), WALL) for i in range(3)]

    two = np.zeros((5, 9), dtype=np.uint8)
    [two.itemset((i, 3), WALL) for i in range(4)]
    [two.itemset((i, 5), WALL) for i in range(4)]
    [two.itemset((2, i), WALL) for i in range(4)]
    [two.itemset((2, 5 + i), WALL) for i in range(4)]
    two.itemset((3, 0), WALL)
    two.itemset((4, 0), WALL)

    three = np.zeros((5, 9), dtype=np.uint8)
    [three.itemset((0, 1+i), WALL) for i in range(3)]
    [three.itemset((0, 5+i), WALL) for i in range(4)]
    [three.itemset((4, i), WALL) for i in range(4)]
    [three.itemset((4, 5+i), WALL) for i in range(4)]
    [three.itemset((2+i, 3), WALL) for i in range(3)]
    [three.itemset((2+i, 5), WALL) for i in range(3)]
    three.itemset((1, 8), WALL)

    four = np.zeros((5, 9), dtype=np.uint8)
    [four.itemset((0, 3+i), WALL) for i in range(3)]
    [four.itemset((2, 1+i), WALL) for i in range(3)]
    [four.itemset((2, 5+i), WALL) for i in range(4)]
    [four.itemset((i, 8), WALL) for i in range(2)]
    four.itemset((3, 8), WALL)
    four.itemset((1, 3), WALL)
    four.itemset((4, 3), WALL)
    four.itemset((1, 5), WALL)
    four.itemset((4, 5), WALL)

    five = np.zeros((5, 9), dtype=np.uint8)
    [five.itemset((2, 3+i), WALL) for i in range(3)]
    [five.itemset((4, 1+i), WALL) for i in range(3)]
    [five.itemset((4, 5+i), WALL) for i in range(4)]
    [four.itemset((2+i, 8), WALL) for i in range(2)]
    five.itemset((3, 3), WALL)
    five.itemset((3, 5), WALL)
    return one, two, three, four


def test():
    dg = Dungeon()
    one, two, three, four = generate()
    grid1 = Grids(one)

    dg.forward(grid1)
    nxt = dg.next_step()
    # print(dg.steps, dg.main)
    # print(grid1.uid)
    # print(grid1.role)
    # print(grid1.graph)
    print(f'click next {nxt} in {grid1.uid}')

    two.itemset((2, 4), ROLE)
    grid2 = Grids(two)
    dg.forward(grid2)
    nxt = dg.next_step()
    # print(dg.steps, dg.main)
    # print(grid2.uid)
    # print(grid2.role)
    # print(grid2.graph)
    print(f'click next {nxt} in {grid2.uid}')

    three.itemset((2, 4), ROLE)
    grid3 = Grids(three)
    dg.forward(grid3)
    nxt = dg.next_step()
    # print(dg.steps, dg.main)
    # print(grid3.uid)
    # print(grid3.role)
    # print(grid3.graph)
    print(f'click next {nxt} in {grid3.uid}')

    four.itemset((2, 4), ROLE)
    grid4 = Grids(four)
    dg.forward(grid4)
    nxt = dg.next_step()
    print(dg.steps, dg.main)
    print(grid4.uid)
    print(grid4.role)
    print(grid4.graph)
    print(f'click next {nxt} in {grid4.uid}')


def test1():
    matrix = np.zeros((5, 9), dtype=np.uint8)
    matrix.itemset((2, 4), ROLE)
    [matrix.itemset((i, 3), WALL) for i in range(5)]
    [matrix.itemset((i, 5), WALL) for i in range(5)]
    matrix.itemset((0, 4), WALL)
    matrix.itemset((4, 4), WALL)
    # matrix.itemset((2, 3), 0)
    # matrix.itemset((2, 5), 0)
    print(matrix)
    grids = Grids(matrix)
    dg = Dungeon()
    dg.forward(grids)
    nxt = dg.next_step()
    print(nxt)
    print(grids.graph)


if __name__ == '__main__':
    test()
    # test1()




