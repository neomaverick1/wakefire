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


def goat(view, t=0.0, step=0.0, head='normal', bob=0, mouth=False, chew=0):
    """side view faces right. head: normal, down (eating), up (bleating), stare (turned to us), butt."""
    cv = Canvas(CELL, CELL)
    cx, base = FX, FY
    by = base - 11 + bob
    if view == 'side':
        # far legs
        legs = layer()
        for k, (lx, ph) in enumerate(((-7, 0.0), (5, 0.5), (-5, 0.5), (7, 0.0))):
            sw = math.sin((t + ph) * 2 * math.pi) * step
            lift = max(0, int(round(-math.cos((t + ph) * 2 * math.pi) * step * 1.5)))
            hip = cx + lx
            x = hip + int(round(sw * 2))
            c = GOAT[3] if k < 2 else GOAT[2]
            line(legs, hip, by + 3, x, base - 2 - lift, c, 2)
            legs.px(x, base - 1 - lift, rgb('#3a3030')); legs.px(x + 1, base - 1 - lift, rgb('#3a3030'))
            if k == 1:
                put(cv, legs); legs = layer()
        put(cv, legs)
        body = layer()
        ellipse(body, cx - 1, by, 9, 5, GOAT)
        # tail tuft
        line(body, cx - 10, by - 3, cx - 11, by - 6, GOAT[1])
        put(cv, body)
        # neck and head
        hd = layer()
        if head == 'down':
            hx, hy = cx + 10, by + 4
        elif head == 'up':
            hx, hy = cx + 9, by - 9
        elif head == 'butt':
            hx, hy = cx + 11, by + 1
        else:
            hx, hy = cx + 8, by - 6
        line(hd, cx + 5, by - 1, hx - 1, hy + 1, GOAT[1], 3)
        if head == 'stare':
            goat_face(hd, int(hx), int(hy) - 1, False, False, 0)
            put(cv, hd)
            goat_horns(cv, int(hx), int(hy) - 1)
            goat_eyes(cv, int(hx), int(hy) - 1)
            return cv
        ellipse(hd, hx, hy, 3.6, 3.0, GOAT)
        # muzzle
        mx = hx + (3 if head != 'down' else 2)
        my = hy + (1 if head not in ('down',) else 2)
        ellipse(hd, mx, my, 2.0, 1.6, GOAT)
        hd.px(int(mx + 1), int(my), rgb('#d89a9a'))
        if mouth:
            hd.px(int(mx), int(my + 1), O); hd.px(int(mx + 1), int(my + 1), O)
        # beard
        for k in range(3 + chew):
            hd.px(int(mx - 1), int(my + 2 + k), GOAT[2] if k else GOAT[1])
        # ear
        line(hd, hx - 2, hy - 1, hx - 5, hy + 1, GOAT[2], 1)
        hd.px(int(hx - 5), int(hy + 2), GOAT[3])
        put(cv, hd)
        # horns, curving back
        hn = layer()
        for k in range(6):
            a = math.radians(-100 - k * 18)
            hn.px(int(round(hx - 1 + math.cos(a) * (2 + k * 0.7))), int(round(hy - 2 + math.sin(a) * (2 + k * 0.6))), HORN[min(2, k // 2)])
        put(cv, hn)
        # the eye: amber with a goat's flat black pupil
        cv.px(int(hx), int(hy - 1), AMBER); cv.px(int(hx + 1), int(hy - 1), AMBER); cv.px(int(hx + 1), int(hy - 1), O)
        return cv
    # front (down) and back (up)
    back = view == 'up'
    legs = layer()
    for k, lx in enumerate((-4, 3)):
        sw = math.sin((t + k * 0.5) * 2 * math.pi) * step
        lift = max(0, int(round(sw * 1.5)))
        for y in range(by + 2, base - 1 - lift):
            legs.px(cx + lx, y, GOAT[2]); legs.px(cx + lx + 1, y, GOAT[3])
        legs.px(cx + lx, base - 1 - lift, rgb('#3a3030')); legs.px(cx + lx + 1, base - 1 - lift, rgb('#3a3030'))
    put(cv, legs)
    body = layer()
    ellipse(body, cx, by - 1, 6, 6 if not back else 6.5, GOAT)
    if back:
        line(body, cx, by - 7, cx, by - 9, GOAT[1])
    put(cv, body)
    hd = layer()
    hy = by - 8 if head != 'down' else by - 3
    goat_face(hd, cx, hy, back, mouth, chew)
    put(cv, hd)
    goat_horns(cv, cx, hy)
    if not back:
        goat_eyes(cv, cx, hy)
    return cv


def goat_face(hd, cx, hy, back=False, mouth=False, chew=0):
    if not back:
        ellipse(hd, cx, hy, 4.2, 3.6, GOAT)
        ellipse(hd, cx, hy + 3, 2.4, 2.0, GOAT)
        hd.px(cx - 1, hy + 4, rgb('#d89a9a')); hd.px(cx, hy + 4, rgb('#d89a9a'))
        if mouth:
            hd.px(cx - 1, hy + 5, O); hd.px(cx, hy + 5, O)
        for k in range(3 + chew):
            hd.px(cx - 1 + (k % 2), hy + 6 + k, GOAT[2])
        # ears stick out sideways
        line(hd, cx - 4, hy - 1, cx - 7, hy, GOAT[2]); line(hd, cx + 4, hy - 1, cx + 7, hy, GOAT[3])
    else:
        ellipse(hd, cx, hy, 4.0, 3.4, [GOAT[1], GOAT[2], GOAT[2], GOAT[3]])
        line(hd, cx - 4, hy, cx - 7, hy + 1, GOAT[2]); line(hd, cx + 4, hy, cx + 7, hy + 1, GOAT[3])


def goat_horns(cv, cx, hy):
    hn = layer()
    for s_ in (-1, 1):
        for k in range(6):
            a = math.radians(-90 + s_ * (20 + k * 14))
            hn.px(int(round(cx + s_ * 2 + math.cos(a) * (1 + k * 0.6))), int(round(hy - 3 + math.sin(a) * (1 + k * 0.7))), HORN[min(2, k // 2)])
    put(cv, hn)


def goat_eyes(cv, cx, hy):
    # the stare: two amber eyes with the flat black bar of a goat's pupil, set wide
    for ex in (cx - 3, cx + 2):
        cv.px(ex, hy - 1, AMBER); cv.px(ex + 1, hy - 1, AMBER)
        cv.px(ex + (1 if ex < cx else 0), hy - 1, O)


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


GALLOP = [  # hind foot offset, front foot offset, lift, body stretch, bob
    (3, -3, 0, 0, -1),     # gathered under
    (-3, 3, 0, 2, 0),      # pushing off, reaching
    (-4, 4, 2, 3, -2),     # in the air
    (1, 1, 0, 1, 0),       # landing
]


def hound(view, ramp, t=0.0, step=0.0, pose='stand', bob=0, ears='tall', snout=5, length=8, eye=rgb('#f0d060'),
          gallop=None):
    """A lean four-legged animal facing right (side) or the viewer (down) or away (up).
    pose: stand, crouch, lunge, sleep. gallop: a frame of the run (0-3) for the side view."""
    cv = Canvas(CELL, CELL)
    cx, base = FX, FY
    low = {'stand': 0, 'crouch': 3, 'lunge': -1, 'sleep': 6}[pose]
    g = GALLOP[gallop] if gallop is not None and view == 'side' else None
    by = base - 10 + low + bob + (g[4] if g else 0)
    if view == 'side':
        stretch = 3 if pose == 'lunge' else (g[3] if g else 0)
        legs = layer()
        if pose != 'sleep':
            for k, (lx, ph) in enumerate(((-length + 2, 0.0), (length - 2, 0.5), (-length + 4, 0.5), (length, 0.0))):
                sw = math.sin((t + ph) * 2 * math.pi) * step
                lift = max(0, int(round(-math.cos((t + ph) * 2 * math.pi) * step * 2)))
                hip = cx + lx + (stretch if k in (1, 3) else -stretch)
                foot = hip + int(round(sw * 2.5))
                if g:
                    foot = hip + (g[0] if k in (0, 2) else g[1]) + (1 if k >= 2 else 0)
                    lift = g[2]
                if pose == 'lunge':
                    foot = hip + (-3 if k in (0, 2) else 4)
                c = ramp[3] if k < 2 else ramp[2]
                line(legs, hip, by + 2, foot, base - 2 - lift, c)
                legs.px(foot, base - 1 - lift, ramp[3]); legs.px(foot + 1, base - 1 - lift, ramp[3])
                if k == 1:
                    put(cv, legs); legs = layer()
        put(cv, legs)
        body = layer()
        ellipse(body, cx, by, length + stretch, 3.6, ramp)
        # dark saddle along the back
        for x in range(cx - length + 2, cx + length - 1):
            body.px(x, int(by - 3), ramp[3] if (x % 3) else ramp[2])
        # tail
        tx = cx - length - stretch
        for k in range(6):
            body.px(tx - k, int(by - 1 + k * (0.5 if pose != 'sleep' else 0.2)), ramp[2] if k < 4 else ramp[3])
            body.px(tx - k, int(by + k * 0.5), ramp[3])
        put(cv, body)
        hd = layer()
        if pose == 'sleep':
            hx, hy = cx + length - 1, by
        elif pose == 'crouch':
            hx, hy = cx + length + 2, by - 1
        elif pose == 'lunge':
            hx, hy = cx + length + 5, by - 2
        else:
            hx, hy = cx + length + 1, by - 5
        line(hd, cx + length - 3, by - 1, hx - 1, hy + 1, ramp[1], 3)
        ellipse(hd, hx, hy, 3.2, 2.8, ramp)
        line(hd, hx + 2, hy + 1, hx + 2 + snout - 2, hy + 1.5, ramp[1], 1)
        line(hd, hx + 2, hy + 2, hx + 2 + snout - 3, hy + 2, ramp[2], 1)
        hd.px(int(hx + snout), int(hy + 1), O)
        if pose == 'lunge':
            hd.px(int(hx + snout - 1), int(hy + 3), rgb('#f4ecdc')); hd.px(int(hx + snout - 2), int(hy + 3), O)
        # ears
        if ears == 'tall':
            line(hd, hx - 1, hy - 2, hx - 2, hy - 6, ramp[1]); line(hd, hx, hy - 2, hx, hy - 6, ramp[2])
        else:
            line(hd, hx - 1, hy - 2, hx - 3, hy + 1, ramp[2]); hd.px(int(hx - 3), int(hy + 2), ramp[3])
        put(cv, hd)
        if pose != 'sleep':
            cv.px(int(hx + 1), int(hy - 1), eye)
        else:
            cv.px(int(hx + 1), int(hy - 1), O)
        return cv
    back = view == 'up'
    legs = layer()
    for k, lx in enumerate((-3, 2)):
        sw = math.sin((t + k * 0.5) * 2 * math.pi) * step
        lift = max(0, int(round(sw * 2)))
        for y in range(by + 1, base - 1 - lift):
            legs.px(cx + lx, y, ramp[2]); legs.px(cx + lx + 1, y, ramp[3])
        legs.px(cx + lx, base - 1 - lift, ramp[3]); legs.px(cx + lx + 1, base - 1 - lift, ramp[3])
    put(cv, legs)
    body = layer()
    ellipse(body, cx, by - 1, 5, 5 + (2 if back else 0), ramp)
    if back:
        for k in range(5):
            body.px(cx, by + 3 + k, ramp[2] if k < 3 else ramp[3])
    put(cv, body)
    hd = layer()
    hy = by - 7 + (3 if pose in ('crouch',) else 0) + (2 if pose == 'lunge' else 0)
    ellipse(hd, cx, hy, 3.6, 3.2, ramp if not back else [ramp[1], ramp[2], ramp[2], ramp[3]])
    if not back:
        ellipse(hd, cx, hy + 3, 1.8, 2.0, ramp)
        hd.px(cx - 1, hy + 5, O); hd.px(cx, hy + 5, O)
        if pose == 'lunge':
            hd.px(cx - 1, hy + 6, rgb('#f4ecdc')); hd.px(cx, hy + 6, O)
    if ears == 'tall':
        line(hd, cx - 2, hy - 2, cx - 4, hy - 7, ramp[1]); line(hd, cx + 2, hy - 2, cx + 4, hy - 7, ramp[2])
    else:
        line(hd, cx - 3, hy - 1, cx - 5, hy + 2, ramp[2]); line(hd, cx + 3, hy - 1, cx + 5, hy + 2, ramp[3])
    put(cv, hd)
    if not back:
        if pose == 'sleep':
            cv.px(cx - 2, hy - 1, O); cv.px(cx + 1, hy - 1, O)
        else:
            cv.px(cx - 2, hy - 1, eye); cv.px(cx + 1, hy - 1, eye)
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
