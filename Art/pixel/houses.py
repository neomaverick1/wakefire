"""The buildings of Ashkel, each its own: no two share a plan, a front or a roof. A builder
returns a Building: the forge Model (origin the middle of its front foot, body running north and
up, in tiles) and what the map needs to know about it: where its walls stand, which parts of
its roof can be walked, where its doors, stairs and ladders are."""
import math
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from forge import (Model, M, Mat, RAMPS, hash2, vnoise, fbm, m_brick, m_ashlar, m_plaster, m_planks, m_mottle,
                   m_stripes, m_reeds, m_glazed, m_clumps)
import town
from town import Mats, PX, rnd, door, window, beam_ends, parapet, jar, stairs, ladder, cloth, merlons


class Building:
    def __init__(self, key, model, w, d, h, **spec):
        self.key, self.model, self.w, self.d, self.h = key, model, w, d, h
        self.doors = spec.get('doors', [])           # (x, kind): kind 'door', 'open', 'barred', 'gong'
        self.stair = spec.get('stair')               # (x_foot, x_head): steps along the front, from the street up to the roof
        self.ladders = spec.get('ladders', [])       # x of each ladder up the front
        self.upper = spec.get('upper')               # (x0, x1, depth, height): a block standing on the back of the roof
        self.blocks = spec.get('blocks', [])         # (x0, y0, x1, y1) on the roof that cannot be walked (tiles, y from the front)
        self.roof_door = spec.get('roof_door')       # x of a door in the upper block, at roof level
        self.hatch = spec.get('hatch')               # (x, y) of a trapdoor in the roof
        self.extra = spec.get('extra', [])           # (x0, y0, x1, y1) solid ground beside or in front (an oven, a porch post)
        self.walk = spec.get('walk')                 # (x0, x1): the part of the roof that can be walked on; None = none of it
        self.tall = spec.get('tall', [])             # (x0, x1, how much higher than the roof): parts that stand up over it
        self.leaves = spec.get('leaves', {})         # door index -> (kind, w, h, bands): a door shut in that doorway
        self.door_w = spec.get('door_w', 0.9)        # how wide the way in is, in tiles


# ------------------------------------------------------------------ surfaces
def m_cones(period=8, colours=3):
    """Cone mosaic: thousands of clay cones pushed into wet plaster point first, their heads dipped
    red, black or left pale, in lozenges."""
    def f(u, v, P, seed):
        a = (u + v) % period; b = (u - v) % period
        loz = (np.minimum(a, period - a) + np.minimum(b, period - b))
        k = (loz * colours // period) % colours
        dot = ((u + (v % 2)) % 2 == 0)
        t = np.where(k == 0, 1.2, np.where(k == 1, -1.6, 0.0)) + np.where(dot, 0.25, -0.25)
        return t, k == 1
    return f


def m_zigzag(period=8, rise=3, band=2):
    def f(u, v, P, seed):
        z = np.abs((u % period) - period // 2) * rise // (period // 2)
        on = ((v + z) % (rise + band)) < band
        return np.where(on, 0.6, -0.1), on
    return f


def m_band(rows=((0, 2),)):
    """Painted lines along a wall: (first row, how many) of each, counted up from the foot of the face."""
    def f(u, v, P, seed):
        on = np.zeros(u.shape, bool)
        for a, n in rows:
            on |= (v >= a) & (v < a + n)
        return np.where(on, 0.2, 0.0), on
    return f


def m_studs(step=5):
    """A door of planks with rows of bronze nail heads (ramp2 the bronze)."""
    pl = m_planks(4, 'v', knots=False)
    def f(u, v, P, seed):
        t, _ = pl(u, v, P, seed)
        nail = ((u % step) == step // 2) & ((v % step) == step // 2)
        return np.where(nail, 1.0, t), nail
    return f


def m_soot(z0, h):
    """Plaster going black upwards, the way it does over a fire."""
    base = m_mottle(9, 0.4)
    def f(u, v, P, seed):
        t, _ = base(u, v, P, seed)
        k = np.clip((P[..., 2] - z0) / h, 0, 1)
        return t - k * 2.6 - (hash2(u, v, seed) < k * 0.5) * 0.8, None
    return f


def m_lattice(step=3):
    def f(u, v, P, seed):
        on = ((u + v) % step == 0) | ((u - v) % step == 0)
        return np.where(on, 0.8, -3.0), None
    return f


# ------------------------------------------------------------------ parts
def shell(m, mt, x0, x1, d, h, y0=0.0, roof=None, plinth=None, foot=0.38):
    """A block of the building: walls, roof, and the course of fired brick it stands on."""
    m.part(); m.box(x0, y0, 0, x1, y0 + d, h, mt.wall, top=roof or mt.roof)
    m.part(); m.box(x0 - PX, y0 - PX, 0, x1 + PX, y0 + d, foot, plinth or mt.plinth, top=mt.trim)


def buttresses(m, mat, x0, x1, y, h, n, wd=0.5, out=0.14, top=None, z0=0.0):
    """The front of a great house: piers standing out of the wall with recesses between, as the temples have them."""
    step = (x1 - x0) / n
    for i in range(n):
        cx = x0 + step * (i + 0.5)
        m.part(); m.box(cx - wd / 2, y - out, z0, cx + wd / 2, y, h, mat, top=top or mat)


def arched(m, mt, x, y, w, h, mat, rise=None, depth=0.03):
    """A doorway or window with a round head, as a flat shape on the wall at y."""
    rise = rise if rise is not None else w / 2
    pts = [(x - w / 2, 0.0 if h is None else h[0]), (x + w / 2, 0.0 if h is None else h[0])]
    z0, z1 = h
    pts = [(x - w / 2, z0), (x + w / 2, z0), (x + w / 2, z1 - rise)]
    for k in range(1, 6):
        a = math.pi * k / 6
        pts.append((x + math.cos(a) * w / 2, z1 - rise + math.sin(a) * rise))
    pts.append((x - w / 2, z1 - rise))
    m.part(); m.face(pts, y - depth, mat)


def big_door(m, mt, x, y, w=1.5, h=2.0, mat=None, arch=True, bands=3, frame=None, ajar=False):
    """A doorway for a house that matters: a deep reveal, two leaves of cedar with bronze across them, a frame."""
    frame = frame or mt.stone
    m.part(); m.box(x - w / 2 - 0.16, y - 0.10, 0, x - w / 2, y, h + 0.16, frame)
    m.box(x + w / 2, y - 0.10, 0, x + w / 2 + 0.16, y, h + 0.16, frame)
    m.box(x - w / 2 - 0.16, y - 0.12, h, x + w / 2 + 0.16, y, h + 0.18, frame, top=mt.trim)
    m.part(); m.quad((x - w / 2, y - 0.02, 0), (x + w / 2, y - 0.02, 0), (x + w / 2, y - 0.02, h), (x - w / 2, y - 0.02, h), mt.dark)
    leaf = mat or M('cedar', 4.1, m_studs(5), ramp2='bronze')
    if ajar:
        m.part(); m.quad((x - w / 2, y - 0.04, 0), (x - w / 2 + w * 0.34, y - 0.04, 0), (x - w / 2 + w * 0.34, y - 0.04, h), (x - w / 2, y - 0.04, h), leaf)
    else:
        m.part(); m.quad((x - w / 2, y - 0.04, 0), (x + w / 2, y - 0.04, 0), (x + w / 2, y - 0.04, h), (x - w / 2, y - 0.04, h), leaf)
        m.part(); m.box(x - PX / 2, y - 0.05, 0, x + PX / 2, y - 0.04, h, mt.dark)
        for k in range(bands):
            z = h * (k + 0.6) / (bands + 0.3)
            m.part(); m.box(x - w / 2, y - 0.06, z, x + w / 2, y - 0.04, z + 1.5 * PX, mt.bronze)
        for sx in (-1, 1):
            m.part(); m.blob(x + sx * 0.14, y - 0.08, h * 0.46, 0.05, 0.03, 0.05, mt.bronze, n=6, rings=3)
    m.part(); m.box(x - w / 2 - 0.22, y - 0.42, 0, x + w / 2 + 0.22, y, 2 * PX, mt.stone)
    m.part(); m.box(x - w / 2 - 0.12, y - 0.24, 2 * PX, x + w / 2 + 0.12, y, 4 * PX, mt.stone)


def doorway(m, mt, x, y, w=1.0, h=1.75, glow=True, ajar=0.38, leaf=None):
    """A door standing open: the dark of the room, the light of it if anybody is home, the leaf swung back."""
    m.part(); m.quad((x - w / 2 - PX, y - 0.02, 0), (x + w / 2 + PX, y - 0.02, 0), (x + w / 2 + PX, y - 0.02, h + PX), (x - w / 2 - PX, y - 0.02, h + PX), mt.dark)
    if glow:
        m.part(); m.quad((x - w / 2, y - 0.03, 0), (x + w / 2, y - 0.03, 0), (x + w / 2, y - 0.03, h * 0.6), (x - w / 2, y - 0.03, h * 0.6), mt.glow_dim)
        m.light(x, y - 0.4, 0.9, 2.6, (1.0, 0.72, 0.4), 0.6)
    if ajar:
        m.part(); m.quad((x - w / 2, y - 0.05, 0), (x - w / 2 + w * ajar, y - 0.05, 0), (x - w / 2 + w * ajar, y - 0.05, h), (x - w / 2, y - 0.05, h), leaf or mt.door)
    m.part(); m.box(x - w / 2 - 3 * PX, y - 0.10, h, x + w / 2 + 3 * PX, y, h + 3 * PX, mt.beam)
    m.part(); m.box(x - w / 2 - 2 * PX, y - 0.34, 0, x + w / 2 + 2 * PX, y, 2 * PX, mt.stone)


def leaf(kind='plain', w=1.0, h=1.75, bands=3, seed=0):
    """A door shut in its doorway, as a thing of its own, so that the house can be drawn with the doorway open
    behind it: 'plain' planks and a ring, 'barred' with two planks nailed across from inside (the nails came
    through), 'big' two leaves of cedar under bronze."""
    mt = Mats(seed, 2)
    m = Model()
    if kind == 'big':
        lf = M('cedar', 4.1, m_studs(5), ramp2='bronze')
        m.part(); m.quad((-w / 2, -0.04, 0), (w / 2, -0.04, 0), (w / 2, -0.04, h), (-w / 2, -0.04, h), lf)
        m.part(); m.box(-PX / 2, -0.05, 0, PX / 2, -0.04, h, mt.dark)
        for k in range(bands):
            z = h * (k + 0.6) / (bands + 0.3)
            m.part(); m.box(-w / 2, -0.06, z, w / 2, -0.04, z + 1.5 * PX, mt.bronze)
        for sx in (-1, 1):
            m.part(); m.blob(sx * 0.14, -0.08, h * 0.46, 0.05, 0.03, 0.05, mt.bronze, n=6, rings=3)
        return m
    m.part(); m.quad((-w / 2, -0.04, 0), (w / 2, -0.04, 0), (w / 2, -0.04, h), (-w / 2, -0.04, h), mt.door)
    m.part(); m.box(w * 0.22, -0.07, h * 0.48, w * 0.22 + PX, -0.04, h * 0.48 + 2 * PX, mt.bronze)
    if kind == 'barred':
        for z in (0.62, 1.14):
            m.part(); m.box(-w / 2 - 0.1, -0.09, z, w / 2 + 0.1, -0.05, z + 0.13, M('wood', 4.6, m_planks(3, 'h')))
            m.part()
            for nx in (-w / 2 + 0.06, w / 2 - 0.1):
                m.box(nx, -0.1, z + 0.04, nx + PX, -0.09, z + 0.04 + PX, mt.bronze)
    return m


def trapdoor(m, mt, x, y, z, w=0.8, d=0.7, open_=True):
    """A hatch in a flat roof: a frame of beams, and the dark of the ladder down."""
    m.part(); m.box(x - w / 2, y - d / 2, z, x + w / 2, y + d / 2, z + 0.1, mt.beam, top=mt.dark if open_ else mt.wood)
    if open_:
        m.part(); m.box(x - w / 2 + 0.06, y + d / 2 - 0.05, z + 0.1, x + w / 2 - 0.06, y + d / 2 + 0.02, z + 0.1 + d * 0.9, mt.wood)       # the lid, thrown back
        for sx in (-0.14, 0.14):
            m.part(); m.box(x + sx - PX / 2, y - d / 2 + 0.08, z + 0.1, x + sx + PX / 2, y - d / 2 + 0.14, z + 0.3, mt.beam)                # the ladder's horns
    else:
        m.part(); m.box(x - 0.04, y - d / 2 + 0.02, z + 0.1, x + 0.04, y - d / 2 + 0.1, z + 0.14, mt.bronze)


def curtain(m, x, y, w, h, colours=('fig', 'blue'), z0=0.0, sway=0.06):
    """Cloth hung in a doorway."""
    cols, rows = 7, 5
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        for k in range(cols):
            s = k / (cols - 1)
            g[i, k] = (x - w / 2 + w * s, y - 0.05 - sway * math.sin(math.pi * 2 * s) * t, z0 + h * (1 - t))
    m.part(); m.sheet(g, cloth(*colours, w=3))


def shade(m, mt, x, y, w, out=1.0, z=1.9, drop=0.3, colours=('red', 'cream'), sag=0.08, poles=True):
    """A striped cloth from the wall out over the street."""
    x0, x1 = x - w / 2, x + w / 2
    cols, rows = 9, 5
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        for k in range(cols):
            s = k / (cols - 1)
            g[i, k] = (x0 + (x1 - x0) * s, y - out * t, z - drop * t - sag * math.sin(math.pi * s) * t - 0.04 * math.sin(math.pi * t))
    m.part(); m.sheet(g, cloth(*colours))
    if poles:
        m.part()
        for px in (x0 + 2 * PX, x1 - 2 * PX):
            m.box(px - PX, y - out, 0, px + PX, y - out + 2 * PX, z - drop + PX, mt.beam)
        m.box(x0, y - out, z - drop, x1, y - out + PX, z - drop + PX, mt.beam)


def bracket_sign(m, mt, x, y, z, what, out=0.5):
    """A sign on an arm over the street: the thing itself, not a picture of it."""
    m.part(); m.box(x - PX, y - out, z, x + PX, y, z + 1.5 * PX, mt.beam)
    m.part(); m.box(x - PX / 2, y - out + PX, z - 0.22, x + PX / 2, y - out + 2 * PX, z, mt.rope)
    cx, cy, cz = x, y - out + 1.5 * PX, z - 0.42
    if what == 'loaf':
        m.part(); m.blob(cx, cy, cz, 0.24, 0.12, 0.16, M('straw', 3.9, m_mottle(3, 0.5)), n=8, rings=5)
        for k in (-1, 0, 1):
            m.part(); m.box(cx + k * 0.1 - PX / 2, cy - 0.13, cz - 0.02, cx + k * 0.1 + PX / 2, cy - 0.12, cz + 0.1, M('wood', 2.8))
    elif what == 'jar':
        jar(m, mt, cx, cy, cz - 0.26, s=0.62, kind=0, mat=M('clay', 4.6, gloss=0.02))
    elif what == 'scales':
        m.part(); m.box(cx - 0.3, cy - PX / 2, cz + 0.2, cx + 0.3, cy + PX / 2, cz + 0.2 + PX, mt.bronze)
        for sx in (-0.28, 0.28):
            m.part(); m.box(cx + sx - PX / 2, cy - PX / 2, cz - 0.02, cx + sx + PX / 2, cy + PX / 2, cz + 0.2, mt.bronze)
            m.part(); m.turned(cx + sx, cy, [(0.02, cz - 0.1), (0.13, cz - 0.04), (0.14, cz - 0.02)], mt.bronze, n=8, cap=M('bronze', 3.2))
    elif what == 'fish':
        m.part(); m.blob(cx, cy, cz, 0.28, 0.06, 0.12, M('bronze', 4.6, gloss=0.03), n=8, rings=5)
        m.part(); m.face([(cx + 0.24, cz), (cx + 0.42, cz + 0.14), (cx + 0.42, cz - 0.14)], cy - 0.01, M('bronze', 4.0), two=True)
    elif what == 'cup':
        m.part(); m.turned(cx, cy, [(0.05, cz - 0.2), (0.07, cz - 0.16), (0.03, cz - 0.1), (0.14, cz + 0.04), (0.17, cz + 0.16)], M('bronze', 4.6, gloss=0.03), n=9, cap=M('dark', 1.4))


def lamp(m, mt, x, y, z, strength=0.6, radius=2.6):
    """A clay lamp in a niche or on a bracket, lit."""
    m.part(); m.blob(x, y, z, 0.09, 0.07, 0.05, mt.pot, n=7, rings=3)
    m.part(); m.blob(x + 0.07, y, z + 0.07, 0.035, 0.03, 0.06, mt.glow, n=5, rings=3)
    m.light(x, y - 0.3, z + 0.1, radius, (1.0, 0.72, 0.38), strength)


def dome(m, mat, cx, cy, r, z0, rise=None, n=16, cap=None, squash=1.0):
    """A beehive dome: courses of brick stepping in to a point."""
    rise = rise or r * 1.25
    prof = [(r, z0)]
    for k in range(1, 9):
        t = k / 8.0
        prof.append((r * math.cos(t * math.pi / 2) ** 0.8, z0 + rise * math.sin(t * math.pi / 2)))
    m.part(); m.turned(cx, cy, prof, mat, n=n, cap=cap or mat, squash=squash)


def sacks(m, mt, x, y, z=0.0, n=3, seed=0):
    r = rnd(seed)
    m.part()
    for k in range(n):
        m.blob(x + k * 0.34 + r.uniform(-0.04, 0.04), y + r.uniform(-0.05, 0.05), z + 0.16, 0.2, 0.15, 0.17, mt.sack, n=7, rings=4, seed=seed + k)
    if n > 2:
        m.blob(x + 0.34, y + 0.02, z + 0.42, 0.2, 0.15, 0.15, mt.sack, n=7, rings=4, seed=seed + 9)


def rack(m, mt, x0, x1, y, z, h=0.8, cloths=('red', 'cream', 'blue'), seed=0):
    """A pole on two posts with things hung over it."""
    r = rnd(seed)
    m.part()
    for px in (x0, x1):
        m.box(px - PX / 2, y, z, px + PX / 2, y + PX, z + h, mt.beam)
    m.box(x0, y, z + h - PX, x1, y + PX, z + h, mt.beam)
    cx = x0 + 0.08
    k = 0
    while cx < x1 - 0.3:
        wd = r.uniform(0.22, 0.34)
        cl = M(cloths[k % len(cloths)], 4.5, soft=True)
        m.part(); m.quad((cx, y - 0.02, z + h - 0.06 - r.uniform(0.3, 0.52)), (cx + wd, y - 0.02, z + h - 0.06 - r.uniform(0.3, 0.52)), (cx + wd, y - 0.02, z + h - 0.03), (cx, y - 0.02, z + h - 0.03), cl, two=True)
        cx += wd + 0.06; k += 1


def add(m, other, at=(0, 0, 0)):
    """Stand another model in this one (a tree in a tub, a jar on a shelf)."""
    off = np.asarray(at, float)
    base = m._part + 1
    for i in range(len(other.P)):
        m.P.append(other.P[i] + off); m.UV.append(other.UV[i]); m.N.append(other.N[i])
        m.mat.append(m._mid(other.mats[other.mat[i]])); m.pt.append(base + other.pt[i]); m.two.append(other.two[i])
    m._part = base + (max(other.pt) if other.pt else 0)
    for (x, y, z, r, c, st) in other.lights:
        m.lights.append((x + off[0], y + off[1], z + off[2], r, c, st))


def shutters(m, x, y, z, w=0.5, h=0.56, colour='blue', shut=True):
    """A window with plank shutters, shut or thrown back against the wall."""
    pl = M(colour, 3.4, m_planks(3, 'v', knots=False))
    m.part(); m.quad((x - w / 2, y - 0.02, z), (x + w / 2, y - 0.02, z), (x + w / 2, y - 0.02, z + h), (x - w / 2, y - 0.02, z + h), M('dark', 1.2))
    m.part()
    if shut:
        m.quad((x - w / 2, y - 0.04, z), (x + w / 2, y - 0.04, z), (x + w / 2, y - 0.04, z + h), (x - w / 2, y - 0.04, z + h), pl)
        m.box(x - PX / 2, y - 0.05, z, x + PX / 2, y - 0.04, z + h, M('dark', 1.4))
    else:
        for sx in (-1, 1):
            xa = x + sx * w / 2; xb = x + sx * (w / 2 + w * 0.5)
            m.quad((min(xa, xb), y - 0.04, z), (max(xa, xb), y - 0.04, z), (max(xa, xb), y - 0.04, z + h), (min(xa, xb), y - 0.04, z + h), pl)
    m.part(); m.box(x - w / 2 - PX, y - 0.08, z - PX, x + w / 2 + PX, y, z, M('sandstone', 4.6))


def pots_row(m, mt, x0, x1, y, z, step=0.3, s=0.5, seed=0):
    r = rnd(seed)
    x = x0
    k = 0
    while x <= x1:
        jar(m, mt, x, y, z, s=s * float(r.uniform(0.85, 1.15)), kind=(0, 1, 0, 3)[k % 4] if s > 0.45 else 0, mat=(mt.pot, mt.pot2, M('clay', 4.0))[k % 3], n=8)
        x += step; k += 1


def tub(m, mt, x, y, r, colour):
    """A dyer's vat: fired clay, and what is in it."""
    m.part(); m.turned(x, y, [(r * 0.9, 0), (r, 0.3), (r * 0.96, 0.44), (r * 0.82, 0.44), (r * 0.82, 0.34)], M('clay', 3.8), n=12, cap=M(colour, 3.2, m_mottle(3, 0.5)), squash=0.8)


def post_roof(m, mt, x0, x1, y0, y1, z, mat=None, posts=3, thick=0.08):
    """A roof of reed on posts: a porch, a shed."""
    mat = mat or mt.reed
    m.part()
    for k in range(posts):
        px = x0 + 0.1 + (x1 - x0 - 0.2) * k / max(1, posts - 1)
        m.box(px - PX, y0, 0, px + PX, y0 + 2 * PX, z, mt.beam)
    m.part(); m.box(x0, y0 - 0.1, z, x1, y1, z + thick, mat, top=mat)
    m.part(); m.box(x0, y0 - 0.12, z - PX, x1, y0 - 0.1, z + thick, mt.beam)


# ------------------------------------------------------------------ the lower town
def bakery():
    """Hesha's. The shop front is a hatch with a shelf to put the bread on and a cloth over it; the
    oven's chimney comes up through the roof and has blacked the wall behind it; she sleeps over
    the shop, and the stair to the roof is outside, as it is on any house with a baker in it."""
    w, d, h = 10.0, 4.0, 2.75
    mt = Mats(11, 2)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h, gap=(x1 - 0.62, x1))
    beam_ends(m, mt, x0 + 0.3, x1 - 2.6, 0, h - 0.42)
    # the hatch: a wide opening with a shelf, loaves on it, a striped cloth over it
    hx = -2.6
    m.part(); m.quad((hx - 1.3, -0.02, 0.95), (hx + 1.3, -0.02, 0.95), (hx + 1.3, -0.02, 1.85), (hx - 1.3, -0.02, 1.85), mt.dark)
    m.part(); m.quad((hx - 1.22, -0.025, 1.0), (hx + 1.22, -0.025, 1.0), (hx + 1.22, -0.025, 1.5), (hx - 1.22, -0.025, 1.5), mt.glow_dim)
    m.light(hx, -0.5, 1.3, 3.0, (1.0, 0.70, 0.36), 0.55)
    m.part(); m.box(hx - 1.4, -0.34, 0.86, hx + 1.4, 0, 0.95, mt.wood_h, top=M('wood', 4.9))
    for sx in (-1.3, 1.3):
        m.part(); m.box(hx + sx - PX, -0.3, 0.38, hx + sx + PX, -0.22, 0.86, mt.beam)
    crust = [M('straw', 3.6, m_mottle(3, 0.5)), M('wood', 4.6, m_mottle(3, 0.4)), M('straw', 4.2, m_mottle(3, 0.4))]
    m.part()
    for k, lx in enumerate((-1.05, -0.62, -0.2, 0.26, 0.7, 1.08)):
        m.blob(hx + lx, -0.17, 1.02, 0.17, 0.11, 0.075, crust[k % 3], n=7, rings=4, seed=k)
    m.part()
    for k, lx in enumerate((-0.84, -0.4, 0.5)):
        m.blob(hx + lx, -0.17, 1.14, 0.15, 0.1, 0.07, crust[(k + 1) % 3], n=7, rings=4, seed=10 + k)
    m.part(); m.box(hx - 1.38, -0.06, 1.85, hx + 1.38, 0, 1.94, mt.beam)
    shade(m, mt, hx, 0, 3.0, out=0.72, z=2.5, drop=0.22, colours=('red', 'cream'), poles=False)
    # the door, the peel leaning by it, sacks
    dx = 1.3
    door(m, mt, dx, 0, w=1.05, h=1.8, lit=True)
    m.part(); m.beam((dx + 0.95, -0.12, 0), (dx + 0.86, -0.03, 1.9), 1.1 * PX, mt.beam)
    m.part(); m.box(dx + 0.72, -0.05, 1.8, dx + 1.0, -0.03, 2.2, M('wood', 4.8))
    sacks(m, mt, 0.0, -0.22, n=3, seed=4)
    bracket_sign(m, mt, dx - 0.9, 0, 2.3, 'loaf')
    window(m, mt, 3.0, 0, 1.45, 0.44, 0.5, lit=True)
    # the bedroom over the shop
    ux0, ux1, ud, uh = x0, x0 + 4.2, 2.0, 2.0
    m.part(); m.box(ux0, d - ud, h, ux1, d, h + uh, mt.wall, top=mt.roof)
    parapet(m, mt, ux0, d - ud, ux1, d, h + uh, h=0.19)
    beam_ends(m, mt, ux0 + 0.3, ux1 - 0.3, d - ud, h + uh - 0.36)
    m.push((0, 0, h))
    door(m, mt, ux0 + 3.2, d - ud, w=0.8, h=1.5)
    window(m, mt, ux0 + 1.4, d - ud, 0.8, 0.5, 0.5, lit=True)
    m.pop()
    # the chimney, and what forty nights of it have done to the wall
    cx, cy = 2.6, d - 0.7
    m.part(); m.box(cx - 0.36, cy - 0.36, h, cx + 0.36, cy + 0.36, h + 1.5, M('brick', 4.0, m_soot(h + 0.5, 1.6)), top=M('dark', 1.0))
    m.part(); m.box(cx - 0.44, cy - 0.44, h + 1.38, cx + 0.44, cy + 0.44, h + 1.5, M('brick', 3.4), top=M('dark', 0.8))
    m.light(cx, cy - 0.4, h + 1.5, 2.2, (1.0, 0.55, 0.25), 0.35)
    # the roof: flour drying, a rack
    m.part(); m.box(-0.4, 0.5, h, 1.5, 1.7, h + 0.5 * PX, mt.reed)
    sacks(m, mt, 3.4, 1.0, z=h, n=2, seed=7)
    rack(m, mt, -0.3, 1.5, 3.2, h, cloths=('cream', 'linen', 'cream'), seed=3)
    # the stair, outside, on the right
    stairs(m, mt, x1 - 2.6, x1, 0, h)
    return Building('lt_bakery', m, w, d, h, doors=[(dx, 'open')], stair=(x1 - 2.6, x1), upper=(ux0, ux1, ud, uh), roof_door=ux0 + 3.2, walk=(x0, x1),
                    blocks=[(3.2, 0.7, 4.3, 1.6), (-0.5, 3.1, 1.7, d)], tall=[(cx - 0.5, cx + 0.5, 1.5, cy - 0.55)], extra=[(-4.1, -0.4, -1.1, 0), (-0.3, -0.45, 0.95, 0)])


def tax_office():
    """The counting house. Dressed stone to the height of a man, because the first two were of brick; windows a
    cat could not get through; a door with more bronze on it than a shield. The scales over it have
    never once come down on the side of the man paying."""
    w, d, h = 7.5, 3.5, 3.0
    mt = Mats(13, 3)
    m = Model()
    x0, x1 = -w / 2, w / 2
    stone = M('stone', 3.9, m_ashlar(16, 8))
    m.part(); m.box(x0, 0, 0, x1, d, h, mt.wall, top=mt.roof)
    m.part(); m.box(x0 - PX, -PX, 0, x1 + PX, d, 1.5, stone, top=M('stone', 4.7))
    m.part(); m.box(x0 - PX, -1.5 * PX, 1.5, x1 + PX, d, 1.62, M('stone', 4.5), top=M('stone', 4.9))
    # a band of writing under the roof: what is owed, by whom, since when
    m.part(); m.box(x0, -0.5 * PX, h - 0.62, x1, d, h - 0.3, M('sandstone', 4.2, town.m_cuneiform(5)))
    crown = M('sandstone', 4.5, m_mottle(9, 0.3))
    parapet(m, mt, x0, 0, x1, d, h, h=0.22, mat=crown)
    merlons(m, crown, x0, x1, 0, 3 * PX, h + 0.22, mw=0.5, mh=0.34)
    for wx in (-2.7, -1.5, 1.5, 2.7):
        m.part(); m.quad((wx - 0.19, -0.03, 1.84), (wx + 0.19, -0.03, 1.84), (wx + 0.19, -0.03, 2.42), (wx - 0.19, -0.03, 2.42), mt.dark)
        m.part()
        for bx in (-0.07, 0.07):
            m.box(wx + bx - PX / 2, -0.05, 1.84, wx + bx + PX / 2, -0.03, 2.42, mt.bronze)
        m.part(); m.box(wx - 0.26, -0.07, 1.76, wx + 0.26, 0, 1.84, M('stone', 4.7))
        m.part(); m.box(wx - 0.26, -0.06, 2.42, wx + 0.26, 0, 2.5, M('stone', 4.3))
    big_door(m, mt, 0.0, 0, w=1.5, h=2.0, bands=4, frame=M('stone', 4.3, m_ashlar(8, 6)), ajar=True)
    bracket_sign(m, mt, -1.3, 0, 2.6, 'scales', out=0.62)
    for sx in (-1.0, 1.0):
        lamp(m, mt, sx * 1.02, -0.2, 1.72, strength=0.45, radius=2.2)
    # the board by the door, which says what it has always said
    m.part(); m.box(1.5, -0.05, 0.9, 2.3, 0, 1.45, M('wood', 3.6, m_planks(3, 'h')))
    m.part(); m.box(1.58, -0.06, 1.0, 2.22, -0.05, 1.36, M('limewash', 4.2, town.m_cuneiform(4)))
    return Building('lt_tax', m, w, d, h, doors=[(0.0, 'gong')], leaves={0: ('big', 1.5, 2.0, 4)})


def oracle_house():
    """Ummi's. A room under a beehive of brick, the way they build where her mother came from: the
    smoke of whatever she burns goes up the middle of it and out at the top. Lime-washed, a band of
    lapis round it under the dome, and a cloth in the doorway the colour of a fig."""
    w, d, h = 6.0, 4.5, 2.0
    mt = Mats(17, 1)
    m = Model()
    x0, x1 = -w / 2, w / 2
    white = M('limewash', 4.6, m_plaster(bricks=True))
    m.part(); m.box(x0, 0, 0, x1, d, h, white, top=M('limewash', 4.2, m_mottle(12, 0.4)))
    m.part(); m.box(x0 - PX, -PX, 0, x1 + PX, d, 0.34, mt.plinth, top=mt.trim)
    m.part(); m.box(x0 - PX, -PX, h - 0.4, x1 + PX, d, h - 0.14, M('lapis', 3.6, m_zigzag(8, 3, 2), ramp2='gold'))
    m.part(); m.box(x0 - 1.5 * PX, -1.5 * PX, h - 0.14, x1 + 1.5 * PX, d + PX, h, M('limewash', 4.9))
    dome(m, M('limewash', 4.3, m_brick(8, 4, -0.7, 0.6)), 0, d / 2 + 0.1, 2.45, h, rise=2.7, n=18, cap=M('dark', 0.9), squash=0.8)
    m.part(); m.turned(0, d / 2 + 0.1, [(0.34, h + 2.6), (0.4, h + 2.74), (0.3, h + 2.8)], M('brick', 3.4), n=10, cap=M('dark', 0.7), squash=0.8)
    m.light(0, d / 2 - 0.6, h + 2.8, 2.4, (0.75, 0.6, 1.0), 0.4)
    # the doorway and its cloth; a lamp either side, burning something that is not oil
    dx = 0.0
    m.part(); m.box(dx - 0.74, -0.1, 0, dx - 0.56, 0, 1.78, M('lapis', 3.8))
    m.box(dx + 0.56, -0.1, 0, dx + 0.74, 0, 1.78, M('lapis', 3.8))
    arched(m, mt, dx, 0, 1.12, (0.0, 1.78), mt.dark, rise=0.5)
    curtain(m, dx, 0, 1.0, 1.5, colours=('fig', 'blue'), z0=0.1)
    m.part(); m.box(dx - 0.8, -0.36, 0, dx + 0.8, 0, 2 * PX, mt.stone)
    for sx in (-1.5, 1.5):
        m.part(); m.box(sx - 0.14, -0.08, 0.9, sx + 0.14, 0, 1.3, mt.dark)
        m.part(); m.blob(sx, -0.1, 0.98, 0.08, 0.06, 0.05, mt.pot, n=7, rings=3)
        m.part(); m.blob(sx + 0.05, -0.1, 1.06, 0.03, 0.03, 0.06, Mat(RAMPS['fig'], 4.0, glow=True), n=5, rings=3)
        m.light(sx, -0.4, 1.05, 2.0, (0.8, 0.55, 1.0), 0.5)
    # charms on cords along the eaves: bronze discs that turn in a wind nobody else can feel
    for k, cx in enumerate(np.linspace(x0 + 0.5, x1 - 0.5, 8)):
        if abs(cx - dx) < 0.7:
            continue
        ln = 0.3 + 0.16 * ((k * 7) % 3)
        m.part(); m.box(cx - PX / 4, -0.12, h - 0.4 - ln, cx + PX / 4, -0.11, h - 0.4, mt.rope)
        m.part(); m.turned(cx, -0.12, [(0.0, h - 0.4 - ln - 0.12), (0.07, h - 0.4 - ln - 0.06), (0.0, h - 0.4 - ln)], mt.gold if k % 2 else mt.bronze, n=6, squash=0.25)
    shade(m, mt, dx, 0, 2.4, out=0.6, z=h + 0.05, drop=0.12, colours=('fig', 'blue'), poles=False)
    return Building('lt_oracle', m, w, d, h, doors=[(dx, 'open')], tall=[(x0, x1, 2.9)])


def pottery():
    """Kesh's. Two roofs: the low one is where the jars dry, in rows, and he counts them; the high one is the
    loft he keeps the sacred ones in, with its front left open so that the street can see what it cannot afford."""
    w, d = 10.0, 4.0
    h, h2 = 2.25, 3.5
    mt = Mats(19, 0)
    m = Model()
    x0, x1 = -w / 2, w / 2
    xs = 1.4                                          # where the loft begins
    shell(m, mt, x0, xs, d, h)
    m.part(); m.box(xs, 0, 0, x1, d, h2, mt.wall, top=mt.roof)
    m.part(); m.box(xs - PX, -PX, 0, x1 + PX, d, 0.38, mt.plinth, top=mt.trim)
    parapet(m, mt, x0, 0, xs, d, h)
    parapet(m, mt, xs, 0, x1, d, h2, h=0.2)
    beam_ends(m, mt, x0 + 0.3, xs - 0.3, 0, h - 0.4)
    beam_ends(m, mt, xs + 0.3, x1 - 0.3, 0, h2 - 0.4)
    # a band of sherds pressed into the plaster: every pot that did not survive the kiln
    m.part(); m.box(x0, -0.5 * PX, 1.5, xs, d, 1.72, M('clay', 4.0, m_cones(6, 3), ramp2='dark'))
    # the loft's open front: three shelves, and what stands on them
    lx0, lx1 = xs + 0.5, x1 - 0.5
    m.part(); m.quad((lx0, -0.02, 1.9), (lx1, -0.02, 1.9), (lx1, -0.02, 3.1), (lx0, -0.02, 3.1), mt.dark)
    m.part(); m.quad((lx0 + 0.05, -0.025, 1.92), (lx1 - 0.05, -0.025, 1.92), (lx1 - 0.05, -0.025, 2.5), (lx0 + 0.05, -0.025, 2.5), mt.glow_dim)
    m.light((lx0 + lx1) / 2, -0.5, 2.4, 3.0, (1.0, 0.72, 0.4), 0.5)
    for z in (1.9, 2.5):
        m.part(); m.box(lx0 - 0.05, -0.16, z - PX, lx1 + 0.05, 0, z, mt.beam)
        pots_row(m, mt, lx0 + 0.2, lx1 - 0.15, -0.08, z, step=0.36, s=0.5, seed=int(z * 10))
    m.part(); m.box(lx0 - 0.1, -0.08, 3.1, lx1 + 0.1, 0, 3.2, mt.beam)
    door(m, mt, xs + 1.8, 0, w=1.0, h=1.7, lit=True)
    bracket_sign(m, mt, xs + 0.5, 0, 1.8, 'jar', out=0.55)
    # the yard side: his door, the big jars standing along the wall
    window(m, mt, -3.6, 0, 1.0, 0.44, 0.46, lit=False)
    for k, jx in enumerate((-2.7, -2.0, -1.2, -0.4, 0.5)):
        jar(m, mt, jx, -0.3, 0, s=1.0 if k % 2 == 0 else 0.86, kind=3, mat=mt.pot if k % 3 else mt.pot2)
    # the low roof: rows of jars drying, a mat, the ladder up to the loft roof
    for ry in (1.0, 1.6, 2.2, 2.8, 3.4):
        pots_row(m, mt, x0 + 1.5, xs - 2.9, ry, h, step=0.42, s=0.42, seed=int(ry * 7))
    m.part(); m.box(xs - 2.2, 0.7, h, xs - 0.9, 1.9, h + 0.5 * PX, mt.reed)
    trapdoor(m, mt, xs - 0.9, 2.9, h)
    ladder(m, mt, x0 + 0.6, 0, h, lean=0.45, w=0.4)
    return Building('lt_pottery', m, w, d, h, doors=[(xs + 1.8, 'open')], ladders=[x0 + 0.6], hatch=(xs - 0.9, 2.9), walk=(x0, xs),
                    blocks=[(x0 + 1.25, 0.8, xs - 2.6, 3.75)], tall=[(xs, x1, h2 - h)], extra=[(-3.1, -0.62, 0.9, 0)])


def beer_house():
    """The Seven Jars. Long and low, the whole front open on the street under a roof of reed, and a second
    roof over that one where they sit when the weather is good, which in Ashkel is every night for forty
    nights. The stair is at the left end. The light in the doorway has not gone out; neither has anybody."""
    w, d, h = 11.5, 4.0, 2.5
    mt = Mats(23, 4)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h, gap=(x0, x0 + 0.62))
    beam_ends(m, mt, x0 + 2.8, x1 - 0.3, 0, h - 0.42)
    # a painted band the height of a sitting man's head: seven jars, over and over
    m.part(); m.box(x0 + 2.7, -0.5 * PX, 1.26, x1, d, 1.5, M('ochre', 3.6, m_zigzag(10, 4, 2), ramp2='red'))
    # the doorway: wide, no door, light and noise
    dx = 0.6
    m.part(); m.box(dx - 1.0, -0.08, 0, dx - 0.82, 0, 2.0, mt.beam)
    m.box(dx + 0.82, -0.08, 0, dx + 1.0, 0, 2.0, mt.beam)
    m.box(dx - 1.06, -0.1, 2.0, dx + 1.06, 0, 2.14, mt.beam)
    m.part(); m.quad((dx - 0.82, -0.02, 0), (dx + 0.82, -0.02, 0), (dx + 0.82, -0.02, 2.0), (dx - 0.82, -0.02, 2.0), mt.dark)
    m.part(); m.quad((dx - 0.8, -0.025, 0), (dx + 0.8, -0.025, 0), (dx + 0.8, -0.025, 1.3), (dx - 0.8, -0.025, 1.3), mt.glow_dim)
    m.light(dx, -0.6, 0.9, 4.2, (1.0, 0.72, 0.4), 0.8)
    m.part(); m.box(dx - 1.1, -0.4, 0, dx + 1.1, 0, 2 * PX, mt.stone)
    for wx in (-1.6, 2.7, 3.9):
        window(m, mt, wx, 0, 1.62, 0.46, 0.4, lit=True, bars=False)
    bracket_sign(m, mt, dx + 1.5, 0, 2.4, 'cup', out=0.6)
    # the bench along the wall, the big jars with their drinking reeds, a table somebody is still at
    m.part(); m.box(2.0, -0.42, 0, 5.2, -0.1, 0.34, mt.wall_plain, top=mt.trim)
    for k, jx in enumerate((-1.45, -0.86)):
        jar(m, mt, jx, -0.36, 0, s=0.96, kind=3, mat=mt.pot2 if k else mt.pot)
        m.part(); m.beam((jx + 0.06, -0.36, 1.0), (jx + 0.34, -0.5, 1.5), 0.6 * PX, M('straw', 4.6))
        m.part(); m.beam((jx - 0.04, -0.36, 1.0), (jx - 0.3, -0.46, 1.46), 0.6 * PX, M('straw', 4.4))
    m.part(); m.box(3.0, -0.95, 0.34, 4.0, -0.5, 0.4, mt.wood_h, top=M('wood', 4.8))
    m.part(); m.box(3.4, -0.8, 0, 3.6, -0.66, 0.34, mt.beam)
    m.part()
    for cx in (3.2, 3.55, 3.84):
        m.turned(cx, -0.72, [(0.035, 0.4), (0.06, 0.52)], mt.pot, n=6, cap=mt.dark)
    # the roof they drink on: benches, jars, a lamp on a pole
    m.part(); m.box(-1.5, 1.0, h, 1.5, 1.24, h + 0.3, mt.wood_h, top=M('wood', 4.8))
    m.part(); m.box(-1.5, 2.6, h, 1.5, 2.84, h + 0.3, mt.wood_h, top=M('wood', 4.8))
    m.part(); m.box(-0.9, 1.6, h + 0.3, 0.9, 2.3, h + 0.38, mt.wood_h, top=M('wood', 4.9))
    for lx, ly in ((-0.7, 1.75), (0.7, 2.15)):
        m.part(); m.box(lx - 0.05, ly - 0.05, h, lx + 0.05, ly + 0.05, h + 0.3, mt.beam)
    jar(m, mt, 3.6, 2.0, h, s=1.0, kind=3)
    jar(m, mt, 4.4, 1.3, h, s=0.8, kind=0)
    jar(m, mt, 0.0, 1.95, h + 0.38, s=0.5, kind=0, mat=mt.pot2)
    m.part(); m.box(4.9 - PX, 3.4 - PX, h, 4.9 + PX, 3.4 + PX, h + 1.3, mt.beam)
    lamp(m, mt, 4.9, 3.3, h + 1.32, strength=0.6, radius=3.0)
    # the stair, outside, on the left
    stairs(m, mt, x0 + 2.6, x0, 0, h)
    return Building('lt_beer', m, w, d, h, doors=[(dx, 'open')], stair=(x0 + 2.6, x0), walk=(x0, x1), door_w=1.5,
                    blocks=[(-1.6, 0.9, 1.6, 3.1), (3.2, 1.0, 4.8, 2.9), (4.6, 3.2, 5.2, d)], extra=[(2.0, -0.45, 5.2, 0), (-1.8, -0.6, -0.5, 0), (2.9, -1.0, 4.1, -0.45)])


def weavers():
    """The house of the weavers and the dyers, who are sisters and do not speak. An open gallery across the back
    of the roof, and from its rail the cloth of forty nights ago still hanging down the front of the house, dry.
    The street door is bolted: they come and go by the roof, like the cats."""
    w, d, h = 9.5, 4.0, 2.75
    mt = Mats(29, 1)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h)
    beam_ends(m, mt, x0 + 0.3, x1 - 0.3, 0, h - 0.42)
    dx = -2.9
    door(m, mt, dx, 0, w=1.0, h=1.75)
    window(m, mt, 3.6, 0, 1.4, 0.46, 0.5, lit=True)
    window(m, mt, -4.0, 0, 1.4, 0.4, 0.5, lit=False)
    # the gallery: posts, a rail, a roof of reed; it stops short of the east end, where the stair comes up
    gx1 = x1 - 2.5
    gy = d - 1.7
    uh = 1.9
    m.part(); m.box(x0, d - 0.25, h, gx1, d, h + uh, mt.wall, top=mt.roof)
    for k in range(5):
        px = x0 + 0.14 + (gx1 - x0 - 0.28) * k / 4
        m.part(); m.box(px - 1.2 * PX, gy, h, px + 1.2 * PX, gy + 2.4 * PX, h + uh, mt.beam)
    m.part(); m.box(x0, gy - 0.02, h + 0.62, gx1, gy + PX, h + 0.7, mt.beam)
    m.part(); m.box(x0 - 0.1, gy - 0.3, h + uh, gx1 + 0.1, d, h + uh + 0.1, mt.reed, top=mt.reed)
    m.part(); m.box(x0 - 0.1, gy - 0.32, h + uh - PX, gx1 + 0.1, gy - 0.3, h + uh + 0.1, mt.beam)
    # the head of the stair: a hut of its own on the roof, with a door
    sx0, sx1, sd, sh = x1 - 2.2, x1 - 0.2, 1.75, 1.75
    m.part(); m.box(sx0, d - sd, h, sx1, d, h + sh, mt.wall, top=mt.roof)
    parapet(m, mt, sx0, d - sd, sx1, d, h + sh, h=0.16)
    m.push((0, 0, h))
    doorway(m, mt, (sx0 + sx1) / 2, d - sd, w=0.85, h=1.45, glow=True, ajar=0.35, leaf=M('blue', 3.4, m_planks(3, 'v', knots=False)))
    m.pop()
    # the cloth: lengths of it over the rail and down the wall, each its own colour
    dyes = [('red', 'red'), ('blue', 'lapis'), ('ochre', 'gold'), ('cream', 'linen'), ('fig', 'red'), ('green', 'olive')]
    r = rnd(5)
    for k, cx in enumerate((-1.7, -0.75, 0.2, 1.15)):
        a, b = dyes[k % len(dyes)]
        wd = 0.78
        z1 = h + 0.7
        z0 = 0.7 + float(r.uniform(0, 0.7))
        cols, rows = 4, 7
        g = np.zeros((rows, cols, 3))
        for i in range(rows):
            t = i / (rows - 1)
            z = z1 - (z1 - z0) * t
            for q in range(cols):
                sx = q / (cols - 1)
                # over the rail at the top, then hanging clear of the front wall
                y = (gy - 0.04) if z > h + 0.05 else (-0.07 - 0.03 * math.sin(math.pi * 3 * sx + k))
                g[i, q] = (cx - wd / 2 + wd * sx, y, z)
        m.part(); m.sheet(g, M(a, 4.4, m_stripes(9, 'v'), ramp2=b, soft=True))
    # the vats, in front, and the stick they are stirred with
    for k, (vx, col) in enumerate(((0.6, 'red'), (1.7, 'lapis'), (2.7, 'ochre'))):
        tub(m, mt, vx, -0.75 - 0.2 * (k % 2), 0.46, col)
    m.part(); m.beam((1.7, -0.9, 0.3), (2.2, -1.2, 1.2), 0.8 * PX, mt.beam)
    # a loom's frame by the door, with the warp still on it
    lx = -4.4
    m.part()
    for sx in (lx, lx + 0.9):
        m.box(sx - PX, -0.3, 0, sx + PX, -0.2, 1.5, mt.beam)
    m.box(lx, -0.3, 1.42, lx + 0.9, -0.2, 1.5, mt.beam); m.box(lx, -0.3, 0.12, lx + 0.9, -0.2, 0.2, mt.beam)
    m.part(); m.quad((lx + 0.06, -0.26, 0.2), (lx + 0.84, -0.26, 0.2), (lx + 0.84, -0.26, 1.42), (lx + 0.06, -0.26, 1.42), M('linen', 4.4, m_stripes(2, 'u'), ramp2='red', soft=True), two=True)
    # the ladder, at the east end
    ladder(m, mt, 4.1, 0, h, lean=0.5, w=0.4)
    return Building('lt_weavers', m, w, d, h, doors=[(dx, 'locked')], ladders=[4.1], walk=(x0, x1), upper=(sx0, sx1, sd, sh), roof_door=(sx0 + sx1) / 2,
                    tall=[(x0 - 0.1, gx1 + 0.15, 1.9, gy - 0.35)], extra=[(0.1, -1.4, 3.3, 0), (lx - 0.1, -0.4, lx + 1.0, 0)],
                    leaves={0: ('plain', 1.0, 1.75, 0)})


def net_loft():
    """Where the boats' gear is kept, on the quay. Stone to the knee, reed above that, and for a roof the hull
    of the Abu-Nur's father's boat, keel up, which is the driest thing in the harbour."""
    w, d, h = 8.5, 3.5, 2.0
    mt = Mats(31, 4)
    m = Model()
    x0, x1 = -w / 2, w / 2
    reed = M('reed', 4.0, m_reeds(3))
    m.part(); m.box(x0, 0, 0, x1, d, h, reed, top=M('wood', 3.2, m_planks(5, 'h')))
    m.part(); m.box(x0 - PX, -PX, 0, x1 + PX, d, 0.56, M('stone', 3.9, m_ashlar(12, 6)), top=M('stone', 4.6))
    for k in range(5):
        px = x0 + 0.1 + (w - 0.2) * k / 4
        m.part(); m.box(px - 1.2 * PX, -1.5 * PX, 0.56, px + 1.2 * PX, 0, h, mt.beam)
    m.part(); m.box(x0, -1.5 * PX, h - 0.1, x1, 0, h, mt.beam)
    # the hull: ribs of the old boat under planks gone silver
    hull = M('wood', 3.9, m_planks(4, 'h'))
    cy = d / 2
    for i in range(12):
        t0, t1 = i / 12.0, (i + 1) / 12.0
        xa, xb = x0 - 0.3 + (w + 0.6) * t0, x0 - 0.3 + (w + 0.6) * t1
        ra = math.sin(math.pi * (t0 + t1) / 2) ** 0.6
        hw = (d / 2 + 0.2) * ra; hz = 1.25 * ra
        m.part()
        prof = [(-hw, 0.0), (-hw * 0.82, hz * 0.55), (-hw * 0.45, hz * 0.9), (0, hz), (hw * 0.45, hz * 0.9), (hw * 0.82, hz * 0.55), (hw, 0.0)]
        for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
            m.quad((xa, cy + ya, h + za), (xb, cy + ya, h + za), (xb, cy + yb, h + zb), (xa, cy + yb, h + zb), hull, two=True)
    m.part(); m.box(x0 - 0.36, cy - PX, h + 1.2, x1 + 0.36, cy + PX, h + 1.34, M('wood', 4.6))
    # the doors: two leaves, one of them never shut since the hinge went
    dx = -1.2
    m.part(); m.quad((dx - 1.0, -0.02, 0), (dx + 1.0, -0.02, 0), (dx + 1.0, -0.02, 1.8), (dx - 1.0, -0.02, 1.8), mt.dark)
    m.part(); m.quad((dx - 1.0, -0.04, 0), (dx - 0.05, -0.04, 0), (dx - 0.05, -0.04, 1.8), (dx - 1.0, -0.04, 1.8), M('wood', 3.6, m_planks(4, 'v')))
    m.part(); m.quad((dx + 1.0, -0.04, 0), (dx + 1.55, -0.3, 0), (dx + 1.55, -0.3, 1.8), (dx + 1.0, -0.04, 1.8), M('wood', 3.9, m_planks(4, 'v')), two=True)
    m.part(); m.box(dx - 1.1, -0.1, 1.8, dx + 1.1, 0, 1.92, mt.beam)
    bracket_sign(m, mt, dx + 2.2, 0, 1.9, 'fish', out=0.6)
    # nets over a rail at the east end, oars, floats
    net = M('straw', 3.8, m_lattice(3), soft=True)
    m.part()
    for px in (2.0, 3.9):
        m.box(px - PX, -0.5, 0, px + PX, -0.4, 1.5, mt.beam)
    m.box(2.0, -0.5, 1.44, 3.9, -0.4, 1.5, mt.beam)
    g = np.zeros((6, 7, 3))
    for i in range(6):
        t = i / 5.0
        for q in range(7):
            sx = q / 6.0
            g[i, q] = (2.05 + 1.8 * sx, -0.52 - 0.3 * t - 0.06 * math.sin(sx * 9), 1.46 - 1.3 * t + 0.1 * math.sin(sx * 7) * t)
    m.part(); m.sheet(g, net)
    for k, ox in enumerate((0.6, 0.9)):
        m.part(); m.beam((ox, -0.14, 0), (ox + 0.2, -0.04, 2.3), 0.9 * PX, mt.beam)
        m.part(); m.box(ox + 0.12, -0.06, 1.9, ox + 0.34, -0.04, 2.5, M('wood', 4.6))
    m.part()
    for k in range(4):
        m.blob(3.4 + 0.24 * k, -0.9, 0.1, 0.1, 0.1, 0.1, M('cedar', 3.8), n=6, rings=3, seed=k)
    return Building('lt_netloft', m, w, d, h, doors=[(dx, 'open')], door_w=1.2, tall=[(x0, x1, 1.4)], extra=[(1.9, -1.1, 4.2, 0), (0.5, -0.2, 1.3, 0)])


def goat_house():
    """The house the goat stands on. Shutters to, door barred from the inside with two planks and a spite. Nobody
    has lived in it since before the sleep. Somebody has kept the roof very tidy."""
    w, d, h = 7.0, 3.5, 2.5
    mt = Mats(37, 3)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h)
    beam_ends(m, mt, x0 + 0.3, x1 - 0.3, 0, h - 0.42)
    dx = -0.8
    doorway(m, mt, dx, 0, w=1.0, h=1.75, glow=False, ajar=0.3)
    for wx in (-2.6, 1.6, 2.7):
        shutters(m, wx, 0, 1.36, colour='cedar', shut=True)
    # the ladder: somebody else's, borrowed forty nights ago
    ladder(m, mt, 2.15, 0, h, lean=0.5, w=0.4)
    # the roof: what was a garden in tubs, eaten level; a hatch; one sandal
    for k, tx in enumerate((-2.5, -1.6, -0.7)):
        m.part(); m.box(tx - 0.34, 2.2, h, tx + 0.34, 2.9, h + 0.3, M('clay', 3.8), top=M('wood', 2.4))
        m.part()
        for q in range(4):
            m.box(tx - 0.24 + q * 0.16, 2.44, h + 0.3, tx - 0.2 + q * 0.16, 2.48, h + 0.36, M('olive', 3.0))
    trapdoor(m, mt, 1.3, 1.9, h)
    return Building('lt_goat', m, w, d, h, doors=[(dx, 'barred')], ladders=[2.15], hatch=(1.3, 1.9), walk=(x0, x1),
                    blocks=[(-3.0, 2.1, -0.3, 3.3)], leaves={0: ('barred', 1.0, 1.75, 0)})


# ------------------------------------------------------------------ the gate square
def watch_house():
    """The night watch's own. A tower at one corner with the watch fire on it, shields over the bench in the
    order they were won, and over the door the lamp that is never put out, which is why Azar could read."""
    w, d, h = 9.5, 4.0, 3.0
    mt = Mats(41, 3)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h, plinth=M('sandstone', 3.7, m_ashlar(12, 6)), foot=0.7)
    crown = M('sandstone', 4.5, m_mottle(9, 0.3))
    tw, th = 2.5, 5.0
    parapet(m, mt, x0 + tw, 0, x1, d, h, h=0.22, mat=crown, gap=(x1 - 0.62, x1))
    merlons(m, crown, x0 + tw + 0.1, x1 - 0.7, 0, 3 * PX, h + 0.22, mw=0.46, mh=0.32)
    # the tower
    m.part(); m.box(x0, -PX, 0, x0 + tw, tw, th, mt.wall, top=mt.roof)
    m.part(); m.box(x0 - PX, -2 * PX, 0, x0 + tw + PX, tw, 0.7, M('sandstone', 3.7, m_ashlar(12, 6)), top=M('sandstone', 4.6))
    parapet(m, mt, x0, -PX, x0 + tw, tw, th, h=0.22, mat=crown)
    merlons(m, crown, x0, x0 + tw, -PX, 2 * PX, th + 0.22, mw=0.46, mh=0.32)
    for z in (1.6, 3.5):
        m.part(); m.quad((x0 + tw / 2 - 0.12, -PX - 0.03, z), (x0 + tw / 2 + 0.12, -PX - 0.03, z), (x0 + tw / 2 + 0.12, -PX - 0.03, z + 0.7), (x0 + tw / 2 - 0.12, -PX - 0.03, z + 0.7), mt.dark)
        m.part(); m.box(x0 + tw / 2 - 0.2, -PX - 0.07, z - PX, x0 + tw / 2 + 0.2, -PX, z, crown)
    # the watch fire, in its iron basket
    bx, by = x0 + tw / 2, tw / 2
    m.part(); m.turned(bx, by, [(0.1, th), (0.14, th + 0.5), (0.4, th + 0.62), (0.46, th + 0.86), (0.36, th + 0.86)], M('iron', 3.2), n=10, cap=Mat(RAMPS['glow'], 1.4, town.m_coals(), glow=True))
    town.flame(m, bx, by, th + 0.86, s=1.25, frame=0, seed=4)
    m.light(bx, by - 0.5, th + 1.2, 6.0, (1.0, 0.68, 0.34), 0.85)
    # the door standing open (somebody left in a hurry, forty nights ago), the lamp over it
    dx = 1.2
    jamb = M('sandstone', 4.2, m_ashlar(8, 6))
    m.part(); m.box(dx - 0.86, -0.1, 0, dx - 0.7, 0, 2.16, jamb)
    m.box(dx + 0.7, -0.1, 0, dx + 0.86, 0, 2.16, jamb)
    doorway(m, mt, dx, 0, w=1.4, h=2.0, glow=True, ajar=0.3, leaf=M('cedar', 4.1, m_studs(5), ramp2='bronze'))
    # the rule of the watch, cut over the door, and the lamp it is read by
    m.part(); m.box(dx - 0.9, -0.08, 2.16, dx + 0.9, 0, 2.4, M('sandstone', 4.5, town.m_cuneiform(4)), top=M('sandstone', 4.9))
    lamp(m, mt, dx, -0.2, 2.54, strength=0.7, radius=3.4)
    for wx in (-1.6, -0.5):
        window(m, mt, wx, 0, 2.24, 0.3, 0.42, lit=True, bars=True)
    # the bench the day watch sat on, and over it the shields
    m.part(); m.box(-2.1, -0.44, 0, 0.1, -0.1, 0.34, mt.wall_plain, top=mt.trim)
    for k, sx in enumerate((-1.75, -1.15, -0.55, 0.0)):
        col = ('bronze', 'bronze', 'gold', 'bronze')[k]
        m.part(); m.face([(sx + 0.26 * math.cos(a), 1.75 + 0.26 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)], -0.05, M(col, 4.2 + 0.2 * (k % 2), gloss=0.03))
        m.part(); m.face([(sx + 0.07 * math.cos(a), 1.75 + 0.07 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)], -0.07, M(col, 5.0, gloss=0.04))
    # the roof: the rack the rattles hang on, a mat
    m.part(); m.box(0.0, 1.2, h, 1.6, 2.4, h + 0.5 * PX, mt.reed)
    m.part(); m.box(-1.8, 3.2, h, -0.2, 3.3, h + 1.0, mt.beam)
    for k in range(4):
        m.part(); m.box(-1.6 + k * 0.4, 3.14, h + 0.5, -1.5 + k * 0.4, 3.2, h + 0.86, M('wood', 4.6))
    stairs(m, mt, x1 - 2.7, x1, 0, h)
    return Building('ak_watch', m, w, d, h, doors=[(dx, 'open')], stair=(x1 - 2.7, x1), walk=(x0 + tw, x1), door_w=1.2,
                    tall=[(x0, x0 + tw, 2.0, 0.0)], blocks=[(-1.9, 3.0, -0.1, d)], extra=[(-2.1, -0.45, 0.1, 0)])


def merchant_house():
    """The house of Ilu-Bani, who sold the temple its cedar. Piers and recesses along the front, as on the temple
    itself, which the temple minded; a band of cones in three colours; a porch on two pillars; and above, set
    back, the rooms with the round-headed windows where the family slept, and sleeps."""
    w, d, h = 11.0, 4.5, 3.0
    mt = Mats(43, 1)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h, foot=0.5)
    pier = M('limewash', 4.5, m_mottle(12, 0.3))
    for k in range(8):
        cx = x0 + (w / 8) * (k + 0.5)
        if abs(cx) < 1.3:
            continue
        m.part(); m.box(cx - 0.3, -0.16, 0.5, cx + 0.3, 0, h, pier, top=M('limewash', 4.9))
    m.part(); m.box(x0 - PX, -0.18, 1.72, x1 + PX, d, 2.08, M('cream', 4.2, m_cones(8, 3), ramp2='red'))
    m.part(); m.box(x0 - 1.5 * PX, -0.2, h - 0.16, x1 + 1.5 * PX, d + PX, h - 0.02, M('limewash', 4.8), top=M('limewash', 5.0))
    parapet(m, mt, x0, 0, x1, d, h, h=0.2, mat=M('limewash', 4.6))
    # the porch: shallow, on two pillars
    for sx in (-1.15, 1.15):
        add(m, town.pillar(2.3), (sx, -0.85, 0))
    m.part(); m.box(-1.5, -1.1, 2.36, 1.5, 0, 2.56, M('cedar', 4.0, m_planks(4, 'h')), top=mt.roof)
    m.part(); m.box(-1.56, -1.16, 2.56, 1.56, 0, 2.66, M('limewash', 4.8), top=M('limewash', 5.0))
    big_door(m, mt, 0.0, 0, w=1.6, h=2.1, bands=3, frame=M('limewash', 4.4), ajar=True)
    for sx in (-1.0, 1.0):
        lamp(m, mt, sx * 0.98, -0.2, 1.5, strength=0.5, radius=2.4)
    m.part(); m.box(-1.6, -1.25, 0, 1.6, 0, 2 * PX, mt.stone)
    for sx in (-2.6, 2.6):
        m.part(); m.turned(sx, -0.6, [(0.3, 0), (0.36, 0.36), (0.3, 0.42)], M('clay', 4.0), n=10, cap=M('wood', 2.2))
        add(m, town.palm(int(sx * 3) + 9, 1.9), (sx, -0.6, 0.3))
    # the upper rooms, set back, with their round-headed windows
    ux0, ux1, ud, uh = -3.5, 3.5, 2.5, 2.25
    m.part(); m.box(ux0, d - ud, h, ux1, d, h + uh, mt.wall, top=mt.roof)
    m.part(); m.box(ux0 - PX, d - ud - PX, h + uh - 0.16, ux1 + PX, d, h + uh - 0.02, M('limewash', 4.8), top=M('limewash', 5.0))
    parapet(m, mt, ux0, d - ud, ux1, d, h + uh, h=0.19, mat=M('limewash', 4.6))
    for k, wx in enumerate((-2.6, -1.5, 1.5, 2.6)):
        arched(m, mt, wx, d - ud, 0.5, (h + 0.7, h + 1.6), mt.glow if k in (1, 2) else mt.dark, rise=0.25)
        m.part(); m.box(wx - 0.32, d - ud - 0.08, h + 0.64, wx + 0.32, d - ud, h + 0.7, M('limewash', 4.9))
        if k in (1, 2):
            m.light(wx, d - ud - 0.5, h + 1.2, 2.6, (1.0, 0.74, 0.4), 0.5)
    m.push((0, 0, h))
    doorway(m, mt, 0.0, d - ud, w=0.9, h=1.6, glow=True, ajar=0.35)
    m.pop()
    # the roof in front of them: a rug, cushions
    m.part(); m.box(-1.6, 0.45, h, 1.6, 1.3, h + 0.5 * PX, M('red', 3.4, m_zigzag(8, 3, 2), ramp2='gold'))
    for k, (cx, cy) in enumerate(((-3.6, 1.0), (3.5, 1.2), (4.2, 0.8))):
        m.part(); m.blob(cx, cy, h + 0.1, 0.24, 0.2, 0.09, M(('blue', 'fig', 'ochre')[k], 4.0, soft=True), n=7, rings=3, seed=k)
    return Building('ak_merchant', m, w, d, h, doors=[(0.0, 'barred')], upper=(ux0, ux1, ud, uh), roof_door=0.0, walk=(x0, x1), door_w=1.5,
                    leaves={0: ('big', 1.6, 2.1, 3)},
                    extra=[(-1.32, -1.02, -0.98, -0.68), (0.98, -1.02, 1.32, -0.68), (-2.98, -0.98, -2.22, -0.26), (2.22, -0.98, 2.98, -0.26)])


def tablet_house():
    """The tablet house, where the sons of Ashkel learn to write and wish they were dead. A long room with its
    windows too high to look out of. Today's tablets are on the roof to dry, in rows, forty nights dry."""
    w, d, h = 10.0, 3.5, 2.5
    mt = Mats(47, 0)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h)
    beam_ends(m, mt, x0 + 0.3, x1 - 0.3, 0, h - 0.42)
    dx = 2.4
    for k in range(6):
        wx = x0 + 1.0 + k * 1.3
        if abs(wx - dx) < 1.0:
            continue
        window(m, mt, wx, 0, 1.7, 0.36, 0.36, lit=(k == 2), bars=False)
    red = M('red', 3.4)
    m.part(); m.box(dx - 0.72, -0.08, 0, dx - 0.56, 0, 1.86, red)
    m.box(dx + 0.56, -0.08, 0, dx + 0.72, 0, 1.86, red)
    m.box(dx - 0.72, -0.1, 1.86, dx + 0.72, 0, 2.0, red)
    doorway(m, mt, dx, 0, w=1.05, h=1.8, glow=True, ajar=0.36)
    m.part(); m.box(dx - 0.8, -0.07, 2.02, dx + 0.8, 0, 2.4, M('clay', 4.4, town.m_cuneiform(4)), top=M('clay', 4.8))
    # the bench the length of the wall, and on it what was handed in
    m.part(); m.box(x0 + 0.4, -0.46, 0, 1.4, -0.1, 0.36, mt.wall_plain, top=mt.trim)
    clay = [M('clay', 4.3, m_mottle(4, 0.5)), M('clay', 3.7, m_mottle(4, 0.5)), M('sandstone', 4.3, m_mottle(4, 0.4))]
    r = rnd(8)
    for k in range(7):
        bx = x0 + 0.8 + k * 0.72
        for q in range(int(r.integers(1, 5))):
            m.part(); m.box(bx - 0.2 + r.uniform(-0.03, 0.03), -0.38 + r.uniform(-0.02, 0.02), 0.36 + q * 0.06, bx + 0.2, -0.16, 0.42 + q * 0.06, clay[(k + q) % 3], top=clay[(k + q + 1) % 3])
    # the roof: today's lines, in rows, with a way left along the front and at the east end
    for ry in np.arange(0.9, 3.1, 0.5):
        for rx in np.arange(x0 + 0.6, x1 - 2.9, 0.56):
            if hash2(int(rx * 10), int(ry * 10), 3) < 0.12:
                continue
            m.part(); m.box(rx, ry, h, rx + 0.4, ry + 0.3, h + 0.05, clay[int(hash2(int(rx * 7), int(ry * 9), 5) * 3)], top=clay[int(hash2(int(rx * 3), int(ry * 5), 7) * 3)])
    trapdoor(m, mt, 3.7, 2.2, h)
    ladder(m, mt, 4.3, 0, h, lean=0.45, w=0.4)
    return Building('ak_tablets', m, w, d, h, doors=[(dx, 'open')], ladders=[4.3], walk=(x0, x1), hatch=(3.7, 2.2),
                    blocks=[(x0 + 0.45, 0.8, x1 - 2.6, 3.3)], extra=[(x0 + 0.4, -0.5, 1.4, 0)])


def ilta_house():
    """Widow Ilta's. Lime-washed, blue at the door and the shutters, and the door standing open, as it has every
    night since she took to walking. Her bed is on the roof, where it is cool. The blanket is where she left it,
    which is on the ladder."""
    w, d, h = 6.5, 3.5, 2.5
    mt = Mats(53, 1)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h)
    beam_ends(m, mt, x0 + 0.3, x1 - 0.3, 0, h - 0.42)
    blue = M('blue', 3.2, m_planks(3, 'v', knots=False))
    dx = -1.0
    m.part(); m.box(dx - 0.66, -0.08, 0, dx - 0.52, 0, 1.84, M('blue', 2.8))
    m.box(dx + 0.52, -0.08, 0, dx + 0.66, 0, 1.84, M('blue', 2.8))
    m.box(dx - 0.66, -0.1, 1.84, dx + 0.66, 0, 1.96, M('blue', 2.8))
    m.part(); m.quad((dx - 0.52, -0.02, 0), (dx + 0.52, -0.02, 0), (dx + 0.52, -0.02, 1.84), (dx - 0.52, -0.02, 1.84), mt.dark)
    m.part(); m.quad((dx - 0.5, -0.025, 0), (dx + 0.5, -0.025, 0), (dx + 0.5, -0.025, 0.9), (dx - 0.5, -0.025, 0.9), mt.glow_dim)
    m.light(dx, -0.5, 0.8, 2.6, (1.0, 0.74, 0.42), 0.5)
    # the door itself, swung right out into the street
    m.part(); m.quad((dx + 0.52, -0.04, 0), (dx + 0.98, -0.78, 0), (dx + 0.98, -0.78, 1.8), (dx + 0.52, -0.04, 1.8), blue, two=True)
    m.part(); m.box(dx - 0.7, -0.36, 0, dx + 0.7, 0, 2 * PX, mt.stone)
    shutters(m, 1.0, 0, 1.36, colour='blue', shut=False, w=0.46)
    # the ladder, and the blanket
    ladder(m, mt, 2.4, 0, h, lean=0.5, w=0.4)
    m.part(); m.quad((2.2, -0.3, 1.2), (2.6, -0.3, 1.2), (2.6, -0.16, 1.9), (2.2, -0.16, 1.9), M('red', 3.6, m_stripes(4, 'v'), ramp2='cream', soft=True), two=True)
    # the bed on the roof, empty
    m.part(); m.box(-2.4, 1.6, h, -0.6, 2.6, h + 0.26, mt.wood_h, top=M('linen', 4.4, soft=True))
    m.part(); m.box(-2.4, 1.6, h + 0.26, -2.0, 2.6, h + 0.36, M('linen', 4.8, soft=True))
    jar(m, mt, 0.3, 2.8, h, s=0.8, kind=0)
    return Building('ak_ilta', m, w, d, h, doors=[(dx, 'open')], ladders=[2.4], walk=(x0, x1),
                    blocks=[(-2.5, 1.5, -0.5, 2.9), (0.0, 2.5, 0.7, 3.2)], extra=[(dx + 0.5, -0.8, dx + 1.0, 0)])


def lamp_house():
    """The lamp-seller's. Every niche in the front of it has one of his lamps in it, and every one of them was lit
    the night the god lay down. He has not been awake to put them out, and oil was cheap that week."""
    w, d, h = 7.5, 3.5, 3.0
    mt = Mats(59, 2)
    m = Model()
    x0, x1 = -w / 2, w / 2
    shell(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h)
    beam_ends(m, mt, x0 + 0.3, x1 - 0.3, 0, h - 0.42)
    dx = 1.6
    doorway(m, mt, dx, 0, w=1.0, h=1.75, glow=True, ajar=0.36)
    k = 0
    for row, z in enumerate((0.86, 1.56, 2.2)):
        for nx in np.arange(x0 + 0.7, x1 - 0.5, 0.95):
            if abs(nx - dx) < 0.95 and z < 2.0:
                continue
            lit = hash2(k * 7 + row * 13, row * 5 + 3, 23) < 0.88
            m.part(); m.box(nx - 0.2, -0.03, z, nx + 0.2, 0, z + 0.36, mt.glow_dim if lit else mt.dark)
            m.part(); m.box(nx - 0.24, -0.07, z - PX, nx + 0.24, 0, z, mt.trim)
            m.part(); m.blob(nx, -0.05, z + 0.06, 0.09, 0.05, 0.05, mt.pot if k % 2 else mt.pot2, n=7, rings=3)
            if lit:
                m.part(); m.blob(nx + 0.07, -0.05, z + 0.14, 0.035, 0.03, 0.06, mt.glow, n=5, rings=3)
                if k % 3 == 0:
                    m.light(nx, -0.4, z + 0.2, 2.0, (1.0, 0.72, 0.38), 0.45)
            k += 1
    # a trestle of them outside, for sale
    m.part(); m.box(-2.6, -0.8, 0.5, -0.4, -0.36, 0.56, mt.wood_h, top=M('wood', 4.8))
    for sx in (-2.5, -0.5):
        m.part(); m.box(sx - PX, -0.7, 0, sx + PX, -0.5, 0.5, mt.beam)
    for q in range(6):
        m.part(); m.blob(-2.4 + q * 0.36, -0.58, 0.6, 0.09, 0.06, 0.05, mt.pot if q % 2 else mt.pot2, n=7, rings=3)
    for q in range(9):
        m.part(); m.blob(-2.6 + (q % 5) * 0.4, 1.0 + (q // 5) * 0.5, h + 0.05, 0.1, 0.07, 0.05, M('clay', 3.4), n=6, rings=3, seed=q)
    return Building('ak_lamps', m, w, d, h, doors=[(dx, 'lit')], leaves={0: ('plain', 1.0, 1.75, 2)}, extra=[(-2.7, -0.85, -0.3, 0)])


# ------------------------------------------------------------------ what stands in the yards
def fig_tree(seed=0, size=1.25):
    """A fig, forty years old: a grey trunk that forks low, a wide dark head, and the fruit showing in it."""
    r = rnd(seed); m = Model()
    bark = M('stone', 3.6, m_mottle(5, 0.4))
    leaf_ = M('green', 3.0, m_clumps(6), soft=True)
    s = size
    m.part()
    m.limb([(0, 0.3, 0), (0.05, 0.3, 0.45 * s), (-0.1, 0.32, 0.9 * s)], [0.24 * s, 0.2 * s, 0.14 * s], bark, n=7)
    m.limb([(0.03, 0.3, 0.4 * s), (-0.6 * s, 0.3, 1.0 * s), (-1.0 * s, 0.3, 1.3 * s)], [0.15 * s, 0.1 * s, 0.05 * s], bark, n=6)
    m.limb([(0.05, 0.3, 0.45 * s), (0.6 * s, 0.34, 1.05 * s), (1.05 * s, 0.3, 1.35 * s)], [0.14 * s, 0.1 * s, 0.05 * s], bark, n=6)
    m.part()
    n = 13
    for i in range(n):
        a_ = 2 * math.pi * i / n + r.uniform(-0.2, 0.2)
        rad = r.uniform(0.7, 1.25) * s
        cx = math.cos(a_) * rad; cy = 0.35 + math.sin(a_) * rad * 0.5
        cz = (1.6 + r.uniform(-0.15, 0.3) - 0.12 * rad) * s
        rr = r.uniform(0.46, 0.66) * s
        m.blob(cx, cy, cz, rr, rr * 0.85, rr * 0.78, leaf_, seed=seed * 7 + i, bump=0.14, n=9, rings=5)
    for i in range(4):
        m.blob(r.uniform(-0.5, 0.5) * s, 0.35, (1.95 + r.uniform(0, 0.25)) * s, 0.62 * s, 0.5 * s, 0.5 * s, leaf_, seed=seed * 7 + 31 + i, bump=0.14, n=9, rings=5)
    m.part()
    fig = M('fig', 3.2, soft=True)
    for i in range(16):
        a_ = r.uniform(0, 2 * math.pi); rad = r.uniform(0.3, 1.2) * s
        m.blob(math.cos(a_) * rad, 0.05 + abs(math.sin(a_)) * 0.1, (1.1 + r.uniform(0, 0.9)) * s, 0.06, 0.05, 0.07, fig, n=5, rings=3, seed=i)
    return m


def pell(seed=0):
    """What the watch hits instead of each other: a post as thick as a man, bound with rope where a man is softest,
    with an old shield nailed to it."""
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.cyl(0, 0.2, 0, 1.5, 0.17, M('wood', 3.8, m_planks(3, 'v')), n=9, cap=M('wood', 4.6))
    m.part(); m.cyl(0, 0.2, 0.62, 1.0, 0.19, M('straw', 4.0, m_stripes(2, 'u')), n=9)
    m.part(); m.box(-0.5, 0.17, 1.14, 0.5, 0.23, 1.24, M('wood', 4.2))
    m.part(); m.face([(-0.42 + 0.2 * math.cos(a), 1.02 + 0.2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)], 0.14, M('bronze', 3.8, m_mottle(3, 0.5)))
    m.part()
    for z in (0.36, 0.5, 1.32):                              # where it has been hit
        m.box(-0.19, 0.0, z, 0.19, 0.03, z + PX, M('wood', 2.4))
    return m


def butt(seed=0):
    """A target of coiled straw on three legs. There are arrows in it. There are more in the wall behind it."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for a in (-0.4, 0.4):
        m.beam((a, 0.25, 0), (a * 0.5, 0.3, 1.2), 1.2 * PX, mt.beam)
    m.beam((0, 0.7, 0), (0, 0.34, 1.2), 1.2 * PX, mt.beam)
    for k, (rad, col, tone) in enumerate(((0.52, 'straw', 4.2), (0.36, 'red', 3.4), (0.2, 'straw', 4.6), (0.08, 'red', 3.6))):
        m.part(); m.face([(rad * math.cos(a), 0.86 + rad * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)], 0.2 - 0.01 * k, M(col, tone, m_stripes(2, 'u') if col == 'straw' else None, soft=True))
    m.part()
    for (ax, az) in ((0.3, 1.1), (-0.34, 0.66), (0.1, 0.5)):
        m.beam((ax, 0.16, az), (ax + 0.05, -0.2, az + 0.06), 0.5 * PX, M('wood', 4.8))
        m.box(ax + 0.03, -0.24, az + 0.03, ax + 0.07, -0.18, az + 0.1, M('linen', 4.8))
    return m


def tortoise(seed=0):
    """A tortoise. It was not asleep before, it is not asleep now, and nobody has ever been able to tell."""
    m = Model()
    m.part(); m.blob(0, 0.22, 0.12, 0.2, 0.16, 0.12, M('olive', 3.2, m_ashlar(4, 3)), n=9, rings=4)
    m.part()
    for (lx, ly) in ((-0.14, 0.12), (0.14, 0.12), (-0.14, 0.32), (0.14, 0.32)):
        m.blob(lx, ly, 0.04, 0.05, 0.05, 0.04, M('olive', 2.4), n=5, rings=3)
    m.part(); m.blob(0.22, 0.2, 0.1, 0.06, 0.05, 0.05, M('olive', 2.8), n=6, rings=3)
    return m


def rules_stone():
    """The rules of the night watch, cut in a slab let into the wall by the door."""
    m = Model()
    m.part(); m.box(-0.45, 0, 0.5, 0.45, 0.08, 1.7, M('sandstone', 4.2, town.m_cuneiform(4)), top=M('sandstone', 4.8))
    m.part(); m.box(-0.5, -0.02, 0.44, 0.5, 0.1, 0.5, M('sandstone', 3.6))
    return m


ALL = [('bakery', bakery), ('tax office', tax_office), ('oracle', oracle_house), ('pottery', pottery), ('beer house', beer_house),
       ('weavers', weavers), ('net loft', net_loft), ('goat house', goat_house), ('watch house', watch_house),
       ('merchant', merchant_house), ('tablet house', tablet_house), ('sleepwalker', ilta_house), ('lamp seller', lamp_house)]
