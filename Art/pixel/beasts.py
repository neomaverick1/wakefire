"""The animals and creatures of Ashkel in the hand-built pixel style: the goat (who is always
awake), the dog by the well, the jackals of the terraces, the brine crabs, the dream moths.

Drawn in code from simple shaded shapes with a dark outline round every part, light from the
top left. Writes Resources/Sprites/<sheet>.png/.json with the animations and frame counts the
game already asks for.

    python3 beasts.py preview [names]
    python3 beasts.py [names]
"""
import sys, math, json
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas
from hero import PAL, O, outlined, with_outline, CELL, FX, FY
import os
PREVIEWS = os.environ.get('WF_PREVIEWS', '/tmp/wakefire-previews')
os.makedirs(PREVIEWS, exist_ok=True)

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Sprites'


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def ellipse(part, cx, cy, rx, ry, ramp, light=(-0.6, -0.8)):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = dx * dx + dy * dy
            if d <= 1.0:
                l = -(dx * light[0] + dy * light[1]) * 0.6 + (1 - d) * 0.35
                i = 0 if l > 0.45 else 1 if l > 0.1 else 2 if l > -0.3 else 3
                part.px(x, y, ramp[i])


def line(part, x0, y0, x1, y1, c, w=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        f = i / n
        x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        for k in range(w):
            part.px(int(round(x)) + k, int(round(y)), c)


def layer():
    return Canvas(CELL, CELL)


def put(cv, part):
    with_outline(part)
    cv.blit(part, 0, 0)


# ----------------------------------------------------------------------------- the goat
GOAT = [rgb('#f8f4e8'), rgb('#dcd4c4'), rgb('#ada294'), rgb('#7a7068')]
HORN = [rgb('#c8b494'), rgb('#8c7a62'), rgb('#5a4c40')]
AMBER = rgb('#f0b440')


GP = {'O': O, 'W': rgb('#fbf7ec'), 'w': rgb('#d8d0c0'), 'g': rgb('#a89e92'), 'G': rgb('#6e6660'), 'H': rgb('#d8c4a0'),
      'h': rgb('#8c7a62'), 'A': rgb('#f0b440'), 'P': rgb('#e8a0a0'), 'K': rgb('#3a3030')}
G_BODY = [
    ".O...............",
    "OWO.OOOOOOOO.....",
    "OWWOWWWWWWWWOO...",
    ".OWWWWWWWWWWWWO..",
    ".OWWWWWWWWWWWWWO.",
    ".OWWWWWWWWWWWWwO.",
    ".OwWWWWWWWWWWwwO.",
    ".OwwWWWWWWWwwwgO.",
    "..OgwwwwwwwwggO..",
    "...OOOOOOOOOOO...",
]
G_HEAD = [
    "......OO.....",
    ".....OHHO....",
    "....OHhOOO...",
    "...OhhOWWWO..",
    ".OOOOOWWAOWO.",
    "OwwOWWWWWWWPO",
    ".OwOWWWWWWOO.",
    "..OOwWWWwO...",
    "....OwwOgO...",
    ".....OOOgO...",
    ".......OOO...",
]
G_FRONT = [
    "..OO......OO..",
    ".OHhO....OhHO.",
    ".OhHOOOOOOHhO.",
    "..OOWWWWWWOO..",
    "OOOWWWWWWWWOOO",
    "OwwWAOWWOAWwwO",
    ".OOWWWWWWWWOO.",
    "..OWWwPPwWWO..",
    "..OwWWWWWWwO..",
    ".OWWWOggOWWWO.",
    ".OWWWWggWWWWO.",
    ".OWWWWWWWWWwO.",
    ".OwWWWWWWWwwO.",
    "..OwwwwwwwgO..",
]
G_BACK = [
    "..OO......OO..",
    ".OHhO....OhHO.",
    ".OhHOOOOOOHhO.",
    "..OOWWWWWWOO..",
    "OOOWWWWWWWWOOO",
    "OwwWWWWWWWWwwO",
    ".OOWWWWWWwwOO.",
    "..OWWWWWWWwO..",
    ".OWWWWOOWWWwO.",
    ".OWWWWOWOWWwO.",
    ".OWWWWWOWWwwO.",
    ".OWWWWWWWWwwO.",
    ".OwWWWWWWwwgO.",
    "..OwwwwwwggO..",
]


def stamp(cv, rows, x0, y0, pal=None):
    pal = pal or GP
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != '.' and 0 <= x0 + i < CELL and 0 <= y0 + j < CELL:
                cv.a[y0 + j, x0 + i] = pal[ch]


def gleg(cv, x, top, base, far, dx=0, lift=0):
    """A goat leg: two pixels wide, outlined, a dark hoof."""
    c1, c2 = ('g', 'G') if far else ('w', 'g')
    n = base - 2 - lift - top
    for k in range(max(1, n)):
        xx = x + int(round(dx * (k + 1) / max(1, n)))
        y = top + k
        cv.a[y, xx] = GP[c1]; cv.a[y, xx + 1] = GP[c2]
        for ox in (-1, 2):
            if cv.a[y, xx + ox, 3] == 0:
                cv.a[y, xx + ox] = O
    fy = base - 2 - lift
    for ox in (-1, 0, 1, 2):
        cv.a[fy, x + dx + ox] = GP['K'] if ox in (0, 1) else O
        cv.a[fy + 1, x + dx + ox] = O


def goat(view, t=0.0, step=0.0, head='normal', bob=0, mouth=False, chew=0):
    """The goat, pixel by pixel. side faces right. head: normal, down, up, stare, butt."""
    cv = Canvas(CELL, CELL)
    base = FY
    if view == 'side':
        bx, by = FX - 9, base - 15 + bob
        ph = [0.0, 0.5, 0.5, 0.0]
        xs = [bx + 3, bx + 11, bx + 5, bx + 13]
        for k in (0, 1, 2, 3):
            sw = math.sin((t + ph[k]) * 2 * math.pi) * step
            lift = max(0, int(round(-math.cos((t + ph[k]) * 2 * math.pi) * step * 1.4)))
            if k == 2:
                stamp(cv, G_BODY, bx, by)
            gleg(cv, xs[k], by + 9, base, k < 2, int(round(sw * 2)), lift)
        if step == 0 and False:
            pass
        # make sure the body covers the far legs' tops
        stamp(cv, G_BODY, bx, by)
        for k in (2, 3):
            sw = math.sin((t + ph[k]) * 2 * math.pi) * step
            lift = max(0, int(round(-math.cos((t + ph[k]) * 2 * math.pi) * step * 1.4)))
            gleg(cv, xs[k], by + 9, base, False, int(round(sw * 2)), lift)
        if head == 'stare':
            stamp(cv, G_FRONT[:10], bx + 9, by - 7)
            return cv
        hx_, hy_ = {'normal': (10, -6), 'down': (12, 3), 'up': (9, -8), 'butt': (13, -2)}[head]
        hrows = [list(r) for r in G_HEAD]
        if mouth:
            hrows[6] = list(".OwOWWWWWOO..")
            hrows[7] = list("..OOwWWwOOO..")
        if chew:
            hrows[8] = list("....OwwOgO...") if chew % 2 == 0 else list("....OwwgOO...")
        stamp(cv, hrows, bx + hx_, by + hy_)
        return cv
    rows = G_FRONT if view == 'down' else G_BACK
    gx, gy = FX - 7, base - 18 + bob
    for k, x in enumerate((gx + 3, gx + 9)):
        sw = math.sin((t + k * 0.5) * 2 * math.pi) * step
        gleg(cv, x, gy + 13, base, k == 1, 0, max(0, int(round(sw * 1.5))))
    rr = [list(r) for r in rows]
    if view == 'down':
        if mouth:
            rr[8] = list("..OwWWOOWWwO..")
        if head == 'down':
            gy += 0
    stamp(cv, rr, gx, gy + (3 if head == 'down' else 0))
    return cv


def goat_frames(name, view, n):
    F = []
    for i in range(n):
        ph = i / n
        if name == 'idle':
            F.append(goat(view, t=ph, bob=1 if i in (2, 3) else 0, chew=i % 2))
        elif name == 'walk':
            F.append(goat(view, t=ph, step=1.0, bob=-1 if i % 4 in (1, 2) else 0))
        elif name == 'eat':
            F.append(goat(view, t=ph, head='down', chew=i % 2))
        elif name == 'bleat':
            F.append(goat(view, t=ph, head='up' if view == 'side' else 'normal', mouth=i in (1, 2)))
        elif name == 'butt':
            F.append(goat(view, t=ph, head='butt', step=0.6 if i < 3 else 0, bob=1 if i == 2 else 0))
        elif name == 'stare':
            # the side body, the head turned full on to look at you
            F.append(goat('side', t=ph, head='stare', bob=0))
        else:
            F.append(goat(view, t=ph))
    return F


# ----------------------------------------------------------------------------- four-legged hunters
JACKAL = [rgb('#e8c48a'), rgb('#c8965a'), rgb('#94683a'), rgb('#5a3c22')]
DOG = [rgb('#d8a874'), rgb('#a8703e'), rgb('#7a4c28'), rgb('#4a2c16')]


HP_JACKAL = {'O': O, 'J': rgb('#e0a860'), 'j': rgb('#a8703a'), 'D': rgb('#5a3c22'), 'c': rgb('#f4e0b4'), 'A': rgb('#ffe060'), 'K': rgb('#241410')}
HP_DOG = {'O': O, 'J': rgb('#c08850'), 'j': rgb('#8a5a30'), 'D': rgb('#6a4424'), 'c': rgb('#ecd8b0'), 'A': rgb('#2a1c18'), 'K': rgb('#241410')}
H_SIDE = [
    "..................OO....",
    ".................OjO.O..",
    ".................OjjOjO.",
    "................OJJJJJO.",
    "...............OJJAJJJJO",
    "OO....OOOOOOOOOOJJJJJJjKO",
    "OjO.OOJJJJJJJJJJJJjjjOOO",
    ".OjOJDDDDDDDDJJJJJjOO...",
    ".OJJJJJJJJJJJJJJJjO.....",
    "..OJJJJJJJJJJJjjjjO.....",
    "..OjjjjccccccccjcO......",
    "...OOOOOOOOOOOOOO.......",
]
H_SIDE_DOG = [
    "........................",
    "........................",
    ".................OOOO...",
    "................OJJJJJO.",
    "...............OjjAJJJJO",
    "OO....OOOOOOOOOOjjJJJJjKO",
    "OjO.OOJJJJJJJJJOjjJjjOOO",
    ".OjOJDDDDDDDDJJJOOjOO...",
    ".OJJJJJJJJJJJJJJJjO.....",
    "..OJJJJJJJJJJJjjjjO.....",
    "..OjjjjccccccccjcO......",
    "...OOOOOOOOOOOOOO.......",
]
H_FRONT = [
    ".OO......OO.",
    "OjjO....OjjO",
    "OjJjOOOOjJjO",
    ".OJJJJJJJJO.",
    ".OJAOJJOAJO.",
    ".OJJJccJJJO.",
    "..OJcKKcJO..",
    "..OJJccJJO..",
    ".OJJJJJJJJO.",
    ".OJJccccJJO.",
    ".OjJccccJjO.",
    "..OjjjjjjO..",
]
H_FRONT_DOG = [
    "............",
    "..OOOOOOOO..",
    ".OJJJJJJJJO.",
    "OjOJJJJJJOjO",
    "OjOAOJJOAOjO",
    "OjOJJccJJOjO",
    ".OOJcKKcJOO.",
    "..OJJccJJO..",
    ".OJJJJJJJJO.",
    ".OJJccccJJO.",
    ".OjJccccJjO.",
    "..OjjjjjjO..",
]
H_BACK = [
    ".OO......OO.",
    "OjjO....OjjO",
    "OjJjOOOOjJjO",
    ".OJJJJJJJJO.",
    ".OJJJJJJJJO.",
    ".OJJDDDDJJO.",
    "..OJDDDDJO..",
    "..OJDDDDJO..",
    ".OJJDDDDJJO.",
    ".OJJJDDJJJO.",
    ".OjJJjjJJjO.",
    "..OjjOOjjO..",
]
GALLOP = [(3, -3, 0), (-3, 3, 0), (-4, 4, 2), (1, 1, 0)]      # hind foot, front foot, lift


def hleg(cv, pal, x, top, base, far, dx=0, lift=0):
    c = pal['j'] if not far else pal['D']
    n = max(1, base - 1 - lift - top)
    for k in range(n):
        xx = x + int(round(dx * (k + 1) / n)); y = top + k
        cv.a[y, xx] = c
        for ox in (-1, 1):
            if cv.a[y, xx + ox, 3] == 0:
                cv.a[y, xx + ox] = O
    fy = base - 1 - lift
    for ox in (-1, 0, 1, 2):
        cv.a[fy, x + dx + ox] = pal['D'] if ox in (0, 1) else O
    for ox in (0, 1):
        if fy + 1 < CELL:
            cv.a[fy + 1, x + dx + ox] = O


def hound(view, ramp, t=0.0, step=0.0, pose='stand', bob=0, ears='tall', snout=5, length=8, eye=None, gallop=None):
    """Jackal (tall ears) or dog (flop ears), pixel by pixel. side faces right."""
    dog = ears != 'tall'
    pal = HP_DOG if dog else HP_JACKAL
    cv = Canvas(CELL, CELL)
    base = FY
    low = {'stand': 0, 'crouch': 2, 'lunge': 0, 'sleep': 4}[pose]
    if view == 'side':
        rows = [list(r) for r in (H_SIDE_DOG if dog else H_SIDE)]
        if pose == 'sleep':
            rows[4] = list(''.join(rows[4]).replace('A', 'K'))
        bx = FX - 11 + (3 if pose == 'lunge' else 0)
        by = base - 17 + bob + low + (-1 if gallop == 2 else 0)
        if pose != 'sleep':
            xs = [bx + 4, bx + 14, bx + 6, bx + 16]
            ph = [0.0, 0.5, 0.5, 0.0]
            for k in range(4):
                sw = math.sin((t + ph[k]) * 2 * math.pi) * step
                lift = max(0, int(round(-math.cos((t + ph[k]) * 2 * math.pi) * step * 1.4)))
                dx = int(round(sw * 2))
                if gallop is not None:
                    g = GALLOP[gallop]; dx = g[0] if k in (0, 2) else g[1]; lift = g[2]
                if pose == 'lunge':
                    dx = -3 if k in (0, 2) else 4
                if k == 2:
                    stamp(cv, rows, bx, by, pal)
                hleg(cv, pal, xs[k], by + 11, base, k < 2, dx, lift)
        stamp(cv, rows, bx, by if pose != 'sleep' else base - 12, pal)
        if pose != 'sleep':
            for k in (2, 3):
                pass
        return cv
    rows = [list(r) for r in ((H_FRONT_DOG if dog else H_FRONT) if view == 'down' else H_BACK)]
    if pose == 'sleep' and view == 'down':
        rows[4] = list(''.join(rows[4]).replace('A', 'K'))
    gx = FX - 6
    gy = base - 16 + bob + low
    if pose != 'sleep':
        for k, x in enumerate((gx + 3, gx + 8)):
            sw = math.sin((t + k * 0.5) * 2 * math.pi) * step
            hleg(cv, pal, x, gy + 11, base, False, 0, max(0, int(round(sw * 1.5))))
    else:
        gy = base - 12
    stamp(cv, rows, gx, gy, pal)
    return cv


def hound_frames(sheet, name, view, n):
    ramp = JACKAL if sheet == 'jackal' else DOG
    ears = 'tall' if sheet == 'jackal' else 'flop'
    snout = 5 if sheet == 'jackal' else 4
    length = 8 if sheet == 'jackal' else 7
    F = []
    for i in range(n):
        ph = i / n
        kw = dict(ears=ears, snout=snout, length=length)
        if name == 'idle':
            F.append(hound(view, ramp, t=ph, bob=1 if i in (1, 2) else 0, **kw))
        elif name == 'walk':
            F.append(hound(view, ramp, t=ph, step=0.8, bob=-1 if i % 2 else 0, **kw))
        elif name == 'run':
            if view == 'side':
                F.append(hound(view, ramp, gallop=i % 4, **kw))
            else:
                F.append(hound(view, ramp, t=ph, step=1.4, bob=-1 if i % 2 else 0, **kw))
        elif name == 'crouch':
            F.append(hound(view, ramp, pose='crouch', **kw))
        elif name == 'lunge':
            F.append(hound(view, ramp, t=ph, step=1.5, pose='lunge', **kw))
        elif name == 'hurt':
            F.append(hound(view, ramp, pose='crouch', bob=-1, **kw))
        elif name == 'sleep':
            F.append(hound(view, ramp, t=ph, pose='sleep', bob=i % 2, **kw))
        else:
            F.append(hound(view, ramp, t=ph, **kw))
    return F


# ----------------------------------------------------------------------------- the brine crab
SHELL = [rgb('#ff9a6a'), rgb('#e0582e'), rgb('#a8341c'), rgb('#6a1c10')]


def crab(t=0.0, claws=0.0, step=0.0, hurt=False):
    """Seen from above and in front: a broad shell, eyes on stalks, two big claws."""
    cv = Canvas(CELL, CELL)
    cx, base = FX, FY
    by = base - 6
    legs = layer()
    for s_ in (-1, 1):
        for k in range(3):
            ph = math.sin((t + k * 0.33 + (0.5 if s_ > 0 else 0)) * 2 * math.pi) * step
            x0 = cx + s_ * 6
            y0 = by - 1 + k * 2
            x1 = cx + s_ * (10 + k)
            y1 = by + 2 + k * 2 + int(round(ph))
            line(legs, x0, y0, x1, y1, SHELL[2])
            legs.px(x1, y1 + 1, SHELL[3])
    put(cv, legs)
    shell = layer()
    ellipse(shell, cx, by - 1, 8, 5, SHELL)
    # a ridge of bumps
    for x in range(cx - 5, cx + 6, 3):
        shell.px(x, by - 4, SHELL[0])
    put(cv, shell)
    # eyes on stalks
    for ex in (cx - 3, cx + 3):
        st = layer()
        line(st, ex, by - 5, ex, by - 8, SHELL[2])
        st.px(ex, by - 9, rgb('#1a0f14')); st.px(ex - 1 if ex < cx else ex + 1, by - 9, rgb('#1a0f14'))
        put(cv, st)
        cv.px(ex, by - 9, rgb('#f4ecdc'))
    # claws: raised and open when it attacks
    for s_ in (-1, 1):
        cl = layer()
        ax, ay = cx + s_ * 8, by - 2
        lift = int(round(claws * 6))
        px_, py_ = ax + s_ * 3, ay - 2 - lift
        line(cl, ax, ay, px_, py_, SHELL[1], 2)
        ellipse(cl, px_ + s_ * 1, py_ - 1, 2.8, 2.2, SHELL)
        # the pincer gap
        gap = 1 + int(round(claws * 2))
        for g in range(gap):
            gx, gy = px_ + s_ * 2, py_ - 2 - g
            if 0 <= gx < CELL and 0 <= gy < CELL:
                cl.a[gy, gx] = (0, 0, 0, 0)
        put(cv, cl)
    if hurt:
        cv.a[:, :, :3] = (cv.a[:, :, :3] * 0.5 + 127).astype('uint8')
    return cv


def crab_frames(name, n):
    F = []
    for i in range(n):
        ph = i / n
        if name == 'walk':
            F.append(crab(t=ph, step=1.2, claws=0.1))
        elif name == 'attack':
            F.append(crab(t=ph, claws=[0.3, 0.8, 1.0, 0.4, 0.1][i % 5]))
        elif name == 'hurt':
            F.append(crab(t=ph, hurt=i == 0, claws=0.5))
        else:
            F.append(crab(t=ph, claws=0.1 + 0.1 * (i % 2)))
    return F


# ----------------------------------------------------------------------------- the dream moth
MOTH = [rgb('#fff4d8'), rgb('#e8c8f0'), rgb('#a884c8'), rgb('#5a3a84')]


def moth(t=0.0):
    cv = Canvas(CELL, CELL)
    cx, cy = FX, FY - 14
    flap = math.sin(t * 2 * math.pi)
    wings = layer()
    for s_ in (-1, 1):
        span = 6 + int(round(flap * 2))
        ellipse(wings, cx + s_ * (span * 0.6), cy - 1 - flap, span * 0.6, 3.2 + flap * 0.6, MOTH)
        ellipse(wings, cx + s_ * 3, cy + 3, 2.6, 2.2, [MOTH[1], MOTH[2], MOTH[2], MOTH[3]])
        # an eye-spot on each wing
        wings.px(int(round(cx + s_ * (span * 0.6))), int(round(cy - 1 - flap)), rgb('#ffd060'))
    put(cv, wings)
    b = layer()
    ellipse(b, cx, cy + 1, 1.6, 4, [rgb('#e8dcc8'), rgb('#b0a090'), rgb('#7a6a5a'), rgb('#4a3c30')])
    line(b, cx - 1, cy - 3, cx - 3, cy - 6, MOTH[2]); line(b, cx + 1, cy - 3, cx + 3, cy - 6, MOTH[2])
    put(cv, b)
    return cv


# ----------------------------------------------------------------------------- export
def frames(sheet, name, view, n):
    if sheet == 'goat':
        return goat_frames(name, view, n)
    if sheet in ('jackal', 'dog'):
        return hound_frames(sheet, name, view, n)
    if sheet == 'crab':
        return crab_frames(name, n)
    if sheet == 'moth':
        return [moth(i / n) for i in range(n)]
    raise KeyError(sheet)


def export(sheet):
    from PIL import Image
    old = json.load(open(f'{OUT}/{sheet}.json'))
    rows = []
    for a in old['anims']:
        view = 'side' if a['dir'] == 'left' else a['dir']
        fr = frames(sheet, a['name'], view, a['frames'])
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
    blocks = []
    for nm in names:
        old = json.load(open(f'{OUT}/{nm}.json'))
        for a in old['anims']:
            view = 'side' if a['dir'] == 'left' else a['dir']
            blocks.append((f"{nm} {a['name']} {a['dir']}", frames(nm, a['name'], view, a['frames'])))
    cols = 8
    out = Image.new('RGB', (200 + cols * (60 * Z + 4), 50 + len(blocks) * (50 * Z + 4)), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((10, 10), 'INTERNAL TEST - creatures (x3)', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26))
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    for r, (label, fr) in enumerate(blocks):
        y = 46 + r * (50 * Z + 4)
        d.text((6, y + 10), label, fill=(220, 220, 220), font=fs)
        for c, f in enumerate(fr[:cols]):
            bg = Image.new('RGBA', (CELL, CELL), (58, 84, 70, 255))
            bg.alpha_composite(f.image())
            out.paste(bg.convert('RGB').crop((10, 18, 70, 68)).resize((60 * Z, 50 * Z), Image.NEAREST), (200 + c * (60 * Z + 4), y))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != 'preview']
    names = args or ['goat', 'dog', 'jackal', 'crab', 'moth']
    if 'preview' in sys.argv:
        preview(names, PREVIEWS + '/internal-test-beasts.png')
    else:
        for n in names:
            export(n)
