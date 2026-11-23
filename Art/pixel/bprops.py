"""What stands in the Generals' Barrow: two armies' worth of mud brick, red on one side and blue
on the other, a sentry's bench, the cold lamps of the dead; and the few things only its dream
has, which are made of moonlight and come away in the hand."""
import math
import numpy as np
import town
from forge import Model, M, Mat, RAMPS, m_mottle, m_planks, m_brick, m_ashlar

PX = 1 / 16.0
MOON = ['#263a78', '#3e5ca8', '#6a8cd2', '#9cbcee', '#cfe0ff', '#f4f8ff']        # moonlight you can pick up
COLD = ['#0c1650', '#1a329a', '#2c5cd8', '#5c98ff', '#a8d0ff', '#ecf5ff']        # the blue fire
EMBLEM = {'red': 'gold', 'blue': 'limewash'}


def moon(base=4.0, marks=None):
    return Mat(MOON, base, marks, glow=True)


# ------------------------------------------------------------------ the walls
def _brick():
    return (M('mud', 3.5, m_brick(8, 4)), M('mud', 3.9, m_mottle(8, 0.4)), M('mud', 3.0, m_brick(8, 4)))


def partition(length, h=1.2, d=0.5):
    """A low wall of mud brick, running east from the origin."""
    m = Model()
    body, top, foot = _brick()
    m.part(); m.box(0, 0, 0, length, d, h, body, top=top)
    m.part(); m.box(0, -PX, 0, length, d, 0.28, foot, top=top)
    return m


def partition_ns(depth, wd=0.5, h=1.2):
    m = Model()
    body, top, foot = _brick()
    m.part(); m.box(0, 0, 0, wd, depth, h, body, top=top)
    m.part(); m.box(-PX, -PX, 0, wd + PX, depth, 0.28, foot, top=top)
    return m


def pier(h=1.9):
    """A square pier of mud brick with a band of each army's colour: what holds the mound up."""
    m = Model()
    m.part(); m.box(-0.42, 0.0, 0, 0.42, 0.62, h, M('mud', 3.6, m_brick(8, 4)), top=M('mud', 4.2, m_mottle(8, 0.3)))
    m.part(); m.box(-0.48, -0.05, 0, 0.48, 0.67, 0.28, M('mud', 3.2, m_brick(8, 4)), top=M('mud', 4.3))
    m.part(); m.box(-0.44, -0.02, h - 0.5, 0.0, 0.64, h - 0.38, M('red', 3.4))
    m.part(); m.box(0.0, -0.02, h - 0.5, 0.44, 0.64, h - 0.38, M('blue', 3.4))
    m.part(); m.box(-0.48, -0.05, h - 0.16, 0.48, 0.67, h, M('mud', 4.0), top=M('mud', 4.4, m_mottle(8, 0.3)))
    return m


def _disc(m, cx, y, cz, r, mat, n=12):
    m.face([(cx + math.cos(a) * r, cz + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)], y, mat)


def wall_shield(m, x, z, side, y=-0.03):
    """A soldier's round shield hung on the wall, in his general's colour, a boss in the middle."""
    m.part(); _disc(m, x, y, z, 0.36, M('bronze', 3.2))
    m.part(); _disc(m, x, y - 0.01, z, 0.31, M(side, 3.6, m_mottle(4, 0.3)))
    m.part(); _disc(m, x, y - 0.02, z, 0.09, M(EMBLEM[side], 4.2, gloss=0.03), n=8)


# ------------------------------------------------------------------ the two camps
def standard(side, down=False):
    """A general's standard on its pole in a stone socket: red with a gold sun, or blue with a silver
    moon. down: hauled down, the cloth in a heap at the foot of the pole."""
    m = Model()
    st = M('stone', 3.8, m_mottle(5, 0.3))
    m.part(); m.box(-0.24, 0.0, 0, 0.24, 0.42, 0.22, st, top=M('stone', 4.5))
    m.part(); m.turned(0, 0.2, [(0.05, 0.2), (0.042, 2.5), (0.03, 2.62)], M('cedar', 4.0), n=6)
    em = M(EMBLEM[side], 4.4, gloss=0.03)
    if side == 'red':
        m.part(); _disc(m, 0, 0.18, 2.74, 0.13, em, n=10)
    else:
        m.part(); m.limb([(-0.12, 0.2, 2.8), (-0.08, 0.2, 2.68), (0.0, 0.2, 2.64), (0.08, 0.2, 2.68), (0.12, 0.2, 2.8)], [0.012, 0.03, 0.036, 0.03, 0.012], em, n=5)
    m.part(); m.box(-0.36, 0.17, 2.44, 0.36, 0.22, 2.49, M('cedar', 3.6))
    cl = M(side, 2.9, m_mottle(5, 0.35), soft=True)
    if not down:
        def sign(u, v, P, seed):
            cu = np.round(u.min() + (u.max() - u.min()) / 2); cv = v.max() - 8
            r2 = (u - cu) ** 2 + (v - cv) ** 2
            on = (r2 <= 6) if side == 'red' else ((r2 <= 8) & ((u - cu - 2) ** 2 + (v - cv) ** 2 > 6))
            return np.where(on, 0.6, 0.0), on
        cloth = M(side, 4.2, sign, ramp2=EMBLEM[side], soft=True)
        rows, cols = 7, 4
        g = np.zeros((rows, cols, 3))
        for i in range(rows):
            t = i / (rows - 1)
            for k in range(cols):
                g[i, k] = (-0.32 + 0.64 * k / (cols - 1) + math.sin(t * 3.0) * 0.03 * t, 0.16 - 0.03 * t * math.cos(k), 2.44 - 1.15 * t)
        m.part(); m.sheet(g[::-1], cloth)
    else:
        m.part(); m.blob(0.1, -0.12, 0.08, 0.42, 0.24, 0.11, cl, seed=3, bump=0.25, n=9, rings=4)
        m.part(); m.blob(-0.2, -0.2, 0.05, 0.2, 0.14, 0.07, cl, seed=5, bump=0.3, n=7, rings=3)
    return m


def shield_rack(side, n=3):
    """A rack of the camp's shields, leaning, with the spears that go with them."""
    m = Model()
    wood = M('cedar', 3.9, m_planks(3, 'h'))
    m.part(); m.box(-0.75, 0.16, 0.5, 0.75, 0.22, 0.58, wood, top=M('cedar', 4.5))
    m.part()
    for sx in (-0.72, 0.66):
        m.box(sx, 0.14, 0, sx + 0.06, 0.24, 0.62, wood)
    for i in range(n):
        x = -0.5 + i * 0.5
        m.part(); _disc(m, x, 0.06, 0.36, 0.3, M('bronze', 3.2))
        m.part(); _disc(m, x, 0.05, 0.36, 0.25, M(side, 3.5, m_mottle(4, 0.3)))
        m.part(); _disc(m, x, 0.04, 0.36, 0.07, M(EMBLEM[side], 4.2), n=8)
    for sx in (-0.25, 0.25):
        m.part(); m.limb([(sx, 0.26, 0.0), (sx, 0.26, 1.5)], [0.028, 0.026], M('wood', 3.9), n=5)
        m.part(); m.limb([(sx, 0.26, 1.5), (sx, 0.26, 1.74)], [0.045, 0.004], M('bronze', 3.9), n=4)
    return m


def drum(side):
    """A war drum on its stand: hide over a clay bowl, a band of the camp's colour round it."""
    m = Model()
    m.part()
    for a in (0.5, 2.6, 4.7):
        m.limb([(math.cos(a) * 0.3, 0.3 + math.sin(a) * 0.2, 0), (math.cos(a) * 0.14, 0.3 + math.sin(a) * 0.1, 0.42)], [0.03, 0.03], M('cedar', 3.8), n=4)
    m.part(); m.turned(0, 0.3, [(0.12, 0.34), (0.3, 0.46), (0.36, 0.7), (0.36, 0.78)], M('clay', 3.6, m_mottle(4, 0.3)), n=12, cap=M('wood', 4.4, m_mottle(5, 0.3)))
    m.part(); m.turned(0, 0.3, [(0.368, 0.66), (0.368, 0.74)], M(side, 3.8), n=12)
    return m


# ------------------------------------------------------------------ Nod
def nod_bench():
    """The sentry's bench by the strongroom door, and the sentry on it: clay like all the rest, but
    made lying down, curled on his side with his helmet over his eyes and his shield for a pillow.
    The potter had clearly met him."""
    m = Model()
    body, top, foot = _brick()
    m.part(); m.box(-1.05, 0.0, 0, 1.05, 0.66, 0.42, body, top=top)
    m.part(); m.box(-1.1, -PX, 0, 1.1, 0.7, 0.14, foot, top=top)
    clay = M('clay', 3.9, m_mottle(5, 0.35))
    dark = M('clay', 3.1, m_mottle(5, 0.35))
    # his shield under his head, at the east end
    m.part(); m.turned(0.72, 0.34, [(0.3, 0.42), (0.3, 0.46), (0.1, 0.5)], M('bronze', 3.4), n=10, cap=M('bronze', 4.0))
    # shins, knees drawn up, hips, back, shoulders
    m.part(); m.limb([(-0.86, 0.22, 0.52), (-0.5, 0.2, 0.54), (-0.3, 0.42, 0.58), (-0.02, 0.4, 0.62), (0.3, 0.36, 0.64), (0.52, 0.34, 0.6)],
                     [0.09, 0.11, 0.13, 0.19, 0.2, 0.15], clay, n=8)
    m.part(); m.limb([(0.34, 0.2, 0.6), (0.12, 0.12, 0.56), (0.34, 0.1, 0.52)], [0.07, 0.065, 0.06], dark, n=6)      # the arm he is not lying on
    m.part(); m.blob(0.7, 0.34, 0.62, 0.13, 0.13, 0.12, clay, n=8, rings=5)
    m.part(); m.blob(0.72, 0.33, 0.69, 0.16, 0.16, 0.1, M('bronze', 3.6, gloss=0.03), n=8, rings=4)                 # the helmet, tipped forward
    # his spear, propped where he could reach it if he woke
    m.part(); m.box(-1.0, 0.6, 0, -0.96, 0.64, 1.7, M('wood', 3.7))
    m.part(); m.limb([(-0.98, 0.62, 1.7), (-0.98, 0.62, 1.94)], [0.045, 0.004], M('bronze', 3.8), n=4)
    return m


def hook():
    """A bronze hook in the wall with nothing on it. There is something on it in the dream."""
    m = Model()
    brz = M('bronze', 3.8, gloss=0.03)
    m.part(); m.box(-0.07, -0.04, 1.5, 0.07, 0.0, 1.64, M('bronze', 3.2))
    m.part(); m.limb([(0, -0.04, 1.56), (0, -0.14, 1.54), (0, -0.16, 1.44), (0, -0.1, 1.4)], [0.022, 0.022, 0.02, 0.012], brz, n=5)
    return m


# ------------------------------------------------------------------ what only the dream has
def dream_key():
    """A key of moonlight hanging on the hook."""
    m = Model()
    mo = moon(4.4)
    y = -0.15
    ring = [(math.cos(a) * 0.12, 1.3 + math.sin(a) * 0.12) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
    m.part(); m.face(ring, y, mo)
    m.part(); _disc(m, 0, y - 0.01, 1.3, 0.05, M('dark', 1.4), n=6)
    m.part(); m.box(-0.032, y - 0.02, 0.74, 0.032, y + 0.02, 1.2, mo)
    m.part(); m.box(0.032, y - 0.02, 0.74, 0.15, y + 0.02, 0.81, mo)
    m.part(); m.box(0.032, y - 0.02, 0.89, 0.12, y + 0.02, 0.95, mo)
    return m


def plank_stack(n=4):
    """Planks of moonlight, stacked the way somebody always stacks them in dreams."""
    m = Model()
    for i in range(n):
        off = (0.0, 0.05, -0.04, 0.03)[i % 4]
        m.part(); m.box(-0.7 + off, 0.02 + (i % 2) * 0.03, i * 0.07, 0.7 + off, 0.36 + (i % 2) * 0.03, i * 0.07 + 0.06,
                        moon(3.3 + i * 0.25, m_planks(5, 'h', knots=False)), top=moon(4.0 + i * 0.3, m_planks(5, 'h', knots=False)))
    return m


def moon_plank(length, hw=0.44):
    """The one plank, laid: it runs south from the origin (its north end), flat on two brackets."""
    m = Model()
    m.part(); m.box(-hw, -length, 0.0, hw, 0, 0.05, moon(3.4, m_planks(7, 'v', knots=False)), top=moon(4.3, m_planks(7, 'v', knots=False)))
    m.part()
    for sx in (-hw - 0.02, hw - 0.02):
        m.box(sx, -length, 0.0, sx + 0.04, 0, 0.07, moon(5.0))
    return m


def brackets():
    """Two bronze brackets set in the lip of a drop, for a plank nobody ever brought."""
    m = Model()
    brz = M('bronze', 3.9, gloss=0.03)
    m.part()
    for sx in (-0.5, 0.36):
        m.box(sx, -0.06, 0, sx + 0.14, 0.1, 0.07, brz, top=M('bronze', 4.6))
        m.box(sx + 0.03, 0.02, 0.07, sx + 0.11, 0.08, 0.12, M('bronze', 3.4), top=M('bronze', 4.2))
    return m


def cold_flame(m, x, y, z, s=1.0, frame=0, seed=0, tongues=5):
    """The blue fire: the same tongues as any fire, the colour of the inside of a shadow."""
    fire = Mat(COLD, 3.3, town.m_fire(z, 0.66 * s), glow=True)
    from forge import hash2
    m.part()
    spots = ((-0.14, 0.34, 0.11), (0.0, 0.62, 0.15), (0.14, 0.4, 0.11), (-0.06, 0.48, 0.12), (0.08, 0.5, 0.12))[:tongues]
    for i, (dx, hh, rr) in enumerate(spots):
        k = hash2(frame * 3 + i, seed, 11)
        h2 = hh * s * (0.8 + 0.45 * k); lean = (hash2(frame, i + seed, 5) - 0.5) * 0.16 * s - dx * 0.25
        m.limb([(x + dx * s, y, z - 0.04), (x + dx * s + lean * 0.4, y, z + h2 * 0.45), (x + dx * s + lean, y, z + h2)],
               [rr * s, rr * s * 0.78, 0.012], fire, n=6, cap=False)


def tripod(fire=False, frame=0):
    """A bronze bowl on three legs. Awake, the ash in it is older than the city wall; in the dream
    somebody has kept the fire in, and it burns blue."""
    m = Model()
    brz = M('bronze', 3.7, gloss=0.03)
    if not fire:
        m.part()
        for a in (0.6, 2.7, 4.8):
            m.limb([(math.cos(a) * 0.4, 0.3 + math.sin(a) * 0.24, 0), (math.cos(a) * 0.16, 0.3 + math.sin(a) * 0.1, 0.46)], [0.034, 0.028], brz, n=4)
        m.part(); m.turned(0, 0.3, [(0.1, 0.4), (0.26, 0.46), (0.33, 0.56), (0.3, 0.59), (0.25, 0.54)], brz, n=12, cap=M('dark', 2.2, m_mottle(2, 0.7)))
    else:
        # only the fire: it is drawn over the cold bowl, for a dreamer
        m.part(); m.turned(0, 0.3, [(0.24, 0.53), (0.24, 0.56)], Mat(COLD, 2.4, m_mottle(3, 0.5), glow=True), n=12, cap=Mat(COLD, 2.6, m_mottle(3, 0.5), glow=True))
        cold_flame(m, 0, 0.3, 0.55, 1.0, frame)
    return m


def blue_lamp(frame=0):
    """A lamp of the dead on its bronze stand. frame 0: cold. 1 to 3: burning blue."""
    m = Model()
    brz = M('bronze', 3.9, gloss=0.03)
    m.part(); m.turned(0, 0.12, [(0.17, 0.0), (0.13, 0.06), (0.045, 0.12), (0.04, 0.9), (0.11, 1.0), (0.16, 1.06)], brz, n=9, cap=M('dark', 1.6))
    m.part(); m.turned(0, 0.12, [(0.06, 0.5), (0.075, 0.53), (0.06, 0.56)], M('lapis', 3.4), n=8)
    if frame > 0:
        f = frame - 1
        sway = (0.0, 0.03, -0.025)[f % 3]; tall = (0.0, 0.05, -0.02)[f % 3]
        m.part(); m.limb([(0, 0.12, 1.06), (sway * 0.5, 0.12, 1.24 + tall), (sway, 0.12, 1.46 + tall * 2)], [0.09, 0.07, 0.012], Mat(COLD, 3.3, glow=True), n=6)
        m.part(); m.limb([(0, 0.11, 1.07), (sway * 0.4, 0.11, 1.22 + tall)], [0.045, 0.02], Mat(COLD, 5.2, glow=True), n=5)
    return m


def snore(frame=0):
    """A snore, where it was left: a curl of breath that hangs over the bench and keeps turning."""
    m = Model()
    t = frame * math.pi / 2
    pts = []
    for i in range(7):
        k = i / 6
        a = t + k * 4.4
        pts.append((math.cos(a) * 0.1 * (1 - k * 0.5), 0.0, 1.0 + k * 0.5 + math.sin(t + k * 3) * 0.02))
    m.part(); m.limb(pts, [0.02, 0.04, 0.05, 0.045, 0.04, 0.03, 0.008], moon(3.8), n=5)
    return m


def last_word():
    """One word, on a scrap of tablet no bigger than a thumb, lying where it was dropped."""
    m = Model()
    m.part(); m.box(-0.16, 0.0, 0.0, 0.16, 0.24, 0.04, moon(3.4), top=moon(4.4, town.m_cuneiform(3)))
    return m


def lock_grille(w=3.0, h=1.4):
    """The strongroom's grille: bronze bars like any other, and in the middle a lock plate with a
    keyhole and a stud of moonstone over it. It has never had a key a waking hand could hold."""
    m = Model()
    brz = M('bronze', 4.3, gloss=0.03); dk = M('bronze', 3.2)
    m.part()
    n = int(w / 0.19)
    for i in range(n + 1):
        x = -w / 2 + w * i / n
        m.box(x - PX / 2, 0.08, 0, x + PX / 2, 0.08 + PX, h, brz if i % 2 == 0 else dk)
    m.part(); m.box(-w / 2, 0.06, h - 0.08, w / 2, 0.14, h, brz)
    m.part(); m.box(-w / 2, 0.06, 0.3, w / 2, 0.14, 0.36, dk)
    m.part(); m.box(-0.22, 0.0, 0.46, 0.22, 0.08, 1.0, M('bronze', 3.6, gloss=0.03), top=M('bronze', 4.4))
    m.part(); _disc(m, 0, -0.01, 0.66, 0.05, M('dark', 1.2), n=6)
    m.part(); m.box(-0.015, -0.02, 0.56, 0.015, -0.01, 0.66, M('dark', 1.2))
    m.part(); _disc(m, 0, -0.02, 0.86, 0.06, Mat(MOON, 4.6, glow=True), n=8)
    return m


# ------------------------------------------------------------------ outside, on the hill
def great_barrow(r=3.0, seed=0):
    """The Generals' Barrow: a mound bigger than any other on the hill, a drum of dressed stone, one
    door (the city could not agree on two), and a standard either side of it that neither army
    will take down first."""
    rr = town.rnd(seed); m = Model()
    stone = M('stone', 3.9, m_ashlar(12, 6))
    earth = M('tomb', 4.5, m_mottle(9, 0.55, specks=0.03, speck_t=1.0))
    m.part(); m.turned(0, r, [(r, 0.0), (r, 0.8)], stone, n=26)
    m.part(); m.turned(0, r, [(r + 0.06, 0.8), (r + 0.06, 0.94)], M('stone', 4.7, m_mottle(6, 0.3)), n=26, cap=M('tomb', 4.2))
    m.part(); m.blob(0, r, 0.94, r * 0.94, r * 0.94, r * 0.5, earth, seed=seed, bump=0.03, n=20, rings=8)
    # the passage: two jambs, a lintel with both emblems on it, the dark
    side = M('stone', 4.1, m_ashlar(10, 5))
    for sgn in (-1, 1):
        m.part(); m.box(sgn * 0.82 - 0.2, -0.5, 0, sgn * 0.82 + 0.2, 0.4, 1.5, side, top=M('stone', 4.8))
    m.part(); m.box(-1.14, -0.56, 1.5, 1.14, 0.1, 1.84, M('stone', 3.3, m_ashlar(14, 6)), top=M('stone', 3.6, m_mottle(6, 0.3)))
    m.part(); m.quad((-0.62, 0.02, 0), (0.62, 0.02, 0), (0.62, 0.02, 1.5), (-0.62, 0.02, 1.5), M('dark', 1.0))
    m.part(); _disc(m, -0.5, -0.57, 1.67, 0.11, M('gold', 4.4), n=8)
    m.part(); m.limb([(0.38, -0.57, 1.74), (0.42, -0.57, 1.63), (0.5, -0.57, 1.6), (0.58, -0.57, 1.63), (0.62, -0.57, 1.74)], [0.01, 0.026, 0.03, 0.026, 0.01], M('limewash', 4.6), n=4)
    m.part(); m.box(-0.62, -0.5, 0, 0.62, 0.0, 0.05, M('stone', 3.6), top=M('stone', 4.3, m_mottle(6, 0.3)))
    return m
