import os.path
import json


def conf(platform: str):
    loc = os.path.join(os.path.dirname(__file__), '../resources/apikey.json')
    with open(loc, 'r', encoding='utf-8') as f:
        raw = json.load(fp=f)
        return raw[platform]


def db_conf(db_type: str):
    loc = os.path.join(os.path.dirname(__file__), '../resources/db.json')
    with open(loc, 'r', encoding='utf-8') as f:
        raw = json.load(fp=f)
        return raw[db_type]


def notify_conf(name: str):
    loc = os.path.join(os.path.dirname(__file__), '../resources/notify.json')
    with open(loc, 'r', encoding='utf-8') as f:
        raw = json.load(fp=f)
        return raw[name]


if __name__ == '__main__':
    # print(load_config())
    print(conf('okx'))
    print(db_conf('mysql'))

