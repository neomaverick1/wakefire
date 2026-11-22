"""The Hill of Sleepers: the houses of the dead, their mounds and markers, the front of the king's
tomb and the things inside it. Built the way everything else is: real shapes, lit by the moon."""
import math
import numpy as np
from forge import Model, Mat, M, RAMPS, hash2, fbm, m_brick, m_ashlar, m_mottle, m_stripes, m_planks, m_glazed
from town import PX, rnd, MT, merlons, m_rosettes, m_chevrons, m_niches, m_cuneiform, m_rings

GHOST = (0.45, 1.0, 0.85)


def _arc(cx, cz, rx, rz, n=9, a0=0.0, a1=math.pi):
    return [(cx + math.cos(a) * rx, cz + math.sin(a) * rz) for a in np.linspace(a0, a1, n)]


def _disc(m, x, y, z, r, mat, n=10):
    """A round plate on a south-facing wall."""
    m.face([(x + math.cos(a) * r, z + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)], y, mat, two=True)


def _crescent(m, x, y, z, r, mat, thick=0.42, n=9):
    """A moon with its horns up, flat against the south."""
    a = np.linspace(math.radians(200), math.radians(340), n)
    outer = [(x + math.cos(t) * r, z + math.sin(t) * r) for t in a]
    inner = [(x + math.cos(t) * r * 0.98, z + r * thick + math.sin(t) * r * (1 - thick * 0.2)) for t in a]
    for i in range(n - 1):
        m.quad((outer[i][0], y, outer[i][1]), (outer[i + 1][0], y, outer[i + 1][1]), (inner[i + 1][0], y, inner[i + 1][1]), (inner[i][0], y, inner[i][1]), mat, two=True)


def _door(m, dx, y, w=0.56, h=1.02, frame='sandstone', lamp=False, pot=True, seed=0):
    """A false door for a spirit to come and go by, its slab for offerings, what was last left on it."""
    fr = M(frame, 4.4, m_mottle(7, 0.3))
    m.part(); m.box(dx - w / 2 - 0.14, y - 0.06, 0.0, dx - w / 2, y + 0.1, h + 0.06, fr)
    m.box(dx + w / 2, y - 0.06, 0.0, dx + w / 2 + 0.14, y + 0.1, h + 0.06, fr)
    m.part(); m.box(dx - w / 2 - 0.22, y - 0.1, h + 0.06, dx + w / 2 + 0.22, y + 0.1, h + 0.22, M(frame, 4.9))
    m.part(); m.quad((dx - w / 2, y - 0.02, 0), (dx + w / 2, y - 0.02, 0), (dx + w / 2, y - 0.02, h + 0.06), (dx - w / 2, y - 0.02, h + 0.06), M('dark', 1.0))
    m.part(); m.box(dx - 0.5, y - 0.62, 0, dx + 0.5, y - 0.1, 0.1, M(frame, 4.0, m_mottle(7, 0.3)), top=M(frame, 4.7, m_mottle(7, 0.25)))
    if pot:
        m.part(); m.turned(dx - 0.22, y - 0.36, [(0.1, 0.1), (0.14, 0.18), (0.1, 0.24)], M('clay', 4.3), n=8, cap=M('dark', 1.8))
    if lamp:
        m.part(); m.turned(dx + 0.24, y - 0.36, [(0.07, 0.1), (0.11, 0.16)], M('bronze', 4.2), n=8, cap=M('bronze', 3.4))
        m.part(); m.blob(dx + 0.24, y - 0.36, 0.26, 0.055, 0.055, 0.1, Mat(RAMPS['ghost'], 3.8, glow=True), n=6, rings=4)
        m.light(dx + 0.24, y - 0.36, 0.3, 2.4, GHOST, 0.5)


def tomb_house(w=5.0, d=3.0, h=1.6, seed=0, style=None, lamp=False):
    """A house for someone dead. Three kinds stand on the hill: a brick vault with a round gable
    and a moon let into it, a flat bench with a toothed parapet, and a small stepped tower for
    someone who wanted the neighbours to look up."""
    r = rnd(seed); m = Model()
    style = style or ('vault', 'flat', 'step')[seed % 3]
    niche = M('tomb', 4.25, m_niches(6, 3))
    plain = M('tomb', 4.0, m_brick(8, 4, jitter=0.8))
    roof = M('tomb', 4.9, m_mottle(12, 0.4, specks=0.012, speck_t=-1.0))
    pale = M('tomb', 5.5)
    x0, x1 = -w / 2, w / 2
    bt = 0.16
    dx = float(r.uniform(-0.3, 0.3)) if style != 'step' else 0.0
    m.part(); m.box(x0, 0, 0, x1, d, 0.3, plain, top=roof)                                      # the foot
    xa, xb, ya, yb = x0 + 0.1, x1 - 0.1, 0.12, d - 0.1
    if style == 'step':
        tiers = ((0.0, 0.3, 0.3 + h * 0.5), (0.42, 0.3 + h * 0.5, 0.3 + h * 0.86), (0.8, 0.3 + h * 0.86, 0.3 + h * 1.16))
        for k, (ins, z0, z1) in enumerate(tiers):
            m.part(); m.box(xa + ins, ya + ins, z0, xb - ins, yb - ins * 0.6, z1, niche if k < 2 else M('lapis', 3.7, m_glazed(8, 4)), top=roof)
            m.part(); m.box(xa + ins - PX, ya + ins - PX, z1 - PX, xb - ins + PX, ya + ins + PX, z1, pale if k < 2 else M('gold', 4.2))
        m.part(); merlons(m, M('tomb', 5.0), xa + 0.84, xb - 0.84, ya + 0.86, ya + 1.0, tiers[2][2], mw=0.22, mh=0.16)
        _door(m, dx, ya, lamp=lamp, seed=seed, h=min(1.02, h * 0.5 + 0.12))
        return m
    top = 0.3 + h
    m.part()
    m.quad((xa, ya, 0.3), (xb, ya, 0.3), (xb - bt, ya + bt, top), (xa + bt, ya + bt, top), niche)                       # the front, leaning back
    if style == 'flat':
        m.quad((xa + bt, ya + bt, top), (xb - bt, ya + bt, top), (xb - bt, yb, top), (xa + bt, yb, top), roof)
        m.part(); m.box(xa + bt - PX, ya + bt - PX, top, xb - bt + PX, ya + bt + 2 * PX, top + PX, pale)
        m.part(); merlons(m, M('tomb', 5.1), xa + bt, xb - bt, ya + bt, ya + bt + 0.14, top + PX, mw=0.26, mh=0.2)
        m.part()                                                                                                       # a low wall round the roof
        for (ax, ay, bx, by) in ((xa + bt, ya + bt, xa + bt + 0.12, yb), (xb - bt - 0.12, ya + bt, xb - bt, yb), (xa + bt, yb - 0.12, xb - bt, yb)):
            m.box(ax, ay, top, bx, by, top + 0.14, M('tomb', 4.5), top=M('tomb', 5.2))
        m.part(); m.box(-0.5 + dx * 0.5, ya + 1.0, top, 0.5 + dx * 0.5, min(yb - 0.4, ya + 1.9), top + 0.1, M('tomb', 4.4), top=M('tomb', 5.3, m_mottle(6, 0.3)))
        m.part(); m.blob(xb - bt - 0.5, yb - 0.5, top, 0.42, 0.34, 0.1, M('tomb', 5.3, m_mottle(5, 0.3)), seed=seed, n=8, rings=3)      # drifted dust
    else:
        # a barrel of brick from front to back, and the round gable it ends in
        R = (xb - xa) / 2 - bt; rz = min(0.95, R * 0.42); cx = (xa + xb) / 2
        y_f, y_b = ya + bt, yb
        ang = np.linspace(math.pi, 0, 11)
        grid = [[(cx + math.cos(a) * R, yy, top + math.sin(a) * rz) for a in ang] for yy in np.linspace(y_f, y_b, 4)]
        m.sheet(grid, M('tomb', 4.7, m_brick(8, 4, -0.8, 0.8, keep=0.75)), two=False)
        m.part(); m.face([(cx - R, top), (cx + R, top)] + _arc(cx, top, R, rz, 11)[1:-1], y_f, M('tomb', 4.5, m_brick(8, 4, -0.9, 0.7)))
        m.part()
        arc_o = _arc(cx, top, R + 0.02, rz + 0.02, 11); arc_i = _arc(cx, top, R - 0.14, rz - 0.12, 11)
        for i in range(10):
            m.quad((arc_o[i][0], y_f - 0.02, arc_o[i][1]), (arc_o[i + 1][0], y_f - 0.02, arc_o[i + 1][1]), (arc_i[i + 1][0], y_f - 0.02, arc_i[i + 1][1]), (arc_i[i][0], y_f - 0.02, arc_i[i][1]), pale, two=True)
        m.part(); m.box(xa + bt - PX, y_f - PX, top - PX, xb - bt + PX, y_f + PX, top + PX, pale)
        m.part(); _disc(m, cx, y_f - 0.03, top + rz * 0.46, 0.2, M('lapis', 3.6), 10)
        m.part(); _crescent(m, cx, y_f - 0.04, top + rz * 0.46, 0.16, M('gold', 4.4), thick=0.5, n=7)
    _door(m, dx, ya, lamp=lamp, seed=seed)
    return m


def tumulus(r=2.2, seed=0, lamp=False):
    """A round barrow: a drum of dressed stone, the earth heaped on it gone to dry grass, a stone
    passage into the south side and a marker on the crown."""
    rr = rnd(seed); m = Model()
    stone = M('stone', 3.9, m_ashlar(12, 6))
    earth = M('tomb', 4.5, m_mottle(9, 0.55, specks=0.03, speck_t=1.0))
    m.part(); m.turned(0, r, [(r, 0.0), (r, 0.6)], stone, n=22)
    m.part(); m.turned(0, r, [(r + 0.06, 0.6), (r + 0.06, 0.72)], M('stone', 4.7, m_mottle(6, 0.3)), n=22, cap=M('tomb', 4.2))
    m.part(); m.blob(0, r, 0.72, r * 0.94, r * 0.94, r * 0.52, earth, seed=seed, bump=0.03, n=18, rings=8)
    crown = 0.72 + r * 0.52
    m.part(); m.turned(0, r, [(0.14, crown - 0.04), (0.16, crown + 0.2), (0.07, crown + 0.42)], M('stone', 4.6, m_mottle(4, 0.3)), n=8, cap=M('stone', 5.0))
    # the passage
    side = M('stone', 4.1, m_ashlar(10, 5))
    for sgn in (-1, 1):
        m.part(); m.box(sgn * 0.5 - 0.12, -0.5, 0, sgn * 0.5 + 0.12, 0.3, 0.5, side, top=M('stone', 4.8))
        m.part(); m.box(sgn * 0.5 - 0.14, 0.0, 0.0, sgn * 0.5 + 0.14, 0.34, 1.0, side, top=M('stone', 4.8))
    m.part(); m.box(-0.74, -0.04, 1.0, 0.74, 0.36, 1.24, M('stone', 4.0, m_mottle(6, 0.3)), top=M('stone', 4.5))
    m.part(); m.quad((-0.38, 0.02, 0), (0.38, 0.02, 0), (0.38, 0.02, 1.0), (-0.38, 0.02, 1.0), M('dark', 1.0))
    m.part(); m.box(-0.38, -0.5, 0, 0.38, 0.0, 0.05, M('stone', 3.6), top=M('stone', 4.3, m_mottle(6, 0.3)))
    if lamp:
        m.part(); m.turned(0.52, -0.62, [(0.08, 0.0), (0.12, 0.08)], M('bronze', 4.2), n=8, cap=M('bronze', 3.4))
        m.part(); m.blob(0.52, -0.62, 0.18, 0.055, 0.055, 0.1, Mat(RAMPS['ghost'], 3.8, glow=True), n=6, rings=4)
        m.light(0.52, -0.62, 0.3, 2.4, GHOST, 0.5)
    return m


def grave_mound(seed=0):
    """Where someone ordinary lies: a long heap of earth and a stone, a stake or a pot at its head."""
    r = rnd(seed); m = Model()
    earth = M('tomb', 3.7 + float(r.uniform(-0.2, 0.3)), m_mottle(5, 0.5, specks=0.03, speck_t=1.0))
    ln = float(r.uniform(0.4, 0.48)); wd = float(r.uniform(0.25, 0.31))
    m.part(); m.blob(0, ln, 0.0, wd, ln, 0.15, earth, seed=seed, bump=0.05, n=10, rings=5)
    m.part()
    for i, a in enumerate((0.5, 2.2, 3.9, 5.4)):
        if r.random() < 0.3: continue
        m.blob(math.cos(a) * (wd + 0.02), ln + math.sin(a) * (ln + 0.02), 0.02, 0.055, 0.05, 0.045, M('stone', 3.8 + float(r.uniform(-0.3, 0.5))), seed=seed + i, bump=0.25, n=5, rings=3, facet=True)
    k = seed % 4
    hy = 2 * ln + 0.06
    if k in (0, 3):
        hh = 0.34 + 0.1 * (seed % 3)
        m.part(); m.box(-0.13, hy, 0, 0.13, hy + 0.09, hh, M('stone', 4.1, m_cuneiform(4)), top=M('stone', 4.7))
        m.part(); m.limb([(0, hy, hh), (0, hy + 0.09, hh)], [0.13, 0.13], M('stone', 4.3), n=8)
    elif k == 1:
        m.part(); m.turned(0.02, hy + 0.04, [(0.07, 0.0), (0.11, 0.1), (0.08, 0.22), (0.1, 0.25)], M('clay', 4.2), n=8, cap=M('dark', 1.8))
    else:
        m.part(); m.limb([(-0.02, hy + 0.04, 0), (0.03, hy + 0.04, 0.44)], [0.035, 0.028], M('trunk', 3.6), n=5)
        m.part(); m.beam((-0.1, hy + 0.04, 0.32), (0.15, hy + 0.04, 0.35), 0.045, M('trunk', 4.0))
    return m


def moon_standard(h=2.8):
    """A standard of the moon god: a bronze pole on a stone foot, the crescent with the sun's disc
    lying in it, two red tassels that have not moved in four hundred years."""
    m = Model()
    brz = M('bronze', 4.1, gloss=0.03); gold = M('gold', 4.5, gloss=0.03)
    m.part(); m.box(-0.22, 0.06, 0, 0.22, 0.42, 0.2, M('stone', 3.8, m_mottle(5, 0.3)), top=M('stone', 4.6))
    m.part(); m.limb([(0, 0.24, 0.2), (0, 0.24, h)], [0.045, 0.035], brz, n=6)
    m.part(); m.box(-0.46, 0.21, h - 0.12, 0.46, 0.27, h - 0.05, brz)
    for sgn in (-1, 1):
        m.part(); m.box(sgn * 0.4 - 0.06, 0.22, h - 0.62, sgn * 0.4 + 0.06, 0.26, h - 0.12, M('red', 3.3, m_stripes(2, 'v')))
        m.part(); m.box(sgn * 0.4 - 0.08, 0.215, h - 0.72, sgn * 0.4 + 0.08, 0.265, h - 0.62, gold)
    m.part(); _crescent(m, 0, 0.24, h + 0.46, 0.5, gold, thick=0.5, n=13)
    m.part(); _disc(m, 0, 0.235, h + 0.44, 0.15, M('gold', 5.0), 9)
    return m


def urn(seed=0):
    """Jars the dead were given for the journey: standing, or on their sides and long since empty."""
    r = rnd(seed); m = Model()
    k = seed % 4
    clay = M(('clay', 'brick', 'mud', 'clay')[k], 4.2, m_mottle(5, 0.3))
    if k == 0:
        m.part(); m.turned(0, 0.26, [(0.1, 0.0), (0.22, 0.2), (0.24, 0.42), (0.14, 0.62), (0.1, 0.7), (0.14, 0.76)], clay, n=10, cap=M('dark', 1.6))
        m.part(); m.turned(0, 0.26, [(0.245, 0.36), (0.245, 0.42)], M('dark', 2.6), n=10)
    elif k == 1:
        m.part(); m.turned(-0.2, 0.3, [(0.1, 0.0), (0.2, 0.14), (0.18, 0.34), (0.1, 0.42), (0.13, 0.46)], clay, n=9, cap=M('dark', 1.6))
        m.part(); m.turned(0.22, 0.2, [(0.07, 0.0), (0.13, 0.1), (0.1, 0.26), (0.08, 0.3)], M('brick', 4.4), n=8, cap=M('dark', 1.6))
    elif k == 2:
        m.part(); m.limb([(-0.3, 0.3, 0.17), (-0.08, 0.3, 0.2), (0.14, 0.3, 0.18), (0.3, 0.3, 0.12)], [0.1, 0.19, 0.17, 0.09], clay, n=9, cap=False)
        m.part(); m.blob(0.36, 0.26, 0.04, 0.12, 0.1, 0.04, M('clay', 3.4), seed=seed, bump=0.3, n=6, rings=3, facet=True)
    else:
        m.part(); m.turned(0, 0.28, [(0.16, 0.0), (0.26, 0.12), (0.24, 0.22)], clay, n=10, cap=M('dark', 1.4))
        for i in range(3):
            a = float(r.uniform(0, 6.28))
            m.part(); m.blob(math.cos(a) * 0.36, 0.28 + math.sin(a) * 0.2, 0.03, 0.1, 0.07, 0.04, M('clay', 3.6 + 0.4 * i), seed=seed + i, bump=0.3, n=5, rings=3, facet=True)
    return m


def bones(seed=0):
    """What is left where nobody was buried properly."""
    r = rnd(seed); m = Model()
    bone = M('bone', 5.0)
    m.part()
    for i in range(int(r.integers(3, 6))):
        x, y = float(r.uniform(-0.4, 0.4)), float(r.uniform(0.1, 0.6)); a = float(r.uniform(0, math.pi))
        ln = float(r.uniform(0.16, 0.3))
        m.limb([(x - math.cos(a) * ln, y - math.sin(a) * ln * 0.6, 0.03), (x + math.cos(a) * ln, y + math.sin(a) * ln * 0.6, 0.03)], [0.03, 0.03], bone, n=4)
        m.part()
    for i in range(3):
        m.limb([(-0.14 + 0.02 * i, 0.3 + 0.1 * i, 0.02), (0.0, 0.33 + 0.1 * i, 0.16), (0.14 - 0.02 * i, 0.3 + 0.1 * i, 0.02)], [0.02, 0.02, 0.02], M('bone', 4.5), n=4, cap=False)
    return m


def thorn(seed=0):
    """A thorn bush with nothing on it."""
    r = rnd(seed); m = Model()
    for i in range(7):
        a = float(r.uniform(0.25, math.pi - 0.25)); ln = float(r.uniform(0.3, 0.62))
        tip = (math.cos(a) * ln, 0.24 + float(r.uniform(-0.12, 0.12)), math.sin(a) * ln * 0.9 + 0.05)
        mid = (tip[0] * 0.5 + float(r.uniform(-0.08, 0.08)), 0.24, tip[2] * 0.62)
        m.part(); m.limb([(0, 0.24, 0), mid, tip], [0.04, 0.028, 0.008], M('trunk', 3.0 + float(r.uniform(0, 1.2))), n=4)
    return m


def broken_column(h=1.3, seed=0, fallen=True):
    """A column that held a roof up once: the stump of it, and the next drum lying where it came down."""
    m = Model()
    st = M('alabaster', 4.3, m_stripes(3, 'u'))
    m.part(); m.turned(0, 0.34, [(0.34, 0.0), (0.34, 0.14)], M('stone', 4.0, m_mottle(5, 0.3)), n=12, cap=M('stone', 4.6))
    m.part(); m.turned(0, 0.34, [(0.26, 0.14), (0.24, h)], st, n=12, cap=M('alabaster', 3.2, m_mottle(3, 0.8)))
    if fallen:
        m.part(); m.limb([(0.5, 0.18, 0.2), (1.1, 0.34, 0.2)], [0.22, 0.21], st, n=10)
        m.part(); m.blob(0.36, 0.06, 0.05, 0.1, 0.08, 0.06, M('alabaster', 3.8), seed=seed, bump=0.3, n=5, rings=3, facet=True)
    return m


def gate_post(h=2.4):
    """One post of a gate onto the hill: squared stone, a band of writing, a bowl of the dead's light on top."""
    m = Model()
    st = M('stone', 4.0, m_ashlar(10, 5))
    m.part(); m.box(-0.5, 0.0, 0, 0.5, 0.9, 0.3, M('stone', 3.5), top=M('stone', 4.4))
    m.part(); m.box(-0.4, 0.08, 0.3, 0.4, 0.82, h, st, top=M('stone', 4.8, m_mottle(6, 0.3)))
    m.part(); m.box(-0.4 - PX, 0.08 - PX, h * 0.56, 0.4 + PX, 0.82, h * 0.56 + 0.3, M('stone', 4.5, m_cuneiform(5)))
    m.part(); m.box(-0.48, 0.0, h, 0.48, 0.9, h + 0.14, M('stone', 4.4), top=M('stone', 5.0))
    m.part(); m.turned(0, 0.45, [(0.12, h + 0.14), (0.26, h + 0.3), (0.28, h + 0.34)], M('bronze', 4.0, gloss=0.03), n=10, cap=M('bronze', 3.0))
    m.part(); m.blob(0, 0.45, h + 0.44, 0.15, 0.12, 0.2, Mat(RAMPS['ghost'], 3.6, glow=True), n=7, rings=5)
    m.light(0, 0.45, h + 0.4, 3.4, GHOST, 0.7)
    return m


def stone_seat():
    m = Model()
    m.part(); m.box(-0.3, 0.08, 0, 0.3, 0.56, 0.44, M('sandstone', 3.9, m_mottle(6, 0.3)), top=M('sandstone', 4.7, m_mottle(6, 0.25)))
    m.part(); m.box(-0.34, 0.04, 0.44, 0.34, 0.6, 0.52, M('sandstone', 4.3), top=M('red', 3.0, m_stripes(3, 'u')))
    return m


def spirit_bowl(frame=0):
    """A wide bronze bowl on a tripod, burning the dead's cold fire: for a king's door, not a commoner's."""
    m = Model()
    brz = M('bronze', 4.0, gloss=0.03)
    for a in (90, 210, 330):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        m.part(); m.limb([(ca * 0.3, 0.34 + sa * 0.2, 0), (ca * 0.12, 0.34 + sa * 0.08, 0.62)], [0.035, 0.03], brz, n=5)
    m.part(); m.turned(0, 0.34, [(0.1, 0.56), (0.34, 0.74), (0.38, 0.8)], brz, n=12, cap=M('dark', 1.6))
    ghost = Mat(RAMPS['ghost'], 3.2, glow=True)
    sway = (0.0, 0.05, -0.03, 0.03)[frame % 4]; tall = (0.0, 0.07, 0.02, -0.03)[frame % 4]
    m.part(); m.limb([(0, 0.34, 0.8), (sway * 0.5, 0.34, 1.04 + tall), (sway, 0.34, 1.36 + tall * 2)], [0.22, 0.15, 0.02], ghost, n=7)
    m.part(); m.limb([(-0.1, 0.33, 0.8), (-0.12 + sway, 0.33, 1.06 + tall)], [0.1, 0.02], ghost, n=5)
    m.part(); m.limb([(0.02, 0.32, 0.82), (sway * 0.4, 0.32, 1.02 + tall)], [0.1, 0.03], Mat(RAMPS['ghost'], 5.0, glow=True), n=5)
    m.light(0, 0.34, 1.0, 4.6, GHOST, 0.85)
    return m


def royal_front(w=10.0, h=4.4):
    """The front of the tomb of Kurashtar, cut and built into the top of the hill: a wall of
    buttressed stone under a frieze of blue brick, a gate tower between two columns of red and
    white cone mosaic, and over the doorway the sun coming up in gold, which it has not done since."""
    m = Model()
    stone = M('sandstone', 4.1, m_niches(10, 6))
    ash = M('sandstone', 4.3, m_ashlar(16, 8))
    top = M('sandstone', 4.9, m_mottle(12, 0.35))
    gold = M('gold', 4.4, gloss=0.03); lap = M('lapis', 3.6, m_glazed(8, 4))
    foot = M('basalt', 3.4, m_ashlar(16, 8))
    hw = w / 2; gw = 2.9
    # the wings
    m.part(); m.box(-hw, 0.5, 0, hw, 1.4, h - 0.5, stone, top=top)
    m.part(); m.box(-hw, 0.5 - PX, 0, hw, 1.4, 0.55, foot, top=M('basalt', 4.2))
    m.part(); m.box(-hw, 0.5 - PX, h - 1.2, hw, 1.4, h - 0.72, M('lapis', 3.9, m_rosettes(16), ramp2='gold'))
    for zz in (h - 1.22, h - 0.72):
        m.part(); m.box(-hw, 0.5 - 1.5 * PX, zz, hw, 1.4, zz + PX, gold)
    m.part(); merlons(m, M('sandstone', 4.7, m_mottle(6, 0.3)), -hw, -gw, 0.5, 0.8, h - 0.5, mw=0.42, mh=0.34, top=top)
    merlons(m, M('sandstone', 4.7, m_mottle(6, 0.3)), gw, hw, 0.5, 0.8, h - 0.5, mw=0.42, mh=0.34, top=top)
    # the gate tower
    m.part(); m.box(-gw, 0.0, 0, gw, 1.4, h, ash, top=top)
    m.part(); m.box(-gw - PX, -PX, 0, gw + PX, 1.4, 0.55, foot, top=M('basalt', 4.2))
    m.part(); merlons(m, M('sandstone', 4.8, m_mottle(6, 0.3)), -gw, gw, 0.0, 0.3, h, mw=0.46, mh=0.4, top=top)
    m.part(); m.box(-gw - PX, -1.5 * PX, h - 0.16, gw + PX, 0.1, h, gold, top=top)
    # the recess the door stands in
    dw, dh = 2.1, 2.95
    m.part(); m.quad((-dw, -0.02, 0), (dw, -0.02, 0), (dw, -0.02, dh), (-dw, -0.02, dh), M('dark', 0.9))
    m.part()
    for sx in (-dw - 0.12, dw):
        m.box(sx, -0.06, 0, sx + 0.12, 0.0, dh + 0.12, gold)
    m.box(-dw - 0.12, -0.06, dh, dw + 0.12, 0.0, dh + 0.12, gold)
    # the sun coming up, on blue
    m.part(); m.quad((-dw - 0.12, -0.03, dh + 0.12), (dw + 0.12, -0.03, dh + 0.12), (dw + 0.12, -0.03, h - 0.22), (-dw - 0.12, -0.03, h - 0.22), lap)
    cz = dh + 0.12
    m.part(); m.face([(-0.62, cz), (0.62, cz)] + _arc(0, cz, 0.62, 0.62, 9)[1:-1], -0.05, M('gold', 5.0, gloss=0.03))
    m.part()
    for a in np.linspace(math.radians(14), math.radians(166), 7):
        ca, sa = math.cos(a), math.sin(a)
        r0, r1 = 0.74, 1.1 if abs(a - math.pi / 2) > 0.3 else 1.14
        r1 = min(r1, (h - 0.3 - cz) / max(sa, 0.2))
        wa = 0.085
        m.quad((ca * r0 - sa * wa, -0.05, cz + sa * r0 + ca * wa), (ca * r0 + sa * wa, -0.05, cz + sa * r0 - ca * wa),
               (ca * r1 + sa * wa * 0.5, -0.05, cz + sa * r1 - ca * wa * 0.5), (ca * r1 - sa * wa * 0.5, -0.05, cz + sa * r1 + ca * wa * 0.5), M('gold', 5.0), two=True)
    # the columns
    for sgn in (-1, 1):
        cxp = sgn * (gw - 0.16)
        m.part(); m.turned(cxp, -0.06, [(0.36, 0.0), (0.36, 0.5)], M('basalt', 3.8, m_mottle(5, 0.3)), n=12, cap=M('basalt', 4.4))
        m.part(); m.turned(cxp, -0.06, [(0.29, 0.5), (0.27, h - 0.62)], M('red', 3.3, m_chevrons(6, 3), ramp2='cream'), n=12)
        m.part(); m.turned(cxp, -0.06, [(0.31, h - 0.62), (0.36, h - 0.46), (0.36, h - 0.36)], gold, n=12, cap=M('gold', 3.6))
        m.part(); m.turned(cxp, -0.06, [(0.3, 1.5), (0.3, 1.62)], gold, n=12)
    # the threshold
    m.part(); m.box(-dw - 0.3, -0.7, 0, dw + 0.3, 0.0, 0.08, M('basalt', 3.4), top=M('basalt', 4.3, m_mottle(8, 0.3)))
    m.light(0, -0.4, dh + 0.6, 4.0, (1.0, 0.8, 0.42), 0.35)
    return m


def king_door(w=4.2, h=2.95, open_=False):
    """What shuts the tomb: two leaves of black stone with the king's name cut in them and a bar of
    bronze across. Open, they have gone back into the dark."""
    m = Model()
    if open_:
        m.part(); m.quad((-w / 2, 0.0, 0), (w / 2, 0.0, 0), (w / 2, 0.0, h), (-w / 2, 0.0, h), M('dark', 0.7))
        for sgn in (-1, 1):
            m.part(); m.box(min(sgn * w / 2, sgn * (w / 2 - 0.3)), 0.0, 0, max(sgn * w / 2, sgn * (w / 2 - 0.3)), 0.06, h, M('basalt', 2.6, m_cuneiform(6)))
        return m
    slab = M('basalt', 3.6, m_cuneiform(6))
    brz = M('bronze', 4.2, gloss=0.03)
    for sgn in (-1, 1):
        m.part(); m.box(min(0, sgn * w / 2), 0.0, 0, max(0, sgn * w / 2), 0.12, h, slab, top=M('basalt', 4.4))
    m.part(); m.box(-PX / 2, -0.01, 0, PX / 2, 0.0, h, M('dark', 0.8))
    m.part(); m.box(-w / 2, -0.05, h * 0.44, w / 2, 0.0, h * 0.44 + 0.2, brz)
    m.part(); m.turned(0, -0.05, [(0.26, h * 0.44 - 0.12), (0.26, h * 0.44 + 0.32)], M('gold', 4.3, gloss=0.03), n=12, squash=0.2)
    for sgn in (-1, 1):
        for zz in (0.5, h - 0.5):
            m.part(); _disc(m, sgn * w * 0.3, -0.01, zz, 0.11, brz, 8)
    return m


def sarcophagus(seed=0, open_=False):
    """A stone coffin for someone who could afford one: niches cut down its sides, a ridged lid
    banded in gold. Or the lid pushed off, and nobody in."""
    m = Model()
    st = M('alabaster', 4.0, m_niches(5, 3))
    lid = M('alabaster', 4.7, m_mottle(8, 0.3))
    gold = M('gold', 4.2, gloss=0.03)
    m.part(); m.box(-1.02, 0.06, 0, 1.02, 0.84, 0.14, M('basalt', 3.4), top=M('basalt', 4.2))
    m.part(); m.box(-0.92, 0.14, 0.14, 0.92, 0.76, 0.6, st, top=M('dark', 1.0) if open_ else lid)
    if open_:
        m.part(); m.box(-0.92, 0.14, 0.56, 0.92, 0.2, 0.6, lid); m.box(-0.92, 0.7, 0.56, 0.92, 0.76, 0.6, lid)
        m.box(-0.92, 0.14, 0.56, -0.86, 0.76, 0.6, lid); m.box(0.86, 0.14, 0.56, 0.92, 0.76, 0.6, lid)
        m.push(at=(0.3, 0.98, 0.0), rot=-9)
        m.part(); m.box(-0.96, 0.0, 0, 0.96, 0.66, 0.12, M('alabaster', 4.3), top=lid)
        m.part(); m.box(-0.9, 0.24, 0.12, 0.9, 0.42, 0.2, M('alabaster', 4.4), top=M('alabaster', 5.2))
        m.pop()
    else:
        m.part(); m.box(-0.96, 0.1, 0.6, 0.96, 0.8, 0.7, M('alabaster', 4.4), top=lid)
        m.part(); m.box(-0.9, 0.34, 0.7, 0.9, 0.56, 0.8, M('alabaster', 4.6), top=M('alabaster', 5.3))
        m.part()
        for sx in (-0.6, 0.0, 0.6):
            m.box(sx - 0.05, 0.09, 0.6, sx + 0.05, 0.81, 0.71, gold)
    return m


def treasure(seed=0):
    """What a king is buried with, heaped where the bearers put it down: coin, cups, a bronze helm,
    a jar of rings gone over, a bolt of red cloth."""
    r = rnd(seed); m = Model()
    coin = Mat(RAMPS['gold'], 3.3, m_mottle(2, 1.5))
    gold = M('gold', 4.4, gloss=0.03); brz = M('bronze', 4.2, gloss=0.03)
    m.part(); m.blob(0, 0.42, 0.0, 0.66, 0.4, 0.3, coin, seed=seed, bump=0.06, n=12, rings=6)
    m.part(); m.blob(0.42, 0.24, 0.0, 0.4, 0.24, 0.16, coin, seed=seed + 1, bump=0.06, n=10, rings=5)
    k = seed % 4
    m.part(); m.turned(-0.36, 0.2, [(0.05, 0.1), (0.035, 0.2), (0.11, 0.34), (0.12, 0.36)], gold, n=8, cap=M('dark', 1.8))                 # a cup
    m.part(); m.turned(0.16, 0.5, [(0.1, 0.24), (0.2, 0.36), (0.17, 0.52), (0.08, 0.6), (0.11, 0.64)], M('lapis', 3.8, m_stripes(3, 'v')), n=9, cap=gold)   # a blue jar
    if k in (0, 2):
        m.part(); m.blob(-0.1, 0.16, 0.2, 0.17, 0.15, 0.16, brz, n=8, rings=5)                                                             # a helm
        m.part(); m.limb([(-0.1, 0.16, 0.34), (-0.1, 0.16, 0.48)], [0.03, 0.015], gold, n=5)
    if k in (1, 2):
        m.part(); m.limb([(-0.62, 0.5, 0.1), (-0.2, 0.62, 0.14)], [0.11, 0.11], M('red', 3.4, m_stripes(3, 'v')), n=8)                    # a bolt of cloth
    if k in (0, 3):
        m.part(); m.box(0.5, 0.42, 0.0, 0.92, 0.72, 0.3, M('cedar', 3.4, m_planks(4, 'h')), top=Mat(RAMPS['gold'], 3.6, m_mottle(2, 1.5)))  # a box left open
        m.part(); m.box(0.5 - PX, 0.42 - PX, 0.22, 0.92 + PX, 0.42, 0.3, brz)
    m.part(); m.turned(0.58, 0.1, [(0.07, 0.0), (0.075, 0.03)], gold, n=8, cap=M('gold', 5.0))                                             # a dish
    return m


def throne():
    """The king's seat on its three steps: black stone, gold lions' feet, a back as tall as a door
    with the sun cut over where his head goes."""
    m = Model()
    st = M('basalt', 3.5, m_mottle(8, 0.3))
    gold = M('gold', 4.4, gloss=0.03)
    for k, (hw, y0, z0) in enumerate(((1.7, 0.0, 0.0), (1.4, 0.3, 0.16), (1.1, 0.6, 0.32))):
        m.part(); m.box(-hw, y0, z0, hw, 2.2, z0 + 0.16, M('basalt', 3.0 + 0.3 * k, m_ashlar(12, 6)), top=M('lapis' if k == 2 else 'basalt', 3.4 if k == 2 else 4.0 + 0.2 * k, m_glazed(8, 4) if k == 2 else m_mottle(8, 0.3)))
        m.part(); m.box(-hw - PX, y0 - PX, z0 + 0.16 - PX, hw + PX, y0 + PX, z0 + 0.16, gold)
    z = 0.48
    m.part(); m.box(-0.62, 1.0, z, 0.62, 1.7, z + 0.56, st, top=M('red', 3.3, m_stripes(3, 'u')))
    m.part(); m.box(-0.74, 1.66, z, 0.74, 1.86, z + 2.3, st, top=M('basalt', 4.4))
    m.part(); m.box(-0.74 - PX, 1.66 - PX, z + 2.2, 0.74 + PX, 1.86, z + 2.3, gold, top=gold)
    for sx in (-0.78, 0.6):
        m.part(); m.box(sx, 0.98, z + 0.56, sx + 0.18, 1.7, z + 0.82, st, top=gold)
        m.part(); m.box(sx, 0.94, z, sx + 0.18, 1.0, z + 0.26, gold)
    cz = z + 1.5
    m.part(); m.face([(-0.3, cz), (0.3, cz)] + _arc(0, cz, 0.3, 0.3, 7)[1:-1], 1.65, M('gold', 5.0))
    m.part()
    for a in np.linspace(math.radians(20), math.radians(160), 5):
        ca, sa = math.cos(a), math.sin(a)
        m.quad((ca * 0.36 - sa * 0.03, 1.65, cz + sa * 0.36 + ca * 0.03), (ca * 0.36 + sa * 0.03, 1.65, cz + sa * 0.36 - ca * 0.03),
               (ca * 0.56 + sa * 0.01, 1.65, cz + sa * 0.56 - ca * 0.01), (ca * 0.56 - sa * 0.01, 1.65, cz + sa * 0.56 + ca * 0.01), gold, two=True)
    return m


def sentinel_niche():
    """A niche in the wall of the tomb with a clay soldier standing in it, spear grounded, waiting to be needed."""
    m = Model()
    m.part(); m.box(-0.5, 0.0, 0, 0.5, 0.2, 1.7, M('basalt', 3.2, m_ashlar(10, 5)), top=M('basalt', 4.2))
    m.part(); m.quad((-0.34, -0.01, 0.12), (0.34, -0.01, 0.12), (0.34, -0.01, 1.5), (-0.34, -0.01, 1.5), M('dark', 1.1))
    clay = M('clay', 3.6, m_mottle(4, 0.3))
    m.part(); m.turned(0, -0.08, [(0.17, 0.12), (0.13, 0.5), (0.19, 0.86), (0.2, 1.0), (0.1, 1.06)], clay, n=8, squash=0.6)
    m.part(); m.blob(0, -0.08, 1.18, 0.12, 0.09, 0.13, M('clay', 4.0), n=7, rings=5)
    m.part(); m.turned(0, -0.08, [(0.13, 1.26), (0.03, 1.4)], M('bronze', 3.8), n=7, squash=0.7)
    m.part(); m.limb([(0.24, -0.1, 0.12), (0.24, -0.1, 1.46)], [0.02, 0.02], M('wood', 3.6), n=4)
    m.part(); m.limb([(0.24, -0.1, 1.46), (0.24, -0.1, 1.62)], [0.04, 0.005], M('bronze', 4.4), n=4)
    return m


def hill_gate(open_=False):
    """The gate to the Hill of Sleepers, in the rock above the terraces: two posts of squared stone,
    a lintel with the moon on it, bars of bronze. The lock is on this side."""
    m = Model()
    st = M('stone', 4.0, m_ashlar(10, 5))
    brz = M('bronze', 4.2, gloss=0.03); gold = M('gold', 4.5, gloss=0.03)
    for sgn in (-1, 1):
        m.part(); m.box(min(sgn * 0.82, sgn * 1.24), 0.0, 0, max(sgn * 0.82, sgn * 1.24), 0.3, 1.36, st, top=M('stone', 4.8))
    m.part(); m.box(-1.34, -0.04, 1.24, 1.34, 0.3, 1.56, M('stone', 4.3, m_mottle(6, 0.3)), top=M('stone', 4.9))
    m.part(); _crescent(m, 0, -0.05, 1.37, 0.13, gold, thick=0.5, n=7)
    m.part(); m.quad((-0.82, 0.16, 0), (0.82, 0.16, 0), (0.82, 0.16, 1.24), (-0.82, 0.16, 1.24), M('dark', 0.8))
    m.part(); m.box(-0.9, -0.3, 0, 0.9, 0.0, 0.05, M('stone', 3.6), top=M('stone', 4.4, m_mottle(6, 0.3)))
    if not open_:
        m.part()
        for i in range(9):
            x = -0.74 + i * 0.185
            m.box(x - PX / 2, 0.08, 0, x + PX / 2, 0.08 + PX, 1.24, brz if i % 2 == 0 else M('bronze', 3.3))
        m.part(); m.box(-0.82, 0.06, 0.86, 0.82, 0.13, 0.94, brz)
        m.part(); m.box(-0.82, 0.06, 0.26, 0.82, 0.13, 0.34, M('bronze', 3.5))
        m.part(); m.box(-0.12, 0.02, 0.48, 0.12, 0.08, 0.74, gold)                       # the lock
        m.part(); m.box(-0.03, 0.01, 0.54, 0.03, 0.02, 0.64, M('dark', 1.0))
    return m


# ------------------------------------------------------------------ things Azar is given
def item_hill_key():
    """The key to the hill gate: bronze, its bow a crescent."""
    m = Model()
    brz = M('bronze', 4.6, gloss=0.04)
    m.part(); m.box(-0.05, 0, 0.1, 0.05, 0.06, 0.56, brz)
    m.part(); m.box(0.05, 0, 0.12, 0.2, 0.06, 0.18, brz); m.box(0.05, 0, 0.24, 0.16, 0.06, 0.3, brz)
    m.part(); _crescent(m, 0, 0.03, 0.74, 0.2, M('gold', 4.6, gloss=0.03), thick=0.5, n=9)
    m.part(); _disc(m, 0, 0.03, 0.62, 0.06, brz, 8)
    return m


def item_dawn_horn():
    """The Dawn Horn. It is a goat's horn with a bronze mouthpiece and two gold bands."""
    m = Model()
    horn = M('bone', 4.4, m_stripes(2, 'v'))
    pts = [(-0.34, 0.03, 0.16), (-0.2, 0.03, 0.12), (0.0, 0.03, 0.16), (0.18, 0.03, 0.3), (0.3, 0.03, 0.5), (0.34, 0.03, 0.72)]
    rad = [0.03, 0.05, 0.075, 0.1, 0.125, 0.15]
    m.part(); m.limb(pts, rad, horn, n=8, cap=False)
    m.part(); m.limb([pts[0], (-0.42, 0.03, 0.2)], [0.04, 0.03], M('bronze', 4.4, gloss=0.03), n=6)
    for i in (2, 4):
        m.part(); m.limb([pts[i], tuple(np.add(pts[i], np.subtract(pts[i + 1], pts[i]) * 0.2))], [rad[i] + 0.014, rad[i] + 0.02], M('gold', 4.6, gloss=0.03), n=8, cap=False)
    m.part(); _disc(m, 0.34, 0.0, 0.74, 0.12, M('dark', 1.4), 8)
    return m


def item_figs():
    """Figs in a twist of cloth. Forty years on a hill has not hurt them, which says something about the hill."""
    m = Model()
    m.part(); m.blob(0, 0.2, 0.06, 0.36, 0.26, 0.1, M('linen', 4.4, soft=True), n=10, rings=4)
    for i, (x, y, z) in enumerate(((-0.14, 0.2, 0.2), (0.14, 0.22, 0.2), (0.0, 0.14, 0.3))):
        m.part(); m.blob(x, y, z, 0.14, 0.13, 0.16, M('fig', 3.2 + 0.4 * i), n=8, rings=5)
        m.part(); m.limb([(x, y, z + 0.15), (x + 0.02, y, z + 0.24)], [0.03, 0.015], M('green', 3.4), n=4)
    return m


def item_crown():
    """The crown of Kurashtar: a tall cap of gold with a blue band and horns turned in, the way gods and kings wear them."""
    m = Model()
    gold = M('gold', 4.5, gloss=0.03)
    m.push(scale=0.8)
    m.part(); m.turned(0, 0.2, [(0.26, 0.08), (0.27, 0.3), (0.24, 0.52), (0.14, 0.66), (0.04, 0.7)], gold, n=12, cap=gold)
    m.part(); m.turned(0, 0.2, [(0.285, 0.08), (0.285, 0.2)], M('lapis', 3.8), n=12)
    for sgn in (-1, 1):
        m.part(); m.limb([(sgn * 0.27, 0.14, 0.22), (sgn * 0.36, 0.14, 0.4), (sgn * 0.22, 0.14, 0.56)], [0.05, 0.04, 0.012], M('bone', 5.0), n=5)
    m.pop()
    return m


def item_bolt(frame=0):
    """A handful of the dead's cold fire, in flight."""
    m = Model()
    g = Mat(RAMPS['ghost'], 3.4, glow=True)
    w = (0.0, 0.04, -0.03)[frame % 3]
    m.part(); m.blob(0, 0.2, 0.3, 0.2 + w, 0.18, 0.2 - w, g, n=8, rings=5)
    m.part(); m.blob(0.02, 0.18, 0.32, 0.1, 0.1, 0.1, Mat(RAMPS['ghost'], 5.2, glow=True), n=6, rings=4)
    m.part(); m.limb([(0, 0.2, 0.46), (w * 2, 0.2, 0.62 + w)], [0.09, 0.01], g, n=5)
    return m
