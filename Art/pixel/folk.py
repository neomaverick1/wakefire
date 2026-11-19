"""The people of Ashkel, in the same hand-built pixel style as Azar.

Every head is a hand-drawn face (front, side, back; eyes open or shut) under a hand-drawn
piece of hair or headwear that makes the character; bodies are drawn in code from a costume
(tunic or long robe, apron, sash, sleeves) so every animation keeps its proportions. Each part
carries its own outline. Writes Resources/Sprites/<sheet>.png/.json with the same animations
and frame counts the game already asks for.

    python3 folk.py preview [names]      # a check sheet
    python3 folk.py [names]              # write the sheets
"""
import sys, math, json
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas
import hero
from hero import PAL, O, outlined, with_outline, limb, CELL, FX, FY
import os
PREVIEWS = os.environ.get('WF_PREVIEWS', '/tmp/wakefire-previews')
os.makedirs(PREVIEWS, exist_ok=True)

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Sprites'


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def m2c(rows, pal=None):
    p = dict(PAL)
    if pal:
        p.update(pal)
    w = max(len(r) for r in rows)
    cv = Canvas(w, len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                cv.px(x, y, p[ch])
    return cv


# ----------------------------------------------------------------------------- faces (12 wide)
FACE = {
    ('down', 'open'): [
        "...oooooo...",
        "..okKKkkSo..",
        ".okKkkkkkSo.",
        ".okkkkkkkSo.",
        ".okhhkkhhSo.",
        ".okowkkwoso.",
        ".oSkkkkkkso.",
        ".oSkkksSkso.",
        "..oSkSSkSo..",
        "...oSSSso...",
        "....oooo....",
    ],
    ('side', 'open'): [
        "...ooooo....",
        "..oKkkkSo...",
        ".oKkkkkkSo..",
        ".okkkkkkkSo.",
        ".oSkkkkhhko.",
        ".oSskkkwokko",
        ".oSskkkkkkKo",
        ".oSsskkkkso.",
        "..oSskkSSo..",
        "...oSSSso...",
        "....oooo....",
    ],
    ('up', 'open'): [
        "...oooooo...",
        "..oSkkkkSo..",
        ".oSkkkkkkso.",
        ".oSkkkkkkso.",
        ".oSkkkkkkso.",
        ".oSSkkkkSso.",
        ".oSSSSSSsso.",
        ".oSSSSSSsso.",
        "..oSSSSSso..",
        "...oSSSso...",
        "....oooo....",
    ],
}
FACE[('down', 'closed')] = FACE[('down', 'open')][:5] + [".okookkooso."] + FACE[('down', 'open')][6:]
FACE[('side', 'closed')] = FACE[('side', 'open')][:5] + [".oSskkkookko"] + FACE[('side', 'open')][6:]
FACE[('up', 'closed')] = FACE[('up', 'open')]
FACE[('down', 'talk')] = FACE[('down', 'open')][:7] + [".oSkkkoSkso.", "..oSkooSSo.."] + FACE[('down', 'open')][9:]
FACE[('side', 'talk')] = FACE[('side', 'open')][:7] + [".oSsskkkoo..", "..oSskkooo.."] + FACE[('side', 'open')][9:]
FACE[('up', 'talk')] = FACE[('up', 'open')]
# small children: the same face, a size down
KID = {
    ('down', 'open'): ["..oooooo..", ".okKKkkSo.", "okKkkkkkSo", "okowkkwoSo", "oSkkkkkkso", ".oSkSSkSo.", "..oSSSSo..", "...oooo..."],
    ('side', 'open'): ["..ooooo...", ".oKkkkkSo.", "okkkkkkkSo", "oSkkkkwoko", "oSskkkkkKo", ".oSskkSSo.", "..oSSSSo..", "...oooo..."],
    ('up', 'open'): ["..oooooo..", ".oSkkkkSo.", "oSkkkkkkso", "oSkkkkkkso", "oSSkkkkSso", ".oSSSSSso.", "..oSSSSo..", "...oooo..."],
}
KID[('down', 'wide')] = KID[('down', 'open')][:3] + ["owwkkkkwwo"[:0] + "okwokkowSo"] + KID[('down', 'open')][4:]
KID[('side', 'wide')] = KID[('side', 'open')]
KID[('up', 'wide')] = KID[('up', 'open')]
for v in ('down', 'side', 'up'):
    KID[(v, 'closed')] = KID[(v, 'open')] if v == 'up' else KID[(v, 'open')][:3] + (["okookkooSo"] if v == 'down' else ["oSkkkkooko"]) + KID[(v, 'open')][4:]
    KID[(v, 'talk')] = KID[(v, 'open')]


# a bronze sentinel's face: the same features cast in bronze, eyes burning
_T = str.maketrans({'K': 'W', 'k': 'N', 'S': 'n', 's': 'b', 'h': 'B', 'w': 'G', 'd': 'b'})
MASK = {}
for (v, e), rows in list(FACE.items()):
    r2 = [r.translate(_T) for r in rows]
    if v != 'up':
        r2 = [r.replace('Go', 'GF').replace('oG', 'FG') for r in r2]
    MASK[(v, e)] = r2
MASK[('down', 'closed')] = MASK[('down', 'open')]
MASK[('side', 'closed')] = MASK[('side', 'open')]


# ----------------------------------------------------------------------------- hair and headwear
# Each: {view: (rows, dx, dy)} drawn over the face (dx, dy from the face's top left), with its
# own small palette. Rows are hand-drawn; '.' leaves the face showing.
H = {}
HP = {}

# Captain Dur: an open bronze helmet with a short black crest, cheek guards; a great black beard
HP['dur'] = {'c': rgb('#3a2a2c'), 'C': rgb('#5c4448')}
H['dur'] = {
    'down': (["....occo....", "...oCCcco...", "..ooooooo...", ".oNWNNnnbbo.", "oNWNnnnnnbBo", "oNnnnnnnnbBo", "oNo......oBo", "oNo......oBo", "obo......obo"], 0, -3),
    'side': (["...occco....", "..oCCccco...", "..ooooooo...", ".oNWNNnnbo..", "oNWNnnnnnbo.", "oNnnnnnnbbo.", "oNnbo.......", "oNnbo.......", "obbo........"], 0, -3),
    'up':   (["....occo....", "...oCCcco...", "..ooooooo...", ".oNWNNnnbbo.", "oNWNnnnnnbBo", "oNnnnnnnnbBo", "oNnnnnnnnbBo", "obnnnnnnnbBo", ".obbbbbbbBo."], 0, -3),
}
HP['sentinel'] = {'c': PAL['n'], 'C': PAL['b']}
H['sentinel'] = {
    'down': (["....occo....", "...oNCcco...", "..ooooooo...", ".oNWNNnnbbo.", "oNWNnnnnnbBo", "oNnnnnnnnbBo", "oNo......oBo", "oNo......oBo", "obo......obo"], 0, -3),
    'side': (["...occco....", "..oNCccco...", "..ooooooo...", ".oNWNNnnbo..", "oNWNnnnnnbo.", "oNnnnnnnbbo.", "oNnbo.......", "oNnbo.......", "obbo........"], 0, -3),
    'up':   (["....occo....", "...oNCcco...", "..ooooooo...", ".oNWNNnnbbo.", "oNWNnnnnnbBo", "oNnnnnnnnbBo", "oNnnnnnnnbBo", "obnnnnnnnbBo", ".obbbbbbbBo."], 0, -3),
}
BEARD = {
    'black': {'down': ([".o......o.", ".ohhhhhhho", ".ohhhhhhhho"[0:10], "..ohhhhho.", "...ohhho.."], 1, 6),
              'side': ([".....oo..", "..ohhhho.", ".ohhhhhho", "..ohhhho.", "...oho..."], 1, 6)},
    'white': {'down': ([".o......o.", ".owwWwwwwo"[:10], ".owwwwwwwo", "..owwwwwo.", "...owwwo.."], 1, 6),
              'side': ([".....oo..", "..owwwwo.", ".owwwwwwo", "..owwwwo.", "...owo..."], 1, 6)},
}
# Hesha the baker: a cream headscarf knotted on top
HP['hesha'] = {'c': rgb('#f0e2c4'), 'C': rgb('#c8b48e'), 'x': rgb('#8e7a5a')}
H['hesha'] = {
    'down': (["....oooo....", "...occcco...", "..oCcccccCo.", ".occcccccCxo", ".ocCCCCCCCxo", ".oco....oxo.", ".oco....oxo.", "..o......o.."], 0, -2),
    'side': (["...oooo.....", "..occccoo...", ".occcccccoo.", "occcccccCxo.", "occCCCCCxo..", "occxo.......", "ocxo........", ".oo........."], 0, -2),
    'up':   (["....oooo....", "...occcco...", "..oCcccccCo.", ".occcccccCxo", ".occcccccCxo", ".occcccccCxo", ".oCcccccCCxo", "..oCCCCCxxo.", "...oxxxxo..."], 0, -2),
}
# Kesh the potter: bald, a grey fringe round the back
HP['kesh'] = {'c': rgb('#8a8486'), 'C': rgb('#5a5458')}
H['kesh'] = {
    'down': ([".o........o.", "oco......oCo", "oco......oCo"], 0, 3),
    'side': (["oco.....", "occo....", "oCco....", ".oo....."], 0, 3),
    'up':   (["............", "............", ".occcccccCo.", "occccccccCCo", "oCcccccccCCo", ".oCCCCCCCCo."], 0, 2),
}
# Ummi the oracle: a deep violet veil with a gold band, falling to the shoulders
HP['ummi'] = {'c': rgb('#5a2a7a'), 'C': rgb('#3a1652'), 'x': rgb('#24103a')}
H['ummi'] = {
    'down': (["...oooooo...", "..occcccCo..", ".occcccccCo.", "onNNnnnnbbBo", "oco......oxo", "oco......oxo", "oco......oxo", "occo....oCxo", "occo....oCxo", "oCCo....oxxo", ".oo......oo."], 0, -1),
    'side': (["..oooooo....", ".occcccCo...", "occcccccCo..", "onNNnnnbbo..", "occcCo......", "occcCo......", "occcCo......", "occCxo......", "oCCxxo......", "oCxxo.......", ".ooo........"], 0, -1),
    'up':   (["...oooooo...", "..occcccCo..", ".occcccccCo.", "onNNnnnnbbBo", "occcccccccxo", "occcccccCcxo", "occcccccCcxo", "occcccccCxxo", "oCcccccCCxxo", "oCCCCCCCxxxo", ".oooooooooo."], 0, -1),
}
# Abu-Nur the fisherman: a wide conical straw hat
HP['abunur'] = {'c': rgb('#e2c27a'), 'C': rgb('#b08c48'), 'x': rgb('#7a5a2c')}
H['abunur'] = {
    'down': ([".....oo.....", "....occo....", "...occcCo...", "..occcccCo..", ".occcccccCo.", "occcccccccCxo", "oxxxxxxxxxxxo"], -1, -3),
    'side': ([".....oo.....", "....occo....", "...occcCo...", "..occcccCo..", ".occcccccCo.", "occcccccccCxo", "oxxxxxxxxxxxo"], -1, -3),
    'up':   ([".....oo.....", "....occo....", "...occcCo...", "..occcccCo..", ".occcccccCo.", "occcccccccCxo", "oxxxxxxxxxxxo"], -1, -3),
}
# Ebrum the high priest: a tall round cap of white felt banded in gold, shaven face
HP['ebrum'] = {'c': rgb('#f4ecdc'), 'C': rgb('#c8bca6'), 'x': rgb('#8a7e6c')}
H['ebrum'] = {
    'down': (["...oooooo...", "..occcccCo..", "..occcccCo..", "..occcccCo..", ".onNNnnnbbo.", ".occcccccCo."], 0, -5),
    'side': (["..oooooo....", ".occcccCo...", ".occcccCo...", ".occcccCo...", "onNNnnnbbo..", "occcccccCo.."], 0, -5),
    'up':   (["...oooooo...", "..occcccCo..", "..occcccCo..", "..occcccCo..", ".onNNnnnbbo.", ".occcccccCo."], 0, -5),
}
# the merchant (sleeper_a): black hair under a red headband
HP['merchant'] = {'c': rgb('#2c1e22'), 'C': rgb('#1a1014'), 'x': rgb('#b8281c'), 'X': rgb('#e05030')}
H['merchant'] = {
    'down': (["...oooooo...", "..occcccCo..", ".occcccccCo.", ".oXXxxxxxxo.", ".oco....oCo."], 0, 0),
    'side': (["...ooooo....", "..occccCo...", ".occcccccCo.", ".oXXxxxxxo..", ".occo......."], 0, 0),
    'up':   (["...oooooo...", "..occcccCo..", ".occcccccCo.", ".oXXxxxxxxo.", ".occcccccCo.", ".occcccccCo.", "..oCCCCCCo..", "...oooooo..."], 0, 0),
}
# the dreamer / tax collector (sleeper_b): a woman with black hair in a long braid
HP['braid'] = {'c': rgb('#2a1c24'), 'C': rgb('#140c12'), 'x': rgb('#d8a040')}
H['braid'] = {
    'down': (["...oooooo...", "..occcccCo..", ".occcccccCo.", ".occccccccCo", ".oco....oCCo", ".oco.....oCo", "..o......oCo", "..........ox", "..........oc"], 0, 0),
    'side': (["...ooooo....", "..occccCo...", ".occcccccCo.", "occcccccCo..", "occcCo......", "occCo.......", "oCco........", "oxo.........", "oco........."], 0, 0),
    'up':   (["...oooooo...", "..occcccCo..", ".occcccccCo.", ".occcccccCo.", ".occcccccCo.", ".oCcccccCCo.", "..oCcCcCo...", "....oco.....", "....oxo.....", "....oco.....", "....oCo.....", ".....o......"], 0, 0),
}
# the sleepwalker / lover (sleeper_c): a young man with thick black curls
HP['curls'] = {'c': rgb('#2e2026'), 'C': rgb('#18101a'), 'x': rgb('#4a363c')}
H['curls'] = {
    'down': (["..oooooooo..", ".occxccxcCo.", "occcxcccxcCo", "ocxcccxcccCo", "oco......oCo", ".o........o."], 0, -1),
    'side': (["..ooooooo...", ".occxccxcCo..", "occcxcccxCo.", "ocxcccxcCo..", "occCo.......", ".oo........."], 0, -1),
    'up':   (["..oooooooo..", ".occxccxcCo.", "occcxcccxcCo", "ocxcccxcccCo", "occcxcccxcCo", "oCcccxcccCCo", ".oCCcCCcCCo.", "..oooooooo.."], 0, -1),
}
# Dur aged six: a helmet three sizes too big, sliding over his eyes (it's his father's)
HP['durkid'] = {}
H['durkid'] = {
    'down': (["....oooo....", "..ooNWnnoo..", ".oNWNnnnnbo.", "oNWNnnnnnnbo", "oNnnnnnnnnbo", "obbbbbbbbbbo", ".oo......oo."], -1, -4),
    'side': (["....oooo....", "..ooNWnnoo..", ".oNWNnnnnbo.", "oNWNnnnnnnbo", "oNnnnnnnnnbo", "obbbbbbbbbo.", ".o........o."], -1, -4),
    'up':   (["....oooo....", "..ooNWnnoo..", ".oNWNnnnnbo.", "oNWNnnnnnnbo", "oNnnnnnnnnbo", "obnnnnnnnnbo", ".obbbbbbbbo."], -1, -4),
}


# ----------------------------------------------------------------------------- costumes
def ramp4(*hexes):
    return [rgb(h) for h in hexes]


COSTUME = {
    'captain': dict(face='adult', hat='dur', beard='black', tunic=ramp4('#8ec07a', '#4f8a4a', '#2e5a34', '#183420'), vest=True,
                    belt='#6c3e22', length='tunic', legs='boots', prop='spear', broad=True),
    'captain_child': dict(face='kid', hat='durkid', tunic=ramp4('#8ec07a', '#4f8a4a', '#2e5a34', '#183420'), belt='#6c3e22',
                          length='tunic', legs='bare', kid=True),
    'baker': dict(face='adult', hat='hesha', tunic=ramp4('#e8b45a', '#c08a34', '#8a5a1e', '#5a3812'), apron='#f2e8d6', belt='#c8b48e',
                  length='robe', legs='robe', sleeves=None, broad=True, flour=True),
    'potter': dict(face='adult', hat='kesh', tunic=ramp4('#c4a888', '#94785c', '#6a5240', '#3e3026'), apron='#b8643c', belt='#5a3a26',
                   length='tunic', legs='bare', thin=True),
    'oracle': dict(face='adult', hat='ummi', tunic=ramp4('#8a54b0', '#5a2a7a', '#3a1652', '#24103a'), belt='#e0b04a',
                   length='robe', legs='robe', jewels=True),
    'fisher': dict(face='adult', hat='abunur', beard='white', tunic=ramp4('#9ab4c8', '#6a8aa4', '#465e78', '#2a3a4e'), belt='#8e6a3c',
                   length='tunic', legs='bare', prop='net'),
    'priest': dict(face='adult', hat='ebrum', tunic=ramp4('#fff6e4', '#e2d6bc', '#b8a888', '#7e705a'), belt='#e0b04a', trim='#e0b04a',
                   length='robe', legs='robe', tall=True),
    'sleeper_a': dict(face='adult', hat='merchant', tunic=ramp4('#d8a070', '#a86e44', '#7a4a2a', '#4a2c18'), belt='#3c2a20',
                      length='tunic', legs='sandal'),
    'sleeper_b': dict(face='adult', hat='braid', tunic=ramp4('#7ab0d8', '#4a7ab0', '#2e5084', '#1a2e52'), belt='#d8a040',
                      length='robe', legs='robe', jewels=True),
    'sentinel': dict(face='mask', hat='sentinel', tunic=[PAL['N'], PAL['n'], PAL['b'], PAL['B']], belt='#5a3412', length='tunic',
                     legs='boots', prop='spear', broad=True, vest=True, shield=True),
    'sleeper_c': dict(face='adult', hat='curls', tunic=ramp4('#e07a5a', '#b04a34', '#7a2c22', '#4a1814'), belt='#3c2a20',
                      length='tunic', legs='sandal'),
}


# ----------------------------------------------------------------------------- drawing
def body(cv, cos, view, top, base, cx, t=0.0, step=(0, 0), stride=0.0, bob=0):
    """Torso, belt, skirt or robe, legs; returns shoulder points."""
    tun = cos['tunic']
    kid = cos.get('kid')
    broad = cos.get('broad'); thin = cos.get('thin')
    half = 6 if not broad else 7
    if thin:
        half = 5
    if kid:
        half = 4
    tor_h = 7 if not kid else 5
    if view == 'side':
        half = max(3, half - 2)
    long_ = cos['length'] == 'robe'
    skirt_h = (base - (top + tor_h + 1)) - 1 if long_ else (3 if not kid else 2)
    # legs first (behind the skirt)
    if not long_:
        legh = base - (top + tor_h + 1 + skirt_h) + 2
        for k, (dx, lift) in enumerate((((-4 if view != 'side' else -2 - int(round(stride * 2))), step[0]),
                                        ((1 if view != 'side' else -2 + int(round(stride * 2))), step[1]))):
            lg = Canvas(5, legh + 2)
            for y in range(legh - lift):
                for x in range(3):
                    if y >= legh - lift - 2:
                        c = PAL['l'] if cos['legs'] != 'bare' else (PAL['L'] if y == legh - lift - 1 else PAL['k'])
                        if cos['legs'] == 'sandal' and y == legh - lift - 2:
                            c = PAL['L']
                        if cos['legs'] == 'boots':
                            c = PAL['l'] if x else PAL['L']
                    else:
                        c = PAL['k' if x == 0 else 'S' if x == 1 else 's'] if cos['legs'] != 'boots' or y < 1 else PAL['l' if x else 'L']
                    lg.px(x + 1, y + 1, c)
            outlined(lg)
            cv.blit(lg, cx + dx - 1, base - legh - 1 + lift - 1 + 1)
    # torso + skirt as one outlined shape
    part = Canvas(CELL, CELL)
    y0 = top
    y_belt = top + tor_h
    y_end = y_belt + skirt_h
    for y in range(y0, y_end + 1):
        if y < y_belt:
            w = half if y > y0 + 1 else half + (1 if not kid else 0)
        elif y == y_belt:
            w = half - (1 if not broad else 0)
        else:
            f = (y - y_belt) / max(1, skirt_h)
            w = half - (1 if not broad else 0) + int(round(f * (2 if long_ else 1.5)))
        if view == 'side':
            xl, xr = cx - w, cx + w - 1
        else:
            xl, xr = cx - w, cx + w - 1
        for x in range(xl, xr + 1):
            u = (x - xl) / max(1, xr - xl)
            c = tun[0] if u < 0.15 else tun[1] if u < 0.6 else tun[2]
            if y == y_belt:
                c = rgb(cos['belt']) if u > 0.08 else rgb(cos['belt'])
            elif y == y_end and long_:
                c = tun[3] if (x + int(t * 4)) % 3 else tun[2]
            elif y > y_belt and not long_ and y == y_end:
                c = tun[3] if u > 0.5 else tun[2]
            part.px(x, y, c)
        # robe hem shows the feet
    if long_:
        for dx in ((-3, 1) if view != 'side' else (-1 + int(round(stride * 2)),)):
            for x in range(3):
                part.px(cx + dx + x, y_end + 1, PAL['L' if x < 2 else 'l'])
    if cos.get('apron') and view != 'up':
        ap = rgb(cos['apron'])
        apd = tuple(int(v * 0.78) for v in ap[:3]) + (255,)
        aw = max(2, half - 3) if view != 'side' else 2
        ax0 = cx - aw if view != 'side' else cx + 1
        for y in range(y0 + 2, y_end):
            for x in range(ax0, ax0 + (2 * aw if view != 'side' else aw + 1)):
                part.px(x, y, ap if x < ax0 + aw else apd)
        if cos.get('flour'):
            for (fx, fy) in ((ax0 + 1, y0 + 4), (ax0 + 3, y0 + 7), (ax0 + 2, y0 + 10)):
                part.px(fx, fy, rgb('#ffffff'))
    if cos.get('vest') and view != 'up':
        for y in range(y0 + 1, y_belt):
            for x in range(cx - half + 2, cx + half - 2):
                if (x + y) % 2 == 0:
                    part.px(x, y, PAL['n'] if x < cx else PAL['b'])
                else:
                    part.px(x, y, PAL['N'] if x < cx - 2 else PAL['n'])
    if cos.get('trim'):
        tr = rgb(cos['trim'])
        for y in range(y0 + 1, y_end + 1):
            part.px(cx - 1 if view != 'side' else cx + half - 2, y, tr)
    if cos.get('jewels') and view == 'down':
        for x in range(cx - 2, cx + 2):
            part.px(x, y0 + 1, PAL['N'] if x % 2 else PAL['n'])
    with_outline(part)
    cv.blit(part, 0, 0)
    sh = (cx - half - 1, top + 2) if view != 'side' else (cx, top + 2)
    sh2 = (cx + half, top + 2) if view != 'side' else (cx + 1, top + 2)
    return sh, sh2


def head_canvas(cos, view, eyes):
    kid = cos['face'] == 'kid'
    faces = KID if kid else MASK if cos['face'] == 'mask' else FACE
    key = (view, eyes) if (view, eyes) in faces else (view, 'open')
    face = m2c(faces[key])
    W = 20
    cv = Canvas(W, 22)
    fx, fy = 4, 6
    cv.blit(face, fx, fy)
    if cos.get('beard') and view != 'up':
        rows, dx, dy = BEARD[cos['beard']][view]
        cv.blit(m2c(rows), fx + dx, fy + dy)
    hat = cos.get('hat')
    if hat:
        rows, dx, dy = H[hat][view]
        cv.blit(m2c(rows, HP.get(hat)), fx + dx, fy + dy)
    neck_x = fx + (6 if not kid else 5)
    neck_y = fy + (len(faces[key]))
    return cv, neck_x, neck_y


def render(sheet, view, t=0.0, bob=0, step=(0, 0), stride=0.0, eyes='open', head_dy=0, head_dx=0, hands=None,
           crouch=0, prop=True, lie=False, extra=None):
    cos = COSTUME[sheet]
    cv = Canvas(CELL, CELL)
    cx, base = FX, FY
    kid = cos.get('kid')
    tall = cos.get('tall')
    top = base - (19 if not kid else 13) + bob + crouch - (1 if tall else 0)
    hands = hands or {}
    # spear / net behind
    if prop and cos.get('prop') == 'spear':
        sx = cx + 9 if view == 'down' else (cx - 9 if view == 'up' else cx + 4)
        for y in range(base - 34, base):
            cv.px(sx, y, PAL['L'] if y > base - 30 else PAL['n'])
            cv.px(sx + 1, y, PAL['l'] if y > base - 30 else PAL['b'])
        for k, y in enumerate(range(base - 38, base - 33)):
            for x in range(sx - (k // 2), sx + 2 + (k // 2)):
                cv.px(x, y, PAL['N'] if x <= sx else PAL['b'])
        with_outline(cv)
    sh, sh2 = body(cv, cos, view, top, base, cx, t, step, stride, bob)
    # arms
    if view == 'side':
        hn = hands.get('near', (int(round(stride * 2)), 7 if not kid else 5))
        limb(cv, sh[0], sh[1], sh[0] + hn[0], sh[1] + hn[1], lit=True, bracer=False)
    else:
        hl = hands.get('L', (0, 7 if not kid else 5)); hr = hands.get('R', (0, 7 if not kid else 5))
        limb(cv, sh[0], sh[1], sh[0] + hl[0], sh[1] + hl[1], lit=view != 'up', bracer=False)
        limb(cv, sh2[0], sh2[1], sh2[0] + hr[0], sh2[1] + hr[1], lit=view == 'up', bracer=False)
    if cos.get('shield') and view != 'up':
        rows = ["..oooo..", ".oNWNno.", "oNWnnnbo", "oNnFnnbo", "onnnnbbo", ".obbbbo.", "..oooo.."]
        sx = cx - 9 if view == 'down' else cx + 1
        cv.blit(m2c(rows), sx, top + 3)
    if extra:
        extra(cv, view, cx, top, base)
    h, nx, ny = head_canvas(cos, view, eyes)
    cv.blit(h, cx - nx + head_dx + (1 if view == 'side' else 0), top - ny + 2 + head_dy)
    if lie:
        import numpy as np
        a = np.rot90(cv.a, k=-1).copy()
        nz = np.nonzero(a[:, :, 3] > 0)
        y0_, y1_ = nz[0].min(), nz[0].max(); x0_, x1_ = nz[1].min(), nz[1].max()
        bodyimg = a[y0_:y1_ + 1, x0_:x1_ + 1]
        out = Canvas(CELL, CELL)
        bh, bw = bodyimg.shape[:2]
        oy, ox = base - bh, cx - bw // 2
        out.a[oy:oy + bh, ox:ox + bw] = bodyimg
        return out
    return cv


def dough(cv, view, cx, top, base):
    """Hesha's dough on the trough in front of her."""
    rows = ["..oooooo..", ".owwwwwko.", "owwwwwkkko", "okkkkkksso", ".oooooooo."]
    cv.blit(m2c(rows), cx - 5, top + 8)


# ----------------------------------------------------------------------------- animations
def anim_frames(sheet, name, view, n):
    F = []
    for i in range(n):
        ph = i / n
        breath = 1 if i in (1, 2) and n == 4 else 0
        if name == 'sleep':
            F.append(render(sheet, view, t=ph, eyes='closed', head_dy=1, bob=breath))
        elif name == 'idle':
            F.append(render(sheet, view, t=ph, bob=breath, eyes='closed' if i == 3 and n == 4 and sheet != 'captain_child' else 'open'))
        elif name == 'talk':
            hand = [(0, 7), (2, 3), (3, 1), (2, 3), (0, 6), (1, 4)][i % 6]
            if view == 'side':
                F.append(render(sheet, view, t=ph, eyes='talk' if i % 2 else 'open', hands={'near': (hand[0] + 1, hand[1])}))
            else:
                F.append(render(sheet, view, t=ph, eyes='talk' if i % 2 else 'open', hands={'R': (hand[0] - 3, hand[1])}))
        elif name == 'lie':
            F.append(render(sheet, 'side', t=ph, eyes='closed', lie=True, bob=i % 2))
        elif name == 'lean':
            # asleep on his feet, both hands on the spear haft
            F.append(render(sheet, view, t=ph, eyes='closed', head_dy=1 + (i in (1, 2)), hands={'R': (2, 4)} if view == 'down' else {'near': (3, 4)}))
        elif name == 'knead':
            k = [(2, 6), (3, 8), (2, 6), (1, 7)][i % 4]
            F.append(render(sheet, view, t=ph, eyes='closed', head_dy=1, hands={'L': (k[0] + 2, k[1]), 'R': (-k[0] - 2, k[1])}, extra=dough))
        elif name == 'cower':
            F.append(render(sheet, view, t=ph, eyes='closed', crouch=2, head_dx=(1 if i % 2 else 0), hands={'L': (3, -3), 'R': (-3, -3)}))
        elif name == 'point':
            F.append(render(sheet, view, eyes='open', hands={'R': (2, 1)} if view == 'down' else {'near': (7, -1)}))
        elif name == 'itemget':
            F.append(render(sheet, view, eyes='wide', hands={'L': (2, -8), 'R': (-2, -8)}))
        elif name in ('walk', 'sleepwalk'):
            s_ = math.sin(ph * 2 * math.pi)
            bob = -1 if i % 4 in (1, 2) else 0
            sleepy = name == 'sleepwalk'
            if view == 'side':
                F.append(render(sheet, view, t=ph, stride=s_, bob=bob, eyes='closed' if sleepy else 'open',
                                hands={'near': (5, 1)} if sleepy else None))
            else:
                F.append(render(sheet, view, t=ph, step=(max(0, int(round(s_ * 2))), max(0, int(round(-s_ * 2)))), bob=bob,
                                eyes='closed' if sleepy else 'open',
                                hands={'L': (2, 3), 'R': (-2, 3)} if sleepy and view == 'down' else None))
        elif name == 'shrug':
            F.append(render(sheet, view, eyes='open', bob=-1, hands={'L': (-3, 2), 'R': (3, 2)}))
        elif name == 'hurt':
            F.append(render(sheet, view, eyes='closed', bob=-1, head_dx=-1 if i % 2 else 0,
                            hands={'L': (-3, 3), 'R': (3, 3)} if view != 'side' else {'near': (-3, 3)}))
        elif name == 'sigh':
            F.append(render(sheet, view, eyes='closed', head_dy=1, bob=1))
        else:
            F.append(render(sheet, view, t=ph))
    return F


def export(sheet):
    from PIL import Image
    old = json.load(open(f'{OUT}/{sheet}.json'))
    rows = []
    for a in old['anims']:
        view = 'side' if a['dir'] == 'left' else a['dir']
        fr = anim_frames(sheet, a['name'], view, a['frames'])
        if a['dir'] == 'left':
            fl = []
            for f in fr:
                g = Canvas(CELL, CELL); g.a[:, :] = f.a[:, ::-1]; fl.append(g)
            fr = fl
        rows.append((a, fr))
    W = max(len(r[1]) for r in rows) * CELL
    img = Image.new('RGBA', (W, len(rows) * CELL), (0, 0, 0, 0))
    meta = {"size": CELL, "pivot": [FX, FY], "anims": []}
    for ri, (a, fr) in enumerate(rows):
        for ci, f in enumerate(fr):
            img.paste(f.image(), (ci * CELL, ri * CELL))
        meta["anims"].append({"name": a['name'], "dir": a['dir'], "row": ri, "frames": len(fr)})
    img.save(f'{OUT}/{sheet}.png')
    json.dump(meta, open(f'{OUT}/{sheet}.json', 'w'))
    print(sheet, img.size)


def preview(names, path):
    from PIL import Image, ImageDraw, ImageFont
    Z = 3
    out = Image.new('RGB', (10 + 9 * (60 * Z + 6), 60 + len(names) * (64 * Z + 6)), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((12, 12), 'INTERNAL TEST - townsfolk (x3)', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28))
    for r, name in enumerate(names):
        cells = [render(name, 'down'), render(name, 'side'), render(name, 'up'), render(name, 'down', eyes='closed', head_dy=1),
                 anim_frames(name, 'talk', 'down', 6)[2], anim_frames(name, 'walk', 'side', 8)[2],
                 render(name, 'side', eyes='closed', lie=True)]
        for c, f in enumerate(cells):
            bg = Image.new('RGBA', (CELL, CELL), (58, 84, 70, 255))
            bg.alpha_composite(f.image())
            out.paste(bg.convert('RGB').crop((10, 10, 70, 74)).resize((60 * Z, 64 * Z), Image.NEAREST), (10 + c * (60 * Z + 6), 56 + r * (64 * Z + 6)))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != 'preview']
    names = args or list(COSTUME)
    if 'preview' in sys.argv:
        preview(names, PREVIEWS + '/internal-test-folk.png')
    else:
        for n in names:
            export(n)
