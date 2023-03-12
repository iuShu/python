import time
import logging
import aiofiles

from src.listener import ZeroListener
from src.calc import sub, mlt, div

sp_diff_log = '../sp-diff.log'
spot_px_log = '../spot-px.log'
perp_px_log = '../perp-px.log'
log_format = '%s %s %s %s\n'    # ts lastPx askPx bidPx
write_interval = 10             # sec


class SPDiff:

    def __init__(self):
        self._repo = []
        self._write_ts = int(time.time())
        self._spot_px = .0
        self._perp_px = .0
        self._max_diff_pct = .0

    async def report(self, t: str, px: float):
        if t == 'spot':
            self._spot_px = px
        else:
            self._perp_px = px

        now = time.time()
        if self._spot_px and self._perp_px:
            rate = calc_rate(self._spot_px, self._perp_px)
            if rate > self._max_diff_pct:
                self._max_diff_pct = rate
                self._repo.append((int(now * 1000), self._spot_px, self._perp_px, rate))
        if int(now) - self._write_ts >= write_interval and self._repo:
            self._write_ts = int(now)
            lines = [log_format % e for e in self._repo]
            self._repo.clear()
            async with aiofiles.open(sp_diff_log, 'a', encoding='utf-8') as f:
                await f.writelines(lines)
                logging.info('wrote %d log' % len(lines))


class SpotListener(ZeroListener):

    def __init__(self, inst: str, inst_id: str, inst_type: str, sp: SPDiff):
        super().__init__(inst, inst_id, inst_type)
        self._repo = []
        self._write_ts = int(time.time())
        self._sp = sp

    def channel(self) -> str:
        return 'tickers'

    def prepare(self):
        pass

    async def consume(self, data: dict):
        body = data['data'][0]
        last = body['last']
        await self._sp.report('spot', float(last))
        self._repo.append((body['ts'], last, body['askPx'], body['bidPx']))

        now = time.time()
        if int(now) - self._write_ts >= write_interval and self._repo:
            self._write_ts = int(now)
            lines = [log_format % e for e in self._repo]
            self._repo.clear()
            async with aiofiles.open(spot_px_log, 'a', encoding='utf-8') as f:
                await f.writelines(lines)


class PerpListener(ZeroListener):

    def __init__(self, inst: str, inst_id: str, inst_type: str, sp: SPDiff):
        super().__init__(inst, inst_id, inst_type)
        self._repo = []
        self._write_ts = int(time.time())
        self._sp = sp

    def channel(self) -> str:
        return 'tickers'

    def prepare(self):
        pass

    async def consume(self, data: dict):
        body = data['data'][0]
        last = body['last']
        await self._sp.report('perp', float(last))
        self._repo.append((body['ts'], last, body['askPx'], body['bidPx']))

        now = time.time()
        if int(now) - self._write_ts >= write_interval and self._repo:
            self._write_ts = int(now)
            lines = [log_format % e for e in self._repo]
            self._repo.clear()
            async with aiofiles.open(perp_px_log, 'a', encoding='utf-8') as f:
                await f.writelines(lines)


def calc_rate(from_px: float, to_px: float) -> float:
    if not from_px and not to_px:
        return .0
    elif not from_px or not to_px:
        return 1.0
    else:
        return round(abs(mlt(div(sub(from_px, to_px), from_px), 100)), 2)
