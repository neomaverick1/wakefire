"""The townsfolk of Ashkel in Azar's hand-pixeled build: one body drawn pixel by pixel in three
views (a long tunic, bare arms, sandals), dressed per person with colours and hand-drawn
headwear, and animated with the same key-pose machinery as Azar.

    python3 folk5.py [sheets]       export
    python3 folk5.py preview
"""
import sys, json
import numpy as np
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import azar
from azar import CELL, FX, FY, hx
from px import Canvas

OUT = azar.OUT
W = 26

# palette letters for the townsfolk (the costume letters are recoloured per person)
BASE = {
    'O': '#1c1024',
    'S': '#f2c49c', 's': '#d4956c', 'k': '#a8664a', 'K': '#6e3c2c', 'E': '#ffffff', 'P': '#241a34',
    'H': '#5a3a2a', 'j': '#3a2418', 'J': '#22140e',              # hair
    'T': '#e8dcc4', 't': '#c4b498', 'v': '#968670', 'V': '#625644',  # tunic
    'A': '#f0e8d8', 'a': '#cfc4b0',                              # apron / shawl / second cloth
    'M': '#6a4428', 'm': '#4a2c18',                              # belt, sandals
    'G': '#ffd860', 'g': '#c8962c',                              # gold trim
    'W': '#fff6cc', 'B': '#f6c656', 'b': '#d9952f', 'n': '#a8621f',  # bronze bits
}


def build(rows):
    out = []
    for segs in rows:
        r = ['.'] * W
        for (c, s) in segs:
            for i, ch in enumerate(s):
                if ch != '.' and 0 <= c + i < W:
                    r[c + i] = ch
        out.append(r)
    return out


FRONT = [
    [(9, "OOOOOOOO")],
    [(8, "OHHHHHHjjO")],
    [(7, "OHHHHHHHHjjO")],
    [(7, "OHHSSSSSSjjO")],
    [(7, "OHSSSSSSSSjO")],
    [(7, "OjSKKSSKKSjO")],
    [(7, "OjSPESSEPSjO")],
    [(7, "OsSSSSkSSSsO")],
    [(8, "OsSSKKSSsO")],
    [(9, "OOsssssO")],
    [(10, "OOkskkOO")],
    [(5, "OOOTTTTttttvvOOO")],
    [(4, "OSsOTTTTtttvvvOskO")],
    [(4, "OSsOTTTttttvvvOskO")],
    [(4, "OSsOTTTttttvvVOskO")],
    [(4, "OSsOTTtttttvvVOskO")],
    [(4, "OSsOMMMMGgMMmmOskO")],
    [(4, "OSsOTTtttttvvVOskO")],
    [(4, "OSkOTTtttttvvVOkkO")],
    [(4, "OOOOTTtttttvvVOOOO")],
    [(7, "OTTtttttvvVO")],
    [(7, "OTtttttvvvVO")],
    [(7, "OtttttvvvVVO")],
    [(7, "OOOOOOOOOOOO")],
    [(8, "OSskOOSskO")],
    [(8, "OSskOOSskO")],
    [(8, "OSskOOSskO")],
    [(7, "OMmmmOOMmmmO")],
    [(7, "OOOOO..OOOOO")],
]
SIDE = [
    [(9, "OOOOOO")],
    [(8, "OHHHHHHO")],
    [(7, "OHHHHHHHjO")],
    [(7, "OjHHHSSSSO")],
    [(7, "OjHHSSSSSSO")],
    [(7, "OjjHSSKSSSO")],
    [(7, "OjjHSSPESSO")],
    [(7, "OjjHsSSSSkSO")],
    [(8, "OjHsSSSKSO")],
    [(9, "OOsssssO")],
    [(10, "OkskkO")],
    [(8, "OOTTTtttvO")],
    [(7, "OTTTSskttvO")],
    [(7, "OTTTSskttvO")],
    [(7, "OTTtSskttvO")],
    [(7, "OTTtSsktvvO")],
    [(7, "OMMMSskmmmO")],
    [(7, "OTTtSskttvO")],
    [(7, "OTTtOOOtvvO")],
    [(7, "OTTtttttvvO")],
    [(7, "OTTttttvvVO")],
    [(7, "OTtttttvvVO")],
    [(7, "OtttttvvvVO")],
    [(7, "OOOOOOOOOOO")],
    [(9, "OskSskO")],
    [(9, "OskSskO")],
    [(9, "OskSskO")],
    [(8, "OmmmMmmmMO")],
    [(8, "OOOOOOOOOO")],
]
BACK = [
    [(9, "OOOOOOOO")],
    [(8, "OHHHHHHjjO")],
    [(7, "OHHHHHHHHjjO")],
    [(7, "OHHHHHHHHjjO")],
    [(7, "OHHHHHHHHHjO")],
    [(7, "OjHHHHHHHHjO")],
    [(7, "OjjHHHHHHjjO")],
    [(7, "OjjjHHHHjjjO")],
    [(8, "OjjjjjjjjO")],
    [(9, "OOkkkkkO")],
    [(10, "OOkskkOO")],
    [(5, "OOOTTTTttttvvOOO")],
    [(4, "OSsOTTTTtttvvvOskO")],
    [(4, "OSsOTTTttttvvvOskO")],
    [(4, "OSsOTTTttttvvVOskO")],
    [(4, "OSsOTTtttttvvVOskO")],
    [(4, "OSsOMMMMmmMMmmOskO")],
    [(4, "OSsOTTtttttvvVOskO")],
    [(4, "OSkOTTtttttvvVOkkO")],
    [(4, "OOOOTTtttttvvVOOOO")],
    [(7, "OTTtttttvvVO")],
    [(7, "OTtttttvvvVO")],
    [(7, "OtttttvvvVVO")],
    [(7, "OOOOOOOOOOOO")],
    [(8, "OSskOOSskO")],
    [(8, "OSskOOSskO")],
    [(8, "OSskOOSskO")],
    [(7, "OMmmmOOMmmmO")],
    [(7, "OOOOO..OOOOO")],
]


GRIDS = {'front': build(FRONT), 'side': build(SIDE), 'back': build(BACK)}
SPLIT = (10, 24)            # head rows end, legs begin
RGBB = {k: hx(v) for k, v in BASE.items()}


def sub(rows, i, old, new):
    rows[i] = list(''.join(rows[i]).replace(old, new))


# ----------------------------------------------------------------------------- who wears what
PEOPLE = {
    'baker':   dict(skin='warm', hair=('#f0e6c8', '#c8b890', '#9a8a68'), tunic=('#d87a48', '#b0582e', '#843e20', '#5a2a14'),
                    apron=True, top='scarf'),
    'potter':  dict(skin='tan', hair=('#c8c4cc', '#9a96a2', '#6a6672'), tunic=('#c8a050', '#a07c34', '#785a22', '#4e3a14'),
                    top='bald', beard='#9a96a2'),
    'oracle':  dict(skin='warm', hair=('#9a6ad0', '#6e44a8', '#48287a'), tunic=('#8a5ac8', '#6a3ea6', '#4a2a7c', '#2e1a52'),
                    top='veil'),
    'fisher':  dict(skin='dark', hair=('#4a3a30', '#2e221c', '#1a120e'), tunic=('#6a8ab0', '#4a6a90', '#344e6c', '#22344a'),
                    top='strawhat', beard='#3a2a20'),
    'priest':  dict(skin='warm', hair=('#f4f0f8', '#d0ccdc', '#a8a2b8'), tunic=('#f4f0e8', '#d8d0c0', '#b0a690', '#7c7462'),
                    top='tallcap', beard='#e8e4f0', trim=True),
    'sleeper_a': dict(skin='tan', hair=('#3a2418', '#24160e', '#140c08'), tunic=('#d85a3a', '#b03e26', '#822a18', '#561a0e'),
                      top='headband'),
    'sleeper_b': dict(skin='warm', hair=('#6a4a30', '#4a321e', '#2c1c10'), tunic=('#7a9a5a', '#5a7a40', '#40582c', '#28381a'),
                      top=None),
    'sleeper_c': dict(skin='dark', hair=('#2a1a14', '#1a100c', '#0e0806'), tunic=('#4aa0a0', '#2e7c80', '#1e5a5e', '#123c40'),
                      top='curls'),
    'captain_child': dict(skin='warm', hair=('#5a3a2a', '#3a2418', '#22140e'), tunic=('#c84040', '#a02a2e', '#741c22', '#4a1016'),
                          top='kidhelm', child=True),
}
SKINS = {'warm': ('#f2c49c', '#d4956c', '#a8664a', '#6e3c2c'), 'tan': ('#e0a878', '#bc8456', '#8e5c3a', '#5c3624'),
         'dark': ('#b07850', '#8a5636', '#643c24', '#3e2416')}


def recolor_map(who):
    p = PEOPLE[who]
    m = {}
    S = SKINS[p['skin']]
    m.update({'S': S[0], 's': S[1], 'k': S[2], 'K': S[3]})
    m.update({'H': p['hair'][0], 'j': p['hair'][1], 'J': p['hair'][2]})
    m.update({'T': p['tunic'][0], 't': p['tunic'][1], 'v': p['tunic'][2], 'V': p['tunic'][3]})
    return m


def dress(rows, view, who):
    """Headwear and beards, drawn over the head rows."""
    p = PEOPLE[who]
    rows = [list(r) for r in rows]
    top = p.get('top')
    if top == 'bald':
        for y in range(0, 3):
            rows[y] = ['S' if c in 'Hj' else c for c in rows[y]]
    if top == 'veil' and view != 'back':
        sub(rows, 3, 'HHSSSSSS' if view == 'front' else 'HHHSSSSO', 'HHGGGGGG' if view == 'front' else 'HHHGGGGO')
    if top == 'headband':
        r = rows[3]
        for x in range(W):
            if r[x] in 'SHj' and 7 <= x <= 18:
                r[x] = 'G' if (x % 3) else 'g'
    if p.get('beard') and view != 'back':
        if view == 'front':
            sub(rows, 7, 'OsSSSSkSSSsO', 'OsJJSSkSJJsO')
            sub(rows, 8, 'OsSSKKSSsO', 'OJJJKKJJJO')
            sub(rows, 9, 'OOsssssO', 'OOJJJJJO')
        else:
            sub(rows, 8, 'OjHsSSSKSO', 'OjHsJJJKJO')
            sub(rows, 9, 'OOsssssO', 'OOJJJJJO')
    return rows


def hat(cv, view, who, ox, hy):
    """Hats that rise above the head."""
    p = PEOPLE[who]
    top = p.get('top')
    def put(x, y, ch, col=None):
        xx, yy = ox + x, hy + y
        if 0 <= xx < CELL and 0 <= yy < CELL:
            cv.a[yy, xx] = hx(col) if col else RGBB[ch]
    if top == 'strawhat':
        straw = ['#f0d890', '#d0b060', '#a8883c', '#7a6024']
        brim_y = 2
        for x in range(4, 22):
            put(x, brim_y, None, straw[1] if x < 14 else straw[2]); put(x, brim_y + 1, None, straw[3])
            put(x, brim_y - 1, 'O'); put(x, brim_y + 2, 'O')
        put(3, brim_y, 'O'); put(3, brim_y + 1, 'O'); put(22, brim_y, 'O'); put(22, brim_y + 1, 'O')
        for y in range(-3, brim_y - 1):
            for x in range(9, 17):
                put(x, y, None, straw[0] if x < 12 else straw[1] if x < 15 else straw[2])
            put(8, y, 'O'); put(17, y, 'O')
        for x in range(9, 17):
            put(x, -4, 'O')
    if top == 'tallcap':
        for y in range(-6, 2):
            for x in range(9, 17):
                put(x, y, None, '#f4f0f8' if x < 13 else '#d0ccdc')
            put(8, y, 'O'); put(17, y, 'O')
        for x in range(9, 17):
            put(x, -7, 'O'); put(x, 0, 'G' if x % 2 else 'g'); put(x, 1, 'g')
    if top == 'kidhelm':
        # Dur at six, in his father's helmet, much too big for him, black crest and all
        widths = [6, 10, 12, 14, 14, 14, 14]
        for j, w in enumerate(widths):
            y = j - 3
            x0 = 13 - w // 2
            for x in range(x0, x0 + w):
                rel = (x - x0) / max(1, w - 1)
                c = 'W' if (rel < 0.3 and j in (1, 2)) else 'B' if rel < 0.55 else 'b' if rel < 0.85 else 'n'
                if j == len(widths) - 1:
                    c = 'n' if rel > 0.1 else 'b'
                put(x, y, c)
            put(x0 - 1, y, 'O'); put(x0 + w, y, 'O')
        for x in range(13 - 3, 13 + 3):
            put(x, -4, 'O')
        for x in range(13 - 7, 13 + 7):
            put(x, 4, 'O')
        for (x, y) in ((11, -5), (12, -6), (13, -6), (14, -5), (12, -5), (13, -5)):
            put(x, y, None, '#3a3a48')
        for (x, y) in ((11, -6), (12, -7), (13, -7), (14, -6), (15, -5), (10, -5)):
            put(x, y, 'O')
    if top == 'curls' and view != 'back':
        for (x, y) in ((8, 1), (10, 0), (13, 0), (16, 1), (17, 3)):
            put(x, y, 'J')


def side_legs(stride):
    near_dx, far_dx, lift_n, lift_f = stride
    h = 6
    out = [['.'] * W for _ in range(h)]
    def leg(hx_, dx, lift, far):
        cols = ['s', 'k'] if far else ['S', 's', 'k']
        for r in range(3):
            x = hx_ + int(round(dx * (r + 1) / 4))
            y = r - (lift if r >= 1 else 0)
            for k, ch in enumerate(cols):
                if 0 <= y < h and 0 <= x + k < W:
                    out[y][x + k] = ch
        fx, fy = hx_ + dx, 3 - lift
        for k in range(4 if far else 5):
            if 0 <= fy < h and 0 <= fx + k < W:
                out[fy][fx + k] = 'm' if far else 'M'
    leg(10, far_dx, lift_f, True)
    leg(12, near_dx, lift_n, False)
    return azar.outline_rows(out)


def legs_lift(rows, lift_l, lift_r):
    h = len(rows)
    out = [['.'] * W for _ in range(h)]
    for y in range(h):
        for x in range(W):
            ch = rows[y][x]
            if ch == '.':
                continue
            lift = lift_l if x < 13 else lift_r
            yy = y - lift
            if 0 <= yy < h and out[yy][x] == '.':
                out[yy][x] = ch
    return out


def frame(who, view, k=0, bob=0, eye='open', mouth=False, head_dy=0, lift=(0, 0), stride=None, squash=0,
          lie=False, arms_up=False, arm_out=False, flash=False):
    p = PEOPLE[who]
    g = GRIDS[view]
    head, body, legs = [list(r) for r in g[:SPLIT[0]]], [list(r) for r in g[SPLIT[0]:SPLIT[1]]], [list(r) for r in g[SPLIT[1]:]]
    if p.get('child'):
        body = body[:4] + body[7:]          # a shorter body and shorter legs, the same head
        legs = legs[1:]
    if p.get('apron') and view == 'front':
        for y in range(5, len(body)):
            body[y] = ['A' if (c in 'Tt' and 8 <= x <= 15) else 'a' if (c in 'vV' and 8 <= x <= 15) else c for x, c in enumerate(body[y])]
    if p.get('trim'):
        for y in (len(body) - 2,):
            body[y] = ['G' if c in 'Ttv' else c for c in body[y]]
    head = dress(head, view, who)
    if eye != 'open' and view != 'back':
        if view == 'front':
            sub(head, 6, 'SPESSEPS', 'SKKSSKKS' if eye == 'shut' else 'SKPSSPKS')
        else:
            sub(head, 6, 'PE', 'KK' if eye == 'shut' else 'PK')
    if mouth and view == 'front':
        sub(head, 8, 'SKKS', 'SOOS')
    cv = Canvas(CELL, CELL)
    ox = FX - 13
    if view == 'side' and stride is not None:
        legs = side_legs(stride)
    elif view != 'side':
        legs = legs_lift(legs, *lift)
    total = len(head) + len(body) + len(legs)
    oy = FY - total
    def paint(rows, x0, y0):
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.' and 0 <= y0 + y < CELL:
                    cv.a[y0 + y, x0 + x] = RGBB[ch]
    paint(legs, ox, oy + len(head) + len(body))
    by = oy + len(head) + bob
    paint(body, ox, by)
    hy = oy + bob + head_dy
    paint(head, ox, hy)
    hat(cv, view, who, ox, hy)
    if arms_up or arm_out:
        layer = Canvas(CELL, CELL)
        arms = []
        if arms_up:
            arms = [((6, len(head) + 2), (9, -1)), ((19, len(head) + 2), (16, -1))] if view != 'side' else [((12, len(head) + 2), (14, -1))]
        else:
            arms = [((19, len(head) + 2), (24, len(head) + 2))] if view == 'front' else [((13, len(head) + 2), (19, len(head) + 3))]
        for (sx, sy), (ex, ey) in arms:
            n = max(abs(ex - sx), abs(ey - sy), 1)
            for i in range(n + 1):
                t = i / n
                x = ox + int(round(sx + (ex - sx) * t)); y = hy + int(round(sy + (ey - sy) * t))
                if 0 <= y < CELL and 0 <= x + 1 < CELL:
                    layer.a[y, x] = RGBB['S']; layer.a[y, x + 1] = RGBB['k']
        layer.outline(RGBB['O'])
        cv.blit(layer, 0, 0)
    # colours for this person
    rec = recolor_map(who)
    src = cv.a.copy()
    for letter, h in rec.items():
        old = RGBB[letter]
        m = (src[:, :, 0] == old[0]) & (src[:, :, 1] == old[1]) & (src[:, :, 2] == old[2]) & (src[:, :, 3] > 0)
        cv.a[m, :3] = hx(h)[:3]
    if squash:
        a = cv.a.copy(); out = np.zeros_like(a); dst = FY - 1
        for y in range(FY - 1, -1, -1):
            if y > FY - 28 and (FY - y) % max(2, 6 - squash) == 0:
                continue
            out[dst] = a[y]; dst -= 1
            if dst < 0:
                break
        cv.a = out
    if lie:
        rot = np.rot90(cv.a, -1)
        out = np.zeros_like(cv.a)
        ys, xs = np.nonzero(rot[:, :, 3])
        if len(ys):
            dy = FY - 1 - ys.max(); dx = FX - int(xs.mean())
            for y, x in zip(ys, xs):
                if 0 <= y + dy < CELL and 0 <= x + dx < CELL:
                    out[y + dy, x + dx] = rot[y, x]
        cv.a = out
    if flash:
        m = cv.a[:, :, 3] > 0
        cv.a[m, :3] = (cv.a[m, :3].astype(np.int32) * 0.3 + 255 * 0.7).astype(np.uint8)
    return cv


WALK_FB = azar.WALK_FB
WALK_SIDE = [(3, -2, 0, 0), (1, -1, 1, 0), (0, 0, 1, 0), (-1, 1, 0, 0), (-2, 3, 0, 0), (-1, 1, 0, 1), (0, 0, 0, 1), (1, -1, 0, 0)]
VIEW = {'down': 'front', 'left': 'side', 'up': 'back'}


def anim(who, name, view, n):
    F = []
    for i in range(n):
        if name == 'idle':
            F.append(frame(who, view, bob=1 if i in (1, 2) else 0))
        elif name == 'talk':
            F.append(frame(who, view, mouth=i % 2 == 1, bob=1 if i in (2, 3) else 0, head_dy=-1 if i == 4 else 0))
        elif name == 'sleep':
            F.append(frame(who, view, eye='shut', head_dy=1 + (1 if i in (1, 2) else 0), bob=1 if i in (1, 2) else 0))
        elif name == 'lie':
            F.append(frame(who, 'side', eye='shut', lie=True, bob=i % 2))
        elif name in ('walk', 'sleepwalk'):
            eye = 'shut' if name == 'sleepwalk' else 'open'
            if view == 'side':
                F.append(frame(who, view, eye=eye, stride=WALK_SIDE[i % 8], bob=-1 if i % 4 == 2 else 0, arm_out=name == 'sleepwalk'))
            else:
                F.append(frame(who, view, eye=eye, lift=WALK_FB[i % 8], bob=-1 if i % 4 in (1, 2) else 0))
        elif name == 'knead':
            F.append(frame(who, view, eye='shut', bob=[0, 1, 2, 1][i % 4], head_dy=1))
        elif name == 'shrug':
            F.append(frame(who, view, eye='half', bob=-1, arms_up=False))
        elif name == 'point':
            F.append(frame(who, view, arm_out=True))
        elif name == 'cower':
            F.append(frame(who, view, eye='shut', squash=2 + (i % 2)))
        elif name == 'itemget':
            F.append(frame(who, view, arms_up=True))
        elif name == 'sigh':
            F.append(frame(who, view, eye='half', bob=1 + i))
        elif name == 'hurt':
            F.append(frame(who, view, flash=i == 0, bob=-1))
        elif name == 'lean':
            F.append(frame(who, view, eye='shut', head_dy=1))
        else:
            F.append(frame(who, view))
    return F


def export(sheet):
    from PIL import Image
    old = json.load(open(f'{OUT}/{sheet}.json'))
    rows = []
    for a in old['anims']:
        view = VIEW[a['dir']]
        fr = anim(sheet, a['name'], view, a['frames'])
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
    img.save(f'{OUT}/{sheet}.png')
    json.dump(meta, open(f'{OUT}/{sheet}.json', 'w'))
    print(sheet, img.size)


def preview(path):
    from PIL import Image, ImageDraw, ImageFont
    Z = 3
    who = list(PEOPLE)
    out = Image.new('RGB', (len(who) * (52 * Z + 4) + 4, 2 * (56 * Z + 4) + 40), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - townsfolk v4', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22))
    for i, w_ in enumerate(who):
        for r, (view, name) in enumerate((('front', 'talk'), ('side', 'idle'))):
            f = anim(w_, name, view, 2)[1 if name == 'talk' else 0]
            bg = Image.new('RGBA', (CELL, CELL), (64, 104, 66, 255)); bg.alpha_composite(f.image())
            out.paste(bg.convert('RGB').crop((14, 8, 66, 64)).resize((52 * Z, 56 * Z), Image.NEAREST), (4 + i * (52 * Z + 4), 38 + r * (56 * Z + 4)))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    if 'preview' in sys.argv:
        preview(azar.PREVIEWS + '/internal-test-folk5.png')
    else:
        for s in (sys.argv[1:] or [k for k in PEOPLE]):
            export(s)
