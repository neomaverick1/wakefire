"""The on-screen buttons for phones, made the way a smith would make them: each one is a little
relief in bronze, gold and dark blue enamel. The shapes are laid down as heights, the heights are
lit from the upper left like metal under a lamp, and the result is saved large so it stays sharp
on any screen.  python3 touch_art.py [preview.png]"""
import math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/UI/Touch'
DENSITY = 6            # texture pixels per game pixel
SS = 3                 # each texture pixel is worked out from SS x SS samples

BRONZE, GOLD, ENAMEL, DARK = 0, 1, 2, 3
ALBEDO = np.array([(0.56, 0.33, 0.15), (0.95, 0.68, 0.22), (0.045, 0.055, 0.15), (0.10, 0.06, 0.05)])
SPEC = np.array([(1.00, 0.80, 0.52), (1.00, 0.93, 0.66), (0.45, 0.55, 0.90), (0.3, 0.25, 0.2)])
SHINE = np.array([26.0, 44.0, 70.0, 12.0])
GLINT = np.array([0.55, 0.85, 0.30, 0.1])
KEY = np.array([-0.46, -0.64, 0.62]); KEY /= np.linalg.norm(KEY)
FILL = np.array([0.55, 0.50, 0.67]); FILL /= np.linalg.norm(FILL)


def grid(n):
    c = (np.arange(n * SS) + 0.5) / (n * SS) * 2 - 1
    return np.meshgrid(c * 1.08, c * 1.08)          # a little room round the disc for its shadow


# ------------------------------------------------------------------ shapes as distances (inside is negative)
def circle(X, Y, cx, cy, r): return np.hypot(X - cx, Y - cy) - r


def capsule(X, Y, a, b, r):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / (dx * dx + dy * dy + 1e-12), 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) - r


def stroke(X, Y, pts, radii):
    """A line of changing thickness through the points."""
    d = np.full(X.shape, 9.0)
    pts = np.asarray(pts, float); radii = np.broadcast_to(np.asarray(radii, float), (len(pts),))
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, 6, endpoint=False):
            p = pts[i] + (pts[i + 1] - pts[i]) * t; r = radii[i] + (radii[i + 1] - radii[i]) * t
            d = np.minimum(d, np.hypot(X - p[0], Y - p[1]) - r)
    d = np.minimum(d, np.hypot(X - pts[-1][0], Y - pts[-1][1]) - radii[-1])
    return d


def polygon(X, Y, pts):
    pts = np.asarray(pts, float)
    d = np.full(X.shape, 9.0); inside = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        d = np.minimum(d, capsule(X, Y, a, b, 0.0))
        cond = ((a[1] > Y) != (b[1] > Y)) & (X < (b[0] - a[0]) * (Y - a[1]) / (b[1] - a[1] + 1e-12) + a[0])
        inside ^= cond
    return np.where(inside, -d, d)


def box(X, Y, cx, cy, hw, hh, r=0.0):
    qx = np.abs(X - cx) - hw + r; qy = np.abs(Y - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def rot(pts, deg, s=1.0, at=(0, 0)):
    c, sn = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [((x * c - y * sn) * s + at[0], (x * sn + y * c) * s + at[1]) for (x, y) in pts]


def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


# ------------------------------------------------------------------ the engraved signs (y runs down the screen)
def khopesh(X, Y):
    """The sickle-sword: grip and pommel, a straight neck, then the blade swinging out and hooking back."""
    T = lambda pts: rot(pts, 38, 0.86, (-0.02, 0.03))
    grip = stroke(X, Y, T([(0, 0.80), (0, 0.50)]), [0.06, 0.06])
    pommel = circle(X, Y, *T([(0, 0.84)])[0], 0.085)
    guard = stroke(X, Y, T([(-0.15, 0.47), (0.15, 0.47)]), [0.04, 0.04])
    neck = stroke(X, Y, T([(0, 0.47), (0, 0.06)]), [0.05, 0.058])
    curve = arc(-0.13, -0.36, 0.45, 73, -62, 30)
    w = [0.058 + 0.045 * math.sin(math.pi * min(1.0, t * 1.15)) for t in np.linspace(0, 1, 30)]
    w = [wi * (1 - max(0.0, t - 0.72) / 0.28 * 0.86) for wi, t in zip(w, np.linspace(0, 1, 30))]
    blade = stroke(X, Y, T(curve), w)
    return np.minimum.reduce([grip, pommel, guard, neck, blade]), None


def flame(X, Y):
    """The Wakefire: a flame standing in a lamp bowl."""
    f = stroke(X, Y, [(0.0, 0.14), (0.06, -0.06), (0.10, -0.26), (0.02, -0.46), (-0.07, -0.66)], [0.25, 0.235, 0.17, 0.10, 0.015])
    lick = stroke(X, Y, [(-0.16, 0.10), (-0.24, -0.10), (-0.20, -0.30)], [0.10, 0.07, 0.012])
    heart = stroke(X, Y, [(0.0, 0.17), (0.035, 0.03), (0.02, -0.14)], [0.105, 0.085, 0.012])
    bowl = np.maximum(circle(X, Y, 0, 0.14, 0.50), -(Y - 0.36))             # the lower slice of a big circle
    bowl = np.maximum(bowl, -(Y - 0.36))
    foot = box(X, Y, 0, 0.70, 0.20, 0.035, 0.03)
    stem = box(X, Y, 0, 0.64, 0.055, 0.06)
    return np.minimum.reduce([np.minimum(f, lick), bowl, foot, stem]), heart


def moon(X, Y):
    """Nodding off: the horned moon and two stars."""
    c = np.maximum(circle(X, Y, -0.06, 0.02, 0.56), -circle(X, Y, 0.17, -0.12, 0.47))
    def star(cx, cy, r):
        a = np.abs(X - cx) / r; b = np.abs(Y - cy) / r
        return (np.minimum(a * 3.2 + b, a + b * 3.2) - 1.0) * r * 0.45
    return np.minimum.reduce([c, star(0.30, -0.16, 0.20), star(0.44, 0.24, 0.12)]), None


def talk(X, Y):
    """Speaking: a word-balloon with three marks in it."""
    b = box(X, Y, 0.0, -0.09, 0.56, 0.36, 0.17)
    tail = polygon(X, Y, [(-0.30, 0.20), (-0.40, 0.60), (0.0, 0.24)])
    dots = np.minimum.reduce([circle(X, Y, dx, -0.09, 0.075) for dx in (-0.27, 0.0, 0.27)])
    return np.minimum(b, tail), dots


def roll(X, Y):
    """Rolling clear: an arrow turning on itself."""
    a0, a1 = -52, 222
    ring = stroke(X, Y, arc(0, 0.03, 0.40, a0, a1, 36), [0.08] * 36)
    ex, ey = 0.40 * math.cos(math.radians(a0)), 0.03 + 0.40 * math.sin(math.radians(a0))
    tx, ty = math.sin(math.radians(a0)), -math.cos(math.radians(a0))          # the way the arrow is travelling
    nx, ny = -ty, tx
    head = polygon(X, Y, [(ex + tx * 0.34, ey + ty * 0.34), (ex + nx * 0.23 - tx * 0.04, ey + ny * 0.23 - ty * 0.04), (ex - nx * 0.23 - tx * 0.04, ey - ny * 0.23 - ty * 0.04)])
    return np.minimum(ring, head), None


def fine(X, Y, pts, radii, k=8):
    """A stroke with enough points along it that thin lines stay lines."""
    pts = np.asarray(pts, float); radii = np.asarray(radii, float)
    P, Rr = [], []
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, k, endpoint=False):
            P.append(pts[i] + (pts[i + 1] - pts[i]) * t); Rr.append(radii[i] + (radii[i + 1] - radii[i]) * t)
    P.append(pts[-1]); Rr.append(radii[-1])
    return stroke(X, Y, P, Rr)


def shield(X, Y):
    """Guarding: the round mirror shield, a groove inside its rim and a ring round its boss."""
    R = np.hypot(X, Y)
    disc = R - 0.64
    cuts = np.minimum(np.abs(R - 0.47) - 0.032, np.abs(R - 0.20) - 0.03)
    return disc, cuts


def eye(X, Y):
    """Looking and reading: an eye, the way the old cities drew it, under its brow."""
    Y = Y - 0.07
    almond = np.maximum(circle(X, Y, 0, 0.44, 0.80), circle(X, Y, 0, -0.44, 0.80))
    brow = fine(X, Y, [(-0.52, -0.42), (-0.22, -0.58), (0.22, -0.58), (0.52, -0.42)], [0.03, 0.045, 0.045, 0.03])
    return np.minimum(almond, brow), np.abs(circle(X, Y, 0, 0, 0.21)) - 0.06


def key(X, Y):
    """Opening: a key, bow uppermost."""
    bow = circle(X, Y, 0, -0.40, 0.27)
    shaft = stroke(X, Y, [(0, -0.16), (0, 0.66)], [0.075, 0.075])
    teeth = np.minimum(box(X, Y, 0.15, 0.36, 0.13, 0.055), box(X, Y, 0.13, 0.58, 0.11, 0.055))
    return np.minimum.reduce([bow, shaft, teeth]), circle(X, Y, 0, -0.40, 0.115)


def sling(X, Y):
    """The sling: two cords, a cradle, and the stone in it."""
    left = fine(X, Y, [(-0.10, -0.66), (-0.34, -0.30), (-0.30, 0.10), (-0.10, 0.36)], [0.045, 0.045, 0.05, 0.055])
    right = fine(X, Y, [(0.22, -0.60), (0.38, -0.26), (0.30, 0.12), (0.10, 0.36)], [0.045, 0.045, 0.05, 0.055])
    loop = np.abs(circle(X, Y, -0.02, -0.66, 0.10)) - 0.04
    stone = circle(X, Y, 0, 0.40, 0.21)
    return np.minimum.reduce([left, right, loop, stone]), None


def stick(X, Y):
    """The throwing stick: one bent length of wood, thicker at the elbow."""
    pts = rot([(-0.62, 0.20), (-0.30, -0.10), (0.0, -0.20), (0.30, -0.06), (0.60, 0.30)], -14)
    return fine(X, Y, pts, [0.06, 0.09, 0.105, 0.09, 0.06]), None


def wheel(X, Y):
    """The Sun Wheel: a rim, a hub, and eight rays between them."""
    d = np.minimum(np.abs(np.hypot(X, Y) - 0.56) - 0.065, circle(X, Y, 0, 0, 0.14))
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        c, sn = math.cos(a), math.sin(a)
        d = np.minimum(d, stroke(X, Y, [(c * 0.17, sn * 0.17), (c * 0.50, sn * 0.50)], [0.055, 0.035]))
    return d, None


def fork(X, Y):
    """A tuning fork: two tines on a yoke, a stem, a knob."""
    tines = np.minimum(stroke(X, Y, [(-0.24, -0.66), (-0.24, 0.02)], [0.075, 0.085]), stroke(X, Y, [(0.24, -0.66), (0.24, 0.02)], [0.075, 0.085]))
    yoke = fine(X, Y, [(-0.24, 0.0), (-0.16, 0.16), (0.16, 0.16), (0.24, 0.0)], [0.085, 0.09, 0.09, 0.085])
    stem = stroke(X, Y, [(0, 0.16), (0, 0.50)], [0.07, 0.065])
    return np.minimum.reduce([tines, yoke, stem, circle(X, Y, 0, 0.60, 0.12)]), None


def rosette(X, Y):
    """The eight-petalled flower the old cities put on everything."""
    d = circle(X, Y, 0, 0, 0.15)
    for k in range(8):
        a = math.radians(k * 45)
        c, sn = math.cos(a), math.sin(a)
        d = np.minimum(d, stroke(X, Y, [(c * 0.22, sn * 0.22), (c * 0.40, sn * 0.40), (c * 0.60, sn * 0.60)], [0.035, 0.105, 0.03]))
    ringcut = np.abs(np.hypot(X, Y) - 0.185) - 0.022
    return d, ringcut


def bars(X, Y):
    return np.minimum(box(X, Y, -0.21, 0, 0.11, 0.38, 0.05), box(X, Y, 0.21, 0, 0.11, 0.38, 0.05)), None


# ------------------------------------------------------------------ the metalwork
def relief(n, sign=None, rim=0.14, beads=30, face=ENAMEL, notches=0, sign_scale=0.60, glass=1.0):
    """One round button n texture pixels across. Returns RGBA floats."""
    X, Y = grid(n)
    R = np.hypot(X, Y); A = np.arctan2(Y, X)
    h = np.zeros(X.shape); mat = np.full(X.shape, DARK)
    r_out = 1.0; r_rim = r_out - rim                      # the rim is a rounded hoop between r_rim and r_out
    hoop = np.abs(R - (r_out - rim / 2)) / (rim / 2)
    in_hoop = hoop < 1
    hh = 0.62 + 0.38 * np.sqrt(np.clip(1 - hoop ** 2, 0, 1))
    if notches:                                            # the big button's rim is cut like a sun-disc
        cut = (np.cos(A * notches) > 0.55) & (hoop < 0.62)
        hh = np.where(cut, hh - 0.10, hh)
    hh = np.where(np.abs(hoop - 0.66) < 0.07, hh - 0.045, hh)
    h = np.where(in_hoop, hh, h); mat[in_hoop] = BRONZE
    # a ring of gold beads inside the hoop
    r_bead = r_rim - 0.055; bead_r = 0.043
    if beads:
        k = np.round(A / (2 * math.pi) * beads) * (2 * math.pi) / beads
        bd = np.hypot(X - r_bead * np.cos(k), Y - r_bead * np.sin(k)) / bead_r
        on = bd < 1
        h = np.where(on, np.maximum(h, 0.46 + 0.26 * np.sqrt(np.clip(1 - bd ** 2, 0, 1))), h); mat[on & (R < r_rim - 0.004)] = GOLD
        gap = (np.abs(R - r_bead) < bead_r * 1.15) & ~on & (R < r_rim)
        h = np.where(gap, 0.30, h)
    r_face = (r_bead - bead_r * 1.25) if beads else r_rim - 0.02
    on_face = R < r_face
    h = np.where(on_face, 0.34 + 0.07 * (1 - (R / r_face) ** 2), h); mat[on_face] = face
    lip = on_face & (R > r_face - 0.035)                   # a fine gold line round the enamel
    h = np.where(lip, h + 0.07, h); mat[lip] = GOLD
    cut_mask = np.zeros(X.shape, bool)
    if sign is not None:
        d, cut = sign(X / sign_scale, Y / sign_scale)
        d = d * sign_scale
        up = np.clip(-d / 0.035, 0, 1)                     # a bevelled edge, then flat
        on = (d < 0) & on_face
        h = np.where(on, h + 0.20 * up * (2 - up), h); mat[on] = GOLD
        if cut is not None:
            cut = cut * sign_scale
            c = (cut < 0) & on
            h = np.where(c, h - 0.16 * np.clip(-cut / 0.03, 0, 1), h); mat[c] = face; cut_mask = c
    disc = R < r_out
    # light it
    px = 2.16 / (n * SS)
    hs = ndimage.gaussian_filter(h, SS * 0.6)
    gy, gx = np.gradient(hs, px)
    k = 0.085
    N = np.dstack([-gx * k, -gy * k, np.ones_like(hs)]); N /= np.linalg.norm(N, axis=2, keepdims=True)
    key = np.clip(N @ KEY, 0, 1); fill = np.clip(N @ FILL, 0, 1)
    H = KEY + np.array([0, 0, 1.0]); H /= np.linalg.norm(H)
    sp = np.clip(N @ H, 0, 1)
    ao = np.clip(1 - 2.6 * (ndimage.gaussian_filter(h, n * SS * 0.022) - h), 0.30, 1.0)
    # a cast shadow: anything tall to the upper left darkens what is below and right of it
    sh = np.ones_like(h)
    for step in (1, 2, 3):
        off = int(round(n * SS * 0.012 * step))
        shifted = np.roll(np.roll(h, off, 0), off, 1)
        sh *= np.where(shifted - h > 0.05 + 0.03 * step, 0.80, 1.0)
    sh = ndimage.gaussian_filter(sh, SS * 0.8)
    alb = ALBEDO[mat]
    # hammered bronze, a little uneven; enamel with depth
    rng = np.random.default_rng(n * 7 + beads)
    grain = ndimage.gaussian_filter(rng.standard_normal(h.shape), SS * 1.4) * 0.5
    alb = alb * (1 + grain[..., None] * np.where(mat == BRONZE, 0.16, np.where(mat == GOLD, 0.06, 0.25))[..., None])
    en = (mat == ENAMEL)
    alb = np.where(en[..., None], alb * (0.75 + 0.9 * np.clip(0.5 - Y * 0.5 - X * 0.2, 0, 1))[..., None] + np.array([0.0, 0.004, 0.02]), alb)
    light = (0.30 + 0.86 * key[..., None] * np.array([1.0, 0.95, 0.84]) + 0.20 * fill[..., None] * np.array([0.55, 0.66, 1.0]))
    col = alb * light * ao[..., None] * sh[..., None]
    col += SPEC[mat] * (sp ** SHINE[mat])[..., None] * GLINT[mat][..., None] * sh[..., None]
    # the glass gloss on enamel: a soft bright band across the upper left
    gloss = np.clip(1 - np.hypot(X + 0.30, Y + 0.36) / 0.62, 0, 1) ** 2 * 0.16
    col += np.where(en[..., None], gloss[..., None] * np.array([0.6, 0.75, 1.0]), 0)
    col = np.clip(col, 0, 1) ** (1 / 1.12)
    alpha = np.where(disc, 1.0, 0.0)
    alpha = np.where(en | cut_mask, glass, alpha)
    # a soft shadow under it, falling down and to the right
    shadow = np.clip(1 - (np.hypot(X - 0.03, Y - 0.05) - 0.98) / 0.09, 0, 1) * 0.55
    a_out = np.where(disc, alpha, shadow * (1 - disc))
    col = np.where(disc[..., None], col, np.array([0.02, 0.015, 0.04]))
    rgba = np.dstack([col, a_out])
    # down to size
    rgba[..., :3] *= rgba[..., 3:4]
    small = rgba.reshape(n, SS, n, SS, 4).mean((1, 3))
    small[..., :3] /= np.maximum(small[..., 3:4], 1e-6)
    return small


def ring(n):
    """The thumbstick's seat: a bronze hoop with beads, open in the middle, four gold darts for the ways to go."""
    X, Y = grid(n)
    def darts(Xs, Ys):
        d = np.full(Xs.shape, 9.0)
        for a in (0, 90, 180, 270):
            d = np.minimum(d, polygon(Xs, Ys, rot([(-0.13, 0.10), (0.13, 0.10), (0.0, -0.13)], a, 1.0, rot([(0, -0.93)], a)[0])))
        return d, None
    return relief(n, darts, rim=0.10, beads=44, sign_scale=0.76, glass=0.26)


def knob(n):
    """The thumbstick itself: a round boss with a gold flower on it, the kind a shield has in the middle."""
    return relief(n, rosette, rim=0.17, beads=0, face=BRONZE, sign_scale=1.0)


def save(name, rgba):
    im = Image.fromarray(np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8), 'RGBA')
    im.save(os.path.join(OUT, name + '.png'))
    return im


SIZES = {'attack': 40, 'nod': 30, 'item': 30, 'talk': 30, 'roll': 30, 'pause': 20, 'stick_base': 62, 'stick_knob': 28,
         'act_open': 30, 'act_look': 30, 'act_guard': 30, 'item_wheel': 30, 'item_fork': 30}

if __name__ == '__main__':
    made = {}
    made['attack'] = relief(SIZES['attack'] * DENSITY, khopesh, rim=0.13, beads=36, notches=24, sign_scale=0.68)
    made['nod'] = relief(SIZES['nod'] * DENSITY, moon, sign_scale=0.66)
    made['item'] = relief(SIZES['item'] * DENSITY, flame, sign_scale=0.66)
    made['talk'] = relief(SIZES['talk'] * DENSITY, talk, sign_scale=0.64)
    made['roll'] = relief(SIZES['roll'] * DENSITY, roll, sign_scale=0.70)
    # what the action button turns into, and what the item button can carry
    made['act_open'] = relief(SIZES['act_open'] * DENSITY, key, sign_scale=0.66)
    made['act_look'] = relief(SIZES['act_look'] * DENSITY, eye, sign_scale=0.70)
    made['act_guard'] = relief(SIZES['act_guard'] * DENSITY, shield, sign_scale=0.66)
    made['item_wheel'] = relief(SIZES['item_wheel'] * DENSITY, wheel, sign_scale=0.70)
    made['item_fork'] = relief(SIZES['item_fork'] * DENSITY, fork, sign_scale=0.70)
    made['pause'] = relief(SIZES['pause'] * DENSITY, bars, rim=0.17, beads=0, sign_scale=0.62)
    made['stick_base'] = ring(SIZES['stick_base'] * DENSITY)
    made['stick_knob'] = knob(SIZES['stick_knob'] * DENSITY)
    ims = {k: save(k, v) for k, v in made.items()}
    for k, im in ims.items(): print(k, im.size)
    if len(sys.argv) > 1:
        # a look at them on a patch of the game's colours, at the size a 1080p phone shows them
        from PIL import ImageDraw
        W, H = 1900, 560
        bg = Image.new('RGB', (W, H), (70, 62, 78))
        d = ImageDraw.Draw(bg)
        for i in range(0, W, 80):
            for j in range(0, H, 40):
                d.rectangle([i + (j // 40 % 2) * 40, j, i + (j // 40 % 2) * 40 + 76, j + 36], fill=(96 + (i * 7 + j * 3) % 24, 88 + (i * 5 + j) % 20, 92))
        d.rectangle([0, 280, W, H], fill=(150, 120, 84))
        x = 20
        for k in ('attack', 'nod', 'item', 'talk', 'roll', 'act_open', 'act_look', 'act_guard', 'item_wheel', 'item_fork', 'pause'):
            im = ims[k]; s = SIZES[k] * 5                 # 1080p: five screen pixels to the game pixel
            sm = im.resize((s, s), Image.LANCZOS)
            a = sm.split()[3].point(lambda v: int(v * 0.94))
            bg.paste(sm, (x, 40), a); bg.paste(sm, (min(W - s - 4, x), 320), a)
            x += s + 16
        d.text((8, 6), "INTERNAL TEST  -  touch buttons, not the final look", fill=(255, 200, 60))
        bg.save(sys.argv[1]); print(sys.argv[1], bg.size)
