
from kara.constants import *
from kara.simulator import Simulator


class Dungeon(object):

    def __init__(self, sml: Simulator, power, role):
        self.sml = sml
        self.power = power
        self.role = role
        self.karas = [role]
        self.level = 0
        self.select_level()
        self.init_healthy()

    def select_level(self):
        pass

    def init_healthy(self):
        pass

    def start(self):
        pass


class Kara(object):

    def __init__(self, pics):
        self.pics = pics
        self.healthy = 0

