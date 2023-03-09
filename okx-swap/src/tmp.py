from calc import add, sub, mlt, div
import pprint


def analysis():
    repo = {}
    with open(r'E:\download\okx-swap.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        batch = {}
        for line in lines:
            if 'order filled at' in line:
                batch = order_fill(line, batch)
            elif 'close at' in line:
                order_close(line, batch)
                if not repo.get(batch['inst']):
                    repo[batch['inst']] = []
                repo[batch['inst']].append(batch)
                batch = {}
    # pprint.pprint(repo)
    print(len(repo['CFX']))

    idx, stat = 1, [.0, 0, 0, 0]
    for k, batches in repo.items():
        for batch in batches:
            desc = [str(idx), batch['pos_side'], str(batch['pnl'])]
            for order in batch['orders']:
                desc.append(str(order['px']))
            desc.append(str(calc_rate(batch['avg'], float(desc[-1]), batch['lever'])) + '%')
            if batch['pnl'] < 0:
                desc.append('x')
            idx += 1
            print(' '.join(['%10s' for _ in range(0, len(desc))]) % tuple(desc))

            stat[0] = add(batch['pnl'], stat[0])
            stat[1] = len(batch['orders']) - 1 + stat[1]
            if batch['pnl'] > 0:
                stat[2] += 1
            elif batch['pnl'] < 0:
                stat[3] += 1
    print('ttl pnl is', stat[0])
    print('ttl ord is', stat[1])
    print('ttl tpo is', stat[2])
    print('ttl slo is', stat[3])


def order_fill(line: str, batch: dict) -> dict:
    arr = line[line.rfind(': ') + 2:].split(' ')
    if len(arr) != 9:
        print('unexpected match line at', line)
        raise SystemExit(1)
    order = _order(line[:line.find(',') + 4], float(arr[4]), float(arr[5]), float(arr[7].split('=')[1]), float(arr[8].split('=')[1]))
    if not batch:
        batch = _batch(arr[0], arr[6])
    batch['ttl_sz'] = add(batch['ttl_sz'], order['sz'])
    batch['orders'].append(order)
    return batch


def order_close(line: str, batch: dict):
    arr = line[line.rfind(': ') + 2:].split(' ')
    if len(arr) != 9:
        print('unexpected match line at', line)
        raise SystemExit(1)
    order = _order(line[:line.find(',') + 4], float(arr[4]), float(arr[5]))
    batch['avg'] = float(arr[7].split('=')[1])
    max_px = arr[8].split('=')[1]
    batch['mpx'] = float(max_px[:max_px.find('(')])
    batch['st'] = batch['orders'][0]['t']
    batch['et'] = order['t']
    # batch['pnl'] = float(arr[6].split('=')[1])
    batch['pnl'] = calc_pnl(batch['avg'], order['px'], batch['ttl_sz'], batch['pos_side'])
    batch['orders'].append(order)


def calc_pnl(avg: float, cpx: float, ttl_sz: float, pos_side: str) -> float:
    if pos_side == 'long':
        diff = sub(cpx, avg)
    else:
        diff = sub(avg, cpx)
    return float(mlt(diff, ttl_sz))


def calc_rate(from_px: float, to_px: float, lever=1.0) -> float:
    return round(abs(mlt(mlt(div(sub(from_px, to_px), from_px), lever), 100)), 2)


def _batch(inst, pos_side, lv=75, fv=10, st='', et='', avg=.0, mpx=.0) -> dict:
    return {
        'st': st,
        'et': et,
        'inst': inst,
        'pos_side': pos_side,
        'lever': lv,
        'face_value': fv,
        'ttl_sz': .0,
        'avg': avg,
        'mpx': mpx,
        'pnl': .0,
        'orders': [],
    }


def _order(t, px, sz, nxt=.0, sl=.0) -> dict:
    return {
        't': t,
        'px': px,
        'sz': sz,
        'nxt': nxt,
        'sl': sl
    }


if __name__ == '__main__':
    analysis()
    pass
