import numpy as np

from kara.instance import KaraInstance
from kara import utils
from kara.constants import ARENA_GENERAL, ARENA_ADVANCED
from script import textocr


class Arena(object):

    def __init__(self, inst: KaraInstance):
        self.inst = inst
        self.karas = []
        self.level = ''

    def start(self):
        self.init_kara()
        self.select_level()
        self.match_battle()

    def init_kara(self):
        self.inst.forward()
        cap, ks = self.inst.sml.capture(), []
        for i in range(3):
            lt = np.array(utils.pos(f'arena.kara.{i}'))
            rb = lt + (78, 28)
            txt = textocr.text_recognize(cap[lt[1]:rb[1], lt[0]:rb[0]])
            if not txt or ':' not in txt:
                raise AssertionError(f'recognize {i} ev error')
            ev = int(txt.split(':')[1])

            lt += (0, 28)
            rb += (0, 28)
            txt = textocr.text_recognize(cap[lt[1]:rb[1], lt[0]:rb[0]])
            if not txt or ':' not in txt:
                raise AssertionError(f'recognize {i} lv error')
            lv = int(txt.split(':')[1])

            ks.append(Kara(ev, lv))
        self.karas = sorted(ks, key=lambda k: k.sort_key(), reverse=True)

    def select_level(self):
        self.inst.forward()
        upmost, level = self.karas[0], ''
        scenario = ARENA_GENERAL if upmost.ev == 0 else ARENA_ADVANCED
        val = upmost.lv if upmost.ev == 0 else upmost.ev
        for i in scenario.keys():
            if val <= i:
                level = ARENA_GENERAL[i]
                break
        if not level:
            raise AssertionError('select level error')
        self.level = level
        self.inst.sml.click(utils.pos(level))

    def match_battle(self):
        self.inst.forward()
        self.inst.sml.click(utils.pos('arena.start'))
        pass


class Kara(object):

    def __init__(self, ev, lv):
        self.ev = ev
        self.lv = lv

    def __str__(self):
        return f'Kara {self.ev} {self.lv}'

    def sort_key(self):
        return self.ev * 10000 + self.lv


if __name__ == '__main__':
    pass
