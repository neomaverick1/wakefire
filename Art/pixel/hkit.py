"""Standing a Building (houses.py) on a map, and the yard round it. A building's picture is drawn
as the ground is drawn, under everything that stands on it, against it or in front of it; what of it
is wall stops feet and whatever is thrown, and what of it is roof can be walked on, hopped down
from, and reached by its own stair or ladder. Round each house go the low walls, hedges, fences,
beds and paths that make the plot it stands on."""
import math
import numpy as np
import forge
from forge import Model, M, Mat, RAMPS, m_brick, m_mottle, m_planks, m_reeds, m_clumps, m_stripes, fbm
import town
from town import Mats, PX, rnd
import houses
import dprops


# ------------------------------------------------------------------ what a yard is made of
WALL_BODY = lambda: M('limewash', 4.3, m_mottle(14, 0.35))
WALL_TOP = lambda: M('limewash', 5.0, m_mottle(20, 0.2))
WALL_CAP = lambda: M('brick', 4.4, m_brick(6, 3, -0.7, 0.5))


def low_wall(length, seed=0, plaster=1, h=0.5, d=0.375):
    """A yard wall a man can see over: a foot of fired brick, mud brick under lime wash, a course of tile
    along the top. Runs east from the origin, faces south."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(0, 0, 0, length, d, h, WALL_BODY(), top=WALL_TOP())
    m.part(); m.box(-PX / 2, -PX / 2, 0, length + PX / 2, d, 0.14, mt.plinth, top=mt.trim)
    m.part(); m.box(-PX / 2, -PX, h - 0.07, length + PX / 2, 0, h, WALL_CAP(), top=M('brick', 4.9))
    return m


def low_wall_ns(depth, seed=0, plaster=1, h=0.5, wd=0.375):
    """The same wall running north from the origin."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(0, 0, 0, wd, depth, h, WALL_BODY(), top=WALL_TOP())
    m.part(); m.box(-PX / 2, -PX / 2, 0, wd + PX / 2, depth, 0.14, mt.plinth, top=mt.trim)
    m.part(); m.box(-PX, -PX, h, 0, depth, h + 0.03, WALL_CAP(), top=M('brick', 4.9))
    m.part(); m.box(wd, -PX, h, wd + PX, depth, h + 0.03, WALL_CAP(), top=M('brick', 4.9))
    return m


def pier(seed=0, plaster=1, h=1.0, lamp=False):
    """A gate pier, where a path goes into a yard: a pot on it, or a lamp that somebody lit."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(-0.25, 0, 0, 0.25, 0.5, h, WALL_BODY(), top=WALL_TOP())
    m.part(); m.box(-0.25 - PX, -PX, 0, 0.25 + PX, 0.5, 0.18, mt.plinth, top=mt.trim)
    m.part(); m.box(-0.31, -0.06, h, 0.31, 0.56, h + 0.1, M('brick', 4.3, m_brick(6, 3, -0.8, 0.5)), top=M('brick', 4.9))
    if lamp:
        m.part(); m.blob(0, 0.25, h + 0.16, 0.12, 0.1, 0.07, mt.pot, n=7, rings=3)
        m.part(); m.blob(0.08, 0.25, h + 0.26, 0.04, 0.04, 0.08, mt.glow, n=5, rings=3)
        m.light(0, 0.0, h + 0.3, 2.8, (1.0, 0.72, 0.38), 0.6)
    else:
        m.part(); m.turned(0, 0.25, [(0.05, h + 0.1), (0.15, h + 0.16), (0.17, h + 0.3), (0.09, h + 0.4), (0.11, h + 0.44)], M('clay', 4.4, gloss=0.012), n=9, cap=mt.dark)
    return m


def hedge(length, seed=0, h=0.62, d=0.55, flowers=None, leaf='green'):
    """Myrtle, clipped square the way a careful house keeps it. Runs east from the origin.
    (leaf: what it is a hedge of. On the Hill of Sleepers it is thorn, dead, and clipped all the same.)"""
    r = rnd(seed); m = Model()
    side = M(leaf, 3.0, m_clumps(4), soft=True)
    top = M(leaf, 4.0, m_clumps(3), soft=True)
    m.part(); m.box(0, 0, 0, length, d, h - 0.08, side, top=top)
    n = max(2, int(round(length / 0.42)))
    m.part()
    for i in range(n):
        cx = (i + 0.5) * length / n + float(r.uniform(-0.04, 0.04))
        m.blob(cx, d / 2, h - 0.12, length / n * 0.62, d / 2 + 0.02, 0.2, top, seed=seed * 5 + i, bump=0.14, n=8, rings=4)
    if flowers:
        fl = Mat(RAMPS[flowers], 4.8, soft=True)
        m.part()
        for i in range(int(length * 2.2)):
            m.blob(float(r.uniform(0.1, length - 0.1)), float(r.uniform(0.02, d - 0.05)), h + float(r.uniform(-0.02, 0.06)), 0.045, 0.045, 0.04, fl, n=4, rings=2)
    return m


def hedge_ns(depth, seed=0, h=0.62, wd=0.55, flowers=None, leaf='green'):
    r = rnd(seed); m = Model()
    side = M(leaf, 3.0, m_clumps(4), soft=True)
    top = M(leaf, 4.0, m_clumps(3), soft=True)
    m.part(); m.box(0, 0, 0, wd, depth, h - 0.08, side, top=top)
    n = max(2, int(round(depth / 0.42)))
    m.part()
    for i in range(n):
        cy = (i + 0.5) * depth / n + float(r.uniform(-0.04, 0.04))
        m.blob(wd / 2, cy, h - 0.12, wd / 2 + 0.02, depth / n * 0.62, 0.2, top, seed=seed * 5 + i, bump=0.14, n=8, rings=4)
    if flowers:
        fl = Mat(RAMPS[flowers], 4.8, soft=True)
        m.part()
        for i in range(int(depth * 2.2)):
            m.blob(float(r.uniform(0.05, wd - 0.05)), float(r.uniform(0.1, depth - 0.1)), h + float(r.uniform(-0.02, 0.06)), 0.045, 0.045, 0.04, fl, n=4, rings=2)
    return m


def fence(length, seed=0, h=0.62):
    """Reed hurdles between posts: what keeps a goat out of the onions, in theory."""
    m = Model(); mt = Mats(seed, 0)
    reed = M('reed', 4.0, m_reeds(2))
    m.part(); m.box(0, 0.03, 0.05, length, 0.08, h - 0.08, reed, top=M('reed', 4.6))
    n = max(2, int(round(length / 0.75)) + 1)
    m.part()
    for i in range(n):
        x = length * i / (n - 1)
        m.box(x - PX, 0, 0, x + PX, 0.11, h, mt.beam)
    m.part(); m.box(0, 0.0, h - 0.24, length, 0.03, h - 0.17, mt.beam)
    return m


def fence_ns(depth, seed=0, h=0.62):
    m = Model(); mt = Mats(seed, 0)
    reed = M('reed', 4.0, m_reeds(2))
    m.part(); m.box(0.03, 0, 0.05, 0.08, depth, h - 0.08, reed, top=M('reed', 4.6))
    n = max(2, int(round(depth / 0.75)) + 1)
    m.part()
    for i in range(n):
        y = depth * i / (n - 1)
        m.box(0, y - PX, 0, 0.11, y + PX, h, mt.beam)
    return m


def washing(seed=0, w=2.6, cloths=('cream', 'red', 'linen', 'blue')):
    """A line between two posts, and what was hung on it forty nights ago. It is very dry."""
    m = Model(); mt = Mats(seed, 0)
    houses.rack(m, mt, 0.0, w, 0.0, 0.0, h=1.3, cloths=cloths, seed=seed)
    return m


def bench(w=1.5, seed=0):
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.box(0, 0, 0.3, w, 0.4, 0.38, mt.wood_h, top=M('wood', 4.9))
    m.part()
    for x in (0.1, w - 0.2):
        m.box(x, 0.05, 0, x + 0.1, 0.35, 0.3, mt.beam)
    return m


def tub_tree(seed=0, kind='palm'):
    """A tree in a tub of fired clay, by a door."""
    m = Model()
    m.part(); m.turned(0, 0.3, [(0.26, 0), (0.33, 0.34), (0.28, 0.4)], M('clay', 4.0, gloss=0.01), n=10, cap=M('wood', 2.2))
    houses.add(m, town.palm(seed + 3, 1.7) if kind == 'palm' else town.olive(seed + 3, 0.6), (0, 0.0, 0.3))
    return m


def trough(seed=0, w=1.4):
    """A stone trough, with water in it that nothing has drunk."""
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.box(0, 0, 0, w, 0.5, 0.36, M('stone', 3.9, m_mottle(8, 0.4)), top=M('water', 2.8, m_mottle(4, 0.6)))
    m.part(); m.box(-PX, -PX, 0.3, w + PX, 0.5 + PX, 0.4, M('stone', 4.4))
    m.part(); m.box(0.08, 0.08, 0.34, w - 0.08, 0.42, 0.36, M('water', 2.8, m_mottle(4, 0.6)))
    return m


def coop(seed=0):
    """A hen house of reed on four legs, with its ramp."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for x, y in ((0.06, 0.06), (0.94, 0.06), (0.06, 0.6), (0.94, 0.6)):
        m.box(x - PX, y - PX, 0, x + PX, y + PX, 0.3, mt.beam)
    m.part(); m.box(0, 0, 0.3, 1.0, 0.66, 0.8, M('reed', 4.1, m_reeds(2)), top=M('reed', 4.7, m_reeds(3)))
    m.part(); m.box(-0.06, -0.06, 0.8, 1.06, 0.72, 0.86, M('straw', 4.2, m_reeds(3)), top=M('straw', 4.7, m_reeds(3)))
    m.part(); m.quad((0.36, -0.01, 0.34), (0.64, -0.01, 0.34), (0.64, -0.01, 0.62), (0.36, -0.01, 0.62), mt.dark)
    m.part(); m.quad((0.38, -0.5, 0.0), (0.62, -0.5, 0.0), (0.62, 0.0, 0.32), (0.38, 0.0, 0.32), M('wood', 4.4, m_planks(3, 'h')), two=True)
    return m


def cave_mouth(seed=0, w=1.1, h=1.2):
    """A way into a cliff at the foot of it: a hole the height of a crouching man, the rock round it worn smooth
    by whatever uses it."""
    r = rnd(seed); m = Model()
    rock = M('sandstone', 3.4, m_mottle(6, 0.6))
    pts = [(-w / 2, 0.0), (w / 2, 0.0)]
    for k in range(1, 8):
        a = math.pi * k / 8
        pts.append((math.cos(a) * w / 2 * (1.0 + 0.08 * math.sin(k * 2.3)), math.sin(a) * h * (1.0 + 0.06 * math.cos(k * 1.7))))
    m.part(); m.face(pts, -0.04, M('dark', 0.6))
    m.part()
    for k in range(9):
        a = math.pi * (k + 0.5) / 9
        m.blob(math.cos(a) * (w / 2 + 0.1), -0.08, math.sin(a) * (h + 0.06), 0.17, 0.1, 0.15, rock, seed=seed * 3 + k, bump=0.3, n=6, rings=4)
    m.part(); m.blob(0, -0.3, 0.02, w * 0.6, 0.3, 0.05, M('sandstone', 2.6, m_mottle(4, 0.6)), n=8, rings=3, seed=seed, bump=0.3)
    return m


def round_tree(seed=0, s=1.0):
    """The tree a town plants along its ways: a short bole, and a head as round as a loaf."""
    r = rnd(seed); m = Model()
    bark = M('trunk', 3.4, m_mottle(5, 0.4))
    leaf = M('green', 3.5, m_clumps(5), soft=True)
    m.part(); m.limb([(0, 0.3, 0), (0.02, 0.3, 0.75 * s)], [0.2 * s, 0.15 * s], bark, n=7)
    m.part()
    m.blob(0, 0.35, 1.45 * s, 0.92 * s, 0.78 * s, 0.84 * s, leaf, seed=seed, bump=0.1, n=12, rings=7)
    for i in range(7):
        a = 2 * math.pi * i / 7 + float(r.uniform(-0.2, 0.2))
        m.blob(math.cos(a) * 0.6 * s, 0.35 + math.sin(a) * 0.3 * s, (1.35 + 0.25 * math.sin(a * 2 + seed)) * s, 0.48 * s, 0.42 * s, 0.44 * s, leaf, seed=seed * 7 + i, bump=0.14, n=9, rings=5)
    return m


def fruit_tree(seed=0, s=0.8, fruit='red'):
    """A pomegranate, smaller than the trees along the ways, and hung with fruit."""
    r = rnd(seed + 40); m = round_tree(seed + 40, s)
    fl = Mat(RAMPS[fruit], 4.6, soft=True)
    m.part()
    k = 0
    while k < 10:
        # on the side of the head that whoever is looking can see (its top and its front): the fruit sits just proud of the leaves
        n = r.normal(0, 1, 3); n = n / (float(np.linalg.norm(n)) + 1e-6)
        if n[2] - n[1] < 0.3 or abs(n[0]) > 0.8: continue
        m.blob(float(n[0]) * 0.94 * s, 0.35 + float(n[1]) * 0.8 * s, (1.45 + float(n[2]) * 0.86) * s, 0.1, 0.08, 0.1, fl, n=6, rings=4, seed=k)
        k += 1
    return m


def lamp_post(frame=0):
    """A lamp on a post at the side of a way: a bowl of fired clay on a turned stem, burning."""
    m = Model()
    m.part(); m.turned(0, 0.2, [(0.16, 0), (0.1, 0.1), (0.055, 0.2), (0.05, 1.2), (0.1, 1.28), (0.2, 1.36), (0.22, 1.44), (0.16, 1.44)], M('bronze', 3.8, gloss=0.02), n=9, cap=Mat(RAMPS['glow'], 1.6, glow=True))
    town.flame(m, 0, 0.2, 1.44, s=0.62, frame=frame, seed=7, tongues=3)
    m.light(0, -0.2, 1.7, 3.6, (1.0, 0.72, 0.38), 0.75)
    return m


# ------------------------------------------------------------------ putting them on the map
def tree(m, x, y, sd=0):
    """One of the town's round trees, its foot at (x, y)."""
    return m.model("rtree", round_tree(1, 1.08), x, y, box=(-4, -6, 4, 0))


def fruit(m, x, y, sd=0, fruit='red'):
    return m.model(f"ftree_{fruit}", fruit_tree(0, 0.8, fruit), x, y, box=(-3, -5, 3, 0))


def lamp(m, x, y):
    """A lamp post, lit."""
    m.model("lamp_post", lamp_post, x, y, box=(-2, -4, 2, 0), frames=3, kind="torch")


def name_post(m, x, y, uid, text):
    """The board by a door that says whose door it is."""
    m.model("name_post", town.sign(), x, y, box=(-2, -4, 2, 0), kind="look", data={"id": "say", "text": text})


def wall_ew(m, x0, x1, y, seed=0, plaster=1):
    """A low wall from x0 east to x1, its south face at y."""
    L = x1 - x0
    m.model(f"lw_{L}_{seed}_{plaster}", low_wall(L / 16.0, seed, plaster), x0, y, box=(0, -6, L, 0))


def wall_ns(m, x, y0, y1, seed=0, plaster=1):
    """A low wall from y0 (north) down to y1, its west face at x."""
    D = y1 - y0
    m.model(f"lwn_{D}_{seed}_{plaster}", low_wall_ns(D / 16.0, seed, plaster), x, y1, box=(0, -D, 6, 0))


def gate_pier(m, x, y, seed=0, plaster=1, lamp=False):
    key = f"pier_{seed}_{plaster}{'_l' if lamp else ''}"
    m.model(key, pier(seed, plaster, lamp=lamp), x, y, box=(-4, -8, 4, 0))


def hedge_ew(m, x0, x1, y, seed=0, flowers=None, leaf='green'):
    L = x1 - x0
    m.model(f"hedge_{L}_{seed}_{flowers}" + ("" if leaf == 'green' else "_" + leaf), hedge(L / 16.0, seed, flowers=flowers, leaf=leaf), x0, y, box=(0, -8, L, 0), kind="hedge")


def hedge_sn(m, x, y0, y1, seed=0, flowers=None, leaf='green'):
    D = y1 - y0
    m.model(f"hedgen_{D}_{seed}_{flowers}" + ("" if leaf == 'green' else "_" + leaf), hedge_ns(D / 16.0, seed, flowers=flowers, leaf=leaf), x, y1, box=(0, -D, 9, 0), kind="hedge")


def fence_ew(m, x0, x1, y, seed=0):
    L = x1 - x0
    m.model(f"fence_{L}_{seed}", fence(L / 16.0, seed), x0, y, box=(0, -2, L, 0))


def fence_sn(m, x, y0, y1, seed=0):
    D = y1 - y0
    m.model(f"fencen_{D}_{seed}", fence_ns(D / 16.0, seed), x, y1, box=(0, -D, 2, 0))


def plot(m, x0, y0, x1, y1, gates=(), sides='swe', seed=0, plaster=1, lamp=(), hedge=''):
    """Low walls round a plot (x0, y0)-(x1, y1), with a way through wherever a path goes in.
    gates: (side, a, b) = the opening, along that side. lamp: which gates have a lit pier.
    hedge: the sides that are clipped myrtle instead of wall (the same ground, the same gates)."""
    def wall_ew_(m_, a, b, y, sd, pl, side):
        if side in hedge: hedge_ew(m_, a, b, y + 1, sd % 4)
        else: wall_ew(m_, a, b, y, sd, pl)

    def wall_ns_(m_, x, a, b, sd, pl, side):
        if side in hedge: hedge_sn(m_, x - 1, a, b, sd % 4)
        else: wall_ns(m_, x, a, b, sd, pl)
    g = {s: sorted((a, b) for (sd, a, b) in gates if sd == s) for s in 'nswe'}
    k = [0]

    def run(a, b, cuts):
        out = []
        for (ca, cb) in cuts:
            if ca > a: out.append((a, ca))
            a = max(a, cb)
        if a < b: out.append((a, b))
        return out
    if 's' in sides:
        for (a, b) in run(x0, x1, g['s']):
            wall_ew_(m, a, b, y1, seed + k[0], plaster, 's'); k[0] += 1
        for i, (a, b) in enumerate(g['s']):
            gate_pier(m, a - 4, y1 + 1, seed, plaster, lamp=('s', i) in lamp)
            gate_pier(m, b + 4, y1 + 1, seed + 1, plaster, lamp=('s', i) in lamp)
    if 'n' in sides:
        for (a, b) in run(x0, x1, g['n']):
            wall_ew_(m, a, b, y0 + 6, seed + k[0], plaster, 'n'); k[0] += 1
        for i, (a, b) in enumerate(g['n']):
            gate_pier(m, a - 4, y0 + 7, seed, plaster)
            gate_pier(m, b + 4, y0 + 7, seed + 1, plaster)
    ya = y0 + (6 if 'n' in sides else 0); yb = y1 - (6 if 's' in sides else 0)
    for sd, x in (('w', x0), ('e', x1 - 6)):
        if sd not in sides: continue
        for (a, b) in run(ya, yb, g[sd]):
            wall_ns_(m, x, a, b, seed + k[0], plaster, sd); k[0] += 1
        for i, (a, b) in enumerate(g[sd]):
            gate_pier(m, x + 3, a, seed, plaster, lamp=(sd, i) in lamp)
            gate_pier(m, x + 3, b + 8, seed + 1, plaster, lamp=(sd, i) in lamp)


# ------------------------------------------------------------------ the ground of a tidy town
def calm(T, mask, ramp='dust', base=4.2, seed=1, amp=0.5, pebbles=0.0015):
    """Swept ground: one colour, a breath of a second, a pebble now and then."""
    X, Y = T.xx, T.yy
    big = fbm(X / 60.0, Y / 60.0, T.seed + seed, 2)
    fine = fbm(X / 5.0, Y / 5.0, T.seed + seed + 5, 2)
    tone = base + (big > 0.62) * amp - (big < 0.36) * amp + (fine - 0.5) * 0.5
    T.put(mask, ramp, tone, (fine - 0.5) * 0.25)
    if pebbles:
        T.pebbles(mask, pebbles, seed + 11)


def paved(T, mask, seed=2, kerb='pale', rows=(8,), wmin=10, wmax=16, ramp='flag', base=3.8, kerb_tone=4.2):
    """A street or a path: cut stone laid square to the town, with a kerb of paler stone round it."""
    T.slabs(mask, seed=seed, rows=rows, wmin=wmin, wmax=wmax, ramp=ramp, base=base, whole=False, jitter=0.7, crack=0.03, wear=0.3)
    if kerb:
        ring = T.border(mask, ramp=kerb, tone=kerb_tone, width=2, hgt=1.2)
        # the kerb is stones too: a joint every so often
        X, Y = T.xx, T.yy
        T.add(ring & (((X + Y) % 9) == 0), -1.4)
    return mask


def bed(T, x, y, w, h, seed=0, crop='grass'):
    """A garden bed: turned earth in rows, something green coming up in it, a row of stones round it."""
    area = T.rect(x, y, w, h)
    T.put(area, 'rock', np.full((T.H, T.W), 3.4), 1.0)
    X, Y = T.xx, T.yy
    T.add(area & (((X + Y * 3) % 5) == 0), -1.0)
    inner = T.rect(x + 2, y + 2, w - 4, h - 4)
    T.soil(inner, seed=seed)
    rows = inner & ((Y - y) % 5 == 3) & (((X + (Y // 5) * 3) % 4) < 3)
    T.put(rows, crop if crop in ('grass', 'dry', 'moss') else 'grass', np.where(((X * 7 + Y * 3) % 5) < 2, 4.6, 3.6), 0.8)
    return area


def lawn(T, mask, seed=5, flowers=0.01):
    T.grass(mask, seed=seed, flowers=flowers, tufts=0.02, fringe=0)


def green(T, mask, seed=5, base=3.55, ramp='lawn'):
    """The grass a town stands in, kept: one green with a breath of a second in it, and the blades in rows like a weave.
    (ramp: the same ground in another country's colour: the straw of the Hill of Sleepers, where nothing has grown in years.)"""
    X, Y = T.xx, T.yy
    big = fbm(X / 70.0, Y / 70.0, T.seed + seed, 2)
    tone = base + (big > 0.62) * 0.2
    T.put(mask, ramp, tone, np.zeros((T.H, T.W)))
    row = Y // 6
    xs = (X + (row % 2) * 4) % 8
    lat = ((Y % 6) == 2) & ((xs == 3) | (xs == 4)) & (forge.hash2((X + (row % 2) * 4) // 8, row, T.seed + seed + 3) < 0.82) & mask
    foot = np.roll(lat, 1, 0) & mask & ~lat
    T.tone[lat] += 0.9; T.hgt[lat] += 0.6
    T.tone[foot] -= 0.7


def track(T, mask, seed=3):
    """A way that nobody paved: earth trodden pale, with a darker lip where the grass begins."""
    calm(T, mask, 'dust', base=4.3, seed=seed, amp=0.2, pebbles=0.004)
    T.border(mask, ramp='earth', tone=2.9, width=1, hgt=0.6)
    return mask


def edge_stones(T, mask, ramp='path', tone=2.3):
    """The kerb round a piece of paving: a line of darker stones just inside its edge, a joint every so often."""
    ring = T.border(mask, ramp=ramp, tone=tone, width=2, hgt=1.2)
    X, Y = T.xx, T.yy
    T.add(ring & (((X + Y) % 9) == 0), -1.4)
    return ring


def streets(T, parts, base=4.2, ramp='path', kerb=('path', 2.3)):
    """The ways through a town, of warm cut stone: each part (mask, seed, least and most width of a slab, and if it
    likes the height of a course and its tone) laid in its own size of stone, and one kerb round the lot, so that where a path meets a street nothing is drawn across its mouth."""
    whole = None
    for part in parts:
        mask, seed, wmin, wmax = part[:4]
        rows = part[4] if len(part) > 4 else (8,)
        T.slabs(mask, seed=seed, rows=rows, wmin=wmin, wmax=wmax, ramp=ramp, base=part[5] if len(part) > 5 else base, whole=False, jitter=0.7, crack=0.03, wear=0.3)
        whole = mask if whole is None else (whole | mask)
    edge_stones(T, whole, kerb[0], kerb[1])
    return whole


def street(T, mask, seed=2, rows=(8,), wmin=10, wmax=16):
    """A way through the town: warm cut stone, a darker kerb where it meets the grass."""
    return streets(T, [(mask, seed, wmin, wmax)])


def flowers(T, x, y, kind='w', n=3, leaf='lawn'):
    """Flowers somebody planted: three of them, close together, at (x, y). Four petals round an eye, and a leaf."""
    nm = {'w': 'flower_w', 'y': 'flower_y', 'r': 'flower_r'}[kind]
    rid = T.ramp(nm); leaf = T.ramp(leaf); eye = T.ramp('flower_r' if kind == 'y' else 'flower_y')
    for (dx, dy) in ((0, 0), (7, 3), (2, 8))[:n]:
        px, py = int(x + dx), int(y + dy)
        if not (2 <= px < T.W - 5 and 2 <= py < T.H - 7): continue
        for j, row in enumerate((" pp ", "peep", "peep", " qq ", "s  s", " ll ")):
            for i, ch in enumerate(row):
                if ch == ' ': continue
                yy, xx = py + j, px + i
                if ch in 'pq': T.rid[yy, xx] = rid; T.tone[yy, xx] = 2 if ch == 'p' else 1
                elif ch == 'e': T.rid[yy, xx] = eye; T.tone[yy, xx] = 2 if (i + j) % 2 else 1
                elif ch == 's': T.rid[yy, xx] = leaf; T.tone[yy, xx] = 1.0
                else: T.rid[yy, xx] = leaf; T.tone[yy, xx] = 1.4 + 3.4 * (i == 1)
                if ch in 'pe': T.hgt[yy, xx] += 0.9


# ------------------------------------------------------------------ a building
def _front(m, xa, xb, ya, yb, notches, depth=9):
    """The wall of a front between ya (its top on the map) and yb (its foot), with doorways let into the foot of it."""
    if ya < yb - depth:
        m.solid(xa, ya, xb, yb - depth)
    x = xa
    for (na, nb) in sorted(notches):
        if na > x: m.solid(x, yb - depth, na, yb)
        x = max(x, nb)
    if x < xb: m.solid(x, yb - depth, xb, yb)


def contact(T, b, X, Y):
    """Before the ground is baked: the dark where the building meets it."""
    hw = int(round(b.w * 8))
    T.contact(X - hw, Y - int(round(b.d * 16)), X + hw, Y, reach=5, strength=1.5)


def place(m, b, X, Y, inside=None, say=None, face="down"):
    """Stand building b with the middle of its front foot at map (X, Y). inside = the map its doors lead into
    (None: they are only doors). say = {door index: what a shut door says for itself}. Returns the prop.
    Kinds of door: 'open'; 'locked' (never opens: the way in is somewhere else); 'gong', 'lit', anything else
    (shut until its gong is struck, its sign is lit, its latch is drawn from inside); 'held' (as the last, but in
    the dream it is simply not there)."""
    say = say or {}
    o = m.model(b.key, b.model, X, Y, box=None)
    top = o["py"]
    o["y"] -= top; o["py"] = 0
    if "shy" in o: o["shy"] -= top
    hw = int(round(b.w * 8)); D = int(round(b.d * 16)); Hh = int(round(b.h * 16))
    N, S = Y - D - Hh, Y - Hh                       # the roof on the map: its north edge and its south edge
    xa, xb = X - hw, X + hw

    # ---- the ways in at street level
    notches = []
    for i, (dx, kind) in enumerate(b.doors):
        cx = X + int(round(dx * 16)); dw = int(round(b.door_w * 8))
        name = b.key if i == 0 else f"{b.key}_{i}"
        m.spawn(name, cx, Y + 8, face)
        if kind == 'locked' or inside is None:
            if i in b.leaves:
                lk, lw, lh, lb = b.leaves[i]
                m.model(f"{b.key}_leaf{i}", houses.leaf(lk, lw, lh, lb), cx, Y, box=(-dw, -4, dw, 0), kind="look",
                        data={"id": "say", "text": say.get(i, "Shut.")}, shadow=False, lights=False)
            continue
        if kind == 'held':
            # held shut by whoever is behind it, and bolted: so it is shut in the waking world, and in the dream, where
            # the dead are not, it is not there at all. Once the bolt inside is drawn it stands open in both.
            notches.append((cx - dw, cx + dw))
            m.exit(cx - dw + 2, Y - 9, cx + dw - 2, Y - 4, inside, name + "_in")
            lk, lw, lh, lb = b.leaves[i]
            m.model(f"{b.key}_leaf{i}", houses.leaf(lk, lw, lh, lb), cx, Y, box=(-dw, -9, dw, 0), layer=1, kind="bars", shadow=False, lights=False,
                    data={"id": f"{b.key}_door", "text": f"on:{b.key}_latch", "who": "door|" + say.get(i, "Shut."), "say": say.get(('open', i))})
            continue
        notches.append((cx - dw, cx + dw))
        m.exit(cx - dw + 2, Y - 9, cx + dw - 2, Y - 4, inside, name + "_in")
        if i in b.leaves:
            lk, lw, lh, lb = b.leaves[i]
            when = {'gong': f"gong:{b.key}_gong", 'lit': f"lit:{b.key}_sign"}.get(kind, f"on:{b.key}_latch")
            m.model(f"{b.key}_leaf{i}", houses.leaf(lk, lw, lh, lb), cx, Y, box=(-dw, -9, dw, 0), kind="bars", shadow=False, lights=False,
                    data={"id": f"{b.key}_door", "text": when, "who": "door|" + say.get(i, "Shut."), "say": say.get(('open', i))})

    # ---- wall and roof
    over = max([t[2] for t in b.tall], default=0.0)
    if b.walk is None:
        top_y = N - int(round(over * 16))
        _front(m, xa, xb, top_y, Y, notches)
    else:
        wa, wb = X + int(round(b.walk[0] * 16)), X + int(round(b.walk[1] * 16))
        _front(m, xa, xb, S + 1, Y, notches)
        fall = Hh
        m.solid(wa, S - 3, wb, S + 1, kind=f"ledge_s:{fall}")
        m.solid(wa, N - 1, wb, N + 3, kind=f"ledge_x:{fall}")
        if wa <= xa: m.solid(wa - 1, N, wa + 3, S, kind=f"ledge_w:{fall}")
        if wb >= xb: m.solid(wb - 3, N, wb + 1, S, kind=f"ledge_e:{fall}")
        # parts of the building that stand up over the roof: walls, all the way up the picture
        for t in b.tall:
            tx0, tx1, th = t[:3]
            back = t[3] if len(t) > 3 else 0.0                          # how far from the front edge of the roof it begins
            m.solid(X + int(round(tx0 * 16)), N - int(round(th * 16)), X + int(round(tx1 * 16)), S - int(round(back * 16)))
        if wa > xa: m.solid(xa, N, wa, S)
        if wb < xb and not any(abs(X + int(round(t[0] * 16)) - wb) <= 1 for t in b.tall): m.solid(wb, N, xb, S)
        for (bx0, by0, bx1, by1) in b.blocks:
            m.solid(X + int(round(bx0 * 16)), S - int(round(by1 * 16)), X + int(round(bx1 * 16)), S - int(round(by0 * 16)))
        if b.upper:
            ux0, ux1, ud, uh = b.upper
            foot = S - int(round((b.d - ud) * 16))                      # where the upper block stands on the roof
            ua, ub = X + int(round(ux0 * 16)), X + int(round(ux1 * 16))
            un = []
            if b.roof_door is not None:
                rx = X + int(round(b.roof_door * 16))
                un.append((rx - 6, rx + 6))
                m.spawn(b.key + "_roof", rx, foot + 8, "down")
                if inside:
                    m.exit(rx - 4, foot - 9, rx + 4, foot - 4, inside, b.key + "_up")
            _front(m, ua, ub, N - int(round(uh * 16)), foot, un)
        if b.hatch:
            hx, hy = X + int(round(b.hatch[0] * 16)), S - int(round(b.hatch[1] * 16))
            m.spawn(b.key + "_roof", hx, hy + 11, "down")
            if inside:
                m.exit(hx - 5, hy - 5, hx + 5, hy + 3, inside, b.key + "_up")
            # the frame of it, either side and behind, so that the only way on to it is from the front
            m.solid(hx - 10, hy - 7, hx - 7, hy + 4); m.solid(hx + 7, hy - 7, hx + 10, hy + 4); m.solid(hx - 10, hy - 9, hx + 10, hy - 5)

    # ---- the stair along the front, and ladders: ways a walker is carried up and down
    if b.stair:
        xf, xh = b.stair
        sgn = 1 if xh > xf else -1
        fa, ha = X + int(round(xf * 16)), X + int(round(xh * 16))
        m.solid(min(fa, ha), Y, max(fa, ha), Y + 9)
        foot = (fa - sgn * 3, Y + 5)
        head = (ha - sgn * 10, Y + 5 - Hh)
        m.markers.append({"kind": "rail", "x": foot[0], "y": foot[1], "w": head[0] - foot[0], "h": head[1] - foot[1], "who": "stair", "id": b.key + "_stair"})
    for k, lx in enumerate(b.ladders):
        px = X + int(round(lx * 16))
        m.markers.append({"kind": "rail", "x": px, "y": Y + 9, "w": 0, "h": (S + 3) - (Y + 9), "who": "ladder", "id": f"{b.key}_ladder{k}"})
        m.solid(px - 4, Y, px + 4, Y + 5)                              # the foot of it
    for (ex0, ey0, ex1, ey1) in b.extra:
        m.solid(X + int(round(ex0 * 16)), Y - int(round(ey1 * 16)), X + int(round(ex1 * 16)), Y - int(round(ey0 * 16)))
    return o


def gong(m, x, y, uid):
    """A gong in a frame of its own: what a shut house answers to."""
    m.model("gong_stand", dprops.gong_stand, x, y, box=(-11, -4, 11, 0), frames=3, names=["gong_stand", "gong_stand_a", "gong_stand_b"], still=True,
            kind="gong", data={"id": uid, "who": "hand"}, lights=False)
