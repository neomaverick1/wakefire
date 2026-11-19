"""Soldiers in Azar's hand-pixeled build: Captain Dur of the Temple Gate (black crest, spear,
asleep on his feet) and the bronze sentinels of the ziggurat (all bronze, eyes of fire, spear
and shield). They are Azar's own key poses in other colours, so the cast matches.

    python3 folk4.py [captain sentinel]
"""
import sys, json
import numpy as np
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import azar
from azar import frame, CELL, FX, FY, RGB, hx, WALK_FB, WALK_SIDE
from px import Canvas

OUT = azar.OUT

DUR = {
    # a black horsehair crest, a darker cloak, a weathered face
    'y': '#8a8a9a', 'Y': '#5a5a6c', 'F': '#3c3c4c', 'R': '#2a2a38', 'r': '#1e1e2a', 'Q': '#141420',
    'C': '#a03a3a', 'c': '#7a2430', 'x': '#561824', 'X': '#360e18',
    'S': '#eab890', 's': '#c88a64', 'k': '#9a5c40',
}
BRONZE = {
    # a statue: everything cast in bronze, the eyes two coals
    'y': '#fff0b0', 'Y': '#f2c25c', 'F': '#c98a34', 'R': '#9a5c22', 'r': '#6c3a16', 'Q': '#46240e',
    'S': '#e8b860', 's': '#c08a36', 'k': '#8e5a22', 'K': '#5a3414', 'h': '#7a4a1c',
    'C': '#d09a44', 'c': '#a8702c', 'x': '#7c4a1c', 'X': '#52300e',
    'l': '#b08040', 'm': '#7c5228', 'M': '#4a3016', 'E': '#ffb43a',
}


def spear(cv, x, y_top, y_bot, bronze=False):
    """A spear held upright: ash shaft, bronze leaf blade at the top."""
    shaft = [hx('#c09060'), hx('#7a5434')] if not bronze else [hx('#d09a44'), hx('#7c4a1c')]
    for y in range(y_top + 5, y_bot):
        cv.a[y, x] = shaft[0]; cv.a[y, x + 1] = shaft[1]
    tip = ["..O..", ".OWO.", ".OWbO", "OWBbO", "OBbnO", ".ObO.", "..O.."]
    for j, row in enumerate(tip):
        for i, ch in enumerate(row):
            if ch != '.':
                cv.a[y_top + j, x - 2 + i] = RGB[ch]
    for y in range(y_top + 5, y_bot):
        for xx in (x - 1, x + 2):
            if cv.a[y, xx, 3] == 0:
                cv.a[y, xx] = RGB['O']


def shield(cv, cx, cy, r=6):
    """A round bronze shield with a boss and a lit rim."""
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r + 0.5:
                if d > r - 0.6:
                    c = 'O'
                elif d > r - 1.6:
                    c = 'W' if (x - cx) + (y - cy) < 0 else 'n'
                elif d < 1.6:
                    c = 'W' if (x - cx) + (y - cy) < 0 else 'b'
                else:
                    c = 'B' if (x - cx) * 0.6 + (y - cy) < 0 else 'b'
                cv.a[y, x] = RGB[c]


def body_top(view):
    head, body, legs = azar.parts(view)
    return FY - len(legs) - len(body) - len(head) + len(head)


def soldier(sheet, view, i, name, n):
    pal = DUR if sheet == 'captain' else BRONZE
    kw = dict(recolor=pal, k=i)
    asleep = sheet == 'captain'
    if name in ('idle', 'lean', 'sleep', 'talk'):
        eye = 'shut' if asleep else 'open'
        bob = [0, 0, 1, 1, 0, 0][i % 6] if name != 'sleep' else [0, 1, 1, 0][i % 4]
        head_dy = 1 if name in ('sleep', 'lean') else 0
        mouth = name == 'talk' and i % 2 == 1
        cv = frame(view, eye=eye, bob=bob, head_dy=head_dy, mouth=mouth, lean=1 if name == 'lean' else 0, **kw)
    elif name == 'walk':
        if view == 'side':
            cv = frame(view, stride=WALK_SIDE[i % 8], bob=-1 if i % 4 == 2 else 0, cape=i % 2, **kw)
        else:
            cv = frame(view, lift=WALK_FB[i % 8], bob=-1 if i % 4 in (1, 2) else 0, **kw)
    elif name == 'hurt':
        cv = frame(view, flash=i == 0, lean=-2 if view == 'side' else 0, bob=-1, **kw)
    else:
        cv = frame(view, **kw)
    # the spear in the right hand, the shield on the left arm for the sentinels
    by = body_top(view)
    ox = FX - 13
    if view == 'front':
        spear(cv, ox + 3, by - 22, by + 11, bronze=not asleep)
        if not asleep:
            shield(cv, ox + 19, by + 7, 6)
    elif view == 'side':
        spear(cv, ox + 16, by - 22, by + 12, bronze=not asleep)
        if not asleep:
            shield(cv, ox + 9, by + 6, 6)
    else:
        spear(cv, ox + 21, by - 22, by + 11, bronze=not asleep)
        if not asleep:
            shield(cv, ox + 6, by + 7, 6)
    return cv


VIEW = {'down': 'front', 'left': 'side', 'up': 'back'}


def export(sheet):
    from PIL import Image
    old = json.load(open(f'{OUT}/{sheet}.json'))
    rows = []
    for a in old['anims']:
        view = VIEW[a['dir']]
        fr = [soldier(sheet, view, i, a['name'], a['frames']) for i in range(a['frames'])]
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
    Z = 4
    cells = [soldier('captain', 'front', 0, 'lean', 4), soldier('captain', 'side', 0, 'idle', 4),
             soldier('sentinel', 'front', 0, 'idle', 4), soldier('sentinel', 'side', 2, 'walk', 8), soldier('sentinel', 'back', 0, 'idle', 4)]
    out = Image.new('RGB', (len(cells) * (56 * Z + 6) + 6, 64 * Z + 44), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - soldiers', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22))
    for i, f in enumerate(cells):
        bg = Image.new('RGBA', (CELL, CELL), (64, 104, 66, 255)); bg.alpha_composite(f.image())
        out.paste(bg.convert('RGB').crop((12, 2, 68, 66)).resize((56 * Z, 64 * Z), Image.NEAREST), (6 + i * (56 * Z + 6), 38))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    if 'preview' in sys.argv:
        preview(azar.PREVIEWS + '/internal-test-soldiers.png')
    else:
        for s in (sys.argv[1:] or ['captain', 'sentinel']):
            export(s)
