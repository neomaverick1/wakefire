"""Azar, drawn the way 16-bit sprites are drawn: every pixel of his three views placed by hand on
a grid (azar_v3.txt, one letter per pixel). The animations are made the way sprite artists make
them from a key pose: a leg lifted, a body bob, lids lowered, the crest flickering, the khopesh
and its swing drawn over the top.

    python3 azar.py            export Resources/Sprites/azar.png/.json (same animations as before)
    python3 azar.py preview    a sheet of key frames
"""
import os, sys, json, math
import numpy as np
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas

PREVIEWS = os.environ.get('WF_PREVIEWS', '/tmp/wakefire-previews')
os.makedirs(PREVIEWS, exist_ok=True)
OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Sprites'
GRIDS = '/srv/Wakefire/Art/pixel/azar_v3.txt'
W = 26
CELL, FX, FY = 80, 40, 62


def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


PAL = {
    'O': '#1c1024',
    'y': '#fff6c4', 'Y': '#ffd447', 'F': '#ff9a2a', 'R': '#e85a1e', 'r': '#b8301a', 'Q': '#6e1612',
    'W': '#fff6cc', 'B': '#f6c656', 'b': '#d9952f', 'n': '#a8621f', 'N': '#6a3a16',
    'S': '#ffdcb8', 's': '#f0aa7c', 'k': '#c0754e', 'K': '#7e4430', 'E': '#ffffff', 'P': '#241a34',
    'w': '#b89ac8', 'h': '#8a5a44',
    'L': '#9ccaff', 'U': '#5a8ae8', 'u': '#3456b8', 'V': '#1e2c78',
    'C': '#ff7058', 'c': '#d8342e', 'x': '#96182a', 'X': '#560e1e',
    'l': '#c08850', 'm': '#7e5030', 'M': '#46281a', 'G': '#ffe27a', 'g': '#d8a032', 'Z': '#fff6c0', 'z': '#ffc040',
}
RGB = {k: hx(v) for k, v in PAL.items()}


def load():
    blocks, cur = {}, None
    for line in open(GRIDS).read().splitlines():
        if line.startswith('#') or not line.strip():
            continue
        if line.startswith('== '):
            cur = line[3:].strip(); blocks[cur] = []; continue
        r = line.rstrip()
        if '|' in r:
            c, body = r.split('|', 1)
            r = ('.' * int(c) + body).ljust(W, '.')
        if len(r) < W:
            st = (W - len(r)) // 2
            r = '.' * st + r + '.' * (W - st - len(r))
        blocks[cur].append(list(r[:W]))
    return blocks


G = load()
SPLIT = {'front': (20, 29), 'back': (20, 29), 'side': (19, 28)}      # head ends, legs begin


def blank(h):
    return [['.'] * W for _ in range(h)]


def paint(cv, rows, ox, oy, remap=None):
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '.':
                continue
            if remap and ch in remap:
                ch = remap[ch]
            xx, yy = ox + x, oy + y
            if 0 <= xx < cv.w and 0 <= yy < cv.h:
                cv.a[yy, xx] = RGB[ch]


def crest_map(k):
    """Three states of the flame crest, cycled frame to frame."""
    return [None, {'y': 'Y', 'Y': 'y', 'F': 'Y', 'R': 'F'}, {'F': 'R', 'R': 'r', 'Y': 'F', 'r': 'R'}][k % 3]


def sub(rows, i, old, new):
    rows[i] = list(''.join(rows[i]).replace(old, new))


def eyes(rows, view, state):
    rows = [list(r) for r in rows]
    if view == 'front':
        if state == 'half':
            sub(rows, 15, 'EP', 'KP'); sub(rows, 15, 'PE', 'PK')
        elif state == 'shut':
            sub(rows, 15, 'EP', 'KK'); sub(rows, 15, 'PE', 'KK')
        elif state == 'wide':
            sub(rows, 14, 'SKKKSSSSKKKS', 'SSKSSSSSSKSS')
    elif view == 'side':
        if state == 'half':
            sub(rows, 13, 'PE', 'PK')
        elif state == 'shut':
            sub(rows, 13, 'PE', 'KK')
    return rows


def mouth_open(rows, view):
    rows = [list(r) for r in rows]
    if view == 'front':
        sub(rows, 17, 'hhhKKhhh', 'hhOOOOhh'); sub(rows, 18, 'khhhhhhk', 'khOOOOhk')
    elif view == 'side':
        sub(rows, 15, 'hhhhSk', 'hhOOSk')
    return rows


def parts(view):
    g = G[view]
    a, b = SPLIT[view]
    return g[:a], g[a:b], g[b:]


# ----------------------------------------------------------------------------- legs
def legs_lift(legrows, view, lift_left=0, lift_right=0):
    """Front and back: a stepping foot rises (the kilt hides the top of the leg)."""
    h = len(legrows)
    out = blank(h)
    mid = 12 if view == 'front' else 13
    for y in range(h):
        for x in range(W):
            ch = legrows[y][x]
            if ch == '.':
                continue
            if not (6 < x < 18):
                out[y][x] = ch
                continue
            lift = lift_left if x < mid else lift_right
            yy = y - lift
            if 0 <= yy < h and out[yy][x] == '.':
                out[yy][x] = ch
    return out


def side_legs(near_dx=0, far_dx=0, near_lift=0, far_lift=0):
    """Side view: each leg a two-pixel column of thigh, greave and sandal, sheared by the stride."""
    h = 9
    out = blank(h)

    def leg(hip_x, dx, lift, far):
        skin = ['s', 'k'] if far else ['S', 'k']
        greave = [['b', 'n'], ['b', 'n'], ['n', 'N']] if far else [['B', 'b'], ['B', 'n'], ['b', 'n']]
        rows = [skin, skin] + greave
        for r, pair in enumerate(rows):
            t = (r + 1) / (len(rows) + 1)
            x = hip_x + int(round(dx * t))
            y = r - (lift if r >= 2 else 0)
            for k, ch in enumerate(pair):
                if 0 <= y < h and 0 <= x + k < W:
                    out[y][x + k] = ch
        fx, fy = hip_x + dx, len(rows) - lift
        for k in range(4):
            if 0 <= fy < h and 0 <= fx + k < W:
                out[fy][fx + k] = ('m' if far else 'M') if k < 3 else 'M'
            if 0 <= fy + 1 < h and 0 <= fx + k < W:
                out[fy + 1][fx + k] = 'M'
    leg(12, far_dx, far_lift, True)
    leg(14, near_dx, near_lift, False)
    return out


def outline_rows(rows):
    h = len(rows)
    out = [list(r) for r in rows]
    for y in range(h):
        for x in range(W):
            if rows[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < h and rows[yy][xx] not in '.O':
                    out[y][x] = 'O'
                    break
    return out


# ----------------------------------------------------------------------------- the khopesh and its swing
KHOPESH = {
    'right': ["OOO.........",
              "OmMOOOOOO...",
              "OOOWWWBBbOO.",
              "...OOOObbBnO",
              "........ObnO",
              ".........OO."],
    'up': ["....OO", "...ObO", "..ObBO", ".OBWO.", ".OWBO.", ".OWBO.", "OOOO..", "OmO...", "OMO...", "OOO..."],
    'down': ["OOO...", "OMO...", "OmO...", "OOOO..", ".OWBO.", ".OWBO.", ".OBbO.", "..ObnO", "...OnO", "....OO"],
}


def flip_rows(rows):
    return [list(reversed(r)) for r in rows]


def smear(cv, cx, cy, r0, r1, a0, a1, fade=1.0):
    """The swing: a crescent of light along the blade's path, thickest at the leading end."""
    steps = 48
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        thick = (r1 - r0) * (0.2 + 0.8 * t) * fade
        for k in range(int(thick) + 1):
            if t < 0.3 and k > 0:
                continue
            r = r1 - k
            x, y = int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r))
            if 0 <= x < cv.w and 0 <= y < cv.h:
                cv.a[y, x] = RGB['y'] if k == 0 else RGB['Y'] if k < 2 else RGB['F']


# ----------------------------------------------------------------------------- composing a frame
def frame(view, k=0, bob=0, lift=(0, 0), stride=None, eye='open', mouth=False, head_dy=0, lean=0,
          blade=None, swing=None, cape=0, arms_up=False, lantern_up=0, squash=0, flash=False, lie=False):
    cv = Canvas(CELL, CELL)
    head, body, legs = parts(view)
    head = eyes(head, view, eye)
    if mouth:
        head = mouth_open(head, view)
    ox = FX - 13 + lean
    if view == 'side' and stride is not None:
        legs = outline_rows(side_legs(*stride))
        ly = FY - 7
        oy = FY - 7 - len(body) - len(head)
    else:
        if view != 'side':
            legs = legs_lift(legs, view, *lift)
        oy = FY - len(legs) - len(body) - len(head)
        ly = oy + len(head) + len(body)
    paint(cv, legs, ox, ly)
    if view == 'side' and cape:
        body = [list(r) for r in body]
        for y in range(5, len(body)):
            row = body[y]
            cols = [x for x in range(W) if row[x] in 'CcxX' and x < 10]
            if cols:
                x0 = min(cols)
                row[x0] = 'O'
                if x0 - 1 >= 0 and row[x0 - 1] == 'O':
                    row[x0 - 1] = '.'
    by = oy + len(head) + bob
    paint(cv, body, ox, by)
    hy = oy + bob + head_dy
    paint(cv, head, ox, hy, remap=crest_map(k))
    if arms_up:
        # both hands raised over the crest, holding up whatever he has found
        top = hy - 4
        arms = [((5, len(head) + 2), (9, 0)), ((20, len(head) + 2), (16, 0))] if view != 'side' else [((13, len(head) + 2), (15, 0))]
        layer = Canvas(CELL, CELL)
        for (sx, sy), (ex, ey) in arms:
            n = max(abs(ex - sx), abs(ey - sy))
            for i in range(n + 1):
                t = i / n
                x = ox + int(round(sx + (ex - sx) * t)); y = hy + int(round(sy + (ey - sy) * t)) - 4
                c1, c2 = (RGB['S'], RGB['k']) if t > 0.35 else (RGB['B'], RGB['n'])
                if 0 <= y < CELL:
                    layer.a[y, x] = c1; layer.a[y, x + 1] = c2
            hx_, hy_ = ox + ex, hy + ey - 6
            for (dx, dy) in ((0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (2, 1)):
                if 0 <= hy_ + dy < CELL:
                    layer.a[hy_ + dy, hx_ + dx] = RGB['S'] if dy == 0 else RGB['s']
        layer.outline(RGB['O'])
        cv.blit(layer, 0, 0)
    if blade:
        rows = [list(l) for l in KHOPESH[blade[0]]]
        if blade[3]:
            rows = flip_rows(rows)
        paint(cv, rows, ox + blade[1], by + blade[2])
    if swing:
        smear(cv, ox + swing[0], by + swing[1], swing[2], swing[3], swing[4], swing[5], swing[6] if len(swing) > 6 else 1.0)
    if lantern_up:
        lx, ly2 = ox + (19 if view != 'side' else 17), by - lantern_up
        for (dx, dy, c) in ((0, 0, 'O'), (1, 0, 'g'), (2, 0, 'O'), (-1, 1, 'O'), (0, 1, 'Z'), (1, 1, 'Z'), (2, 1, 'z'), (3, 1, 'O'),
                            (-1, 2, 'O'), (0, 2, 'z'), (1, 2, 'Z'), (2, 2, 'z'), (3, 2, 'O'), (0, 3, 'O'), (1, 3, 'g'), (2, 3, 'O')):
            if 0 <= lx + dx < cv.w and 0 <= ly2 + dy < cv.h:
                cv.a[ly2 + dy, lx + dx] = RGB[c]
    if squash:
        a = cv.a.copy()
        out = np.zeros_like(a)
        drop = max(2, 6 - squash)
        dst = FY - 1
        for y in range(FY - 1, -1, -1):
            if y > FY - 32 and (FY - y) % drop == 0:
                continue
            out[dst] = a[y]
            dst -= 1
            if dst < 0:
                break
        cv.a = out
    if lie:
        rot = np.rot90(cv.a, -1)
        out = np.zeros_like(cv.a)
        ys, xs = np.nonzero(rot[:, :, 3])
        if len(ys):
            dy = FY - 1 - ys.max()
            dx = FX - int(xs.mean())
            for y, x in zip(ys, xs):
                ty, tx = y + dy, x + dx
                if 0 <= ty < CELL and 0 <= tx < CELL:
                    out[ty, tx] = rot[y, x]
        cv.a = out
    if flash:
        m = cv.a[:, :, 3] > 0
        cv.a[m, :3] = (cv.a[m, :3].astype(np.int32) * 0.3 + 255 * 0.7).astype(np.uint8)
    return cv


# ----------------------------------------------------------------------------- the animations
WALK_FB = [(0, 0), (2, 0), (1, 0), (0, 0), (0, 0), (0, 2), (0, 1), (0, 0)]
WALK_SIDE = [(4, -3, 0, 0), (2, -1, 1, 0), (0, 0, 2, 0), (-2, 2, 1, 0), (-3, 4, 0, 0), (-1, 2, 0, 1), (0, 0, 0, 2), (2, -2, 0, 1)]


def blade_for(view, phase):
    if view == 'side':
        return {'wind': ('up', 4, -12, False), 'strike': ('right', 15, 1, False), 'follow': ('down', 16, 2, False)}[phase]
    if view == 'front':
        return {'wind': ('up', 19, -12, False), 'strike': ('right', 13, 4, False), 'follow': ('down', 4, 3, True)}[phase]
    return {'wind': ('up', 2, -12, True), 'strike': ('right', 1, -8, True), 'follow': ('down', 19, -4, False)}[phase]


def swing_for(view, strength=1.0):
    if view == 'side':
        return (14, 0, 9, 16, -110, 60, strength)
    if view == 'front':
        return (13, 4, 9, 16, -30, 200, strength)
    return (13, -2, 9, 16, 200, 340, strength)


def frames_for(anim, view, n):
    F = []
    for i in range(n):
        if anim == 'idle':
            F.append(frame(view, k=i, bob=1 if i in (1, 2) else 0))
        elif anim == 'run':
            if view == 'side':
                F.append(frame(view, k=i, stride=WALK_SIDE[i % 8], bob=-1 if i % 4 == 2 else 0, cape=i % 2))
            else:
                F.append(frame(view, k=i, lift=WALK_FB[i % 8], bob=-1 if i % 4 in (1, 2) else 0))
        elif anim in ('attack1', 'attack2', 'attack3'):
            strike = 3 if anim == 'attack3' else 2
            if i < strike:
                F.append(frame(view, k=i, blade=blade_for(view, 'wind'), lean=-1 if view == 'side' else 0, bob=1 if i == strike - 1 else 0))
            elif i == strike:
                F.append(frame(view, k=i, blade=blade_for(view, 'strike'), swing=swing_for(view, 1.0), lean=2 if view == 'side' else 0))
            elif i == strike + 1:
                F.append(frame(view, k=i, blade=blade_for(view, 'follow'), swing=swing_for(view, 0.5), lean=1 if view == 'side' else 0))
            else:
                F.append(frame(view, k=i, blade=blade_for(view, 'follow')))
        elif anim == 'roll':
            sq = [1, 2, 3, 3, 3, 3, 3, 2, 1, 0][i % 10]
            F.append(frame(view, k=i, squash=sq, lean=(i - 5) // 2 if view == 'side' else 0))
        elif anim == 'hurt':
            F.append(frame(view, k=i, flash=i == 0, eye='wide', lean=-2 if view == 'side' else 0, bob=-1))
        elif anim == 'death':
            if i < 2:
                F.append(frame(view, k=i, eye='wide', flash=i == 0))
            elif i < 4:
                F.append(frame(view, k=i, eye='half', squash=2 + (i - 2)))
            else:
                F.append(frame('side', k=i, eye='shut', lie=True))
        elif anim == 'nod':
            F.append(frame(view, k=i, eye=['half', 'shut', 'shut'][i], head_dy=[0, 1, 2][i]))
        elif anim == 'wake':
            F.append(frame(view, k=i, eye=['shut', 'wide', 'wide', 'open'][i], head_dy=[2, -1, 0, 0][i], bob=[1, -1, 0, 0][i]))
        elif anim == 'use':
            F.append(frame(view, k=i, lantern_up=[6, 12, 12][i]))
        elif anim == 'itemget':
            F.append(frame(view, k=i, arms_up=True, eye='wide'))
        elif anim == 'push':
            if view == 'side':
                nd, fd, nl, fl = WALK_SIDE[(i * 2) % 8]
                F.append(frame(view, k=i, stride=(nd // 2, fd // 2, nl, fl), lean=2, bob=1))
            else:
                F.append(frame(view, k=i, lift=WALK_FB[(i * 2) % 8], bob=1))
        elif anim == 'block':
            F.append(frame(view, k=i, blade=blade_for(view, 'strike'), eye='wide'))
        elif anim == 'doze':
            F.append(frame(view, k=i, eye='shut', head_dy=[1, 1, 2, 2, 2, 1, 1, 2, 2][i], bob=1 if i % 3 == 0 else 0))
        elif anim == 'yawn':
            F.append(frame(view, k=i, eye='shut' if 2 <= i <= 5 else 'half', mouth=2 <= i <= 5, head_dy=-1 if 2 <= i <= 5 else 0))
        elif anim == 'shrug':
            F.append(frame(view, k=i, eye='half', bob=-1))
        elif anim == 'point':
            F.append(frame(view, k=i, blade=blade_for(view, 'strike')))
        elif anim == 'sigh':
            F.append(frame(view, k=i, eye='half', bob=1 + i))
        elif anim == 'idle_nod':
            F.append(frame(view, k=i, eye=['open', 'half', 'shut', 'shut', 'wide'][i], head_dy=[0, 1, 2, 3, 0][i]))
        else:
            F.append(frame(view, k=i))
    return F


VIEW = {'down': 'front', 'left': 'side', 'up': 'back'}


def export():
    from PIL import Image
    old = json.load(open(f'{OUT}/azar.json'))
    rows = []
    for a in old['anims']:
        view = VIEW[a['dir']]
        fr = frames_for(a['name'], view, a['frames'])
        if a['dir'] == 'left':
            fl = []
            for f in fr:
                g = Canvas(CELL, CELL); g.a[:, :] = f.a[:, ::-1]; fl.append(g)
            fr = fl
        rows.append((a, fr))
    Wd = max(len(r[1]) for r in rows) * CELL
    img = Image.new('RGBA', (Wd, len(rows) * CELL), (0, 0, 0, 0))
    meta = {"size": CELL, "pivot": [FX, FY], "anims": []}
    for ri, (a, fr) in enumerate(rows):
        for ci, f in enumerate(fr):
            img.paste(f.image(), (ci * CELL, ri * CELL))
        meta["anims"].append({"name": a['name'], "dir": a['dir'], "row": ri, "frames": len(fr)})
    img.save(f'{OUT}/azar.png')
    json.dump(meta, open(f'{OUT}/azar.json', 'w'))
    print('azar', img.size, len(rows), 'rows')


def preview(names, path):
    from PIL import Image, ImageDraw, ImageFont
    Z = 4
    blocks = []
    for nm in names:
        an, dr, n = nm.split(':')
        blocks.append((nm, frames_for(an, VIEW[dr], int(n))))
    cols = max(len(b[1]) for b in blocks)
    cw, ch = 48, 54
    out = Image.new('RGB', (150 + cols * (cw * Z + 4), 40 + len(blocks) * (ch * Z + 4)), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - Azar v3 animations', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22))
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    for r, (label, fr) in enumerate(blocks):
        y = 38 + r * (ch * Z + 4)
        d.text((4, y + 40), label, fill=(220, 220, 220), font=fs)
        for c, f in enumerate(fr):
            bg = Image.new('RGBA', (CELL, CELL), (64, 104, 66, 255))
            bg.alpha_composite(f.image())
            out.paste(bg.convert('RGB').crop((16, 10, 16 + cw, 10 + ch)).resize((cw * Z, ch * Z), Image.NEAREST), (150 + c * (cw * Z + 4), y))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        preview(sys.argv[2:] or ['idle:down:4', 'run:down:8', 'run:left:8', 'run:up:8', 'attack1:left:6', 'attack1:down:6'],
                PREVIEWS + '/internal-test-azar-v3.png')
    else:
        export()
