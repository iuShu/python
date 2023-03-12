import aiofiles
import os
import json
import logging

config_path = '../config.json'
history_path = '../ema_history'
update_config_interval = 5.0
cache = dict()
history = dict()
mt = os.path.getmtime(os.path.join(os.path.dirname(__file__), config_path))

period2ms = {
    '1m': 60,
    '2m': 60 * 2,
    '5m': 60 * 5,
    '10m': 60 * 10,
    '15m': 60 * 15,
    '30m': 60 * 30,
    '1H': 60 * 60,
    '4H': 60 * 60 * 4,
    '1D': 60 * 60 * 4 * 24,
    '1W': 60 * 60 * 4 * 24 * 7,
}


def sys(key=''):
    return _conf()['sys'][key] if key else _conf()['sys']


def trade(inst=''):
    return _conf()['trade'][inst] if inst else _conf()['trade']


def ntf(key=''):
    return _conf()['notifier'][key] if key else _conf()['notifier']


def _conf() -> dict:
    global cache
    if not cache:
        loc = os.path.join(os.path.dirname(__file__), config_path)
        with open(loc, 'r', encoding='utf-8') as f:
            cache = json.load(fp=f)
            _init_logging(cache['log'])
        logging.info(f'loaded config from {loc}')
    return cache


def _init_logging(conf):
    logging.basicConfig(**conf)
    console = logging.StreamHandler()
    console.setLevel(conf['level'])
    console.setFormatter(logging.Formatter(conf['format']))
    logging.root.addHandler(console)


async def watch():
    global cache, mt
    t = os.path.getmtime(config_path)
    if t == mt:
        return

    loc, mt = os.path.join(os.path.dirname(__file__), config_path), t
    async with aiofiles.open(loc, 'r', encoding='utf-8') as f:
        text = await f.read()
        cache = json.loads(s=text)
        logging.info('reloaded config')


def last_ema(inst_id: str) -> tuple:
    global history
    if not history:
        loc = os.path.join(os.path.dirname(__file__), history_path)
        with open(loc, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                pair = line.strip().split('=')
                if len(pair) != 2:
                    logging.error('illegal ema history format')
                    raise SystemExit(1)
                seg = pair[1].strip().split('#')
                history[pair[0]] = seg
    return history[inst_id]


def save_ema(inst_id: str, t: str, val):
    global history
    if not history or not history.get(inst_id):
        return

    history[inst_id] = [t, val]
    loc = os.path.join(os.path.dirname(__file__), history_path)
    with open(loc, 'w', encoding='utf-8') as f:
        f.writelines([f'{k}={v[0]}#{v[1]}\n' for k, v in history.items()])
    logging.info('wrote back ema history')


if __name__ == '__main__':
    # print(sys('apikey'))
    pass
