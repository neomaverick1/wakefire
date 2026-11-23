"""Things that stand in the dungeons and are worked from a distance: gongs for a sling stone or
a throwing stick, sun discs for the light off a raised shield, the scales of the tomb."""
import math
import numpy as np
import town
from forge import Model, M, Mat, RAMPS, m_mottle, m_planks, m_brick

PX = 1 / 16.0


def _disc(m, cx, y, cz, r, mat, n=14):
    m.face([(cx + math.cos(a) * r, cz + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)], y, mat)


def gong_wall(frame=0, z=1.55):
    """A bronze gong hung on a wall from a cedar bracket, too high for a blade. frame 1 and 2 are
    it swinging after a hit. Origin at the foot of the wall under it."""
    m = Model()
    sw = (0.0, 0.07, -0.07)[frame]
    wood = M('cedar', 4.2, m_planks(3, 'h'))
    brz = M('bronze', 4.2, m_mottle(5, 0.4), gloss=0.03)
    m.part(); m.box(-0.62, -0.34, z + 0.56, 0.62, 0.0, z + 0.66, wood, top=M('cedar', 4.8))
    m.part()
    for sx in (-0.5, 0.5):
        m.box(sx - PX, -0.08, z + 0.2, sx + PX, 0.0, z + 0.56, wood)
    m.part()
    for sx in (-0.2, 0.2):
        m.box(sx + sw * 0.5 - PX / 2, -0.24, z + 0.36, sx + sw * 0.5 + PX / 2, -0.2, z + 0.58, M('straw', 4.0))
    m.part(); _disc(m, sw, -0.22, z, 0.44, M('bronze', 3.3))
    m.part(); _disc(m, sw, -0.24, z, 0.39, brz)
    m.part(); _disc(m, sw, -0.26, z, 0.15, M('gold', 4.4, gloss=0.03))
    m.part(); _disc(m, sw, -0.27, z + 0.02, 0.06, M('gold', 5.2))
    return m


def gong_stand(frame=0):
    """The same gong in a frame of its own, to stand on a floor."""
    m = Model()
    sw = (0.0, 0.07, -0.07)[frame]
    wood = M('cedar', 4.2, m_planks(3, 'v'))
    brz = M('bronze', 4.2, m_mottle(5, 0.4), gloss=0.03)
    z = 0.86
    m.part()
    for sx in (-0.62, 0.56):
        m.box(sx, 0.0, 0, sx + 0.07, 0.1, 1.6, wood, top=M('cedar', 4.8))
        m.box(sx - 0.08, -0.12, 0, sx + 0.15, 0.2, 0.08, M('cedar', 3.6), top=M('cedar', 4.4))
    m.part(); m.box(-0.66, 0.0, 1.5, 0.67, 0.1, 1.6, wood, top=M('cedar', 4.8))
    m.part()
    for sx in (-0.2, 0.2):
        m.box(sx + sw * 0.5 - PX / 2, 0.03, z + 0.36, sx + sw * 0.5 + PX / 2, 0.07, 1.5, M('straw', 4.0))
    m.part(); _disc(m, sw, 0.04, z, 0.44, M('bronze', 3.3))
    m.part(); _disc(m, sw, 0.02, z, 0.39, brz)
    m.part(); _disc(m, sw, 0.0, z, 0.15, M('gold', 4.4, gloss=0.03))
    m.part(); _disc(m, sw, -0.01, z + 0.02, 0.06, M('gold', 5.2))
    return m


def sun_disc(lit=False, z=1.5):
    """A disc of polished gold let into a wall, rayed like the sun: dull until light is thrown on it."""
    m = Model()
    gold = Mat(RAMPS['glow'], 2.6, glow=True) if lit else M('gold', 3.2, m_mottle(5, 0.4))
    ray = Mat(RAMPS['glow'], 1.9, glow=True) if lit else M('gold', 2.6)
    m.part(); _disc(m, 0, -0.03, z, 0.5, M('lapis', 3.4))
    m.part()
    for k in range(12):
        a = k / 12 * 2 * math.pi
        ca, sa = math.cos(a), math.sin(a)
        m.quad((ca * 0.3 - sa * 0.05, -0.05, z + sa * 0.3 + ca * 0.05), (ca * 0.3 + sa * 0.05, -0.05, z + sa * 0.3 - ca * 0.05),
               (ca * 0.47 + sa * 0.012, -0.05, z + sa * 0.47 - ca * 0.012), (ca * 0.47 - sa * 0.012, -0.05, z + sa * 0.47 + ca * 0.012), ray, two=True)
    m.part(); _disc(m, 0, -0.06, z, 0.27, gold)
    m.part(); _disc(m, 0, -0.07, z, 0.12, Mat(RAMPS['glow'], 3.4, glow=True) if lit else M('gold', 4.4, gloss=0.03))
    if lit:
        m.light(0, -0.3, z, 3.2, (1.0, 0.86, 0.5), 0.7)
    return m


# ------------------------------------------------------------------ the great chests
def bigchest(open_=False):
    """A great chest, for one of the few things the game turns on: twice the size of the others, on a
    step of pale stone, cedar bound in bronze with gold at every corner and the sun in gold on its
    lid. Open, the lid stands back and the inside is all light."""
    m = Model()
    wood = M('cedar', 3.1, m_planks(5, 'h'))
    lidw = M('cedar', 3.6, m_planks(4, 'u'))
    brz = M('bronze', 4.6, gloss=0.04)
    gold = M('gold', 4.7, gloss=0.04)
    x0, x1, y0, y1, z0, h = -0.94, 0.94, 0.14, 1.0, 0.12, 0.56
    yc, r = (y0 + y1) / 2, (y1 - y0) / 2
    bands = (-0.56, 0.42)
    m.part(); m.box(x0 - 0.2, y0 - 0.18, 0, x1 + 0.2, y1 + 0.12, z0, M('sandstone', 4.2, m_mottle(8, 0.3)), top=M('sandstone', 4.8, m_mottle(8, 0.3)))
    m.part(); m.box(x0 - 0.1, y0 - 0.09, z0, x1 + 0.1, y1 + 0.06, z0 + 0.05, gold, top=M('gold', 4.2))
    inside = Mat(RAMPS['glow'], 2.9, m_mottle(2, 1.2), glow=True) if open_ else M('dark', 1.2)
    m.part(); m.box(x0, y0, z0 + 0.05, x1, y1, z0 + h, wood, top=inside)
    m.part()
    for sx in bands:
        m.box(sx, y0 - 0.025, z0 + 0.05, sx + 0.14, y0, z0 + h, brz)
    m.box(x0 - 0.01, y0 - 0.025, z0 + h - 0.06, x1 + 0.01, y0, z0 + h, brz)
    m.part()
    for sx in (x0 - 0.02, x1 - 0.16):                                   # gold at the corners, top to bottom
        m.box(sx, y0 - 0.04, z0 + 0.05, sx + 0.18, y0 - 0.02, z0 + h, gold)
    cz = z0 + 0.05 + (h - 0.05) * 0.5                                   # the sun on its face
    m.part(); _disc(m, -0.07, y0 - 0.04, cz, 0.17, gold, n=12)
    m.part(); _disc(m, -0.07, y0 - 0.05, cz, 0.08, M('gold', 5.4), n=10)
    zt = z0 + h
    if open_:
        m.part(); m.box(x0, y0, zt - 0.02, x1, y0 + 0.05, zt + 0.01, brz); m.box(x0, y1 - 0.05, zt - 0.02, x1, y1, zt + 0.01, brz)
        m.box(x0, y0, zt - 0.02, x0 + 0.05, y1, zt + 0.01, brz); m.box(x1 - 0.05, y0, zt - 0.02, x1, y1, zt + 0.01, brz)
        m.part()
        for k in range(6):
            m.quad((x0, y1 + 0.02 + 0.06 * k, zt + 0.12 * k), (x1, y1 + 0.02 + 0.06 * k, zt + 0.12 * k),
                   (x1, y1 + 0.02 + 0.06 * (k + 1), zt + 0.12 * (k + 1)), (x0, y1 + 0.02 + 0.06 * (k + 1), zt + 0.12 * (k + 1)), M('red', 2.2 + 0.18 * k), two=True)
        m.part()
        for sx in bands + (x0 - 0.02, x1 - 0.16):
            for k in range(6):
                m.quad((sx, y1 + 0.015 + 0.06 * k, zt + 0.12 * k), (sx + 0.16, y1 + 0.015 + 0.06 * k, zt + 0.12 * k),
                       (sx + 0.16, y1 + 0.015 + 0.06 * (k + 1), zt + 0.12 * (k + 1)), (sx, y1 + 0.015 + 0.06 * (k + 1), zt + 0.12 * (k + 1)),
                       M('gold', 3.0) if sx in (x0 - 0.02, x1 - 0.16) else M('bronze', 2.6), two=True)   # the backs of the bands: duller than their faces
        m.part(); m.box(x0 - 0.01, y1 + 0.37, zt + 0.68, x1 + 0.01, y1 + 0.42, zt + 0.76, gold)
        m.light(0, 0.4, 0.7, 3.4, (1.0, 0.82, 0.42), 0.7)
    else:
        m.part(); m.limb([(x0, yc, zt), (x1, yc, zt)], [r, r], lidw, n=14)
        m.part()
        for sx in bands:
            m.limb([(sx, yc, zt), (sx + 0.14, yc, zt)], [r + 0.02, r + 0.02], brz, n=14)
        m.part()
        for sx in (x0 - 0.02, x1 - 0.16):
            m.limb([(sx, yc, zt), (sx + 0.18, yc, zt)], [r + 0.03, r + 0.03], gold, n=14)
        # the sun, let into the crown of the lid
        m.part(); m.turned(-0.07, yc, [(0.21, zt + r - 0.035), (0.21, zt + r + 0.012)], gold, n=14, cap=M('gold', 5.0))
        m.part(); m.turned(-0.07, yc, [(0.1, zt + r + 0.012), (0.08, zt + r + 0.035)], M('gold', 5.2), n=10, cap=M('gold', 5.6))
        m.part()
        for k in range(8):
            a = k / 8 * 2 * math.pi + 0.39
            ca, sa = math.cos(a), math.sin(a)
            px, py = -0.07 + ca * 0.3, yc + sa * 0.3
            dz = zt + math.sqrt(max(0.0, r * r - (sa * 0.3) ** 2)) - 0.012
            m.box(px - 0.035, py - 0.035, dz, px + 0.035, py + 0.035, dz + 0.03, gold)
        m.part(); m.box(-0.2, y0 - 0.06, zt - 0.14, 0.06, y0 - 0.025, zt + 0.12, gold)                  # the hasp
        m.part(); m.box(-0.095, y0 - 0.065, zt - 0.07, -0.045, y0 - 0.06, zt + 0.03, M('dark', 1.0))
    return m


# ------------------------------------------------------------------ the crypt of the first watch
def crypt_door():
    """The way down under the old shrine: two posts and a lintel of squared stone in the rock behind
    the altar, a watchman's lamp cut on the lintel, steps going down into the dark."""
    m = Model()
    st = M('sandstone', 3.9, town.m_ashlar(10, 5))
    for sgn in (-1, 1):
        m.part(); m.box(min(sgn * 0.7, sgn * 1.06), 0.0, 0, max(sgn * 0.7, sgn * 1.06), 0.3, 1.34, st, top=M('sandstone', 4.7))
    m.part(); m.box(-1.16, -0.04, 1.24, 1.16, 0.3, 1.56, M('sandstone', 4.2, m_mottle(6, 0.3)), top=M('sandstone', 4.8))
    m.part(); m.quad((-0.7, 0.16, 0), (0.7, 0.16, 0), (0.7, 0.16, 1.24), (-0.7, 0.16, 1.24), M('dark', 0.6))
    for k in range(3):                                                                               # steps going down
        m.part(); m.box(-0.7, 0.02 + 0.04 * k, 0.0, 0.7, 0.15, 0.36 - 0.12 * k, M('sandstone', 2.9 - 0.7 * k), top=M('sandstone', 3.6 - 0.8 * k))
    m.part(); m.box(-0.78, -0.3, 0, 0.78, 0.0, 0.05, M('sandstone', 3.5), top=M('sandstone', 4.3, m_mottle(6, 0.3)))
    m.part(); m.box(-0.11, -0.06, 1.3, 0.11, -0.04, 1.42, M('bronze', 4.4))                          # the lamp on the lintel
    m.part(); m.box(-0.04, -0.07, 1.42, 0.04, -0.04, 1.5, Mat(RAMPS['glow'], 2.2, glow=True))
    return m


def plaque(w=1.5):
    """Writing cut into a slab let into the foot of a wall: what the watch wanted remembered."""
    m = Model()
    m.part(); m.box(-w / 2, -0.06, 0.34, w / 2, 0.0, 1.3, M('sandstone', 4.5, town.m_cuneiform(5)), top=M('sandstone', 4.9))
    m.part(); m.box(-w / 2 - 0.05, -0.08, 0.28, w / 2 + 0.05, 0.0, 0.34, M('bronze', 4.2))
    m.part(); m.box(-w / 2 - 0.05, -0.08, 1.3, w / 2 + 0.05, 0.0, 1.36, M('bronze', 4.2))
    return m


def stone_bed(sleeper=True, seed=0):
    """A bed of the old watch: a stone slab on two blocks, and on most of them a watchman who went
    off duty for good, under what is left of his cloak, his helmet still on."""
    m = Model()
    st = M('sandstone', 3.6, m_mottle(7, 0.4))
    m.part(); m.box(-0.5, 0.0, 0, 0.5, 1.6, 0.34, st, top=M('sandstone', 4.1, m_mottle(7, 0.3)))
    m.part(); m.box(-0.5, 1.3, 0.34, 0.5, 1.6, 0.44, M('sandstone', 3.9), top=M('sandstone', 4.4))       # the head-rest
    if sleeper:
        cloak = M(('red', 'blue', 'linen')[seed % 3], (2.4, 2.3, 3.0)[seed % 3], m_mottle(5, 0.5), soft=True)
        # feet, knees, hips, chest, shoulders
        m.part(); m.limb([(0, 0.12, 0.40), (0, 0.42, 0.42), (0, 0.78, 0.44), (0, 1.08, 0.47), (0, 1.26, 0.45)], [0.13, 0.15, 0.2, 0.25, 0.2], cloak, n=8)
        m.part(); m.blob(0, 1.42, 0.50, 0.12, 0.12, 0.10, M('bone', 4.4), n=8, rings=5)
        m.part(); m.blob(0, 1.45, 0.57, 0.15, 0.15, 0.09, M('bronze', 3.4 + (seed % 2) * 0.5), n=8, rings=4)   # his helmet, still on
        m.part(); m.box(0.3, 0.08, 0.35, 0.34, 1.5, 0.39, M('wood', 3.6))                                      # his spear beside him
        m.part(); m.limb([(0.32, 1.5, 0.37), (0.32, 1.62, 0.37)], [0.045, 0.005], M('bronze', 3.6), n=4)
    else:
        m.part(); m.box(-0.44, 0.1, 0.34, 0.44, 1.2, 0.38, M('linen', 4.0, soft=True), top=M('linen', 4.4, soft=True))
        m.part(); m.box(-0.44, 0.1, 0.38, 0.44, 0.34, 0.41, M('red', 2.6, soft=True), top=M('red', 3.0, soft=True))   # the blanket, folded back
    return m


def spear_rack():
    """A rack of the old watch's spears against a wall, bronze heads up, most of them green."""
    m = Model()
    wood = M('cedar', 3.6)
    m.part(); m.box(-0.8, 0.0, 0.5, 0.8, 0.08, 0.58, wood); m.box(-0.8, 0.0, 1.2, 0.8, 0.08, 1.28, wood)
    m.part()
    for sx in (-0.8, 0.74):
        m.box(sx, 0.0, 0, sx + 0.06, 0.1, 1.4, wood)
    for i, x in enumerate((-0.6, -0.35, -0.1, 0.18, 0.44, 0.64)):
        if i == 3:
            continue                                                       # one is missing
        m.part(); m.box(x - 0.02, -0.05, 0.0, x + 0.02, -0.01, 1.75, M('wood', 4.0))
        m.part(); m.limb([(x, -0.03, 1.75), (x, -0.03, 1.98)], [0.05, 0.005], M('bronze', 3.4 + (i % 3) * 0.5), n=4)
    return m


def _crypt_wall(brick):
    if brick:
        # a way that was bricked up afterwards, in a hurry, with whatever there was
        return (M('brick', 3.5, m_brick(8, 4)), M('brick', 4.3, m_mottle(8, 0.4)), M('brick', 3.0, m_brick(8, 4)))
    return (M('sandstone', 3.6, town.m_ashlar(12, 6)), M('sandstone', 4.0, m_mottle(10, 0.3)), M('sandstone', 3.2, town.m_ashlar(16, 8)))


def crypt_partition(length, h=1.2, d=0.5, brick=False):
    """A low wall of squared stone inside the crypt, running east from the origin."""
    m = Model()
    body, top, foot = _crypt_wall(brick)
    m.part(); m.box(0, 0, 0, length, d, h, body, top=top)
    m.part(); m.box(0, -PX, 0, length, d, 0.3, foot, top=top)
    return m


def crypt_partition_ns(depth, wd=0.5, h=1.2, brick=False):
    m = Model()
    body, top, foot = _crypt_wall(brick)
    m.part(); m.box(0, 0, 0, wd, depth, h, body, top=top)
    m.part(); m.box(-PX, -PX, 0, wd + PX, depth, 0.3, foot, top=top)
    return m


def pier(h=1.9):
    """A square pier of the crypt: what holds the hill up."""
    m = Model()
    m.part(); m.box(-0.42, 0.0, 0, 0.42, 0.62, h, M('sandstone', 3.7, town.m_ashlar(10, 5)), top=M('sandstone', 4.1, m_mottle(8, 0.3)))
    m.part(); m.box(-0.48, -0.05, 0, 0.48, 0.67, 0.28, M('sandstone', 3.4, town.m_ashlar(12, 6)), top=M('sandstone', 4.3))
    m.part(); m.box(-0.48, -0.05, h - 0.16, 0.48, 0.67, h, M('sandstone', 4.0), top=M('sandstone', 4.3, m_mottle(8, 0.3)))
    return m


def roots(span=3.0, seed=0, thick=0.9):
    """Olive roots, come down through the roof looking for water and grown across a way through:
    a curtain of them as thick as an arm, from the floor to over a man's head, seen from the front.
    Nothing gets through it that cannot cut. Runs east from the origin, across a gap in a wall;
    `thick` is how far back from the wall's face it goes."""
    r = np.random.default_rng(seed + 11); m = Model()
    mid = thick / 2
    n = max(6, int(span * 4.5))
    for i in range(n):
        x = span * (i + 0.5) / n + float(r.uniform(-0.05, 0.05))
        y0, y1, y2 = mid + float(r.uniform(-0.4, 0.4)), mid + float(r.uniform(-0.28, 0.28)), mid + float(r.uniform(-0.36, 0.36))
        top = float(r.uniform(1.25, 1.8))
        m.part(); m.limb([(x, y0, 0.0), (x + float(r.uniform(-0.12, 0.12)), y1, top * 0.45), (x + float(r.uniform(-0.12, 0.12)), y2, top * 0.8), (x, mid + (y2 - mid) * 0.5, top)],
                         [0.095, 0.075, 0.055, 0.025], M('trunk', 3.0 + float(r.uniform(0, 1.5))), n=5)
    for i in range(6):                                                       # the ones that cross
        xa, xb = float(r.uniform(0.05, span * 0.4)), float(r.uniform(span * 0.6, span - 0.05))
        if i % 2: xa, xb = xb, xa
        za, zb = float(r.uniform(0.15, 0.6)), float(r.uniform(0.85, 1.5))
        m.part(); m.limb([(xa, mid + float(r.uniform(-0.3, 0.3)), za), ((xa + xb) / 2, mid + float(r.uniform(-0.25, 0.25)), (za + zb) / 2 + 0.12), (xb, mid + float(r.uniform(-0.3, 0.3)), zb)],
                         [0.065, 0.05, 0.03], M('trunk', 3.5 + 0.3 * i), n=5)
    m.part()
    for i in range(16):                                                      # hair roots
        x = float(r.uniform(0.05, span - 0.05)); y = mid + float(r.uniform(-0.38, 0.1)); z = float(r.uniform(0.5, 1.65))
        m.limb([(x, y, z), (x + float(r.uniform(-0.12, 0.12)), y, z - float(r.uniform(0.25, 0.5)))], [0.018, 0.006], M('trunk', 4.6), n=3)
    for i in range(5):                                                       # and along the floor, out towards whoever comes
        x = float(r.uniform(0.15, span - 0.15))
        m.part(); m.limb([(x, mid - 0.2, 0.03), (x + float(r.uniform(-0.25, 0.25)), -0.1, 0.03), (x + float(r.uniform(-0.4, 0.4)), -0.42, 0.015)], [0.06, 0.04, 0.012], M('trunk', 3.4), n=4)
    return m
