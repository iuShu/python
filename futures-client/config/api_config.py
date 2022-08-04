import os.path
import json


def conf(platform: str):
    loc = os.path.join(os.path.dirname(__file__), 'apikey.json')
    with open(loc, 'r', encoding='utf-8') as f:
        raw = json.load(fp=f)
        return raw[platform]


if __name__ == '__main__':
    # print(load_config())
    print(conf('okx'))

