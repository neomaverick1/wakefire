"""AZAR, the night watchman: hand-built pixel art.

The head (bronze cone helmet, flame-red plume, heavy-lidded eyes) is drawn pixel by pixel below,
one map per facing and expression. The body is put together from outlined parts (legs, skirt,
torso, arms, scarf, lantern, khopesh) drawn in code so that every animation frame keeps the same
proportions and light. Light comes from the top left. Every part carries its own dark outline,
the way 16- and 32-bit sprites were built.

    python3 hero.py preview     # a sheet of poses to look at
    python3 hero.py             # writes Resources/Sprites/azar.png + azar.json
"""
import sys, math, json
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas
import os
PREVIEWS = os.environ.get('WF_PREVIEWS', '/tmp/wakefire-previews')
os.makedirs(PREVIEWS, exist_ok=True)

O = (22, 14, 30, 255)
PAL = {
    'o': O,
    # bronze
    'B': (78, 44, 20, 255), 'b': (142, 86, 34, 255), 'n': (204, 140, 52, 255), 'N': (242, 192, 88, 255), 'W': (255, 242, 186, 255),
    # flame red (plume and scarf)
    'r': (112, 20, 20, 255), 'R': (198, 42, 28, 255), 'F': (246, 100, 40, 255), 'Y': (255, 182, 78, 255),
    # skin
    's': (106, 58, 42, 255), 'S': (158, 96, 62, 255), 'k': (206, 140, 90, 255), 'K': (236, 180, 128, 255),
    'w': (246, 238, 224, 255), 'd': (128, 66, 76, 255), 'h': (70, 40, 44, 255),
    # midnight-blue tunic
    'u': (20, 26, 62, 255), 'U': (36, 54, 118, 255), 'v': (58, 90, 176, 255), 'V': (100, 138, 226, 255),
    # leather
    'l': (62, 36, 24, 255), 'L': (112, 64, 36, 255), 'm': (156, 100, 58, 255),
    # lantern glow
    'g': (255, 214, 120, 255), 'G': (255, 250, 214, 255),
}


def m2c(rows):
    w = max(len(r) for r in rows)
    cv = Canvas(w, len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                cv.px(x, y, PAL[ch])
    return cv


# ----------------------------------------------------------------------------- heads
# A Corinthian-style bronze helmet: high dome, a brow ridge, a T-slot through which two
# sleepless eyes look out, cheek plates, a black beard below; a crest of red horsehair on top
# shaped like a flame. Rows are centred automatically.
def centred(rows, w):
    out = []
    for r in rows:
        pad = (w - len(r)) // 2
        out.append('.' * pad + r + '.' * (w - len(r) - pad))
    return out


DOME = ["oNWNnnbo", "oNWWNnnnnbbo", "oNWNNnnnnnnbBo", "oNNNnnnnnnnbBo", "obbnnnnnnnbbBo"]
SLOT = {
    'open':   ["oNnooonbooobBo", "oNoowonbowooBo"],
    'closed': ["oNnooonbooobBo", "oNooooonboooBo"],
    'squint': ["oNnnoonbboobBo", "oNooooonboooBo"],
    'wide':   ["oNnowonbowobBo", "oNoowonbowooBo"],
}
JAW = {
    'shut': ["oNNnnonbobbbBo", "oNnnohhobbBo", "ohhhhhho"],
    'open': ["oNNnnonbobbbBo", "oNnnooooobBo", "ohhoohho"],
}
BACK = ["oNnnnnnnnnnbBo", "oNnnnnnnnnbbBo", "obnnnnnnnbbbBo", "obbbbbbbbbbBBo", "obbbbbbbbbBo", "ohhhhhho"]

CREST_DOWN = [
    ["oo", "oYFo", "oYFFRo", "oFYFRo", "oFYFRRro", "oRFRFRro", "orRRro", "oNbo"],
    [".oo", ".oYFo", "oYFFRo.", "oFYFRo", "oFYFRRro", "oRFRFRro", "orRRro", "oNbo"],
    ["oo.", "oYFo.", ".oYFFRo", "oFYFRo", "oFYFRRro", "oRFRFRro", "orRRro", "oNbo"],
]

# side view, facing right: the crest is a great arc from the brow back over the dome, its
# horsehair streaming off behind the neck
SIDE = {
    'open': [
        "......oNNnbo....",
        "....oNWNNnnbbo..",
        "...oNWNNnnnnbbo.",
        "..oNNNnnnnnnnbBo",
        "..oNnnnnnnnbbbbo",
        "..oNnnnnbbnooono",
        "..oNnnnnbbnowono",
        "..oNnnnnbbbnnnbo",
        "...oNnnbbbbnobo.",
        "....onbbbBhhho..",
        ".....ohhhhhho...",
    ],
}
SIDE['closed'] = SIDE['open'][:6] + ["..oNnnnnbbnooono"] + SIDE['open'][7:]
SIDE['squint'] = SIDE['closed']
SIDE['wide'] = SIDE['open'][:5] + ["..oNnnnnbbnowono", "..oNnnnnbbnowono"] + SIDE['open'][7:]
SIDE_OPENJAW = ["...oNnnbbbbnooo.", "....onbbbBhooo..", ".....ohhhhhho..."]

CREST_SIDE = [
    [".......oooooo..", ".....ooYYYFFFo.", "....oYFFFFRRRRo", "...oFFFRRRrrrro", "..oFFRRrrooooo.", ".oFRRro........", "oRRro..........", "oRro...........", "oro............"],
    [".......oooooo..", ".....ooYYYFFFo.", "...ooYFFFFRRRRo", "..oFFFFRRRrrrro", ".oFFRRrrooooo..", "oFRRro.........", "oRRo...........", ".oRro..........", "..oo..........."],
    [".......oooooo..", ".....ooYYYFFFo.", "....oYFFFFRRRRo", "...oFFFRRRrrrro", "...oFRRrooooo..", "..oFRro........", ".oRRo..........", ".oRro..........", "oro............"],
]


def head(facing, face='open', plume=0, mouth='shut'):
    """facing: down, up, side (facing right). Returns (canvas, neck_x, neck_y): the point under
    the chin where the head sits on the neck."""
    cv = Canvas(24, 26)
    if facing == 'side':
        rows = list(SIDE.get(face, SIDE['open']))
        if mouth == 'open':
            rows = rows[:8] + SIDE_OPENJAW
        cv.blit(m2c(CREST_SIDE[plume % 3]), 1, 2)
        cv.blit(m2c(rows), 4, 6)
        return cv, 4 + 9, 6 + len(rows)
    if facing == 'up':
        rows = centred(DOME + BACK, 14)
    else:
        rows = centred(DOME + SLOT.get(face, SLOT['open']) + JAW[mouth], 14)
    cr = centred(CREST_DOWN[plume % 3], 8)
    cv.blit(m2c(cr), 5 + 3, 0)
    cv.blit(m2c(rows), 5, 7)
    return cv, 5 + 7, 7 + len(rows)


# ----------------------------------------------------------------------------- body parts
# Drawn maps (outline included) for the torso in each facing; limbs drawn in code so they can
# move. Sleeveless midnight-blue tunic, a leather baldric across the chest with the gold
# Wakefire disc where it crosses, a belt with a gold buckle, a skirt of blue strips tipped in gold.
TORSO = {
    'down': [
        "...oooooooooo...",
        "..oVVvvvvvvUUo..",
        ".oVVLLvvvvvvUUo.",
        ".oVVvLLvvvvvUUo.",
        "..oVvvLNWnvUUo..",
        "..oVvvvnFbLUUo..",
        "..oVvvvvvvLLUo..",
        "..olLLLNWLLllo..",
        "..oVVuvvuvvuUo..",
        ".oVVuvvuvvuvUUo.",
        ".onnonnonnonnbo.",
        "..oo.oo.oo.oo...",
    ],
    'up': [
        "...oooooooooo...",
        "..oVVvvvvvvUUo..",
        ".oVVvvRFvRFvUUo.",
        ".oVVvvRrvRrLUUo.",
        "..oVvvRFvRLLUo..",
        "..oVvvRrvLLvUo..",
        "..oVvvFRLLvvUo..",
        "..olLLLLLLLllo..",
        "..oVVuvvuvvuUo..",
        ".oVVuvvuvvuvUUo.",
        ".onnonnonnonnbo.",
        "..oo.oo.oo.oo...",
    ],
    'side': [
        "..oooooooo..",
        ".oUvvvvVVVo.",
        ".oUvLLvvVVVo",
        ".oUvvLLvVVVo",
        ".oUuvvLNWVo.",
        ".oUuvvvnFLo.",
        ".oUuvvvvLLo.",
        ".olllLLNWLo.",
        ".oUuvvuvvVo.",
        "oUuuvvuvvVVo",
        "onbonnonnNno",
        ".oo.oo.oo.oo",
    ],
}


def outlined(part):
    part.outline(O)
    return part


def with_outline(cv):
    cv.outline(O)
    return cv


def leg(h=8, lit=True):
    """Two rows of bare knee under the skirt, then a wrapped leather boot with a pale cuff."""
    cv = Canvas(5, h + 2)
    for y in range(h):
        for x in range(3):
            if y < 2:
                c = ('k' if x == 0 else 'S' if x == 1 else 's') if lit else ('S' if x < 2 else 's')
            elif y == 2:
                c = 'm' if x < 2 else 'L'
            elif y == h - 1:
                c = 'l'
            else:
                c = ('L' if x == 0 else 'l' if x == 1 else 'l') if lit else 'l'
                if lit and x == 0 and y % 3 == 0:
                    c = 'm'
            cv.px(x + 1, y + 1, PAL[c])
    return outlined(cv)


def arm(length=6, lit=True, fist=True):
    """A bare, heavy arm: upper arm in skin, bronze bracer on the forearm, a big fist."""
    cv = Canvas(6, length + 5)
    for y in range(2):
        cv.px(4, y + 1, PAL['S' if lit else 's'])
    for y in range(length):
        for x in range(3):
            if y >= length - 3:
                c = ('N' if x == 0 else 'n' if x == 1 else 'b') if lit else ('n' if x == 0 else 'b' if x == 1 else 'B')
            else:
                c = ('K' if x == 0 else 'k' if x == 1 else 'S') if lit else ('k' if x == 0 else 'S' if x == 1 else 's')
            cv.px(x + 1, y + 1, PAL[c])
    if fist:
        for y, row in enumerate(("kkS", "kSs") if lit else ("kSs", "Sss")):
            for x, ch in enumerate(row):
                cv.px(x + 1, length + 1 + y, PAL[ch])
    return outlined(cv)


def pauldron(lit=True):
    rows = [".oooo.", "oNnnLo", "onLLlo", ".oooo."] if lit else [".oooo.", "onLLlo", "oLLllo", ".oooo."]
    return m2c(rows)


def scarf_wrap(width=12):
    cv = Canvas(width + 2, 4)
    for x in range(width):
        t = x / (width - 1)
        cv.px(x + 1, 1, PAL['Y' if t < 0.25 else 'F' if t < 0.6 else 'R'])
        cv.px(x + 1, 2, PAL['F' if t < 0.3 else 'R' if t < 0.75 else 'r'])
    return outlined(cv)


def lantern(glow=0):
    rows = [
        "..ooo..",
        ".o.n.o.",
        "oNnnnbo",
        "oNgGgbo" if glow == 0 else "oNGgGbo",
        "onggGbo" if glow == 0 else "onGggbo",
        "oNnnnbo",
        ".obbbo.",
        "..ooo..",
    ]
    return m2c(rows)


def khopesh_hilt():
    return m2c(["oo...", "oNo..", "obo..", ".oLo.", ".olo.", "..oo."])


def cape_back(cv, cx, y0, y1, t=0.0, behind=False, flare=0):
    """The red cape seen from behind (or, with behind=True, its edges framing him from the
    front). y0 shoulders, y1 hem."""
    part = Canvas(CELL, CELL)
    H = y1 - y0
    for i in range(H + 1):
        y = y0 + i
        f = i / max(1, H)
        half = (10 if behind else 8) + f * (2.0 + flare)
        wave = math.sin(t * 2 * math.pi + f * 3.0) * f * 0.8
        xl, xr = int(round(cx - half + wave)), int(round(cx + half - 1 + wave))
        for x in range(xl, xr + 1):
            u = (x - xl) / max(1, xr - xl)
            c = 'F' if u < 0.12 else 'R' if u < 0.7 else 'r'
            # folds: two darker creases that open towards the hem
            for k in (-1, 1):
                fx = cx + k * (1.5 + f * 2.5) + wave
                if abs(x - fx) < 0.6 and f > 0.15:
                    c = 'r'
            if i == 0 or (i == 1 and not behind):
                c = 'N' if u < 0.3 else 'n' if u < 0.7 else 'b'
            if i == H and int(x + t * 6) % 3 == 0:
                c = 'r'
            part.px(x, y, PAL[c])
    with_outline(part)
    cv.blit(part, 0, 0)


def cape_side(cv, ax, ay, run=False, t=0.0, length=None):
    """Facing right: the cape hangs behind his back, or streams out behind him when he runs."""
    part = Canvas(CELL, CELL)
    if run:
        L = length or 16
        for i in range(L):
            f = i / (L - 1)
            wave = math.sin(t * 2 * math.pi - i * 0.45) * (0.4 + 2.2 * f)
            x = ax - i
            ytop = ay + wave * 0.6 - f * 1.0
            ybot = ytop + 6 + f * 5 + math.sin(t * 2 * math.pi - i * 0.5 + 1.0) * f
            for y in range(int(round(ytop)), int(round(ybot)) + 1):
                v = (y - ytop) / max(1, ybot - ytop)
                c = 'F' if v < 0.2 else 'R' if v < 0.75 else 'r'
                if i == L - 1 or (i > L - 4 and (y + i) % 3 == 0):
                    c = 'r'
                part.px(x, y, PAL[c])
    else:
        H = length or 16
        for i in range(H):
            f = i / (H - 1)
            sway = math.sin(t * 2 * math.pi + f * 2.5) * f * 0.9
            xl = int(round(ax - 2 - f * 3.5 + sway))
            xr = int(round(ax + 2 + sway * 0.3))
            for x in range(xl, xr + 1):
                u = (x - xl) / max(1, xr - xl)
                c = 'r' if u < 0.3 else 'R' if u < 0.85 else 'F'
                part.px(x, ay + i, PAL[c])
    with_outline(part)
    cv.blit(part, 0, 0)


def brooch():
    return m2c([".oo.", "oWNo", "oNbo", ".oo."])


# ----------------------------------------------------------------------------- whole poses
CELL = 80
FX, FY = 40, 62     # feet: centre x, the row just below the soles


# ----------------------------------------------------------------------------- the general pose
def limb(cv, x0, y0, x1, y1, lit=True, bracer=True, fist=True):
    """A thick arm from shoulder (x0, y0) to hand (x1, y1): skin, then a bronze bracer, then a fist.
    Drawn on its own layer and outlined, so it reads over the body."""
    part = Canvas(CELL, CELL)
    L = max(1.0, math.hypot(x1 - x0, y1 - y0))
    n = int(L * 2) + 1
    for i in range(n + 1):
        f = i / n
        x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        if bracer and f > 0.5:
            ramp = ('N', 'n', 'b') if lit else ('n', 'b', 'B')
        else:
            ramp = ('K', 'k', 'S') if lit else ('k', 'S', 's')
        for (dx, dy, k) in ((-1, 0, 0), (0, 0, 1), (1, 0, 2), (0, -1, 1), (0, 1, 2)):
            part.px(int(round(x)) + dx, int(round(y)) + dy, PAL[ramp[k]])
    if fist:
        hx, hy = int(round(x1)), int(round(y1))
        for (dx, dy, c) in ((-1, -1, 'k'), (0, -1, 'k'), (1, -1, 'S'), (-1, 0, 'k'), (0, 0, 'S'), (1, 0, 's'), (-1, 1, 'S'), (0, 1, 's'), (1, 1, 's')):
            part.px(hx + dx, hy + dy, PAL[c] if lit else PAL['S' if c == 'k' else 's'])
    with_outline(part)
    cv.blit(part, 0, 0)


def khopesh(cv, hx, hy, ang, length=13):
    """The bronze khopesh from the hand at (hx, hy) pointing at screen angle ang (degrees,
    0 = right, 90 = down): leather grip, a straight neck, then the deep hooked blade, two pixels
    thick with a bright cutting edge on the outside of the curve."""
    part = Canvas(CELL, CELL)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    for i in range(length * 3 + 1):
        f = i / (length * 3)
        d = f * length
        bend = 0 if f < 0.5 else (f - 0.5) ** 1.5 * 10.0
        x, y = hx + ux * d + nx * bend, hy + uy * d + ny * bend
        X, Y = int(round(x)), int(round(y))
        if f < 0.2:
            part.px(X, Y, PAL['l'])
            continue
        part.px(X, Y, PAL['n'])
        if f > 0.32:
            ex, ey = int(round(x + nx * 1.0)), int(round(y + ny * 1.0))
            part.px(ex, ey, PAL['W' if f > 0.45 else 'N'])
            if f > 0.6:
                sx, sy = int(round(x - nx * 1.0)), int(round(y - ny * 1.0))
                part.px(sx, sy, PAL['b'])
    gx, gy = hx + ux * 2.6, hy + uy * 2.6
    for k in (-1.4, -0.7, 0.7, 1.4):
        part.px(int(round(gx + nx * k)), int(round(gy + ny * k)), PAL['N' if k < 0 else 'b'])
    with_outline(part)
    cv.blit(part, 0, 0)


def smear(cv, cx, cy, r0, r1, a0, a1, strength=1.0):
    """The bright crescent a fast blade leaves: crisp at the leading edge (a1), thinning and
    breaking up towards a0. Angles in degrees on screen (0 right, 90 down); the swing goes from
    a0 to a1 either way round."""
    delta = ((a1 - a0 + 540.0) % 360.0) - 180.0      # the short way round
    sgn = 1 if delta >= 0 else -1
    span = max(1.0, abs(delta))
    r0 = max(r0, r1 - 4.5)
    for y in range(int(cy - r1 - 1), int(cy + r1 + 2)):
        for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < r0 or d > r1:
                continue
            ang = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx))
            rel = ((ang - a0) * sgn) % 360.0
            if rel > span:
                continue
            v = rel / span * strength
            rr = (d - r0) / max(0.5, r1 - r0)
            # thinner towards the tail
            if rr < (1 - v) * 0.8:
                continue
            if v > 0.86:
                c = 'G' if rr > 0.45 else 'W'
            elif v > 0.6:
                c = 'W' if rr > 0.6 else 'N'
            elif v > 0.35:
                if (x + y) % 2:
                    continue
                c = 'N'
            else:
                continue
            cv.px(x, y, PAL[c])


def shield(cv, x, y):
    """The Bronze Mirror Shield, face on: a disc of polished bronze with a bright mirror centre."""
    rows = ["..oooooo..", ".obNNNNnbo.", "obNWWWNnnbo", "oNWGWNnnnbo", "oNWWNnnnbbo", "oNNnnnnbbbo", "onnnnnbbbBo", ".obnnbbbBo.", "..oooooo.."]
    cv.blit(m2c(rows), x - 5, y - 4)


def lantern_lit(glow):
    rows = ["..ooo..", ".o.n.o.", "oNnnnbo", "oNGGGbo", "oGGGGGo" if glow > 1 else "oNGGgbo", "oNnnnbo", ".obbbo.", "..ooo.."]
    return m2c(rows)


def ball(cv, cx, cy, ang, t):
    """Mid-roll: wrapped in the cape, a ball of red with the helmet tumbling round its rim."""
    part = Canvas(CELL, CELL)
    R = 7
    for y in range(cy - R, cy + R + 1):
        for x in range(cx - R, cx + R + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= R:
                u = (x - cx + y - cy) / (2 * R)
                c = 'F' if u < -0.45 else 'R' if u < 0.3 else 'r'
                part.px(x, y, PAL[c])
    a = math.radians(ang)
    hx, hy = cx + math.cos(a) * (R - 2), cy + math.sin(a) * (R - 2)
    for y in range(int(hy) - 3, int(hy) + 4):
        for x in range(int(hx) - 3, int(hx) + 4):
            d = math.hypot(x - hx, y - hy)
            if d <= 3.2:
                part.px(x, y, PAL['W' if d < 1.2 and x < hx else 'N' if d < 2.2 else 'n'])
    # the crest flicks out beyond the rim
    for i in range(1, 4):
        part.px(int(round(hx + math.cos(a) * (2 + i))), int(round(hy + math.sin(a) * (2 + i))), PAL['F' if i < 3 else 'R'])
    # boots, tucked
    b = math.radians(ang + 180)
    part.px(int(round(cx + math.cos(b) * (R - 1))), int(round(cy + math.sin(b) * (R - 1))), PAL['l'])
    with_outline(part)
    cv.blit(part, 0, 0)


def render(view, t=0.0, bob=0, crouch=0, step=(0, 0), stride=0.0, run=False, face='open', mouth='shut', crest=None,
           head_dx=0, head_dy=0, hands=None, sword=None, sword_behind=False, smear_=None, shield_=False,
           lantern_='hip', glow=0, flare=0, lean=0, tilt=None):
    """One frame. view: down, up, side (facing right). hands: {'L': (dx, dy), 'R': (dx, dy)}
    offsets of each hand from its shoulder (down/up: L = viewer's left; side: 'near', 'far')."""
    cv = Canvas(CELL, CELL)
    cx, base = FX, FY
    top = base - 21 + bob + crouch
    crest = int(t * 3) % 3 if crest is None else crest
    lift_l, lift_r = step
    legh = 8 - crouch
    if view in ('down', 'up'):
        back = view == 'up'
        sl, sr = (cx - 8, top + 3), (cx + 7, top + 3)
        hands = hands or {}
        hl = hands.get('L', (-1, 9)); hr = hands.get('R', (1, 9))
        L_hand = (sl[0] + hl[0], sl[1] + hl[1]); R_hand = (sr[0] + hr[0], sr[1] + hr[1])
        sword_hand = R_hand if back else L_hand
        if back and (sword or smear_):
            # facing away: the blade is out in front of him, i.e. further up the screen, behind him
            if smear_:
                smear(cv, *smear_)
            if sword:
                khopesh(cv, sword_hand[0], sword_hand[1], *sword)
        if not back:
            cape_back(cv, cx, top + 1, base - 5, t, behind=True, flare=flare)
        cv.blit(leg(max(3, legh - lift_l), lit=not back), cx - 5, base - 1 - max(3, legh - lift_l) - lift_l)
        cv.blit(leg(max(3, legh - lift_r), lit=back), cx, base - 1 - max(3, legh - lift_r) - lift_r)
        if not back and sword_behind and sword:
            khopesh(cv, sword_hand[0], sword_hand[1], *sword)
        cv.blit(m2c(TORSO['up' if back else 'down']), cx - 8, top)
        if back:
            if lantern_ == 'hip':
                cv.blit(lantern(int(t * 4) % 2), cx - 11, top + 9)
            cape_back(cv, cx, top, base - 5, t, behind=False, flare=flare)
        limb(cv, sl[0], sl[1], L_hand[0], L_hand[1], lit=not back)
        limb(cv, sr[0], sr[1], R_hand[0], R_hand[1], lit=back)
        if not back:
            if lantern_ == 'hip':
                cv.blit(lantern(int(t * 4) % 2), cx + 4, top + 9)
            if not sword:
                cv.blit(khopesh_hilt(), cx - 8, top + 8)
        cv.blit(pauldron(not back), cx - 11, top + 1)
        cv.blit(pauldron(back), cx + 5, top + 1)
        if not back:
            cv.blit(scarf_wrap(12), cx - 7, top - 1)
            cv.blit(brooch(), cx - 7, top - 1)
        if lantern_ == 'hand':
            lh = R_hand if not back else L_hand
            cv.blit(lantern_lit(glow), lh[0] - 3, lh[1] - 1)
        h, nx, ny = head('up' if back else 'down', face, crest, mouth)
        cv.blit(h, cx - nx + head_dx, top - ny + 3 + head_dy)
        if shield_ and not back:
            shield(cv, cx, top + 7)
        if not back and not sword_behind:
            if sword:
                khopesh(cv, sword_hand[0], sword_hand[1], *sword)
            if smear_:
                smear(cv, *smear_)
    else:
        sw = int(round(stride * 3))
        sh_near, sh_far = (cx - 1 + lean, top + 3), (cx + 1 + lean, top + 3)
        hands = hands or {}
        hn = hands.get('near', (sw, 9)); hf = hands.get('far', (-sw, 9))
        near_hand = (sh_near[0] + hn[0], sh_near[1] + hn[1]); far_hand = (sh_far[0] + hf[0], sh_far[1] + hf[1])
        cape_side(cv, cx - 3 + lean, top + 1, run=run, t=t)
        limb(cv, sh_far[0], sh_far[1], far_hand[0], far_hand[1], lit=False)
        cv.blit(leg(max(3, legh), lit=False), cx - 2 + sw, base - 1 - max(3, legh) + (1 if run and stride > 0.4 else 0))
        cv.blit(leg(max(3, legh), lit=True), cx - 2 - sw, base - 1 - max(3, legh) + (1 if run and stride < -0.4 else 0))
        cv.blit(m2c(TORSO['side']), cx - 6 + lean, top)
        if lantern_ == 'hip':
            cv.blit(lantern(int(t * 4) % 2), cx - 5 + lean, top + 9)
        cv.blit(pauldron(True), cx - 3 + lean, top + 1)
        if sword_behind and sword:
            khopesh(cv, near_hand[0], near_hand[1], *sword)
        limb(cv, sh_near[0], sh_near[1], near_hand[0], near_hand[1], lit=True)
        if lantern_ == 'hand':
            cv.blit(lantern_lit(glow), near_hand[0] - 3, near_hand[1] - 1)
        cv.blit(scarf_wrap(8), cx - 5 + lean, top - 1)
        h, nx, ny = head('side', face, crest, mouth)
        cv.blit(h, cx - nx + 1 + lean + head_dx, top - ny + 3 + head_dy)
        if shield_:
            shield(cv, cx + 6 + lean, top + 7)
        if sword and not sword_behind:
            khopesh(cv, near_hand[0], near_hand[1], *sword)
        if smear_:
            smear(cv, *smear_)
    if tilt == 'lie':
        # flat on the ground: the whole figure turned onto its side
        import numpy as np
        a = np.rot90(cv.a, k=-1).copy()
        cv = Canvas(CELL, CELL)
        cv.a[:, :] = 0
        sub = a[16:64, 8:56]
        cv.a[64 - 48 + 4 - 18:64 - 18 + 4, 8:56] = sub[:48 - 18 + 18 - 18 + 18][:48] if False else 0
        cv.a[:, :] = 0
        h_, w_ = a.shape[:2]
        # keep what sits on the ground: move the body so it lies along the feet line
        nz = np.nonzero(a[:, :, 3] > 0)
        y0_, y1_ = nz[0].min(), nz[0].max(); x0_, x1_ = nz[1].min(), nz[1].max()
        body = a[y0_:y1_ + 1, x0_:x1_ + 1]
        bh, bw = body.shape[:2]
        oy, ox = base - bh, cx - bw // 2
        cv.a[oy:oy + bh, ox:ox + bw] = body
    return cv


# ----------------------------------------------------------------------------- animations
def frames_for(anim, view):
    """Every animation the game asks for, frame by frame, for one view."""
    F = []
    side = view == 'side'
    if anim == 'idle':
        for i in range(4):
            F.append(render(view, t=i / 4, bob=1 if i in (1, 2) else 0))
    elif anim == 'run':
        for i in range(8):
            ph = i / 8
            s_ = math.sin(ph * 2 * math.pi)
            bob = -1 if i % 4 in (1, 2) else 0
            if side:
                F.append(render(view, t=ph, stride=s_, run=True, bob=bob, lean=1))
            else:
                F.append(render(view, t=ph, step=(max(0, int(round(s_ * 2))), max(0, int(round(-s_ * 2)))), bob=bob,
                                hands={'L': (-1, 9 + int(round(-s_ * 1.5))), 'R': (1, 9 + int(round(s_ * 1.5)))}, flare=1))
    elif anim in ('attack1', 'attack2', 'attack3'):
        F.extend(attack_frames(anim, view))
    elif anim == 'roll':
        for i in range(10):
            if i == 0:
                F.append(render(view, t=0.1, crouch=3, bob=1, face='squint'))
            elif i == 9:
                F.append(render(view, t=0.9, crouch=1, face='open'))
            elif i == 8:
                F.append(render(view, t=0.8, crouch=3, face='squint'))
            else:
                cv = Canvas(CELL, CELL)
                start = {'down': 270, 'up': 90, 'side': 180}[view]
                step_ = {'down': 60, 'up': -60, 'side': 60}[view]
                ball(cv, FX, FY - 8, start + step_ * (i - 1), i / 8)
                F.append(cv)
    elif anim == 'hurt':
        for i in range(2):
            if side:
                F.append(render(view, t=0.3, bob=-1, lean=-1 - i, face='squint', hands={'near': (-4, 4), 'far': (-3, 3)}))
            else:
                F.append(render(view, t=0.3, bob=-1, face='squint', hands={'L': (-4, 2 - i), 'R': (4, 2 - i)}, flare=2))
    elif anim == 'death':
        for i in range(8):
            if i == 0:
                F.append(render(view, t=0.3, bob=-1, face='squint', hands={'L': (-4, 2), 'R': (4, 2)} if not side else {'near': (-4, 4), 'far': (-3, 3)}))
            elif i == 1:
                F.append(render(view, t=0.4, crouch=2, face='squint'))
            elif i in (2, 3):
                F.append(render(view, t=0.5, crouch=4, head_dy=i - 1, face='closed', hands={'L': (0, 6), 'R': (0, 6)} if not side else {'near': (2, 6), 'far': (1, 6)}))
            else:
                F.append(render('side', t=0.2, face='closed', tilt='lie'))
    elif anim == 'block':
        F.append(render(view, t=0.2, shield_=view != 'up', hands={'L': (3, 3), 'R': (-3, 3)} if not side else {'near': (4, 4), 'far': (3, 4)}))
    elif anim == 'push':
        for i in range(6):
            s_ = math.sin(i / 6 * 2 * math.pi)
            if side:
                F.append(render(view, t=i / 6, stride=s_ * 0.6, lean=2, face='squint', hands={'near': (6, 2), 'far': (6, 1)}))
            else:
                F.append(render(view, t=i / 6, step=(max(0, int(round(s_))), max(0, int(round(-s_)))), face='squint',
                                hands={'L': (3, 5), 'R': (-3, 5)} if view == 'down' else {'L': (3, -2), 'R': (-3, -2)}, bob=1))
    elif anim == 'use':
        for i in range(3):
            if side:
                F.append(render(view, t=i / 3, lantern_='hand', glow=1 + (i > 0), hands={'near': (7, 0)}, face='wide' if i else 'open'))
            else:
                F.append(render(view, t=i / 3, lantern_='hand', glow=1 + (i > 0), hands={'R': (-1, 2) if view == 'down' else (-3, -3)}, face='wide' if i else 'open'))
    elif anim == 'itemget':
        F.append(render(view, t=0.2, face='wide', hands={'L': (3, -13), 'R': (-3, -13)} if not side else {'near': (3, -13), 'far': (2, -13)}))
    elif anim == 'nod':
        for i in range(3):
            F.append(render(view, t=i / 3, face='closed', head_dy=i, crest=2))
    elif anim == 'wake':
        seq = [('closed', 2, 0), ('wide', -1, -1), ('wide', 0, 0), ('open', 0, 0)]
        for (f_, hd, bb) in seq:
            F.append(render(view, t=0.3, face=f_, head_dy=hd, bob=bb, hands=None if side else ({'L': (-3, 6), 'R': (3, 6)} if f_ == 'wide' else None)))
    elif anim == 'doze':
        for i in range(9):
            sway = [0, 0, 1, 1, 1, 0, 0, -1, -1][i]
            F.append(render(view, t=i / 9, face='closed', head_dy=2, head_dx=sway if not side else 0, bob=1 if i in (3, 4, 5) else 0, crest=2))
    elif anim == 'idle_nod':
        seq = [('open', 0), ('closed', 1), ('closed', 2), ('closed', 3), ('wide', -1)]
        for (f_, hd) in seq:
            F.append(render(view, t=0.4, face=f_, head_dy=hd))
    elif anim == 'yawn':
        arms = [None, (2, 4), (3, -2), (3, -8), (3, -8), (3, -6), (2, 2), None]
        for i in range(8):
            a = arms[i]
            m_ = 'open' if 2 <= i <= 5 else 'shut'
            f_ = 'closed' if 2 <= i <= 5 else 'open'
            if a is None:
                F.append(render(view, t=i / 8, face=f_, mouth=m_))
            elif side:
                F.append(render(view, t=i / 8, face=f_, mouth=m_, hands={'near': (a[0] - 4, a[1]), 'far': (a[0] - 5, a[1])}, bob=-1 if 3 <= i <= 4 else 0))
            else:
                F.append(render(view, t=i / 8, face=f_, mouth=m_, hands={'L': (-a[0], a[1]), 'R': (a[0], a[1])}, bob=-1 if 3 <= i <= 4 else 0))
    elif anim == 'sigh':
        for i in range(2):
            F.append(render(view, t=0.5, face='closed', head_dy=1, bob=1, hands={'L': (-1, 10), 'R': (1, 10)} if not side else None))
    elif anim == 'shrug':
        F.append(render(view, t=0.5, face='open', bob=-1, hands={'L': (-5, 3), 'R': (5, 3)} if not side else {'near': (4, 3), 'far': (3, 3)}))
    elif anim == 'point':
        F.append(render(view, t=0.5, face='open', hands={'R': (-2, 9)} if view == 'up' else ({'L': (2, 9)} if view == 'down' else {'near': (9, -1)})))
    return F


def attack_frames(anim, view):
    """The three swings of the khopesh combo. The blow lands on frame 2 (frame 3 for the heavy
    third swing); these are the frames the game strikes on."""
    side = view == 'side'
    F = []
    cx, cy = FX, FY - 12
    if view == 'down':
        if anim == 'attack1':      # forehand: from his right (screen left) across the front
            keys = [((-6, -3), 210, None, -1), ((-6, 3), 150, (cx, cy + 2, 7, 15, 190, 150), 0), ((-1, 9), 95, (cx, cy + 2, 7, 16, 165, 90), 1),
                    ((5, 8), 40, (cx, cy + 2, 7, 15, 140, 40), 1), ((4, 6), 60, None, 0), ((1, 7), 100, None, 0)]
        elif anim == 'attack2':    # backhand: back the other way
            keys = [((6, 6), 30, None, 0), ((5, 8), 45, (cx, cy + 2, 7, 15, 20, 50), 0), ((0, 9), 95, (cx, cy + 2, 7, 16, 25, 100), 1),
                    ((-5, 7), 150, (cx, cy + 2, 7, 15, 50, 160), 1), ((-4, 6), 130, None, 0), ((-1, 7), 100, None, 0)]
        else:                      # overhead: raise it high, bring it down hard in front
            keys = [((-3, -2), 260, None, -1), ((-2, -6), 280, None, -2), ((-1, -8), 285, None, -2), ((0, 10), 90, (cx - 1, cy, 6, 18, 215, 95), 2),
                    ((0, 10), 92, (cx - 1, cy, 6, 18, 150, 95), 2), ((0, 9), 100, None, 1), ((0, 8), 110, None, 0)]
        for (h, ang, sm, bob) in keys:
            F.append(render(view, t=0.3, bob=bob if bob < 2 else 1, crouch=1 if bob == 2 else 0, hands={'L': h}, sword=(ang, 12),
                            smear_=sm, face='squint' if sm else 'open'))
    elif view == 'up':
        if anim == 'attack1':
            keys = [((6, -1), 330, None), ((5, -6), 300, (cx, cy - 4, 7, 15, 345, 300)), ((0, -9), 268, (cx, cy - 4, 7, 16, 350, 265)),
                    ((-5, -6), 220, (cx, cy - 4, 7, 15, 320, 215)), ((-4, -3), 230, None), ((-1, 1), 260, None)]
        elif anim == 'attack2':
            keys = [((-6, -1), 210, None), ((-5, -6), 240, (cx, cy - 4, 7, 15, 195, 240)), ((0, -9), 272, (cx, cy - 4, 7, 16, 190, 275)),
                    ((5, -6), 320, (cx, cy - 4, 7, 15, 220, 325)), ((4, -3), 310, None), ((1, 1), 280, None)]
        else:
            keys = [((2, 2), 90, None), ((2, -4), 250, None), ((1, -7), 265, None), ((0, -10), 270, (cx, cy - 2, 6, 18, 90, 270)),
                    ((0, -10), 270, (cx, cy - 2, 6, 18, 150, 270)), ((0, -6), 265, None), ((0, -2), 260, None)]
        for (h, ang, sm) in keys:
            F.append(render(view, t=0.3, hands={'R': h}, sword=(ang, 12), smear_=sm))
    else:  # side, facing right
        if anim == 'attack1':      # overhand cut, high to low in front
            keys = [((-3, -6), 240, None, 0), ((2, -8), 300, (cx + 1, cy + 1, 7, 15, 250, 300), 0), ((8, -1), 0, (cx + 1, cy + 1, 7, 16, 270, 15), 1),
                    ((7, 4), 55, (cx + 1, cy + 1, 7, 15, 300, 60), 1), ((5, 5), 70, None, 0), ((3, 6), 80, None, 0)]
        elif anim == 'attack2':    # rising cut, low to high
            keys = [((4, 7), 80, None, 0), ((7, 4), 50, (cx + 1, cy + 1, 7, 15, 100, 50), 0), ((8, -1), -5, (cx + 1, cy + 1, 7, 16, 90, -10), 1),
                    ((3, -7), 290, (cx + 1, cy + 1, 7, 15, 60, -70), 1), ((1, -5), 280, None, 0), ((2, 0), 330, None, 0)]
        else:                      # heavy: wind back, then a great arc in front
            keys = [((-5, -3), 200, None, 0), ((-4, -7), 235, None, -1), ((-1, -9), 260, None, -1), ((9, 0), 5, (cx + 2, cy, 6, 18, 200, 10), 2),
                    ((9, 2), 20, (cx + 2, cy, 6, 18, 260, 25), 2), ((6, 5), 50, None, 1), ((4, 6), 70, None, 0)]
        for (h, ang, sm, lean) in keys:
            F.append(render(view, t=0.3, lean=lean, crouch=1 if lean == 2 else 0, hands={'near': h}, sword=(ang, 12), smear_=sm,
                            face='squint' if sm else 'open', sword_behind=(ang > 180 and ang < 330 and not sm)))
    return F


ANIMS = [('idle', 4), ('run', 8), ('attack1', 6), ('attack2', 6), ('attack3', 7), ('roll', 10), ('hurt', 2), ('death', 8),
         ('nod', 3), ('wake', 4), ('use', 3), ('itemget', 1), ('push', 6), ('block', 1), ('doze', 9), ('yawn', 8),
         ('shrug', 1), ('point', 1), ('sigh', 2), ('idle_nod', 5)]


def export(out_png='/srv/Wakefire/Assets/Wakefire/Resources/Sprites/azar.png', out_json='/srv/Wakefire/Assets/Wakefire/Resources/Sprites/azar.json'):
    import numpy as np
    from PIL import Image
    rows = []
    for (name, n) in ANIMS:
        for d in ('down', 'left', 'up'):
            view = 'side' if d == 'left' else d
            fr = frames_for(name, view)
            assert len(fr) == n, (name, d, len(fr), n)
            if d == 'left':
                flipped = []
                for f in fr:
                    g = Canvas(CELL, CELL)
                    g.a[:, :] = f.a[:, ::-1]
                    flipped.append(g)
                fr = flipped
            rows.append((name, d, fr))
    W = max(len(r[2]) for r in rows) * CELL
    sheet = Image.new('RGBA', (W, len(rows) * CELL), (0, 0, 0, 0))
    meta = {"size": CELL, "pivot": [FX, FY], "anims": []}
    for ri, (name, d, fr) in enumerate(rows):
        for ci, f in enumerate(fr):
            sheet.paste(f.image(), (ci * CELL, ri * CELL))
        meta["anims"].append({"name": name, "dir": d, "row": ri, "frames": len(fr)})
    sheet.save(out_png)
    json.dump(meta, open(out_json, 'w'))
    print('azar sheet', sheet.size, len(rows), 'rows')
    return rows


def preview_all(path, names=None):
    from PIL import Image, ImageDraw, ImageFont
    names = names or [n for n, _ in ANIMS]
    Z = 3
    blocks = []
    for name in names:
        for view in ('down', 'side', 'up'):
            blocks.append((name, view, frames_for(name, view)))
    cols = 10
    rows_n = len(blocks)
    out = Image.new('RGB', (cols * (CELL * Z + 4) + 160, rows_n * (CELL * Z + 4) + 60), (20, 18, 24))
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    d.text((12, 12), 'INTERNAL TEST - hero animations (x3)', fill=(255, 80, 60), font=f)
    for r, (name, view, fr) in enumerate(blocks):
        y = 50 + r * (CELL * Z + 4)
        d.text((8, y + 8), f'{name}\n{view}', fill=(220, 220, 220), font=fs)
        for c, fcv in enumerate(fr[:cols]):
            bg = Image.new('RGBA', (CELL, CELL), (58, 84, 70, 255))
            bg.alpha_composite(fcv.image())
            out.paste(bg.convert('RGB').resize((CELL * Z, CELL * Z), Image.NEAREST), (150 + c * (CELL * Z + 4), y))
    out.save(path)
    print(out.size)


def preview():
    from PIL import Image, ImageDraw, ImageFont
    frames = []
    for i in range(4):
        c = Canvas(CELL, CELL); pose_down(c, t=i / 4, plume=i % 3, bob=1 if i in (1, 2) else 0); frames.append(c)
    for i in range(4):
        c = Canvas(CELL, CELL); pose_side(c, t=i / 4, plume=i % 3, bob=1 if i in (1, 2) else 0); frames.append(c)
    for i in range(4):
        c = Canvas(CELL, CELL); pose_down(c, t=i / 4, plume=i % 3, bob=1 if i in (1, 2) else 0, back=True); frames.append(c)
    for i in range(8):
        ph = i / 8
        c = Canvas(CELL, CELL); pose_side(c, t=ph, stride=math.sin(ph * 2 * math.pi), plume=i % 3, bob=-1 if i % 4 in (1, 2) else 0, run=True); frames.append(c)
    for i in range(8):
        ph = i / 8
        s = math.sin(ph * 2 * math.pi)
        c = Canvas(CELL, CELL); pose_down(c, t=ph, step=(max(0, int(round(s * 2))), max(0, int(round(-s * 2)))), plume=i % 3, bob=-1 if i % 4 in (1, 2) else 0, arms=((0, int(round(-s))), (0, int(round(s))))); frames.append(c)
    Z = 4
    cols = 8
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGB', (cols * (CELL * Z + 6) + 10, rows * (CELL * Z + 6) + 70), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((12, 12), 'INTERNAL TEST - new hero, first pass (x4)', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30))
    for i, f in enumerate(frames):
        bg = Image.new('RGBA', (CELL, CELL), (58, 84, 70, 255))
        bg.alpha_composite(f.image())
        out.paste(bg.convert('RGB').resize((CELL * Z, CELL * Z), Image.NEAREST), (10 + (i % cols) * (CELL * Z + 6), 60 + (i // cols) * (CELL * Z + 6)))
    out.save(PREVIEWS + '/internal-test-hero-new.png')
    print(out.size)


if __name__ == '__main__':
    if 'preview' in sys.argv:
        preview()
    elif 'anims' in sys.argv:
        preview_all(PREVIEWS + '/internal-test-anims.png', sys.argv[2:] or None)
    else:
        export()
