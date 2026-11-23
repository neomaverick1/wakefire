"""What stands in the king's tomb besides the dead: an offering scale that wants a goat's weight
of gold, a drawbridge on its rope, the lamp a dead man carries, the ball of gold a scarab took
for the sun; and the two things only its dream has, a whole gold goat and an order."""
import math
import numpy as np
import town
from forge import Model, M, Mat, RAMPS, m_mottle, m_planks, m_ashlar
from bprops import moon

PX = 1 / 16.0


def _disc(m, cx, y, cz, r, mat, n=12):
    m.face([(cx + math.cos(a) * r, cz + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)], y, mat)


# ------------------------------------------------------------------ the goat
def goat(m, x, y, z, s=1.0, mat=None):
    """A goat a hand high, cast in one piece: four legs, a barrel, a neck, a head with two horns swept back."""
    g = mat or M('gold', 4.3, gloss=0.03)
    m.part(); m.blob(x, y, z + 0.30 * s, 0.20 * s, 0.10 * s, 0.11 * s, g, n=8, rings=5)
    m.part()
    for dx in (-0.13, 0.12):
        for dy in (-0.04, 0.05):
            m.limb([(x + dx * s, y + dy * s, z + 0.24 * s), (x + dx * s, y + dy * s, z)], [0.035 * s, 0.025 * s], g, n=4)
    m.part(); m.limb([(x + 0.16 * s, y, z + 0.34 * s), (x + 0.26 * s, y, z + 0.5 * s)], [0.06 * s, 0.045 * s], g, n=5)
    m.part(); m.blob(x + 0.31 * s, y, z + 0.52 * s, 0.085 * s, 0.05 * s, 0.055 * s, g, n=6, rings=4)
    m.part()
    for sy in (-0.03, 0.03):
        m.limb([(x + 0.27 * s, y + sy * s, z + 0.57 * s), (x + 0.2 * s, y + sy * s, z + 0.68 * s), (x + 0.1 * s, y + sy * s, z + 0.66 * s)],
               [0.02 * s, 0.015 * s, 0.006 * s], mat or M('gold', 5.0), n=4)
    m.part(); m.limb([(x - 0.2 * s, y, z + 0.34 * s), (x - 0.26 * s, y, z + 0.41 * s)], [0.02 * s, 0.01 * s], g, n=4)


def gold_goat():
    """What a thief dreams of: a whole gold goat, standing on the rest of it."""
    m = Model()
    coin = Mat(RAMPS['gold'], 3.3, m_mottle(2, 1.5))
    m.part(); m.blob(0, 0.22, 0.0, 0.44, 0.26, 0.14, coin, seed=3, bump=0.05, n=10, rings=5)
    goat(m, -0.04, 0.22, 0.12, 1.3)
    return m


def scale(full=False):
    """An offering scale as tall as a man: a bronze beam on a post, a pan either end. The west pan holds a
    goat-weight in stone. The east pan is the offering's: empty, and up; or with its goat in it, and down."""
    m = Model()
    brz = M('bronze', 3.9, gloss=0.03); dk = M('bronze', 3.1)
    m.part(); m.box(-0.34, 0.0, 0, 0.34, 0.5, 0.12, M('stone', 3.4, m_ashlar(8, 4)), top=M('stone', 4.4))
    m.part(); m.box(-0.05, 0.2, 0.12, 0.05, 0.3, 1.86, brz, top=M('bronze', 4.6))
    tilt = 0.16 if full else -0.16
    zl, zr = 1.74 + tilt, 1.74 - tilt
    m.part(); m.limb([(-0.86, 0.25, zl), (0.86, 0.25, zr)], [0.035, 0.035], brz, n=5)
    m.part(); _disc(m, 0, 0.19, 1.86, 0.07, M('gold', 4.6, gloss=0.03), n=8)
    for sx, zt, load in ((-0.86, zl, 'stone'), (0.86, zr, 'gold' if full else None)):
        zp = zt - 0.95
        m.part()
        for dx in (-0.18, 0.18):
            m.limb([(sx, 0.25, zt), (sx + dx, 0.25, zp + 0.04)], [0.008, 0.008], dk, n=3)
        m.part(); m.turned(sx, 0.25, [(0.05, zp - 0.04), (0.26, zp), (0.28, zp + 0.04)], brz, n=10, cap=M('bronze', 4.4))
        if load == 'stone':
            goat(m, sx - 0.04, 0.25, zp + 0.03, 0.72, M('stone', 3.8, m_mottle(4, 0.3)))
        elif load == 'gold':
            goat(m, sx - 0.04, 0.25, zp + 0.03, 0.72)
    return m


def order():
    """An order, hanging in a doorway where it was given: a tablet the size of a hand with one line cut
    in it, lit from nowhere."""
    m = Model()
    m.part(); m.box(-0.2, -0.02, 0.92, 0.2, 0.03, 1.22, moon(3.6), top=moon(4.6))
    m.part(); m.quad((-0.17, -0.025, 0.95), (0.17, -0.025, 0.95), (0.17, -0.025, 1.19), (-0.17, -0.025, 1.19), moon(4.4, town.m_cuneiform(3)))
    return m


# ------------------------------------------------------------------ the drawbridge
def rope_post():
    """The post the drawbridge's rope is made fast to, on the near side of the drop."""
    m = Model()
    m.part(); m.box(-0.1, 0.0, 0, 0.1, 0.2, 0.9, M('cedar', 3.8, m_planks(3, 'v')), top=M('cedar', 4.6))
    m.part(); m.turned(0, 0.1, [(0.14, 0.5), (0.14, 0.7)], M('straw', 3.8), n=8)
    return m


def rope(length):
    """A rope as thick as a wrist, from the post on the near lip up to the top of the drawbridge on the
    far one. Its middle is the origin, out over the drop."""
    m = Model()
    n = 8
    pts = []
    for i in range(n + 1):
        k = i / n
        pts.append((0, (k - 0.5) * length, 0.62 + 1.5 * k - math.sin(k * math.pi) * 0.25))
    m.part(); m.limb(pts, [0.035] * (n + 1), M('straw', 3.9, m_mottle(2, 0.6)), n=5)
    return m


def drawbridge(length, hw=0.75, up=False):
    """Cedar planks bound in bronze. Down, it runs south from the origin (its hinge, on the far lip) across
    the drop. Up, it stands on end at the hinge."""
    m = Model()
    wood = M('cedar', 3.6, m_planks(6, 'v')); top = M('cedar', 4.3, m_planks(6, 'v')); brz = M('bronze', 3.8, gloss=0.03)
    if up:
        m.part(); m.box(-hw, 0.0, 0.0, hw, 0.12, length, wood, top=top)
        for z in (0.2, length * 0.5, length - 0.2):
            m.part(); m.box(-hw - 0.02, -0.02, z - 0.05, hw + 0.02, 0.0, z + 0.05, brz)
    else:
        m.part(); m.box(-hw, -length, 0.0, hw, 0, 0.08, wood, top=top)
        for y in (-0.2, -length * 0.5, -length + 0.2):
            m.part(); m.box(-hw - 0.02, y - 0.05, 0.0, hw + 0.02, y + 0.05, 0.1, brz, top=M('bronze', 4.6))
    return m


# ------------------------------------------------------------------ what the dead carry
def hand_lamp(frame=0, lit=True):
    """The lamp a bearer carries: a bronze saucer with a spout, and a flame the colour of deep water."""
    m = Model()
    brz = M('bronze', 4.0, gloss=0.03)
    m.part(); m.turned(0, 0, [(0.05, 0.0), (0.16, 0.05), (0.17, 0.1), (0.12, 0.12)], brz, n=9, cap=M('dark', 1.6))
    m.part(); m.limb([(0.14, 0, 0.09), (0.26, 0, 0.12)], [0.035, 0.02], brz, n=4)
    if lit:
        ghost = Mat(RAMPS['ghost'], 3.4, glow=True)
        sway = (0.0, 0.03, -0.02)[frame % 3]; tall = (0.0, 0.04, -0.02)[frame % 3]
        m.part(); m.limb([(0.26, 0, 0.12), (0.26 + sway * 0.5, 0, 0.26 + tall), (0.26 + sway, 0, 0.42 + tall * 2)], [0.07, 0.055, 0.01], ghost, n=6)
        m.part(); m.limb([(0.26, -0.01, 0.13), (0.26 + sway * 0.4, -0.01, 0.25 + tall)], [0.035, 0.016], Mat(RAMPS['ghost'], 5.0, glow=True), n=5)
    return m


# ------------------------------------------------------------------ the sun, as a scarab understands it
def gold_ball(frame=0):
    """Cups, rings and a king's ransom in small change, rolled into a ball as tall as a man's chest.
    Four frames of it turning."""
    m = Model()
    r = 0.74
    coin = Mat(RAMPS['gold'], 3.5, m_mottle(3, 1.4))
    m.part(); m.blob(0, 0, r, r, r * 0.92, r, coin, seed=20 + frame, bump=0.05, n=14, rings=9)
    gold = M('gold', 4.8, gloss=0.04); brz = M('bronze', 4.2, gloss=0.03)
    a0 = frame * math.pi / 2
    for k in range(5):
        a = a0 + k * 2 * math.pi / 5
        if math.cos(a) < -0.25:
            continue                                       # round the back
        x = math.sin(a) * r * 0.86
        z = r + math.cos(a + 1.2 * k) * r * 0.55
        y = -r * 0.62 * math.cos(a) * 0.9
        if k % 2 == 0:
            m.part(); _disc(m, x, y, z, 0.12, gold, n=8)                 # the rim of a cup, pressed in
            m.part(); _disc(m, x, y - 0.01, z, 0.07, M('dark', 2.0), n=6)
        else:
            m.part(); _disc(m, x, y, z, 0.09, brz, n=8)                  # a ring
            m.part(); _disc(m, x, y - 0.01, z, 0.05, coin, n=6)
    return m


# ------------------------------------------------------------------ the king's road (3F)
def perch():
    """A bronze perch a spear's length high: a post on a stone foot, a crossbar wound with hide for
    talons, a gold cap at either end of it."""
    m = Model()
    brz = M('bronze', 3.9, gloss=0.03)
    m.part(); m.box(-0.24, 0.0, 0, 0.24, 0.34, 0.1, M('stone', 3.6, m_ashlar(6, 3)), top=M('stone', 4.5))
    m.part(); m.turned(0, 0.17, [(0.055, 0.1), (0.04, 0.3), (0.04, 1.5), (0.065, 1.55)], brz, n=8)
    m.part(); m.limb([(-0.36, 0.17, 1.6), (0.36, 0.17, 1.6)], [0.04, 0.04], M('cedar', 3.2, m_mottle(2, 0.5)), n=6)
    for sx in (-0.38, 0.38):
        m.part(); m.limb([(sx - 0.03, 0.17, 1.6), (sx + 0.03, 0.17, 1.6)], [0.055, 0.055], M('gold', 4.6, gloss=0.03), n=6)
    return m


def counterweight():
    """What holds a grille down: a block of stone the size of a calf, strapped in bronze, on a rope
    over a drop. (The origin is the floor under it, which is not there.)"""
    m = Model()
    st = M('stone', 3.7, m_ashlar(6, 4))
    m.part(); m.box(-0.3, -0.2, 0.55, 0.3, 0.2, 1.08, st, top=M('stone', 4.6))
    m.part(); m.box(-0.33, -0.23, 0.74, 0.33, 0.23, 0.84, M('bronze', 3.8, gloss=0.03), top=M('bronze', 4.6))
    m.part(); m.limb([(0, 0, 1.08), (0, 0, 2.9)], [0.04, 0.04], M('straw', 3.9, m_mottle(2, 0.6)), n=5)
    m.part(); m.turned(0, 0, [(0.07, 1.08), (0.07, 1.16)], M('bronze', 4.4), n=6)
    return m


def item_ghost_key():
    """The Ghost Key: the key to the king's own door, four hundred years dead. A ring for a bow, a
    long shank, three teeth, and the last tooth is not all there."""
    m = Model()
    g = Mat(RAMPS['ghost'], 4.0, glow=True); hi = Mat(RAMPS['ghost'], 5.2, glow=True); lo = Mat(RAMPS['ghost'], 2.4, glow=True)
    m.part(); m.box(-0.04, 0, 0.1, 0.04, 0.05, 0.56, g)
    m.part(); m.box(-0.015, -0.01, 0.14, 0.015, 0.0, 0.52, hi)
    m.part(); m.box(0.04, 0, 0.12, 0.2, 0.05, 0.18, g); m.box(0.04, 0, 0.24, 0.16, 0.05, 0.3, g)
    m.part(); m.box(0.04, 0, 0.36, 0.1, 0.05, 0.4, lo)
    ring = [(math.cos(a) * 0.15, 0.03, 0.72 + math.sin(a) * 0.15) for a in np.linspace(0, 2 * math.pi, 13)]
    m.part(); m.limb(ring, [0.045] * 13, g, n=6, cap=False)
    m.part(); m.limb(ring[2:6], [0.02] * 4, hi, n=4, cap=False)
    return m


def warden_door(view='front'):
    """What a warden of the inner door carries for a shield: the inner door. Cedar plated in bronze, the
    king's sun on the face of it, the hinges still on one edge. Four pictures: its face (he is coming at
    you: his crest shows over the top of it), its back (he is walking away), turned half away (he is going
    past), and flat on the floor (he is not going anywhere)."""
    W, H = 1.1, 1.45
    brz = M('bronze', 3.2, gloss=0.03); hi = M('bronze', 4.2, gloss=0.03); gold = M('gold', 4.4, gloss=0.03)
    if view == 'front':
        m = town.bronze_door(W, H, 'sun')
        for z in (0.26, H - 0.36):                                           # the hinges it was lifted off
            m.part(); m.box(-W / 2 - 0.05, -0.05, z, -W / 2 + 0.16, -0.02, z + 0.1, hi)
        m.part(); m.box(-W / 2, -0.02, H, W / 2, 0.06, H + 0.04, hi)
        return m
    if view == 'back':
        m = Model()
        wood = M('cedar', 3.3, m_planks(6, 'v'))
        m.part(); m.quad((-W / 2, 0, 0), (W / 2, 0, 0), (W / 2, 0, H), (-W / 2, 0, H), wood)
        m.part()
        for z in (0.22, H * 0.5, H - 0.3):
            m.box(-W / 2, -0.04, z, W / 2, 0, z + 0.09, M('cedar', 4.2, m_planks(2, 'h')))
        for sx in (-0.22, 0.22):                                             # two bronze grips, where his hands go
            m.part(); m.limb([(sx, -0.03, H * 0.5 + 0.12), (sx, -0.14, H * 0.5 + 0.24), (sx, -0.03, H * 0.5 + 0.36)], [0.03, 0.03, 0.03], hi, n=5)
        m.part(); m.box(-W / 2, -0.02, H, W / 2, 0.06, H + 0.04, hi)
        return m
    if view == 'side':
        # he is facing east: the door is across his front, its face to the east and a little to us
        m = Model()
        ax, ay, bx, by = 0.16, 0.4, -0.16, -0.4
        plate = M('bronze', 3.5, m_planks(4, 'v', knots=False))
        m.part(); m.quad((ax, ay, 0), (bx, by, 0), (bx, by, H), (ax, ay, H), plate, two=True)
        m.part()
        for z in (0.2, H * 0.5, H - 0.3):
            m.quad((ax + 0.02, ay - 0.01, z), (bx + 0.02, by - 0.01, z), (bx + 0.02, by - 0.01, z + 0.09), (ax + 0.02, ay - 0.01, z + 0.09), hi, two=True)
        m.part(); m.quad((ax, ay, H), (bx, by, H), (bx - 0.06, by + 0.02, H), (ax - 0.06, ay + 0.02, H), M('cedar', 3.0), two=True)
        return m
    m = Model()                                                              # flat on the floor, face up
    m.part(); m.box(-W / 2, -H / 2, 0, W / 2, H / 2, 0.08, M('bronze', 2.4), top=M('bronze', 2.9, m_planks(8, 'v', knots=False)))
    m.part()
    for y in (-H / 2 + 0.16, -0.05, H / 2 - 0.26):
        m.box(-W / 2, y, 0.08, W / 2, y + 0.09, 0.1, brz, top=M('bronze', 3.6))
    m.part(); m.turned(0, 0.05, [(0.22, 0.08), (0.22, 0.1)], M('gold', 3.4), n=12, cap=M('gold', 3.6))
    return m
