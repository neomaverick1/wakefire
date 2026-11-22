"""Ashkel's buildings and street furniture, built for the forge: mud-brick houses with flat roofs,
parapets, roof beams poking through the walls, outside stairs, awnings and roof clutter; the
precinct wall and its glazed gate; stalls, wells, carts, jars, braziers, trees.

Every builder returns a forge Model whose origin is the middle of its front foot (the point the
game sorts it by); the body runs north (+y) and up (+z). Sizes are in tiles."""
import math
import numpy as np
from forge import (Model, M, Mat, RAMPS, hash2, vnoise, fbm, m_brick, m_ashlar, m_plaster, m_planks, m_mottle,
                   m_stripes, m_leaves, m_reeds, m_glazed, m_clumps, m_rubble, m_strata)

PX = 1 / 16.0


def rnd(seed):
    return np.random.default_rng(seed)


# plaster families: (ramp, where the wall sits on it)
PLASTER = [('mud', 4.55), ('limewash', 4.5), ('clay', 4.5), ('sandstone', 4.55), ('mud', 4.2)]


def m_fire(z0, h):
    """Flame colour by height: white-gold at the root, orange at the tip."""
    def f(u, v, P, seed):
        return -np.clip((P[..., 2] - z0) / h, 0, 1) * 3.2, None
    return f


def m_coals():
    def f(u, v, P, seed):
        h = hash2(u, v, seed)
        return np.where(h > 0.72, 2.6, np.where(h > 0.5, 1.0, 0.0)), h > 0.5
    return f


def m_rings(step=3):
    def f(u, v, P, seed):
        return np.where((v % step) == 0, -1.0, (hash2(np.floor_divide(v, step), np.floor_divide(u, 3), seed) - 0.5) * 0.7), None
    return f


def m_rosettes(step=16, band=None):
    """Glazed brick with gold rosettes at intervals (ramp2 is the gold)."""
    g = m_glazed(8, 4)
    def f(u, v, P, seed):
        t, _ = g(u, v, P, seed)
        cx = (u % step) - step // 2; cy = (v % step) - step // 2
        r2 = cx * cx + cy * cy
        ros = (r2 <= 9) & ~((cx == 0) & (cy == 0)) & ((np.abs(cx) + np.abs(cy)) % 2 == 0) | (r2 <= 2)
        t = np.where(ros, np.where(r2 <= 2, 0.8, 0.2), t)
        return t, ros
    return f


class Mats:
    """The surfaces a building or prop is made of."""
    def __init__(self, seed=0, plaster=None):
        r = rnd(seed)
        name, base = PLASTER[plaster if plaster is not None else int(r.integers(0, len(PLASTER)))]
        self.wall = M(name, base, m_plaster(), ramp2='brick')
        self.wall_plain = M(name, base, m_mottle(18, 0.42))
        self.trim = M(name, base + 0.9, m_mottle(20, 0.3))
        self.stain = M(name, base - 0.9, m_mottle(9, 0.4))
        self.plinth = M('brick', 3.6, m_brick(8, 4, -1.0, 0.8))
        self.roof = M('roof', 4.5, m_mottle(16, 0.45, specks=0.012, speck_t=-1.0))
        self.wood = M('wood', 4.3, m_planks(4, 'v'))
        self.wood_h = M('wood', 4.3, m_planks(4, 'h'))
        self.beam = M('wood', 4.7)
        self.dark = M('dark', 1.6)
        self.door = M('cedar', 4.3, m_planks(4, 'v'))
        self.reed = M('reed', 4.4, m_reeds(3))
        self.glow = Mat(RAMPS['glow'], 2.4, glow=True)
        self.glow_dim = Mat(RAMPS['glow'], 0.4, glow=True)
        self.pot = M('clay', 4.6, gloss=0.012)
        self.pot2 = M('brick', 4.5)
        self.stone = M('sandstone', 4.0, m_ashlar(12, 6))
        self.rock = M('stone', 4.3, m_mottle(7, 0.5))
        self.bronze = M('bronze', 4.4, gloss=0.03)
        self.gold = M('gold', 4.2, gloss=0.03)
        self.iron = M('iron', 3.6)
        self.rope = M('straw', 4.2)
        self.linen = M('linen', 4.6, soft=True)
        self.sack = M('straw', 4.3, m_mottle(5, 0.35), soft=True)
        self.water = M('water', 2.6, m_mottle(4, 0.6))


MT = Mats(0, 0)


def cloth(a, b, w=5, soft=True, base=4.6):
    return M(a, base, m_stripes(w, 'u'), ramp2=b, soft=soft)


# ------------------------------------------------------------------ parts of a house
def door(m, mt, x, y, w=1.0, h=1.75, lit=False):
    """A doorway in a south wall whose face is at y: dark reveal, plank door, lintel, step."""
    m.part()
    m.quad((x - w / 2 - PX, y - 0.02, 0), (x + w / 2 + PX, y - 0.02, 0), (x + w / 2 + PX, y - 0.02, h + PX), (x - w / 2 - PX, y - 0.02, h + PX), mt.dark)
    m.part()
    if lit:
        m.quad((x - w / 2, y - 0.03, 0), (x + w / 2, y - 0.03, 0), (x + w / 2, y - 0.03, h), (x - w / 2, y - 0.03, h), mt.glow_dim)
        m.part()
        m.quad((x - w / 2, y - 0.05, 0), (x - w / 2 + w * 0.42, y - 0.05, 0), (x - w / 2 + w * 0.42, y - 0.05, h), (x - w / 2, y - 0.05, h), mt.door)
        m.light(x, y - 0.4, 0.9, 2.6, (1.0, 0.72, 0.4), 0.6)
    else:
        m.quad((x - w / 2, y - 0.04, 0), (x + w / 2, y - 0.04, 0), (x + w / 2, y - 0.04, h), (x - w / 2, y - 0.04, h), mt.door)
        m.part()
        m.box(x + w * 0.22, y - 0.07, h * 0.48, x + w * 0.22 + PX, y - 0.04, h * 0.48 + 2 * PX, mt.bronze)
    m.part()
    m.box(x - w / 2 - 3 * PX, y - 0.10, h, x + w / 2 + 3 * PX, y, h + 3 * PX, mt.beam)            # lintel
    m.part()
    m.box(x - w / 2 - 2 * PX, y - 0.34, 0, x + w / 2 + 2 * PX, y, 2 * PX, mt.stone)               # step


def window(m, mt, x, y, z, w=0.5, h=0.5, lit=False, bars=True):
    m.part()
    m.quad((x - w / 2, y - 0.02, z), (x + w / 2, y - 0.02, z), (x + w / 2, y - 0.02, z + h), (x - w / 2, y - 0.02, z + h), mt.glow if lit else mt.dark)
    m.part()
    if bars:
        n = max(1, int(round(w / (3 * PX))) - 1)
        for i in range(n):
            bx = x - w / 2 + (i + 1) * w / (n + 1)
            m.box(bx - PX / 2, y - 0.05, z, bx + PX / 2, y - 0.02, z + h, mt.beam if not lit else mt.dark)
    m.part()
    m.box(x - w / 2 - PX, y - 0.08, z - PX, x + w / 2 + PX, y, z, mt.trim)                         # sill
    m.box(x - w / 2 - PX, y - 0.06, z + h, x + w / 2 + PX, y, z + h + PX, mt.beam)                 # lintel
    if lit:
        m.light(x, y - 0.5, z + h / 2, 2.4, (1.0, 0.74, 0.4), 0.55)


def beam_ends(m, mt, x0, x1, y, z, step=0.75):
    m.part()
    n = int((x1 - x0) / step)
    off = ((x1 - x0) - n * step) / 2
    for i in range(n + 1):
        x = x0 + off + i * step
        m.box(x - PX, y - 0.22, z - PX, x + PX, y, z + PX, mt.beam)


def parapet(m, mt, x0, y0, x1, y1, z, h=0.25, t=3 * PX, gap=None, mat=None):
    """A low wall round a flat roof. gap = (xa, xb) leaves an opening in the south side."""
    mat = mat or mt.trim
    m.part()
    if gap:
        if gap[0] > x0 + 0.01: m.box(x0, y0, z, gap[0], y0 + t, z + h, mat)
        if gap[1] < x1 - 0.01: m.box(gap[1], y0, z, x1, y0 + t, z + h, mat)
    else:
        m.box(x0, y0, z, x1, y0 + t, z + h, mat)
    m.box(x0, y1 - t, z, x1, y1, z + h, mat)
    m.box(x0, y0 + t, z, x0 + t, y1 - t, z + h, mat)
    m.box(x1 - t, y0 + t, z, x1, y1 - t, z + h, mat)


JAR = {0: [(0.10, 0), (0.22, 0.10), (0.27, 0.26), (0.24, 0.42), (0.13, 0.52), (0.11, 0.58), (0.15, 0.62)],     # water jar
       1: [(0.05, 0), (0.14, 0.14), (0.19, 0.38), (0.17, 0.60), (0.08, 0.76), (0.07, 0.88), (0.11, 0.92)],     # amphora
       2: [(0.12, 0), (0.26, 0.08), (0.30, 0.20), (0.27, 0.26)],                                                # bowl
       3: [(0.14, 0), (0.30, 0.16), (0.36, 0.42), (0.31, 0.70), (0.18, 0.84), (0.16, 0.92), (0.22, 0.98)]}     # big storage jar


def jar(m, mt, x, y, z=0, s=1.0, kind=0, mat=None, n=10):
    m.part()
    mat = mat or (mt.pot if kind != 1 else mt.pot2)
    m.turned(x, y, [(r * s, zz * s + z) for r, zz in JAR[kind]], mat, n=n, cap=mt.dark)


def stairs(m, mt, x0, x1, y, z1, depth=0.55):
    """Steps climbing along a south wall (at y) from the ground at x0 up to z1 at x1."""
    m.part()
    n = max(2, int(round(z1 / 0.25)))
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n; xb = x0 + (x1 - x0) * (i + 1) / n
        m.box(min(xa, xb), y - depth, 0, max(xa, xb), y, z1 * (i + 1) / n, mt.wall_plain, top=mt.trim)


def ladder(m, mt, x, y, z1, lean=0.5, w=0.36):
    m.part()
    for sx in (-w / 2, w / 2):
        m.beam((x + sx, y - lean, 0), (x + sx, y, z1 + 0.2), 1.2 * PX, mt.beam)
    n = int(z1 / 0.3)
    for i in range(1, n + 1):
        t = i / (n + 1)
        m.beam((x - w / 2, y - lean * (1 - t), (z1 + 0.2) * t), (x + w / 2, y - lean * (1 - t), (z1 + 0.2) * t), PX, mt.beam)


def roof_clutter(m, mt, r, x0, y0, x1, y1, z):
    """What people keep on a roof: a reed mat, jars, washing on a rack, a hatch."""
    if x1 - x0 < 1.9 or y1 - y0 < 0.9:
        return
    mx = float(r.uniform(x0, x1 - 1.6))
    m.part()
    m.box(mx, y0 + 0.1, z, mx + 1.5, min(y1, y0 + 1.1), z + 0.5 * PX, mt.reed)
    for i in range(int(r.integers(1, 4))):
        jar(m, mt, float(r.uniform(x0 + 0.2, x1 - 0.2)), float(r.uniform(y0 + 0.2, y1 - 0.1)), z, s=0.8, kind=int(r.integers(0, 3)))
    if r.random() < 0.6 and x1 - x0 > 2.4:
        kx = float(r.uniform(x0, x1 - 1.3)); ky = y1 - 0.1
        m.part()
        for px in (kx, kx + 1.2):
            m.box(px - PX / 2, ky, z, px + PX / 2, ky + PX, z + 0.75, mt.beam)
        m.box(kx, ky, z + 0.72, kx + 1.2, ky + PX, z + 0.72 + PX, mt.beam)
        m.part()
        for cx in np.arange(kx + 0.1, kx + 1.0, 0.36):
            cl = M(['cream', 'red', 'blue', 'ochre', 'linen'][int(r.integers(0, 5))], 4.6, soft=True)
            m.quad((cx, ky - 0.02, z + 0.3 + r.uniform(0, 0.12)), (cx + 0.26, ky - 0.02, z + 0.3 + r.uniform(0, 0.12)), (cx + 0.26, ky - 0.02, z + 0.72), (cx, ky - 0.02, z + 0.72), cl, two=True)
    elif r.random() < 0.5:
        hx = float(r.uniform(x0, x1 - 0.8)); hy = float(r.uniform(y0 + 0.3, max(y0 + 0.31, y1 - 0.7)))
        m.part()
        m.box(hx, hy, z, hx + 0.7, hy + 0.6, z + 0.12, mt.beam, top=mt.wood)


def house(w=5.0, d=3.0, h=2.75, seed=0, plaster=None, door_x=None, upper=None, stair=None, lit=True,
          roof_stuff=True, ladder_x=None, skip=(), plain=False):
    """A mud-brick house. upper = (x0, x1, depth, height) adds a second storey at the back;
    stair = 'l' or 'r' adds an outside stair up to the roof; skip = [(xa, xb)] keeps windows
    out of stretches of the front (behind an awning or a stall); plain = no door at all."""
    r = rnd(seed)
    mt = Mats(seed, plaster)
    m = Model()
    x0, x1 = -w / 2, w / 2
    m.part()
    m.box(x0, 0, 0, x1, d, h, mt.wall, top=mt.roof)
    m.part()
    m.box(x0 - PX, -PX, 0, x1 + PX, d, 0.38, mt.plinth, top=mt.trim)                # the foot of the wall, in fired brick
    gap = None
    if stair:
        gap = (x1 - 0.55, x1) if stair == 'r' else (x0, x0 + 0.55)
    parapet(m, mt, x0, 0, x1, d, h, gap=gap)
    beam_ends(m, mt, x0 + 0.3, x1 - 0.3, 0, h - 0.42)
    dx = door_x if door_x is not None else float(r.uniform(x0 + 1.0, x1 - 1.0))
    if stair == 'r': dx = min(dx, x1 - 3.0)
    if stair == 'l': dx = max(dx, x0 + 3.0)
    if not plain:
        door(m, mt, dx, 0, lit=lit and r.random() < 0.15)
    else:
        dx = 99
    blocked = list(skip)
    if stair == 'r': blocked.append((x1 - 2.5, x1))
    if stair == 'l': blocked.append((x0, x0 + 2.5))
    k = 0
    for wx in np.arange(x0 + 0.8, x1 - 0.5, 1.25):
        if abs(wx - dx) < 1.05 or any(a - 0.3 < wx < b + 0.3 for a, b in blocked):
            continue
        window(m, mt, wx, 0, 1.45, 0.44, 0.5, lit=lit and hash2(k, seed, 3) < 0.22)
        k += 1
    if stair:
        if stair == 'r': stairs(m, mt, x1 - 2.3, x1, 0, h)
        else: stairs(m, mt, x0 + 2.3, x0, 0, h)
    # a damp streak under a spout
    spx = float(r.uniform(x0 + 0.6, x1 - 0.6))
    if abs(spx - dx) > 0.8 and not any(a < spx < b for a, b in blocked):
        m.part()
        m.box(spx - PX, -0.14, h - 0.08, spx + PX, 0, h, mt.beam)
        m.quad((spx - PX, -0.012, h - 1.1 - r.uniform(0, 0.5)), (spx + PX, -0.012, h - 1.3), (spx + PX, -0.012, h - 0.08), (spx - PX, -0.012, h - 0.08), mt.stain)
    ud = 0
    if upper:
        ux0, ux1, ud, uh = upper
        m.part()
        m.box(ux0, d - ud, h, ux1, d, h + uh, mt.wall, top=mt.roof)
        parapet(m, mt, ux0, d - ud, ux1, d, h + uh, h=0.19)
        beam_ends(m, mt, ux0 + 0.3, ux1 - 0.3, d - ud, h + uh - 0.36)
        m.push((0, 0, h))
        door(m, mt, (ux0 + ux1) / 2 - 0.35, d - ud, w=0.8, h=min(1.5, uh - 0.5), lit=False)
        if ux1 - ux0 > 2.4:
            window(m, mt, (ux0 + ux1) / 2 + 0.8, d - ud, 0.8, 0.4, 0.44, lit=lit and r.random() < 0.6)
        m.pop()
        if roof_stuff:
            roof_clutter(m, mt, r, ux0 + 0.4, d - ud + 0.4, ux1 - 0.4, d - 0.4, h + uh)
    if roof_stuff:
        roof_clutter(m, mt, r, x0 + 0.5, 0.45, x1 - 0.5 - (0.6 if stair == 'r' else 0), d - ud - 0.4, h)
    if ladder_x is not None:
        ladder(m, mt, ladder_x, 0, h)
    return m


def awning(w=2.4, out=1.1, z=1.95, drop=0.35, colors=('red', 'cream'), sag=0.10):
    """Striped cloth from a wall out to two poles. The origin is between the poles, so the game
    draws whoever stands under it behind the cloth."""
    m = Model(); mt = MT
    x0, x1 = -w / 2, w / 2
    cols, rows = 9, 5
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        for k in range(cols):
            s = k / (cols - 1)
            g[i, k] = (x0 + (x1 - x0) * s, out * (1 - t), z - drop * t - sag * math.sin(math.pi * s) * t - 0.05 * math.sin(math.pi * t))
    m.part(); m.sheet(g, cloth(*colors))
    m.part()
    for px in (x0 + 2 * PX, x1 - 2 * PX):
        m.box(px - PX, 0, 0, px + PX, 2 * PX, z - drop + PX, mt.beam)
    m.box(x0, 0, z - drop, x1, PX, z - drop + PX, mt.beam)
    return m


# ------------------------------------------------------------------ street furniture
STALL_DEEP = 1.6      # from the front of the table to the back posts


def stall_goods(m, mt, seed, x0, x1, z=0.72):
    xs = np.linspace(x0 + 0.42, x1 - 0.42, 4)
    fruit = ['red', 'fig', 'ochre', 'green', 'cream']
    for i, gx in enumerate(xs):
        k = (seed + i) % 4
        gy = 0.42 + 0.1 * ((i + seed) % 2)
        if k == 0:                                       # a basket of fruit
            m.part(); m.turned(gx, gy, [(0.15, z), (0.23, z + 0.12), (0.24, z + 0.18)], mt.reed, n=9, cap=mt.dark)
            fr = M(fruit[(seed + i) % len(fruit)], 4.4, soft=True)
            m.part()
            for j in range(6):
                a_ = j * 2.4
                m.blob(gx + math.cos(a_) * 0.1, gy + math.sin(a_) * 0.09, z + 0.2 + 0.03 * (j % 2), 0.08, 0.08, 0.07, fr, n=6, rings=3)
        elif k == 1:                                     # jars
            jar(m, mt, gx - 0.12, gy, z, s=0.62, kind=0); jar(m, mt, gx + 0.15, gy + 0.08, z, s=0.55, kind=1)
        elif k == 2:                                     # bolts of cloth
            for j, nm in enumerate(['blue', 'red', 'ochre'][:2 + seed % 2]):
                m.part(); m.box(gx - 0.22, gy - 0.2 + j * 0.15, z, gx + 0.22, gy - 0.08 + j * 0.15, z + 0.1 + 0.04 * j, M(nm, 4.5, soft=True))
        else:                                            # flat loaves on a board
            m.part()
            for j in range(3):
                m.turned(gx - 0.14 + 0.14 * j, gy + (0.08 if j == 1 else -0.04), [(0.1, z), (0.11, z + 0.04), (0.07, z + 0.07)], M('straw', 4.6, soft=True), n=7, cap=M('straw', 4.9))


def stall_front(seed=0, w=2.75):
    """The counter of a market stall with its goods. The seller stands behind it; the posts and
    awning behind him are a second prop (stall_back), so he is drawn between the two."""
    mt = MT; m = Model()
    x0, x1 = -w / 2, w / 2
    m.part(); m.box(x0 + 0.1, 0.1, 0, x1 - 0.1, 0.82, 0.64, mt.wood, top=mt.wood_h)
    m.part(); m.box(x0 + 0.04, 0.05, 0.62, x1 - 0.04, 0.88, 0.72, mt.beam, top=mt.wood_h)
    stall_goods(m, mt, seed, x0, x1)
    return m


def stall_back(seed=0, w=2.75):
    """The back of a market stall: four posts, a striped awning high enough to stand under, a lamp."""
    mt = MT; m = Model()
    x0, x1 = -w / 2, w / 2
    d = 0.8                                             # the awning comes this far forward of the back posts
    zb, zf = 2.55, 2.3
    m.part()
    for px in (x0, x1 - 2 * PX):
        m.box(px, 0, 0, px + 2 * PX, 2 * PX, zb, mt.beam)
        m.box(px, -d, zf - 0.04, px + 2 * PX, 0, zf + 0.04, mt.beam)
    cols, rows = 9, 4
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        for k in range(cols):
            s_ = k / (cols - 1)
            g[i, k] = (x0 - 0.12 + (w + 0.24) * s_, 0.12 - (d + 0.2) * t, zb + 0.04 - (zb - zf) * t - 0.1 * math.sin(math.pi * s_) * math.sin(math.pi * (0.2 + 0.8 * t)))
    cl = cloth(*[('red', 'cream'), ('blue', 'cream'), ('ochre', 'red'), ('green', 'cream')][seed % 4])
    m.part(); m.sheet(g, cl)
    m.part()
    for k in range(cols - 1):
        a_, b_ = g[-1, k], g[-1, k + 1]
        m.quad((a_[0], a_[1] - 0.01, a_[2] - 0.2), (b_[0], b_[1] - 0.01, b_[2] - 0.2), (b_[0], b_[1] - 0.01, b_[2]), (a_[0], a_[1] - 0.01, a_[2]), cl, two=True)
    # a cloth hung across the back, to keep the wind off
    back = M(['cream', 'linen', 'cream', 'linen'][seed % 4], 4.0, m_mottle(9, 0.35), soft=True)
    m.part(); m.quad((x0 + 2 * PX, 0.01, 0.5), (x1 - 2 * PX, 0.01, 0.5), (x1 - 2 * PX, 0.01, 2.2), (x0 + 2 * PX, 0.01, 2.2), back, two=True)
    # the lamp
    lx = x0 + 0.45 if seed % 2 else x1 - 0.45
    m.part(); m.box(lx - PX / 2, -d - 0.06, zf - 0.5, lx + PX / 2, -d - 0.06 + PX, zf - 0.2, mt.rope)
    m.part(); m.box(lx - 1.5 * PX, -d - 0.12, zf - 0.7, lx + 1.5 * PX, -d, zf - 0.5, Mat(RAMPS['glow'], 2.8, glow=True))
    m.light(lx, -d - 0.06, zf - 0.6, 3.0, (1.0, 0.72, 0.38), 0.7)
    return m


def well():
    """A round stone well with a timber frame, a roller, and a bucket on the rim."""
    m = Model(); mt = MT
    st = M('sandstone', 4.1, m_ashlar(9, 5))
    m.part()
    m.turned(0, 0.8, [(0.80, 0), (0.80, 0.56), (0.74, 0.62), (0.56, 0.62), (0.56, 0.22)], st, n=16, cap=mt.water, smooth=True)
    m.part()
    for sx in (-0.86, 0.86):
        m.box(sx - 1.5 * PX, 0.8 - 1.5 * PX, 0, sx + 1.5 * PX, 0.8 + 1.5 * PX, 1.8, mt.beam)
    m.box(-0.98, 0.8 - PX, 1.7, 0.98, 0.8 + PX, 1.82, mt.beam)
    m.part(); m.limb([(-0.7, 0.8, 1.5), (0.7, 0.8, 1.5)], 0.09, mt.wood, n=6)
    m.part(); m.box(0.1 - PX / 2, 0.8 - PX / 2, 0.86, 0.1 + PX / 2, 0.8 + PX / 2, 1.5, mt.rope)
    m.part(); m.turned(0.1, 0.8, [(0.11, 0.62), (0.15, 0.9)], mt.wood, n=7, cap=mt.dark)
    return m


def wheel(m, mt, x, y, z, r=0.42, t=0.08):
    """A solid plank cart wheel standing on its edge, its axle running north-south."""
    m.push((x, y, z), rx=90)
    m.part()
    m.turned(0, 0, [(r, -t / 2), (r, t / 2)], mt.beam, n=14, cap=mt.wood)
    m.turned(0, 0, [(0.1, t / 2), (0.09, t / 2 + 0.05)], mt.bronze, n=6, cap=mt.bronze)
    m.pop()


def cart(seed=0, load=True):
    """A two-wheeled handcart resting on its shafts, with sacks and a jar aboard."""
    m = Model(); mt = MT; r = rnd(seed)
    m.part(); m.box(-0.95, 0.15, 0.42, 0.95, 1.0, 0.52, mt.wood_h, top=mt.wood_h)
    m.part()
    m.box(-0.95, 0.15, 0.52, 0.95, 0.15 + PX, 0.82, mt.wood); m.box(-0.95, 1.0 - PX, 0.52, 0.95, 1.0, 0.82, mt.wood)
    m.box(-0.95, 0.15, 0.52, -0.95 + PX, 1.0, 0.82, mt.wood)
    wheel(m, mt, -0.25, 0.07, 0.42)
    wheel(m, mt, -0.25, 1.08, 0.42)
    m.part()
    for sy in (0.25, 0.9):
        m.beam((0.9, sy, 0.47), (2.0, sy, 0.06), 1.2 * PX, mt.beam)
    m.box(1.9, 0.2, 0.0, 1.98, 0.95, 0.1, mt.beam)
    if load:
        m.part()
        m.blob(-0.5, 0.55, 0.78, 0.36, 0.3, 0.26, mt.sack, seed=seed, n=8, rings=4)
        m.blob(0.05, 0.6, 0.74, 0.33, 0.28, 0.22, mt.sack, seed=seed + 1, n=8, rings=4)
        m.blob(-0.25, 0.5, 1.0, 0.3, 0.27, 0.2, mt.sack, seed=seed + 2, n=8, rings=4)
        jar(m, mt, 0.6, 0.6, 0.52, s=0.8, kind=0)
    return m


def crates(seed=0):
    m = Model(); mt = MT; r = rnd(seed)
    def crate(x, y, z, s, rot):
        m.push((x, y, z), rot=rot)
        m.part(); m.box(-s / 2, -s / 2, 0, s / 2, s / 2, s * 0.9, mt.wood_h, top=mt.wood)
        m.part()
        for sx in (-s / 2, s / 2 - PX):
            m.box(sx, -s / 2 - 0.02, 0, sx + PX, -s / 2, s * 0.9, mt.beam)
        m.box(-s / 2, -s / 2 - 0.02, s * 0.9 - PX, s / 2, -s / 2, s * 0.9, mt.beam)
        m.box(-s / 2, -s / 2 - 0.02, 0, s / 2, -s / 2, PX, mt.beam)
        m.pop()
    crate(-0.35, 0.45, 0, 0.7, 0)
    crate(0.42, 0.5, 0, 0.62, 0)
    crate(-0.2 + 0.2 * (seed % 2), 0.5, 0.63, 0.52, 0)
    return m


def sacks(seed=0):
    m = Model(); mt = MT
    m.part()
    for i, (x, y, z, rx, rz) in enumerate(((-0.3, 0.42, 0.24, 0.34, 0.26), (0.3, 0.46, 0.22, 0.32, 0.24), (0.0, 0.5, 0.58, 0.3, 0.22))):
        m.blob(x, y, z, rx, 0.28, rz, mt.sack, seed=seed + i, n=9, rings=5)
        m.part(); m.blob(x + 0.02, y - 0.05, z + rz, 0.07, 0.07, 0.06, mt.rope, n=5, rings=3); m.part()
    return m


def amphorae(seed=0):
    """Wine jars leaning together against nothing in particular."""
    m = Model(); mt = MT; r = rnd(seed)
    for i, (x, tilt) in enumerate(((-0.34, -14), (-0.02, 3), (0.3, 12))):
        m.push((x, 0.3 + 0.08 * (i % 2), 0), ry=tilt)
        jar(m, mt, 0, 0, 0, s=float(r.uniform(0.95, 1.1)), kind=1 if (i + seed) % 3 else 3 if i == 1 else 1, mat=mt.pot if (i + seed) % 2 else mt.pot2)
        m.pop()
    return m


def pot(big=False, seed=0):
    m = Model(); mt = MT
    jar(m, mt, 0, 0.25, 0, s=1.05 if big else 0.8, kind=3 if big else seed % 2, mat=mt.pot if seed % 3 else mt.pot2)
    return m


def planter(seed=0, w=1.75):
    """A stone trough with a clipped myrtle hedge in it."""
    m = Model(); mt = MT
    st = M('sandstone', 4.2, m_ashlar(10, 5))
    leaf = M('green', 3.6, m_clumps(4), soft=True)
    m.part(); m.box(-w / 2, 0.05, 0, w / 2, 0.65, 0.5, st, top=M('wood', 2.6))
    m.part()
    n = 4
    for i in range(n):
        x = -w / 2 + 0.25 + (w - 0.5) * i / (n - 1)
        m.blob(x, 0.36, 0.72 + 0.04 * (i % 2), 0.34, 0.3, 0.34, leaf, seed=seed + i, bump=0.16, n=9, rings=5)
    return m


def sign():
    m = Model(); mt = MT
    m.part(); m.box(-PX, 0.1, 0, PX, 0.1 + 2 * PX, 1.0, mt.beam)
    m.part(); m.box(-0.5, 0.06, 0.62, 0.5, 0.1, 1.12, mt.wood_h)
    m.part()
    for z in (0.78, 0.94):
        m.box(-0.34, 0.04, z, 0.34 - (0.2 if z > 0.9 else 0), 0.06, z + PX, mt.dark)
    return m


def flame(m, x, y, z, s=1.0, frame=0, seed=0, tongues=5):
    """A fire: tongues of flame leaning together, gold at the root and red at the tips, different every frame."""
    fire = Mat(RAMPS['glow'], 3.3, m_fire(z, 0.66 * s), glow=True)
    m.part()
    spots = ((-0.14, 0.34, 0.11), (0.0, 0.62, 0.15), (0.14, 0.4, 0.11), (-0.06, 0.48, 0.12), (0.08, 0.5, 0.12))[:tongues]
    for i, (dx, hh, rr) in enumerate(spots):
        k = hash2(frame * 3 + i, seed, 11)
        h2 = hh * s * (0.8 + 0.45 * k); lean = (hash2(frame, i + seed, 5) - 0.5) * 0.16 * s - dx * 0.25
        m.limb([(x + dx * s, y, z - 0.04), (x + dx * s + lean * 0.4, y, z + h2 * 0.45), (x + dx * s + lean, y, z + h2)],
               [rr * s, rr * s * 0.78, 0.012], fire, n=6, cap=False)


def brazier(lit=False, frame=0):
    """A fire altar: a bronze dish on a block of dressed stone. Charcoal when it is out, a bed of
    flame once the Wakefire has touched it."""
    m = Model(); mt = MT
    st = M('sandstone', 4.2, m_ashlar(9, 5))
    m.part(); m.box(-0.3, 0.06, 0, 0.3, 0.62, 0.5, st, top=M('sandstone', 4.6))
    m.part(); m.box(-0.36, 0.0, 0, 0.36, 0.68, 0.12, st, top=M('sandstone', 4.6))
    bed = Mat(RAMPS['glow'], 2.2, m_mottle(3, 0.5), glow=True) if lit else M('dark', 2.0, m_mottle(3, 0.6))
    m.part()
    m.turned(0, 0.34, [(0.16, 0.5), (0.34, 0.58), (0.43, 0.72), (0.40, 0.75), (0.34, 0.69)], M('bronze', 3.8), n=12, cap=bed)
    if lit:
        flame(m, 0, 0.34, 0.70, 1.25, frame)
        m.light(0, 0.34, 1.1, 5.5, (1.0, 0.72, 0.36), 0.85)
    else:
        m.part()
        coal = M('dark', 2.6, m_mottle(2, 0.8))
        ash = M('stone', 3.4, m_mottle(2, 0.8))
        for i, (dx, dy, dz) in enumerate(((-0.16, 0.0, 0.0), (0.14, 0.04, 0.0), (0.0, -0.14, 0.0), (0.02, 0.14, 0.0), (-0.04, 0.0, 0.1), (0.08, -0.04, 0.08))):
            m.blob(dx, 0.34 + dy, 0.78 + dz, 0.15, 0.14, 0.1, ash if i == 4 else coal, seed=i, bump=0.3, n=6, rings=3, facet=True)
    return m


def pole_torch(frame=0):
    m = Model(); mt = MT
    m.part(); m.box(-PX, 0.1, 0, PX, 0.1 + 2 * PX, 1.5, mt.beam)
    m.part(); m.turned(0, 0.1 + PX, [(0.06, 1.42), (0.15, 1.56), (0.17, 1.66)], mt.bronze, n=8, cap=M('dark', 2.0))
    flame(m, 0, 0.1 + PX, 1.62, 0.7, frame, seed=3, tongues=3)
    return m


def wall_torch(frame=0, z=2.8):
    """A torch in an iron bracket high on a wall."""
    m = Model(); mt = MT
    m.part(); m.beam((0, 0, z - 0.3), (0, -0.22, z), 1.2 * PX, mt.iron)
    m.part(); m.turned(0, -0.24, [(0.05, z - 0.04), (0.13, z + 0.08), (0.15, z + 0.16)], mt.bronze, n=8, cap=M('dark', 2.0))
    flame(m, 0, -0.24, z + 0.12, 0.7, frame, seed=7, tongues=3)
    return m


def banner(frame=0, h=1.75, w=0.62):
    """A red banner with a gold sun, hung from a bracket on a wall and moving in the night wind."""
    m = Model(); mt = MT
    def sun(u, v, P, seed):
        r2 = (u - np.round(u.min() + (u.max() - u.min()) / 2)) ** 2 + (v - (v.max() - 9)) ** 2
        return np.where(r2 <= 5, 0.6, 0.0), r2 <= 5
    cl = M('red', 4.5, sun, ramp2='gold', soft=True)
    rows, cols = 8, 4
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        sway = math.sin(frame * math.pi / 2 + t * 3.0) * 0.07 * t
        for k in range(cols):
            g[i, k] = (-w / 2 + w * k / (cols - 1) + sway, -0.12 - 0.05 * t * math.cos(frame * math.pi / 2 + k), 2.1 - h * t)
    m.part(); m.sheet(g[::-1], cl)
    m.part(); m.box(-w / 2 - PX, -0.14, 2.1, w / 2 + PX, -0.10, 2.1 + PX, mt.gold)
    return m


def m_chevrons(period=6, rise=3):
    """A band of inlay round a column: zigzags in a second colour."""
    def f(u, v, P, seed):
        z = np.abs((u % period) - period / 2.0)
        k = np.floor_divide(v + z, rise) % 2
        return np.zeros(u.shape), k == 0
    return f


def pillar(h=2.2):
    """A round column of pale stone on a drum, three bands of blue and gold zigzag let into the
    shaft, a spreading head rimmed in gold. Round, so its top reads as a column's and not a box's."""
    m = Model()
    shaft = M('alabaster', 4.7, m_planks(3, 'v', knots=False))
    drum = M('sandstone', 4.2, m_mottle(8, 0.3))
    inlay = M('lapis', 3.9, m_chevrons(6, 2), ramp2='gold')
    gold = M('gold', 4.3, gloss=0.03)
    cy = 0.42
    m.part(); m.turned(0, cy, [(0.44, 0.0), (0.44, 0.14), (0.38, 0.2)], drum, n=16, cap=M('sandstone', 4.8))
    m.part(); m.turned(0, cy, [(0.31, 0.2), (0.285, h - 0.34)], shaft, n=16)
    for z0 in (0.3, h * 0.5 - 0.06, h - 0.52):
        m.part(); m.turned(0, cy, [(0.318, z0), (0.316, z0 + 0.19)], inlay, n=16)
    m.part(); m.turned(0, cy, [(0.29, h - 0.34), (0.36, h - 0.2), (0.41, h - 0.1), (0.41, h)], M('alabaster', 4.5), n=16, cap=M('alabaster', 4.6, m_mottle(6, 0.3)))
    # the top is dressed: a gold ring let into it round a low boss
    m.part(); m.turned(0, cy, [(0.30, h), (0.30, h + 0.012)], M('gold', 3.9), n=16, cap=M('gold', 3.9))
    m.part(); m.turned(0, cy, [(0.24, h + 0.012), (0.2, h + 0.05)], M('alabaster', 4.4), n=16, cap=M('alabaster', 5.0))
    m.part(); m.turned(0, cy, [(0.418, h - 0.1), (0.418, h - 0.03)], gold, n=16)
    return m


# ------------------------------------------------------------------ green things
def olive(seed=0, size=1.0):
    """An old olive: a short twisted trunk forking into a wide silver-green head built of clumps."""
    r = rnd(seed); m = Model()
    bark = M('trunk', 4.3, m_rings(4))
    leaf = M('olive', 3.5, m_clumps(5), soft=True)
    s = size
    lean = float(r.uniform(-0.2, 0.2))
    m.part()
    m.limb([(0, 0.3, 0), (lean * 0.4, 0.3, 0.5 * s), (lean, 0.32, 1.0 * s), (lean * 1.3, 0.3, 1.45 * s)], [0.26 * s, 0.19 * s, 0.15 * s, 0.1 * s], bark, n=7)
    m.limb([(lean * 0.6, 0.3, 0.7 * s), (lean - 0.5 * s, 0.3, 1.25 * s), (lean - 0.8 * s, 0.3, 1.6 * s)], [0.12 * s, 0.09 * s, 0.05 * s], bark, n=6)
    m.limb([(lean * 0.8, 0.3, 0.8 * s), (lean + 0.5 * s, 0.34, 1.3 * s), (lean + 0.85 * s, 0.3, 1.55 * s)], [0.11 * s, 0.08 * s, 0.05 * s], bark, n=6)
    m.part()
    n = int(r.integers(10, 13))
    for i in range(n):
        a_ = 2 * math.pi * i / n + r.uniform(-0.25, 0.25)
        rad = r.uniform(0.6, 1.15) * s
        cx = lean + math.cos(a_) * rad; cy = 0.35 + math.sin(a_) * rad * 0.5
        cz = (1.7 + r.uniform(-0.2, 0.3) - 0.14 * rad) * s
        rr = r.uniform(0.42, 0.62) * s
        m.blob(cx, cy, cz, rr, rr * 0.85, rr * 0.8, leaf, seed=seed * 7 + i, bump=0.12, n=9, rings=5)
    for i in range(3):
        m.blob(lean + r.uniform(-0.4, 0.4) * s, 0.35, (2.0 + r.uniform(0, 0.25)) * s, 0.6 * s, 0.5 * s, 0.5 * s, leaf, seed=seed * 7 + 31 + i, bump=0.12, n=9, rings=5)
    return m


def cypress(seed=0, h=3.0):
    """A tall dark cypress, a little ragged."""
    r = rnd(seed); m = Model()
    leaf = M('cypress', 3.6, m_clumps(4, 0.9, 0.9), soft=True)
    m.part(); m.limb([(0, 0.25, 0), (0, 0.25, 0.5)], [0.1, 0.08], M('trunk', 4.0), n=6)
    m.part()
    n = 7
    for i in range(n):
        t = i / (n - 1)
        z = 0.55 + (h - 0.75) * t
        rr = (0.5 - 0.36 * t ** 1.3) * (1 + r.uniform(-0.08, 0.08))
        m.blob(r.uniform(-0.05, 0.05), 0.25, z, rr, rr * 0.9, (h / n) * 0.9, leaf, seed=seed * 5 + i, bump=0.14, n=8, rings=5)
    return m


def palm(seed=0, h=2.8):
    """A date palm: a ringed trunk with a curve in it, a crown of drooping fronds, a bunch of dates."""
    r = rnd(seed); m = Model()
    bark = M('trunk', 4.5, m_rings(3))
    fr = M('palm', 4.3, m_stripes(2, 'v'), ramp2='green', soft=True)
    bend = float(r.uniform(-0.45, 0.45))
    pts = [(bend * t * t, 0.25, h * t) for t in np.linspace(0, 1, 7)]
    m.part(); m.limb(pts, np.linspace(0.19, 0.12, 7), bark, n=7)
    top = np.array(pts[-1])
    m.part(); m.blob(top[0], top[1], top[2] - 0.12, 0.2, 0.2, 0.16, M('ochre', 3.8, soft=True), n=6, rings=3)
    n = 11
    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-0.15, 0.15)
        ln = r.uniform(1.25, 1.6); rise = r.uniform(0.15, 0.5)
        rows, cols = 7, 3
        g = np.zeros((rows, cols, 3))
        dx, dy = math.cos(a), math.sin(a) * 0.6
        px, py = -dy, dx
        for j in range(rows):
            t = j / (rows - 1)
            c = top + np.array([dx * ln * t, dy * ln * t, rise * math.sin(math.pi * t * 0.9) - 0.85 * t * t])
            wdt = 0.2 * math.sin(math.pi * (0.12 + 0.88 * (1 - t))) + 0.01
            for k in range(cols):
                g[j, k] = c + np.array([px, py, 0]) * wdt * (k - 1) + np.array([0, 0, -0.06 * abs(k - 1)])
        m.part(); m.sheet(g, fr)
    return m


def bush(seed=0, flowers=False):
    r = rnd(seed); m = Model()
    leaf = M('green', 3.7, m_clumps(4), soft=True)
    m.part()
    for i, (x, y, z, rr) in enumerate(((-0.2, 0.3, 0.26, 0.32), (0.2, 0.32, 0.24, 0.3), (0.0, 0.38, 0.42, 0.34), (0.02, 0.2, 0.2, 0.26))):
        m.blob(x, y, z, rr, rr * 0.9, rr * 0.9, leaf, seed=seed * 3 + i, bump=0.2, n=8, rings=5)
    if flowers:
        fl = Mat(RAMPS[['red', 'ochre', 'cream'][seed % 3]], 4.6, soft=True)
        m.part()
        for i in range(5):
            a = i * 1.9 + seed
            m.blob(math.cos(a) * 0.3, 0.26 + math.sin(a) * 0.1, 0.42 + 0.14 * math.sin(a * 2.3), 0.05, 0.05, 0.05, fl, n=4, rings=2)
    return m


def rock(seed=0, s=1.0):
    m = Model()
    st = M('stone', 4.2, m_mottle(6, 0.45))
    m.part()
    m.blob(0, 0.3 * s, 0.2 * s, 0.45 * s, 0.32 * s, 0.34 * s, st, seed=seed, bump=0.22, n=7, rings=4, facet=True)
    m.blob(0.3 * s, 0.22 * s, 0.1 * s, 0.24 * s, 0.2 * s, 0.2 * s, st, seed=seed + 5, bump=0.22, n=6, rings=3, facet=True)
    return m


# ------------------------------------------------------------------ the precinct wall and its gate
def wall_mats():
    class W: pass
    w = W()
    w.base = M('sandstone', 4.0, m_ashlar(16, 8))
    w.brick = M('sandstone', 4.35, m_brick(8, 4, -0.9, 0.8, keep=0.7))
    w.top = M('sandstone', 4.6, m_mottle(14, 0.4))
    w.frieze = M('lapis', 4.0, m_rosettes(16), ramp2='gold')
    w.lapis = M('lapis', 3.9, m_glazed(8, 4))
    w.gold = M('gold', 4.3, gloss=0.03)
    w.dark = M('dark', 1.4)
    w.cedar = M('cedar', 4.4, m_planks(4, 'v'))
    w.bronze = M('bronze', 4.4, gloss=0.03)
    return w


def merlons(m, mat, x0, x1, y0, y1, z, mw=0.5, mh=0.36, top=None):
    n = max(1, int(round((x1 - x0) / (mw * 2))))
    step = (x1 - x0) / n
    for i in range(n):
        xa = x0 + i * step + (step - mw) / 2
        m.box(xa, y0, z, xa + mw, y1, z + mh, mat, top=top or mat)


def city_wall(length=60.0, h=2.2, d=1.2, gate_at=None, gate_w=2.9, seed=0, towers=True, buttress=6.0):
    """The wall of the temple precinct: dressed stone at the foot, mud brick above, a frieze of
    glazed blue brick with gold rosettes, a walk along the top behind a row of merlons. With
    gate_at set, two taller towers stand either side of an arched gateway (the opening is left dark)."""
    m = Model(); w = wall_mats()
    x0, x1 = 0.0, length
    def run(xa, xb):
        m.part(); m.box(xa, 0, 0, xb, d, h, w.brick, top=w.top)
        m.part(); m.box(xa, -PX, 0, xb, d, 0.62, w.base, top=w.top)
        m.part(); m.box(xa, -0.5 * PX, h - 0.62, xb, d, h - 0.30, w.frieze)
        m.part(); m.box(xa, -PX, h - 0.30, xb, d, h - 0.24, w.gold)
        m.part(); m.box(xa, -PX, h - 0.68, xb, d, h - 0.62, w.gold)
        m.part(); m.box(xa, 0, h, xb, 3 * PX, h + 0.22, w.top)
        merlons(m, w.top, xa, xb, 0, 3 * PX, h + 0.22)
        m.part(); m.box(xa, d - 3 * PX, h, xb, d, h + 0.22, w.top)
    if gate_at is None:
        run(x0, x1)
    else:
        ga, gb = gate_at - gate_w / 2, gate_at + gate_w / 2
        tw = 2.4
        run(x0, ga - tw); run(gb + tw, x1)
        th = h + 1.5
        for tx0 in (ga - tw, gb):
            m.part(); m.box(tx0, -0.5, 0, tx0 + tw, d + 0.3, th, w.lapis, top=w.top)
            m.part(); m.box(tx0 - PX, -0.5 - PX, 0, tx0 + tw + PX, d + 0.3, 0.75, w.base, top=w.top)
            m.part(); m.box(tx0 - 0.5 * PX, -0.5 - 0.5 * PX, th - 1.1, tx0 + tw + 0.5 * PX, d + 0.3, th - 0.6, M('lapis', 4.3, m_rosettes(12), ramp2='gold'))
            for zz in (th - 0.6, th - 1.16):
                m.part(); m.box(tx0 - PX, -0.5 - PX, zz, tx0 + tw + PX, d + 0.3, zz + PX, w.gold)
            # a bull in gold brick on each tower
            def bull(u, v, P, seed, tx=tx0):
                x = np.floor((P[..., 0] - tx - tw / 2) * 16).astype(int); z = np.floor((P[..., 2] - 1.35) * 16).astype(int)
                body = (np.abs(x) <= 7) & (z >= 4) & (z <= 9)
                legs = ((np.abs(np.abs(x) - 5) <= 1) & (z >= 0) & (z < 4))
                head = ((x >= 7) & (x <= 11) & (z >= 7) & (z <= 12)) | ((x >= 10) & (x <= 12) & (z >= 12) & (z <= 14))
                tail = (x == -8) & (z >= 3) & (z <= 9)
                on = body | legs | head | tail
                return np.where(on, 0.4, 0.0), on
            m.part(); m.quad((tx0 + 0.3, -0.5 - 0.6 * PX, 1.2), (tx0 + tw - 0.3, -0.5 - 0.6 * PX, 1.2), (tx0 + tw - 0.3, -0.5 - 0.6 * PX, 2.5), (tx0 + 0.3, -0.5 - 0.6 * PX, 2.5),
                             M('lapis', 3.9, bull, ramp2='gold'))
            m.part(); m.box(tx0, -0.5, th, tx0 + tw, -0.5 + 3 * PX, th + 0.22, w.top)
            merlons(m, w.top, tx0, tx0 + tw, -0.5, -0.5 + 3 * PX, th + 0.22, mw=0.44)
            m.part(); m.box(tx0, d + 0.3 - 3 * PX, th, tx0 + tw, d + 0.3, th + 0.22, w.top)
            m.box(tx0, -0.5 + 3 * PX, th, tx0 + 3 * PX, d + 0.3 - 3 * PX, th + 0.22, w.top)
            m.box(tx0 + tw - 3 * PX, -0.5 + 3 * PX, th, tx0 + tw, d + 0.3 - 3 * PX, th + 0.22, w.top)
        # the gateway between them: an arch of glazed brick over a dark passage
        ah = 2.5
        m.part(); m.box(ga, 0, ah, gb, d, th - 0.5, w.lapis, top=w.top)
        m.part(); m.box(ga, -PX, th - 0.5, gb, d, th - 0.42, w.gold)
        m.part(); m.box(ga, 0, th - 0.42, gb, 3 * PX, th - 0.2, w.top)
        merlons(m, w.top, ga, gb, 0, 3 * PX, th - 0.2, mw=0.4)
        m.part(); m.quad((ga, 0.04, 0), (gb, 0.04, 0), (gb, 0.04, ah), (ga, 0.04, ah), w.dark)
        m.part()
        for jx in (ga, gb - 0.16):
            m.box(jx, -0.03, 0, jx + 0.16, 0.05, ah - 0.55, w.base)
        # the arch band: gold voussoirs
        for i in range(8):
            a0, a1 = math.pi * i / 8, math.pi * (i + 1) / 8
            ro, ri = gate_w / 2, gate_w / 2 - 0.16
            pts = [(gate_at + math.cos(a0) * ri, ah - 0.55 + math.sin(a0) * 0.55), (gate_at + math.cos(a0) * ro, ah - 0.55 + math.sin(a0) * 0.72),
                   (gate_at + math.cos(a1) * ro, ah - 0.55 + math.sin(a1) * 0.72), (gate_at + math.cos(a1) * ri, ah - 0.55 + math.sin(a1) * 0.55)]
            m.part(); m.face(pts[::-1], -0.01, w.gold if i % 2 == 0 else w.lapis, two=True)
        # the corners above the arch stay glazed
        for sgn in (-1, 1):
            pts = [(gate_at + sgn * gate_w / 2, ah - 0.55)] + [(gate_at + sgn * math.cos(a) * gate_w / 2, ah - 0.55 + math.sin(a) * 0.72) for a in np.linspace(0, math.pi / 2, 5)] + [(gate_at + sgn * gate_w / 2, ah + 0.17)]
            m.part(); m.face(pts, -0.005, w.lapis, two=True)
    if buttress:
        for bx in np.arange(x0 + buttress / 2, x1, buttress):
            if gate_at is not None and abs(bx - gate_at) < gate_w / 2 + 3.2:
                continue
            m.part(); m.box(bx - 0.5, -0.22, 0, bx + 0.5, 0, h + 0.1, w.brick, top=w.top)
            m.part(); m.box(bx - 0.5 - PX, -0.22 - PX, 0, bx + 0.5 + PX, 0, 0.7, w.base, top=w.top)
    return m


def gate_doors(open_=False, w=2.9, ah=2.5):
    """The two cedar leaves of the Temple Gate under its arch, banded and studded in bronze."""
    m = Model(); wm = wall_mats()
    ri = w / 2 - 0.16
    top = lambda x: ah - 0.55 + 0.55 * math.sqrt(max(0.0, 1 - (x / ri) ** 2))
    def arched(xa, xb, y, mat):
        xs = np.linspace(xb, xa, 7)
        m.face([(xa, 0), (xb, 0)] + [(x, top(x)) for x in xs], y, mat)
    def leaf(xa, xb, y):
        m.part(); arched(xa, xb, y, wm.cedar)
        m.part()
        for z in (0.35, 1.1, 1.8):
            m.box(xa, y - 0.03, z, xb, y, z + 2 * PX, wm.bronze)
            for x in np.arange(xa + 0.14, xb - 0.1, 0.36):
                m.box(x, y - 0.05, z + PX / 2, x + PX, y - 0.03, z + 1.5 * PX, wm.gold)
    if open_:
        m.part(); arched(-ri, ri, 0.02, M('dark', 2.6))
        leaf(-ri, -ri + 0.3, 0.0); leaf(ri - 0.3, ri, 0.0)
        m.light(0, 0.3, 1.0, 3.0, (0.7, 0.8, 1.0), 0.4)
    else:
        leaf(-ri, -PX / 2, 0.0); leaf(PX / 2, ri, 0.0)
        m.part(); m.box(-0.14, -0.06, 0.95, 0.14, -0.03, 1.08, wm.bronze)
    return m


# ------------------------------------------------------------------ the country round the town
def drystone(length, h=1.0, t=0.25, seed=0):
    """A terrace wall of field stone, running east from the origin."""
    m = Model()
    st = M('stone', 4.2, m_rubble(6))
    cap = M('stone', 4.7, m_rubble(7, 0.8, -1.0))
    m.part(); m.box(0, 0, 0, length, t, h, st, top=cap)
    return m


def steps(w=2.5, n=4, rise=1.0, run=1.25, mat=None):
    """Stone steps climbing north: w wide, rising `rise` over `run`."""
    m = Model()
    tread = mat or M('sandstone', 4.9, m_mottle(9, 0.3))
    riser = M('sandstone', 3.7, m_mottle(6, 0.4))
    for i in range(n):
        m.part(); m.box(0, run * i / n, 0, w, run, rise * (i + 1) / n, riser, top=tread)
    return m


def precinct_side(depth=36.0, w=2.0, h=2.2):
    """A wall running north-south, seen from above and from its south end: the walk along its top between two parapets."""
    m = Model(); wm = wall_mats()
    m.part(); m.box(0, 0, 0, w, depth, h, wm.brick, top=wm.top)
    m.part(); m.box(-PX, -PX, 0, w + PX, depth, 0.62, wm.base, top=wm.top)
    for x0 in (0, w - 3 * PX):
        m.part(); m.box(x0, 0, h, x0 + 3 * PX, depth, h + 0.22, wm.top)
        y = 0.25
        while y < depth - 0.5:
            m.part(); m.box(x0, y, h + 0.22, x0 + 3 * PX, y + 0.5, h + 0.58, wm.top)
            y += 1.0
    return m


def cliff(length, h=2.0, seed=0, grass=True, rock='sandstone'):
    """A rock face running east from the origin: beds of stone that stick out and draw back,
    so ledges catch the moon and the hollows under them stay dark. Grass hangs over the top."""
    r = rnd(seed); m = Model()
    st = M(rock, 3.9, m_strata(6))
    layers = max(2, int(round(h / 0.45)))
    lh = h / layers
    for k in range(layers):
        x = 0.0
        while x < length:
            w = float(r.uniform(1.2, 3.4))
            out = float(r.uniform(0.0, 0.28)) * (1.0 - 0.5 * k / layers)
            m.part(); m.box(x, -out, k * lh, min(length, x + w), 0.3, (k + 1) * lh, st, top=M(rock, 4.7, m_mottle(8, 0.4)))
            x += w
    if grass:
        gr = M('green', 3.6, m_clumps(4), soft=True)
        x = 0.0
        while x < length:
            w = float(r.uniform(0.8, 1.8))
            m.part(); m.box(x, -0.06 - float(r.uniform(0, 0.1)), h - 0.04, min(length, x + w), 0.3, h + 0.05, gr)
            x += w
    return m


def boat(seed=0):
    """A fishing boat pulled up or riding at the pier: tarred planks, two thwarts, a coil of net.
    Its origin is the middle of its far (north) side, so anyone lying in it is drawn on top of it."""
    m = Model(); mt = MT
    hull = M('wood', 3.9, m_planks(3, 'h'))
    inside = M('wood', 2.8, m_planks(3, 'h'))
    n = 16
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append((math.cos(a) * 1.45 * (1 - 0.25 * abs(math.sin(a)) ** 2), -0.5 + math.sin(a) * 0.5))
    m.part(); m.prism(pts, 0, 0.36, hull, top=inside)
    m.part()
    for tx in (-0.55, 0.45):
        m.box(tx - 0.1, -0.9, 0.36, tx + 0.1, -0.1, 0.4, mt.beam)
    m.part(); m.blob(0.95 if seed % 2 else -0.95, -0.5, 0.4, 0.2, 0.18, 0.08, M('straw', 3.8, m_mottle(2, 0.7), soft=True), seed=seed, n=7, rings=3)
    return m


def altar():
    """The old shrine's altar: a block of stone with a shallow bowl worn into the top."""
    m = Model()
    st = M('stone', 4.3, m_ashlar(10, 5))
    m.part(); m.box(-0.5, 0.05, 0, 0.5, 0.7, 0.6, st, top=M('stone', 4.8, m_mottle(6, 0.4)))
    m.part(); m.box(-0.58, 0.0, 0, 0.58, 0.75, 0.12, st, top=M('stone', 4.8))
    m.part(); m.turned(0, 0.38, [(0.24, 0.6), (0.26, 0.64), (0.2, 0.62)], M('bronze', 3.6), n=10, cap=M('dark', 2.2))
    return m


def post(h=0.9):
    m = Model()
    m.part(); m.limb([(0, 0.08, 0), (0, 0.08, h)], [0.09, 0.08], M('wood', 4.0, m_rings(4)), n=7)
    m.part(); m.limb([(0, 0.08, h - 0.22), (0, 0.08, h - 0.14)], 0.1, M('straw', 4.2), n=7, cap=False)
    return m


def ziggurat_tier(length=40.0, h=2.6, d=1.2, door_at=None, seed=0):
    """The lowest tier of the ziggurat: fired brick with upright buttresses all along it (their
    shadows give the wall its stripes), a band of glazed blue with gold rosettes, stepped
    merlons, and in the middle a deep doorway framed in gold."""
    m = Model(); w = wall_mats()
    brick = M('clay', 4.1, m_brick(8, 4, -0.9, 0.8, keep=0.75))
    base = M('sandstone', 4.0, m_ashlar(16, 8))
    m.part(); m.box(0, 0, 0, length, d, h, brick, top=w.top)
    m.part(); m.box(0, -PX, 0, length, d, 0.5, base, top=w.top)
    x = 0.5
    while x < length - 1:
        if door_at is None or abs(x + 0.5 - door_at) > 2.2:
            m.part(); m.box(x, -0.25, 0, x + 1.0, 0, h - 0.7, brick, top=w.top)
            m.part(); m.box(x - PX, -0.25 - PX, 0, x + 1.0 + PX, 0, 0.5, base, top=w.top)
        x += 2.0
    m.part(); m.box(0, -0.5 * PX, h - 0.66, length, d, h - 0.26, w.frieze)
    for zz in (h - 0.26, h - 0.72):
        m.part(); m.box(0, -PX, zz, length, d, zz + PX, w.gold)
    m.part(); m.box(0, 0, h, length, 3 * PX, h + 0.2, w.top)
    merlons(m, w.top, 0, length, 0, 3 * PX, h + 0.2, mw=0.5, mh=0.3)
    merlons(m, w.top, 0.125, length - 0.125, 0, 3 * PX, h + 0.5, mw=0.25, mh=0.16)
    if door_at is not None:
        dw, dh = 2.1, 2.1
        m.part(); m.box(door_at - dw / 2 - 0.3, -0.34, 0, door_at + dw / 2 + 0.3, 0, dh + 0.34, w.lapis, top=w.top)
        m.part(); m.box(door_at - dw / 2 - 0.34, -0.36, dh + 0.34, door_at + dw / 2 + 0.34, 0, dh + 0.42, w.gold)
        m.part(); m.quad((door_at - dw / 2, -0.35, 0), (door_at + dw / 2, -0.35, 0), (door_at + dw / 2, -0.35, dh), (door_at - dw / 2, -0.35, dh), w.dark)
        m.part()
        for sx in (door_at - dw / 2 - 0.06, door_at + dw / 2):
            m.box(sx, -0.38, 0, sx + 0.06, -0.34, dh + 0.06, w.gold)
        m.box(door_at - dw / 2 - 0.06, -0.38, dh, door_at + dw / 2 + 0.06, -0.34, dh + 0.06, w.gold)
    return m


def bronze_door(w=2.1, h=2.1, kind='lock'):
    """A door of bronze plates: 'lock' has a keyhole plate, 'bull' the great horned head in relief."""
    m = Model(); wm = wall_mats()
    plate = M('bronze', 3.7, m_planks(8, 'v', knots=False))
    m.part(); m.quad((-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h), plate)
    m.part()
    for z in (0.2, h * 0.5, h - 0.3):
        m.box(-w / 2, -0.03, z, w / 2, 0, z + 2 * PX, M('bronze', 4.6, gloss=0.03))
        for x in np.arange(-w / 2 + 0.2, w / 2 - 0.1, 0.4):
            m.box(x, -0.05, z + PX / 2, x + PX, -0.03, z + 1.5 * PX, wm.gold)
    m.part(); m.box(-PX / 2, -0.02, 0, PX / 2, 0, h, M('dark', 1.6))
    if kind == 'lock':
        m.part(); m.box(-0.2, -0.06, h * 0.5 - 0.24, 0.2, -0.03, h * 0.5 + 0.2, wm.gold)
        m.part(); m.box(-PX, -0.07, h * 0.5 - 0.12, PX, -0.06, h * 0.5 + 0.04, M('dark', 1.4))
    elif kind == 'sun':
        # the king's sign: the sun half up, and its rays
        cz = h * 0.56
        m.part(); m.face([(-0.36, cz), (0.36, cz)] + [(math.cos(a) * 0.36, cz + math.sin(a) * 0.36) for a in np.linspace(0, math.pi, 9)][1:-1], -0.06, M('gold', 5.0, gloss=0.03))
        m.part()
        for a in np.linspace(math.radians(18), math.radians(162), 5):
            ca, sa = math.cos(a), math.sin(a)
            m.quad((ca * 0.44 - sa * 0.05, -0.06, cz + sa * 0.44 + ca * 0.05), (ca * 0.44 + sa * 0.05, -0.06, cz + sa * 0.44 - ca * 0.05),
                   (ca * 0.68 + sa * 0.02, -0.06, cz + sa * 0.68 - ca * 0.02), (ca * 0.68 - sa * 0.02, -0.06, cz + sa * 0.68 + ca * 0.02), wm.gold, two=True)
        m.part(); m.box(-0.5, -0.05, cz - 0.07, 0.5, -0.03, cz, wm.gold)
    else:
        m.part()
        m.blob(0, -0.08, h * 0.6, 0.34, 0.1, 0.3, wm.gold, n=8, rings=4)
        for sgn in (-1, 1):
            m.limb([(sgn * 0.26, -0.08, h * 0.7), (sgn * 0.56, -0.08, h * 0.82), (sgn * 0.62, -0.08, h * 0.98)], [0.07, 0.05, 0.02], wm.gold, n=5)
    return m


def stone_block():
    """A block of stone that can be shoved one tile at a time."""
    m = Model()
    st = M('sandstone', 4.3, m_mottle(7, 0.4))
    m.part(); m.box(-0.5, 0.0, 0, 0.5, 0.75, 0.72, st, top=M('sandstone', 4.7, m_mottle(7, 0.3)))
    m.part()
    for x0, x1, z0, z1 in ((-0.38, 0.38, 0.12, 0.14), (-0.38, 0.38, 0.58, 0.60), (-0.38, -0.36, 0.12, 0.6), (0.36, 0.38, 0.12, 0.6)):
        m.box(x0, -0.01, z0, x1, 0, z1, M('sandstone', 3.2))
    return m


# ------------------------------------------------------------------ statues
def m_feathers(h=3):
    """Rows of carved feathers: a dark line under each row, a notch between feathers."""
    def f(u, v, P, seed):
        row = np.floor_divide(v, h); uu = u + (row % 2) * 2
        t = np.where((v % h) == 0, -1.2, 0.0)
        t = np.where(((uu % 4) == 0) & ((v % h) != h - 1), t - 0.5, t)
        return t, None
    return f


def m_curls(h=2):
    """A carved beard or mane: tight level rows of curls."""
    def f(u, v, P, seed):
        row = np.floor_divide(v, h)
        t = np.where((v % h) == 0, -1.1, 0.3)
        t = np.where(((u + row) % 2) == 0, t - 0.4, t)
        return t, None
    return f


def _bez(P, s):
    P = np.asarray(P, float)
    return ((1 - s) ** 3) * P[0] + 3 * ((1 - s) ** 2) * s * P[1] + 3 * (1 - s) * s * s * P[2] + (s ** 3) * P[3]


def _bez_t(P, s):
    P = np.asarray(P, float)
    d = 3 * ((1 - s) ** 2) * (P[1] - P[0]) + 6 * (1 - s) * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return d / (np.linalg.norm(d) + 1e-9)


def lamassu(mirror=False, scale=1.4):
    """A guardian of the gate, a winged bull with a king's head, cut in alabaster and seen from its
    flank the way the old carvers showed it: striding, the great wing swept back over its body in
    rows of feathers, a long squared beard in rows of curls, hair in a mass on the shoulder, the
    domed crown with the horns of a god. Hooves, horns and the wing's edge are gilded. It faces
    east; mirror=True turns it west."""
    m = Model()
    stone = M('alabaster', 5.0, m_mottle(9, 0.3))
    far = M('alabaster', 3.6, m_mottle(9, 0.25))
    pale = M('alabaster', 5.5)
    basalt = M('basalt', 3.3, m_curls(2))
    gold = M('gold', 4.4, gloss=0.03)
    lapis = M('lapis', 3.9)
    yc = 0.5                                              # the spine runs east-west at this depth
    zp = 0.34                                             # top of the plinth
    m.push(scale=scale)
    # the plinth: a dark foot, a block with a gilded lip
    m.part(); m.box(-1.5, 0.0, 0, 1.5, 1.0, 0.12, M('sandstone', 3.4, m_ashlar(12, 4)), top=M('sandstone', 4.0))
    m.part(); m.box(-1.43, 0.04, 0.12, 1.43, 0.96, zp, M('sandstone', 4.1, m_ashlar(12, 5)), top=M('sandstone', 4.6, m_mottle(8, 0.3)))
    m.part(); m.box(-1.44, 0.03, zp - 0.06, 1.44, 0.04, zp, gold)

    def leg(pts, radii, mat):
        m.part(); m.limb(pts, radii, mat, n=8, cap=False)
        x, y, _ = pts[-1]
        m.part(); m.limb([(x + 0.02, y, zp), (x + 0.01, y, zp + 0.13)], [0.14, 0.115], gold if mat is stone else M('gold', 3.3), n=8, cap=False)

    # the far legs, in shade: the hind one stepping forward, the fore one reaching
    leg([(-0.56, yc + 0.22, zp + 0.74), (-0.60, yc + 0.22, zp + 0.42), (-0.50, yc + 0.22, zp + 0.14), (-0.49, yc + 0.22, zp + 0.02)], [0.17, 0.12, 0.10, 0.115], far)
    leg([(0.86, yc + 0.22, zp + 0.74), (1.04, yc + 0.22, zp + 0.44), (1.02, yc + 0.22, zp + 0.14), (1.03, yc + 0.22, zp + 0.02)], [0.16, 0.12, 0.10, 0.115], far)
    # the body: rump, loin, barrel, the hump of the shoulder, the breast
    m.part()
    m.limb([(-1.04, yc, zp + 1.00), (-0.80, yc, zp + 1.04), (-0.30, yc, zp + 0.99), (0.15, yc, zp + 1.01), (0.55, yc, zp + 1.08), (0.90, yc, zp + 1.04)],
           [0.30, 0.38, 0.33, 0.36, 0.42, 0.35], stone, n=12)
    m.part(); m.blob(-1.06, yc, zp + 1.0, 0.26, 0.3, 0.32, stone, n=10, rings=6)
    m.part(); m.blob(1.0, yc, zp + 0.98, 0.25, 0.33, 0.36, stone, n=10, rings=6)
    # the near legs: the hind one thrust back, the fore one planted
    m.part(); m.blob(-0.84, yc - 0.16, zp + 0.84, 0.30, 0.24, 0.36, stone, n=10, rings=6)            # the haunch
    leg([(-0.82, yc - 0.24, zp + 0.70), (-1.04, yc - 0.24, zp + 0.42), (-0.96, yc - 0.24, zp + 0.14), (-0.95, yc - 0.24, zp + 0.02)], [0.18, 0.125, 0.10, 0.115], stone)
    m.part(); m.blob(0.58, yc - 0.18, zp + 0.86, 0.22, 0.22, 0.34, stone, n=10, rings=6)             # the shoulder
    leg([(0.60, yc - 0.24, zp + 0.72), (0.63, yc - 0.24, zp + 0.42), (0.60, yc - 0.24, zp + 0.14), (0.61, yc - 0.24, zp + 0.02)], [0.17, 0.125, 0.10, 0.115], stone)
    # the tail: down behind the hock to a curled tuft
    m.part(); m.limb([(-1.26, yc, zp + 1.16), (-1.42, yc, zp + 0.86), (-1.38, yc, zp + 0.5)], [0.06, 0.05, 0.045], stone, n=6)
    m.part(); m.blob(-1.37, yc, zp + 0.34, 0.09, 0.09, 0.17, basalt, n=6, rings=4)

    # the wing: an arm rising from the shoulder and sweeping back above the rump; from it hang the
    # flight feathers, every one a blade of its own, a shorter row over them, and scale feathers on the arm
    arm = [(0.50, 1.74), (0.36, 2.44), (-0.45, 2.62), (-1.45, 2.98)]
    trail = [(0.0, 1.72), (-0.80, 1.66), (-1.50, 1.92), (-1.80, 2.86)]
    yw = 0.05

    def feather(a, b, w, y, mat):
        a = np.asarray(a, float); b = np.asarray(b, float)
        d = b - a; L = np.linalg.norm(d); d = d / L; n = np.array([-d[1], d[0]])
        pts = [a - n * w / 2, a - n * w / 2 + d * (L - w * 0.7), b - n * w * 0.16, b + n * w * 0.16, a + n * w / 2 + d * (L - w * 0.7), a + n * w / 2]
        cx, cz = np.mean(pts, 0)
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            m.tri([(cx, y, cz), (p[0], y, p[1]), (q[0], y, q[1])], mat, two=True)

    N = 15
    for tier, (reach, yy, tone) in enumerate(((1.0, yw + 0.03, 4.3), (0.52, yw + 0.015, 5.0))):
        for i in range(N):
            s_ = (i + 0.5) / N
            A = _bez(arm, s_); B = _bez(trail, s_)
            m.part()
            feather(A, A + (B - A) * reach, 0.165, yy - 0.0004 * i, M('alabaster', tone + (0.45 if i % 2 else 0.0)))
    m.part()
    g = np.zeros((2, 9, 3))
    for k in range(9):
        s_ = k / 8.0
        A = _bez(arm, s_); B = _bez(trail, s_); d = (B - A) / np.linalg.norm(B - A)
        g[0, k] = (A[0], yw, A[1]); g[1, k] = (A[0] + d[0] * 0.2 * (1 - 0.4 * s_), yw, A[1] + d[1] * 0.2 * (1 - 0.4 * s_))
    m.sheet(g, M('alabaster', 5.2, m_feathers(3)), smooth=False)
    m.part(); m.limb([(p[0], yw - 0.01, p[1]) for p in [_bez(arm, s_) for s_ in np.linspace(0, 1, 9)]], list(np.linspace(0.065, 0.025, 9)), gold, n=5)

    # neck and head. The head is cut large, as the carvers cut it. The face is the pale part:
    # brow, eye, nose and cheek between crown, hair and beard
    hz = zp + 2.14
    hx = 1.04
    m.part(); m.limb([(0.74, yc, zp + 1.36), (0.98, yc, hz - 0.3)], [0.3, 0.26], stone, n=8, cap=False)
    m.part(); m.blob(hx, yc, hz, 0.32, 0.23, 0.38, pale, n=12, rings=7)
    m.box(hx + 0.26, yc - 0.06, hz - 0.13, hx + 0.385, yc + 0.06, hz + 0.07, pale)                           # the nose, one piece with the face
    m.part(); m.box(hx + 0.04, yc - 0.238, hz + 0.105, hx + 0.31, yc + 0.238, hz + 0.14, M('alabaster', 2.6))    # the brow
    m.part(); m.box(hx + 0.13, yc - 0.236, hz + 0.02, hx + 0.20, yc - 0.21, hz + 0.085, M('basalt', 1.0))      # the eye
    # hair in a heavy mass behind the ear, down onto the shoulder
    m.part(); m.blob(hx - 0.40, yc, hz - 0.22, 0.22, 0.25, 0.42, basalt, n=8, rings=5)
    m.part(); m.blob(hx - 0.2, yc - 0.225, hz - 0.2, 0.05, 0.03, 0.05, gold, n=6, rings=4)                   # an earring
    # the beard: under the nose and along the jaw, then long and squared down the breast in rows of curls
    m.part(); m.box(hx + 0.06, yc - 0.24, hz - 0.42, hx + 0.36, yc + 0.24, hz - 0.18, basalt)
    m.part(); m.box(hx - 0.12, yc - 0.24, hz - 0.42, hx + 0.06, yc + 0.24, hz - 0.28, basalt)
    m.part(); m.box(hx + 0.04, yc - 0.19, zp + 1.10, hx + 0.38, yc + 0.19, hz - 0.4, basalt)
    # the crown: a ribbed dome banded in gold and blue, two pairs of horns laid up its front, a gold knob
    cz0 = hz + 0.22
    m.part(); m.turned(hx - 0.02, yc, [(0.31, cz0), (0.315, cz0 + 0.16), (0.27, cz0 + 0.29), (0.15, cz0 + 0.37), (0.0, cz0 + 0.40)], M('alabaster', 4.5, m_planks(3, 'v', knots=False)), n=12, squash=0.74)
    m.part(); m.turned(hx - 0.02, yc, [(0.32, cz0), (0.324, cz0 + 0.07)], gold, n=12, squash=0.74)
    m.part(); m.turned(hx - 0.02, yc, [(0.326, cz0 + 0.07), (0.328, cz0 + 0.12)], lapis, n=12, squash=0.74)
    for hz_ in (cz0 + 0.13, cz0 + 0.23):
        m.part(); m.limb([(hx - 0.2, yc - 0.235, hz_), (hx + 0.1, yc - 0.235, hz_ + 0.02), (hx + 0.3, yc - 0.1, hz_ + 0.12)], [0.055, 0.05, 0.015], gold, n=5)
    m.part(); m.blob(hx - 0.02, yc, cz0 + 0.42, 0.065, 0.065, 0.07, gold, n=6, rings=4)
    # a band of blue and gold let into the plinth
    m.part()
    for k in range(13):
        x0 = -1.3 + k * 0.2
        m.box(x0, 0.035, 0.16, x0 + 0.1, 0.04, 0.24, lapis if k % 2 == 0 else gold)
    m.pop()
    return m.mirrored() if mirror else m


# ------------------------------------------------------------------ where a street or a field stops
def yard_wall(length, h=1.5, d=0.5, seed=0, plaster=None):
    """A yard wall of mud brick running east from the origin: a foot of fired brick, plaster flaking
    off the brick above it, a rounded cap. Too high to see over, which is the point of it."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(0, 0, 0, length, d, h, mt.wall, top=mt.roof)
    m.part(); m.box(-PX, -PX, 0, length + PX, d, 0.3, mt.plinth, top=mt.trim)
    m.part(); m.limb([(0, d / 2, h), (length, d / 2, h)], [d / 2 + PX, d / 2 + PX], mt.trim, n=8)
    return m


def yard_wall_ns(depth, h=1.5, wd=0.5, seed=0, plaster=None):
    """The same wall running north from the origin: we see its cap all the way along and its south end."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(0, 0, 0, wd, depth, h, mt.wall, top=mt.roof)
    m.part(); m.box(-PX, -PX, 0, wd + PX, depth, 0.3, mt.plinth, top=mt.trim)
    m.part(); m.limb([(wd / 2, 0, h), (wd / 2, depth, h)], [wd / 2 + PX, wd / 2 + PX], mt.trim, n=8)
    return m


def street_gate(w=3.0, h=2.3, seed=0):
    """A gate across a street, shut: two brick piers, a beam over them, two leaves of cedar strapped
    in bronze, and the bar dropped across the lot. Runs east from the origin, faces south."""
    m = Model(); mt = Mats(seed, 2)
    pier = 0.7
    for x0 in (0.0, w - pier):
        m.part(); m.box(x0, 0, 0, x0 + pier, 0.7, h, mt.wall, top=mt.roof)
        m.part(); m.box(x0 - PX, -PX, 0, x0 + pier + PX, 0.7, 0.3, mt.plinth, top=mt.trim)
        m.part(); m.box(x0 - PX, -PX, h, x0 + pier + PX, 0.7 + PX, h + 0.14, mt.trim, top=mt.trim)
    door_m = M('cedar', 3.9, m_planks(4, 'v'))
    m.part(); m.box(pier, 0.22, 0, w - pier, 0.36, h - 0.42, door_m, top=M('cedar', 3.2))
    m.part()
    for z in (0.34, 1.0, 1.56):
        m.box(pier, 0.2, z, w - pier, 0.22, z + 0.1, mt.bronze)
    m.box(w / 2 - PX / 2, 0.2, 0, w / 2 + PX / 2, 0.22, h - 0.42, M('dark', 1.6))             # where the leaves meet
    m.part(); m.box(pier - 0.12, 0.08, 0.72, w - pier + 0.12, 0.2, 0.9, mt.beam)              # the bar
    for bx in (pier + 0.25, w - pier - 0.35):
        m.part(); m.box(bx, 0.06, 0.66, bx + 0.1, 0.2, 0.96, mt.bronze)
    m.part(); m.box(-0.06, 0.1, h - 0.42, w + 0.06, 0.5, h - 0.2, mt.beam, top=mt.beam)       # the lintel
    return m


def cart_wreck(seed=0):
    """A handcart on its side where its owner lay down: one wheel in the air, the load gone
    everywhere. With what spilled, it stops a street."""
    m = Model(); mt = MT; r = rnd(seed)
    bed = mt.wood_h
    m.part(); m.box(-1.0, 0.5, 0.0, 1.0, 0.62, 1.0, bed, top=mt.wood)                          # the bed, standing on edge
    m.part()
    for x0 in (-1.0, 0.0, 1.0 - PX):
        m.box(x0, 0.48, 0.0, x0 + PX, 0.5, 1.0, mt.beam)
    m.box(-1.0, 0.48, 1.0 - PX, 1.0, 0.5, 1.0, mt.beam)
    # the wheel that ended up on top, lying flat
    m.part(); m.turned(-0.2, 0.56, [(0.44, 1.0), (0.44, 1.07)], mt.wood, n=14, cap=mt.wood_h)
    m.part(); m.turned(-0.2, 0.56, [(0.1, 1.07), (0.1, 1.16)], mt.bronze, n=8, cap=mt.bronze)
    m.part()
    for a in range(0, 180, 45):
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        m.beam((-0.2 - c * 0.42, 0.56 - sn * 0.42, 1.09), (-0.2 + c * 0.42, 0.56 + sn * 0.42, 1.09), PX, mt.beam)
    # the shafts, pointing at the sky
    m.part()
    for sx in (-0.8, 0.7):
        m.beam((sx, 0.7, 0.9), (sx + 0.2, 1.3, 1.5), 1.2 * PX, mt.beam)
    # what was on it
    m.part()
    for i, (x, y, z, rx, rz) in enumerate(((-0.7, 0.16, 0.22, 0.36, 0.24), (0.1, 0.1, 0.2, 0.34, 0.22), (-0.3, 0.22, 0.5, 0.3, 0.2), (0.9, 0.2, 0.2, 0.3, 0.22))):
        m.blob(x, y, z, rx, 0.26, rz, mt.sack, seed=seed + i, n=9, rings=5)
        m.part()
    jar(m, mt, 1.4, 0.3, 0.0, s=0.9, kind=0)
    jar(m, mt, -1.35, 0.26, 0.0, s=0.8, kind=1)
    m.part(); m.blob(0.55, -0.08, 0.06, 0.2, 0.14, 0.07, mt.pot2, seed=seed, n=7, rings=3, facet=True)    # a broken one
    return m


def quay(length, h=0.42, d=0.6):
    """The harbour's edge, running east from the origin: big dressed stones with a worn lip, a ring let into them here and there."""
    m = Model()
    st = M('stone', 4.0, m_ashlar(18, 6))
    m.part(); m.box(0, 0, 0, length, d, h, st, top=M('stone', 4.7, m_ashlar(18, 9, 5)))
    m.part()
    x = 1.2
    while x < length - 0.5:
        m.box(x, -0.03, 0.14, x + 0.16, 0, 0.3, M('bronze', 3.6))
        x += 3.4
    return m


# ------------------------------------------------------------------ the hill of sleepers (the dead of Ashkel)
def m_niches(w=6, gap=3):
    """The front of an old tomb: upright niches cut into the brick, the way the first palaces were faced."""
    def f(u, v, P, seed):
        k = u % (w + gap)
        t = np.where(k < gap, -1.3, 0.0)
        t = np.where((k == gap) | (k == w + gap - 1), 0.5, t)
        return t, None
    return f


def m_cuneiform(row=5):
    """Lines of wedge writing cut in stone."""
    def f(u, v, P, seed):
        r_ = np.floor_divide(v, row)
        on = ((v % row) >= 1) & ((v % row) <= 2) & (hash2(np.floor_divide(u, 2), r_, seed) > 0.42)
        t = np.where(on, -1.4, 0.0)
        t = np.where((v % row) == 0, t + 0.3, t)
        return t, None
    return f


def stele(h=1.5, seed=0, lean=0.0):
    """A standing stone with a rounded head, a scene cut at the top and lines of writing under it."""
    m = Model()
    st = M('stone', 4.3, m_cuneiform(5))
    m.push(rx=0, ry=lean)
    m.part(); m.box(-0.36, 0.0, 0, 0.36, 0.3, 0.12, M('stone', 3.6), top=M('stone', 4.4))
    m.part(); m.box(-0.28, 0.06, 0.12, 0.28, 0.24, h - 0.26, st, top=M('stone', 4.8))
    m.part(); m.limb([(0, 0.06, h - 0.26), (0, 0.24, h - 0.26)], [0.28, 0.28], M('stone', 4.5, m_mottle(6, 0.3)), n=12)
    m.part(); m.box(-0.14, 0.045, h - 0.42, 0.14, 0.06, h - 0.18, M('gold', 3.6))                # a sun disc, once gilded
    m.pop()
    return m


def offering_table(seed=0, food=True):
    """A low stone table before a tomb: bowls, a jar, what the living brought and the dead can't eat."""
    m = Model(); r = rnd(seed)
    st = M('sandstone', 4.1, m_mottle(8, 0.3))
    m.part(); m.box(-0.62, 0.1, 0, -0.42, 0.6, 0.3, st); m.box(0.42, 0.1, 0, 0.62, 0.6, 0.3, st)
    m.part(); m.box(-0.74, 0.02, 0.3, 0.74, 0.68, 0.42, st, top=M('sandstone', 4.8, m_mottle(8, 0.25)))
    if food:
        m.part(); m.turned(-0.36, 0.34, [(0.08, 0.42), (0.17, 0.5), (0.16, 0.52)], M('clay', 4.4), n=9, cap=M('fig', 2.6, m_mottle(2, 0.8)))
        m.part(); m.turned(0.3, 0.38, [(0.07, 0.42), (0.13, 0.48), (0.12, 0.5)], M('clay', 4.2), n=9, cap=M('straw', 4.2, m_mottle(2, 0.8)))
        m.part(); m.turned(0.02, 0.26, [(0.05, 0.42), (0.1, 0.5), (0.08, 0.62), (0.05, 0.66)], M('brick', 4.3), n=8, cap=M('dark', 1.8))
    return m


def spirit_lamp(frame=0):
    """A lamp for the dead on a bronze stand: its flame is the colour of deep water and gives no heat."""
    m = Model()
    brz = M('bronze', 3.9, gloss=0.03)
    m.part(); m.turned(0, 0.12, [(0.16, 0.0), (0.12, 0.06), (0.04, 0.12), (0.035, 0.9), (0.1, 1.0), (0.15, 1.06)], brz, n=9, cap=M('bronze', 3.2))
    ghost = Mat(RAMPS['ghost'], 3.4, glow=True)
    sway = (0.0, 0.03, -0.02, 0.02)[frame % 4]; tall = (0.0, 0.04, 0.01, -0.02)[frame % 4]
    m.part(); m.limb([(0, 0.12, 1.06), (sway * 0.5, 0.12, 1.22 + tall), (sway, 0.12, 1.4 + tall * 2)], [0.085, 0.065, 0.012], ghost, n=6)
    m.part(); m.limb([(0, 0.11, 1.07), (sway * 0.4, 0.11, 1.2 + tall)], [0.045, 0.02], Mat(RAMPS['ghost'], 5.0, glow=True), n=5)
    m.light(0, 0.12, 1.2, 3.0, (0.45, 1.0, 0.85), 0.6)
    return m


def dead_tree(seed=0, s=1.0):
    """A tree that has not had leaves in anyone's lifetime: a trunk and a few bare limbs against the sky."""
    r = rnd(seed); m = Model()
    bark = M('trunk', 3.5, m_rings(4))
    lean = float(r.uniform(-0.25, 0.25))
    m.part(); m.limb([(0, 0.3, 0), (lean * 0.4, 0.3, 0.7 * s), (lean, 0.3, 1.5 * s), (lean * 1.4, 0.3, 2.0 * s)], [0.22 * s, 0.16 * s, 0.11 * s, 0.05 * s], bark, n=7)
    for k in range(4):
        z0 = (0.9 + 0.3 * k) * s
        side = -1 if k % 2 == 0 else 1
        x0 = lean * (z0 / (2.0 * s))
        out = float(r.uniform(0.5, 0.95)) * s
        up = float(r.uniform(0.3, 0.7)) * s
        m.part(); m.limb([(x0, 0.3, z0), (x0 + side * out * 0.55, 0.3, z0 + up * 0.35), (x0 + side * out, 0.3, z0 + up)], [0.08 * s, 0.05 * s, 0.018 * s], bark, n=5)
        m.part(); m.limb([(x0 + side * out * 0.55, 0.3, z0 + up * 0.35), (x0 + side * out * 0.75, 0.3, z0 + up * 0.35 + 0.34 * s)], [0.035 * s, 0.012 * s], bark, n=4)
    return m


def game_board():
    """The game of twenty squares, laid out on a stone: two players, seven pieces each, and four hundred years to finish."""
    m = Model()
    st = M('sandstone', 4.0, m_mottle(8, 0.3))
    m.part(); m.box(-0.5, 0.05, 0, 0.5, 0.75, 0.34, st, top=M('sandstone', 4.6))
    def squares(u, v, P, seed):
        a, b = np.floor_divide(u, 3), np.floor_divide(v, 3)
        t = np.where(((u % 3) == 0) | ((v % 3) == 0), -1.2, np.where(((a + b) % 2) == 0, 0.5, -0.3))
        return t, ((a * 3 + b) % 4 == 0) & ((u % 3) == 1) & ((v % 3) == 1)
    m.part(); m.box(-0.38, 0.2, 0.34, 0.38, 0.6, 0.38, M('wood', 3.6), top=M('lapis', 3.6, squares, ramp2='gold'))
    for i, (x, y) in enumerate(((-0.44, 0.14), (-0.3, 0.12), (0.42, 0.66), (0.3, 0.7), (0.44, 0.52))):
        m.part(); m.turned(x, y, [(0.04, 0.34), (0.045, 0.37)], M('bone' if i < 2 else 'dark', 4.6 if i < 2 else 2.4), n=6, cap=M('bone' if i < 2 else 'dark', 5.0 if i < 2 else 2.8))
    return m


def lyre():
    """The great lyre from the tomb: a sounding box of dark wood, two arms and a yoke, eleven strings,
    and at the front a bull's head of gold with a beard of lapis. It still holds one note."""
    m = Model()
    wood = M('cedar', 3.6, m_planks(4, 'h'))
    gold = M('gold', 4.4, gloss=0.03)
    m.part(); m.box(-0.62, 0.1, 0, 0.5, 0.42, 0.62, wood, top=M('cedar', 4.3))
    m.part(); m.box(-0.62, 0.08, 0.46, 0.5, 0.1, 0.56, M('lapis', 3.8, m_stripes(3, 'u'), ramp2='gold'))
    for x in (-0.56, 0.44):
        m.part(); m.box(x - 0.04, 0.2, 0.62, x + 0.04, 0.3, 1.62, wood)
    m.part(); m.box(-0.7, 0.2, 1.52, 0.58, 0.3, 1.62, gold)
    m.part()
    for k in range(9):
        x = -0.46 + k * 0.1
        m.box(x, 0.24, 0.62, x + PX * 0.5, 0.25, 1.52, M('straw', 5.0))
    # the bull's head on the front of the box
    m.part(); m.blob(0.66, 0.26, 0.5, 0.2, 0.17, 0.2, gold, n=8, rings=5)
    m.part(); m.blob(0.84, 0.26, 0.4, 0.13, 0.12, 0.12, gold, n=7, rings=4)
    for sgn in (-1, 1):
        m.part(); m.limb([(0.6, 0.26 + sgn * 0.12, 0.64), (0.62, 0.26 + sgn * 0.26, 0.8), (0.7, 0.26 + sgn * 0.22, 0.94)], [0.045, 0.035, 0.01], gold, n=5)
    m.part(); m.box(0.72, 0.18, 0.06, 0.9, 0.34, 0.32, M('lapis', 3.6, m_curls(2)))
    return m


def m_procession(period=22, feet=3):
    """A painted frieze: bearers walking one behind the other, each with a jar on a shoulder.
    Marks the figures for a second colour; the wall's own colour is the ground of the painting."""
    fig = ["...##....", "..####...", "...##.##.", "..#####..", ".######..", "..####...", "..####...", "..####...", "..#..#...", "..#..#...", ".##..##.."]
    grid = np.array([[c == '#' for c in row] for row in fig])[::-1]
    def f(u, v, P, seed):
        col = u % period; row = v - feet
        on = np.zeros(u.shape, bool)
        ok = (col < grid.shape[1]) & (row >= 0) & (row < grid.shape[0])
        on[ok] = grid[row[ok], col[ok]]
        line = (v == feet - 2) | (v == feet + grid.shape[0] + 2)
        return np.where(line, -0.9, 0.0), on | line
    return f


def tomb_wall(length, h=2.75, d=0.25, door_at=None, door_w=2.5, door_h=2.1, seed=0):
    """A wall of the king's tomb, running east from the origin: a foot of dark stone, plaster the
    colour of old honey painted with a procession of bearers in red, a band of black and red
    lozenges under the cornice, and upright pilasters whose shadows break it up."""
    m = Model()
    foot = M('stone', 3.3, m_ashlar(16, 8))
    plaster = M('ochre', 4.3, m_mottle(16, 0.5))
    paint = M('ochre', 4.3, m_procession(22, 14), ramp2='red')
    top = M('tomb', 4.6, m_mottle(14, 0.4))
    def loz(u, v, P, seed_):
        k = (np.abs((u % 8) - 4) + np.abs((v % 8) - 4)) < 3
        return np.zeros(u.shape), k
    band = M('dark', 3.0, loz, ramp2='red')
    m.part(); m.box(0, 0, 0, length, d, h, plaster, top=top)
    m.part(); m.box(0, -PX, 0, length, d, 0.5, foot, top=top)
    m.part(); m.quad((0, -0.5 * PX, 0.62), (length, -0.5 * PX, 0.62), (length, -0.5 * PX, 0.62 + 1.2), (0, -0.5 * PX, 0.62 + 1.2), paint)
    m.part(); m.box(0, -0.5 * PX, h - 0.75, length, d, h - 0.3, band)
    m.part(); m.box(0, -1.5 * PX, h - 0.14, length, d, h, M('stone', 4.4), top=top)
    x = 2.0
    while x < length - 1.5:
        if door_at is None or abs(x + 0.4 - door_at) > door_w / 2 + 0.9:
            m.part(); m.box(x, -0.14, 0, x + 0.8, 0, h - 0.82, M('stone', 3.8, m_ashlar(10, 6)), top=M('stone', 4.6))
        x += 4.0
    if door_at is not None:
        a, b = door_at - door_w / 2, door_at + door_w / 2
        m.part(); m.box(a - 0.25, -0.2, 0, b + 0.25, 0, door_h + 0.3, foot, top=top)
        m.part(); m.quad((a, -0.21, 0), (b, -0.21, 0), (b, -0.21, door_h), (a, -0.21, door_h), M('dark', 1.2))
        m.part(); m.box(a - 0.1, -0.24, door_h, b + 0.1, -0.2, door_h + 0.1, M('gold', 3.9))
    return m


def tomb_partition(length, h=1.5, d=0.5, seed=0):
    """A lower wall dividing a hall of the tomb: dark stone, a row of niches with a sealed jar in each."""
    m = Model()
    st = M('stone', 3.6, m_ashlar(14, 7))
    m.part(); m.box(0, 0, 0, length, d, h, st, top=M('tomb', 4.6, m_mottle(12, 0.4)))
    m.part(); m.box(0, -PX, 0, length, d, 0.38, M('stone', 3.2, m_ashlar(16, 8)), top=M('stone', 4.2))
    x = 0.8
    while x < length - 1.0:
        m.part(); m.box(x, -0.02, 0.62, x + 0.5, 0, 1.2, M('dark', 1.4))
        m.part(); m.turned(x + 0.25, -0.06, [(0.09, 0.62), (0.14, 0.76), (0.1, 0.92), (0.06, 0.98)], M('clay', 4.0), n=7, cap=M('dark', 1.6), squash=0.5)
        x += 1.5
    m.part(); m.box(0, -PX, h - 0.14, length, d, h, M('ochre', 4.0), top=M('tomb', 4.8))
    return m


def tomb_partition_ns(depth, wd=0.5, h=1.5):
    m = Model()
    st = M('stone', 3.6, m_ashlar(14, 7))
    m.part(); m.box(0, 0, 0, wd, depth, h, st, top=M('tomb', 4.6, m_mottle(12, 0.4)))
    m.part(); m.box(-PX, -PX, 0, wd + PX, depth, 0.38, M('stone', 3.2), top=M('stone', 4.2))
    return m


# ------------------------------------------------------------------ chests, ovens, the potter's things
def chest(open_=False):
    """A treasure chest: dark cedar bound in bright bronze, a barrel lid, a gold lock plate with its
    keyhole. Open, the lid stands back on its hinges and what is inside shows gold."""
    m = Model()
    wood = M('cedar', 3.3, m_planks(4, 'h'))
    lidw = M('cedar', 3.7, m_planks(3, 'u'))
    brz = M('bronze', 4.7, gloss=0.04)
    gold = M('gold', 4.5, gloss=0.03)
    x0, x1, y0, y1, h = -0.52, 0.52, 0.08, 0.62, 0.36
    yc, r = (y0 + y1) / 2, (y1 - y0) / 2
    bands = (x0 + 0.03, -0.06, x1 - 0.15)
    # the box, on four bronze feet
    m.part(); m.box(x0, y0, 0.04, x1, y1, h, wood, top=Mat(RAMPS['gold'], 3.6, m_mottle(2, 1.5), glow=True) if open_ else M('dark', 1.2))
    m.part()
    for fx in (x0 - 0.01, x1 - 0.09):
        m.box(fx, y0 - 0.02, 0, fx + 0.1, y0 + 0.08, 0.07, brz)
    m.part()
    for sx in bands:
        m.box(sx, y0 - 0.02, 0.04, sx + 0.12, y0, h, brz)
    m.box(x0 - 0.01, y0 - 0.02, h - 0.05, x1 + 0.01, y0, h, brz)                       # the rim
    if open_:
        # the lid thrown back: we see its lining, and the box brim-full of gold
        m.part(); m.box(x0, y0, h - 0.02, x1, y0 + 0.04, h + 0.01, brz); m.box(x0, y1 - 0.04, h - 0.02, x1, y1, h + 0.01, brz)
        m.box(x0, y0, h - 0.02, x0 + 0.04, y1, h + 0.01, brz); m.box(x1 - 0.04, y0, h - 0.02, x1, y1, h + 0.01, brz)
        m.part()
        for k in range(5):
            m.quad((x0, y1 + 0.02 + 0.05 * k, h + 0.085 * k), (x1, y1 + 0.02 + 0.05 * k, h + 0.085 * k),
                   (x1, y1 + 0.02 + 0.05 * (k + 1), h + 0.085 * (k + 1)), (x0, y1 + 0.02 + 0.05 * (k + 1), h + 0.085 * (k + 1)), M('red', 2.8 + 0.25 * k), two=True)
        m.part()
        for sx in bands:
            for k in range(5):
                m.quad((sx, y1 + 0.015 + 0.05 * k, h + 0.085 * k), (sx + 0.12, y1 + 0.015 + 0.05 * k, h + 0.085 * k),
                       (sx + 0.12, y1 + 0.015 + 0.05 * (k + 1), h + 0.085 * (k + 1)), (sx, y1 + 0.015 + 0.05 * (k + 1), h + 0.085 * (k + 1)), brz, two=True)
        m.part(); m.box(x0 - 0.01, y1 + 0.26, h + 0.40, x1 + 0.01, y1 + 0.30, h + 0.46, brz)
        m.light(0, 0.3, 0.5, 2.4, (1.0, 0.8, 0.4), 0.55)
    else:
        # the barrel lid, and the bands carried over it
        m.part(); m.limb([(x0, yc, h), (x1, yc, h)], [r, r], lidw, n=12)
        m.part()
        for sx in bands:
            m.limb([(sx, yc, h), (sx + 0.12, yc, h)], [r + 0.02, r + 0.02], brz, n=12)
        m.part(); m.box(-0.11, y0 - 0.05, h - 0.13, 0.11, y0 - 0.02, h + 0.1, gold)   # the lock plate
        m.part(); m.box(-0.025, y0 - 0.055, h - 0.07, 0.025, y0 - 0.05, h + 0.02, M('dark', 1.0))
    return m


def m_firemouth(frame=0):
    def f(u, v, P, seed):
        k = fbm(u / 2.5 + frame * 1.7, v / 2.5, 3 + frame, 2)
        return np.where(k > 0.55, 1.2, np.where(k > 0.42, 0.0, -1.2)), None
    return f


def oven(frame=0):
    """The baker's oven: a beehive of clay brick on a stone footing, its mouth still red after forty nights."""
    m = Model(); mt = MT
    brick = M('clay', 4.2, m_brick(6, 3, -0.9, 0.9, keep=0.7))
    m.part(); m.box(-0.85, 0.0, 0, 0.85, 1.5, 0.3, M('sandstone', 4.0, m_ashlar(10, 5)), top=M('sandstone', 4.5))
    m.part()
    prof = [(0.74, 0.3), (0.76, 0.6), (0.68, 0.95), (0.5, 1.22), (0.24, 1.38), (0.1, 1.42)]
    m.turned(0, 0.76, prof, brick, n=14, cap=M('dark', 1.6))
    # the mouth: an arch of darker brick round the fire
    m.part()
    arch = [(-0.3, 0.3), (0.3, 0.3)] + [(math.cos(a) * 0.3, 0.62 + math.sin(a) * 0.26) for a in np.linspace(0, math.pi, 7)]
    m.face(arch, 0.02, Mat(RAMPS['glow'], 1.6, m_firemouth(frame), glow=True))
    m.part()
    for i in range(7):
        a0, a1 = math.pi * i / 7, math.pi * (i + 1) / 7
        pts = [(math.cos(a0) * 0.3, 0.62 + math.sin(a0) * 0.26), (math.cos(a0) * 0.42, 0.62 + math.sin(a0) * 0.38),
               (math.cos(a1) * 0.42, 0.62 + math.sin(a1) * 0.38), (math.cos(a1) * 0.3, 0.62 + math.sin(a1) * 0.26)]
        m.face(pts[::-1], 0.0, M('brick', 3.4 + 0.5 * (i % 2)), two=True)
    for sx in (-0.42, 0.3):
        m.box(sx, -0.02, 0.3, sx + 0.12, 0.02, 0.62, M('brick', 3.6))
    # the peel, leaning where she left it
    m.part(); m.beam((0.95, 0.2, 0.0), (0.8, 0.7, 1.3), 1.2 * PX, mt.beam)
    m.part(); m.box(0.7, 0.66, 1.25, 0.92, 0.74, 1.6, mt.wood)
    m.light(0, -0.1, 0.55, 3.6, (1.0, 0.6, 0.3), 0.9)
    return m


def kiln(frame=0):
    """The potter's kiln: a tapering stack of fired brick, a firebox at its foot, heat still standing over the top."""
    m = Model()
    brick = M('brick', 4.2, m_brick(6, 3, -0.9, 0.9, keep=0.75))
    m.part(); m.turned(0, 0.62, [(0.62, 0), (0.6, 0.5), (0.5, 1.15), (0.42, 1.5), (0.36, 1.5), (0.36, 1.3)], brick, n=12,
                       cap=Mat(RAMPS['glow'], 1.2, m_firemouth(frame + 2), glow=True))
    m.part(); m.turned(0, 0.62, [(0.64, 0.0), (0.64, 0.16)], M('sandstone', 4.0, m_ashlar(8, 4)), n=12)
    m.part()
    arch = [(-0.2, 0.0), (0.2, 0.0)] + [(math.cos(a) * 0.2, 0.26 + math.sin(a) * 0.16) for a in np.linspace(0, math.pi, 6)]
    m.face(arch, 0.0, Mat(RAMPS['glow'], 1.8, m_firemouth(frame), glow=True))
    m.part(); m.box(-0.28, -0.04, 0.0, -0.2, 0.02, 0.3, M('brick', 3.4)); m.box(0.2, -0.04, 0.0, 0.28, 0.02, 0.3, M('brick', 3.4))
    m.box(-0.28, -0.04, 0.3 + 0.1, 0.28, 0.02, 0.48, M('brick', 3.6))
    m.light(0, -0.1, 0.3, 3.0, (1.0, 0.55, 0.28), 0.8)
    return m


def potters_wheel():
    """A potter's wheel: a stone flywheel low to the ground, the head above it, a half-thrown jar left standing on it."""
    m = Model(); mt = MT
    m.part(); m.turned(0, 0.4, [(0.38, 0.06), (0.38, 0.16)], M('stone', 4.2, m_mottle(5, 0.4)), n=12, cap=M('stone', 4.6))
    m.part(); m.limb([(0, 0.4, 0.16), (0, 0.4, 0.5)], 0.06, mt.beam, n=6)
    m.part(); m.turned(0, 0.4, [(0.26, 0.5), (0.26, 0.56)], mt.wood_h, n=12, cap=M('wood', 4.8))
    m.part(); m.turned(0, 0.4, [(0.1, 0.56), (0.17, 0.68), (0.14, 0.84), (0.16, 0.9)], M('clay', 3.9), n=10, cap=M('dark', 1.6))
    return m


def plate():
    """A pressure plate let into the floor: bronze, worn bright in the middle. Origin at its far edge so feet stand on it."""
    m = Model()
    m.part(); m.box(-0.56, -0.8, 0, 0.56, 0.0, 0.06, M('bronze', 3.6), top=M('bronze', 4.1, m_mottle(4, 0.5)))
    m.part(); m.box(-0.44, -0.68, 0.06, 0.44, -0.12, 0.09, M('gold', 3.9), top=M('gold', 4.2, m_mottle(3, 0.4)))
    return m


def bars(w=5.25, h=1.4):
    """A grille of bronze bars between two posts."""
    m = Model()
    brz = M('bronze', 4.3, gloss=0.03); dk = M('bronze', 3.2)
    m.part()
    n = int(w / 0.19)
    for i in range(n + 1):
        x = -w / 2 + w * i / n
        m.box(x - PX / 2, 0.08, 0, x + PX / 2, 0.08 + PX, h, brz if i % 2 == 0 else dk)
    m.part(); m.box(-w / 2, 0.06, h - 0.08, w / 2, 0.14, h, brz)
    m.part(); m.box(-w / 2, 0.06, 0.3, w / 2, 0.14, 0.36, dk)
    return m


def bull_statue():
    """The bull's head that breathes fire: bronze, set in a block of the wall, horns wide, its mouth a furnace door."""
    m = Model(); wm = wall_mats()
    brz = M('bronze', 3.9, gloss=0.02)
    m.part(); m.box(-1.25, 0.0, 0, 1.25, 0.5, 1.75, wm.lapis, top=wm.top)
    m.part(); m.box(-1.27, -0.02, 1.6, 1.27, 0.5, 1.68, wm.gold)
    m.part(); m.box(-1.27, -0.02, 0, 1.27, 0.5, 0.3, wm.base, top=wm.top)
    # the head
    m.part(); m.blob(0, -0.12, 1.02, 0.46, 0.3, 0.44, brz, n=10, rings=6)                      # the skull
    m.part(); m.blob(0, -0.3, 0.72, 0.32, 0.26, 0.26, brz, n=10, rings=5)                       # the muzzle
    m.part(); m.box(-0.2, -0.56, 0.56, 0.2, -0.5, 0.74, Mat(RAMPS['glow'], 1.6, m_firemouth(0), glow=True))    # the mouth
    m.part()
    for sgn in (-1, 1):
        m.limb([(sgn * 0.36, -0.1, 1.3), (sgn * 0.72, -0.14, 1.42), (sgn * 0.9, -0.16, 1.74)], [0.11, 0.08, 0.02], M('gold', 4.2, gloss=0.03), n=6)
        m.box(sgn * 0.2 - 0.05, -0.42, 1.04, sgn * 0.2 + 0.05, -0.38, 1.12, M('dark', 1.2))          # an eye socket
        m.box(sgn * 0.1 - 0.03, -0.56, 0.8, sgn * 0.1 + 0.03, -0.52, 0.86, M('dark', 1.2))           # a nostril
    m.part(); m.turned(0, -0.52, [(0.09, 0.42), (0.09, 0.46)], M('gold', 4.3), n=8)                  # the ring
    m.light(0, -0.5, 0.65, 2.6, (1.0, 0.6, 0.3), 0.6)
    return m


def bridge_deck(w=3.0, length=8.75):
    """The drawbridge, down: planks on two beams. Origin at the far (north) corner so everyone walks on it."""
    m = Model(); mt = MT
    m.part(); m.box(0, -length, 0.0, w, 0, 0.1, mt.beam, top=M('wood', 4.2, m_planks(5, 'h')))
    m.part()
    for sx in (0.0, w - 2 * PX):
        m.box(sx, -length, 0.1, sx + 2 * PX, 0, 0.2, mt.beam)
    return m


# ------------------------------------------------------------------ inside the ziggurat
def temple_wall(length, h=2.75, d=0.25, door_at=None, door_w=2.5, door_h=2.1, bulls=True, seed=0):
    """A wall of the sanctuary, running east from the origin: a foot of pale stone, glazed blue brick,
    a frieze of gold rosettes under a gold cornice, striding bulls in gold brick at intervals, and
    flat buttresses whose shadows break it up. door_at puts a dark doorway through it, framed in gold."""
    m = Model(); w = wall_mats()
    m.part(); m.box(0, 0, 0, length, d, h, w.lapis, top=w.top)
    m.part(); m.box(0, -PX, 0, length, d, 0.5, w.base, top=w.top)
    m.part(); m.box(0, -0.5 * PX, h - 0.75, length, d, h - 0.3, w.frieze)
    for zz in (h - 0.3, h - 0.81):
        m.part(); m.box(0, -PX, zz, length, d, zz + PX, w.gold)
    m.part(); m.box(0, -1.5 * PX, h - 0.12, length, d, h, w.gold, top=w.top)
    x = 2.0; k = 0
    while x < length - 1.5:
        if door_at is None or abs(x + 0.4 - door_at) > door_w / 2 + 0.9:
            m.part(); m.box(x, -0.14, 0, x + 0.8, 0, h - 0.82, M('lapis', 3.6, m_glazed(8, 4)), top=w.gold)
            m.part(); m.box(x - PX, -0.14 - PX, 0, x + 0.8 + PX, 0, 0.5, w.base, top=w.top)
        x += 4.0; k += 1
    if bulls and h >= 2.4:
        x = 3.2
        while x < length - 2.6:
            if door_at is None or abs(x + 0.8 - door_at) > door_w / 2 + 1.2:
                def bull(u, v, P, seed_, x0=x):
                    bx = np.floor((P[..., 0] - x0 - 0.8) * 16).astype(int); bz = np.floor((P[..., 2] - 0.72) * 16).astype(int)
                    body = (np.abs(bx) <= 7) & (bz >= 4) & (bz <= 9)
                    legs = ((np.abs(np.abs(bx) - 5) <= 1) & (bz >= 0) & (bz < 4))
                    head = ((bx >= 7) & (bx <= 11) & (bz >= 7) & (bz <= 12)) | ((bx >= 10) & (bx <= 12) & (bz >= 12) & (bz <= 14))
                    tail = (bx == -8) & (bz >= 3) & (bz <= 9)
                    on = body | legs | head | tail
                    return np.where(on, 0.4, 0.0), on
                m.part(); m.quad((x, -0.7 * PX, 0.6), (x + 1.6, -0.7 * PX, 0.6), (x + 1.6, -0.7 * PX, 1.8), (x, -0.7 * PX, 1.8), M('lapis', 3.9, bull, ramp2='gold'))
            x += 4.0
    if door_at is not None:
        a, b = door_at - door_w / 2, door_at + door_w / 2
        m.part(); m.box(a - 0.25, -0.2, 0, b + 0.25, 0, door_h + 0.3, w.base, top=w.top)
        m.part(); m.quad((a, -0.21, 0), (b, -0.21, 0), (b, -0.21, door_h), (a, -0.21, door_h), w.dark)
        m.part()
        for sx in (a - 0.07, b):
            m.box(sx, -0.24, 0, sx + 0.07, -0.2, door_h + 0.07, w.gold)
        m.box(a - 0.07, -0.24, door_h, b + 0.07, -0.2, door_h + 0.07, w.gold)
    return m


def partition(length, h=1.5, d=0.5, seed=0):
    """A lower wall dividing a hall, running east from the origin: glazed brick on a stone foot, a gold coping."""
    m = Model(); w = wall_mats()
    m.part(); m.box(0, 0, 0, length, d, h, w.lapis, top=w.top)
    m.part(); m.box(0, -PX, 0, length, d, 0.38, w.base, top=w.top)
    m.part(); m.box(0, -PX, h - 0.14, length, d, h, w.gold, top=w.top)
    m.part(); m.box(0, -0.5 * PX, h - 0.5, length, d, h - 0.2, M('lapis', 4.3, m_rosettes(12), ramp2='gold'))
    return m


def partition_ns(depth, wd=0.5, h=1.5):
    """The same kind of wall running north from the origin, seen from its south end and from above."""
    m = Model(); w = wall_mats()
    m.part(); m.box(0, 0, 0, wd, depth, h, w.lapis, top=w.top)
    m.part(); m.box(-PX, -PX, 0, wd + PX, depth, 0.38, w.base, top=w.top)
    m.part(); m.box(-PX, -PX, h - 0.14, wd + PX, depth, h, w.gold, top=w.top)
    return m


def parapet_ew(length, h=0.45, d=0.75, merlon=True):
    """A low wall along the edge of the summit, running east from the origin, with merlons against the sky."""
    m = Model(); w = wall_mats()
    st = M('sandstone', 4.3, m_ashlar(12, 6))
    m.part(); m.box(0, 0, 0, length, d, h, st, top=M('sandstone', 4.8, m_mottle(8, 0.3)))
    m.part(); m.box(0, d - 2 * PX, h, length, d, h + PX, w.gold)
    if merlon:
        merlons(m, M('sandstone', 4.6, m_mottle(6, 0.3)), 0, length, 0, 0.3, h, mw=0.5, mh=0.32)
    return m


def parapet_ns(depth, h=0.45, wd=0.75, inner='right'):
    """The same low wall running north from the origin; inner says which side the gold coping is on."""
    m = Model(); w = wall_mats()
    st = M('sandstone', 4.3, m_ashlar(12, 6)); cap = M('sandstone', 4.8, m_mottle(8, 0.3))
    m.part(); m.box(0, 0, 0, wd, depth, h, st, top=cap)
    gx = wd - 2 * PX if inner == 'right' else 0
    m.part(); m.box(gx, 0, h, gx + 2 * PX, depth, h + PX, w.gold)
    ox = 0 if inner == 'right' else wd - 0.3
    y = 0.25
    while y < depth - 0.5:
        m.part(); m.box(ox, y, h, ox + 0.3, y + 0.5, h + 0.32, M('sandstone', 4.6, m_mottle(6, 0.3)))
        y += 1.0
    return m
