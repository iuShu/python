import os


class ConfigContext(object):

    def __init__(self):
        self.paths = []
        self.repo = dict()
        self.suffix = '.properties'
        self.scan()
        self.load()

    def scan(self, root='../'):
        for d in os.listdir(root):
            if d.startswith('.') or d.startswith('__'):
                continue
            elif d.endswith(self.suffix):
                self.paths.append(f'{root}{d}')
                continue
            elif os.path.isdir(f'{root}{d}'):
                self.scan(root=f'{root}{d}/')
                # print(f'{root}{d}/')

    def load(self):
        for p in self.paths:
            self.repo[config_name(p)] = Configuration(p)

    def get(self, name: str, key: str):
        conf = self.repo.get(name)
        return conf.props.get(key) if conf else None

    def getint(self, name: str, key: str):
        val = self.get(name, key)
        return int(val) if val else 0


class Configuration(object):

    def __init__(self, path: str):
        self.path = path
        self.props = dict()
        self.load()

    def load(self):
        with open(self.path) as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    seg = line.split('=')
                    self.props[seg[0]] = seg[1]

    def __str__(self):
        return self.path + '\n' + self.props.__str__()


def config_name(path: str):
    seg = path.split('/')
    return seg[len(seg) - 1].split('.')[0]


SINGLETON = ConfigContext()


def instance():
    return SINGLETON


if __name__ == '__main__':
    config = ConfigContext()


