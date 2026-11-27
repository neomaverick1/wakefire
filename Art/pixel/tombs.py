"""The houses of the dead on the Hill of Sleepers: nine of them, no two alike, and somebody at home in every one
but one. They are built with the kit the living are built with, in the stone the dead prefer: walls the white
of bone, kept, and roofs of bronze tile gone green. Up here it is the dead who cannot sleep, so their lamps
are lit, their doors are answered, and their steps are swept."""
import math
import numpy as np
from forge import Model, Mat, M, RAMPS, m_brick, m_ashlar, m_mottle, m_planks, m_glazed
import town
from town import Mats, PX, rnd, merlons, parapet, stairs, m_niches, m_cuneiform
import houses
from houses import Building, shell, big_door, trapdoor
import necro

GHOST = necro.GHOST

# The look of the dead town: every house in the same bone white, under the same green roof.
LOOK = {'plaster': ('bone', 5.0), 'clean': True, 'roof': lambda: M('verdigris', 3.3, m_glazed(8, 8))}


# ------------------------------------------------------------------ surfaces
def m_flock(step=9):
    """A frieze of sheep, nose to tail (ramp2 the sheep)."""
    def f(u, v, P, seed):
        k = u % step
        body = (k >= 1) & (k <= 5) & (v >= 2) & (v <= 4)
        head = (k >= 6) & (k <= 7) & (v >= 3) & (v <= 5)
        legs = ((k == 1) | (k == 5)) & (v >= 0) & (v < 2)
        on = body | head | legs
        return np.where(on, 1.0, 0.0), on
    return f


def m_tally():
    """Counting, scratched in a wall: strokes in fours, row over row."""
    def f(u, v, P, seed):
        k = u % 11; r_ = v % 7
        stroke = (k < 8) & (k % 2 == 0) & (r_ >= 1) & (r_ <= 5)
        return np.where(stroke, -1.5, 0.0), None
    return f


# ------------------------------------------------------------------ parts
def stone():
    return M('stone', 3.5, m_ashlar(12, 6))


def tile():
    return M('verdigris', 3.3, m_glazed(8, 4))


def moon(m, x, y, z, r=0.2):
    """A moon with its horns up on a disc of lapis: the sign over a door on this hill."""
    m.part(); necro._disc(m, x, y - 0.03, z, r, M('lapis', 3.6), 10)
    m.part(); necro._crescent(m, x, y - 0.04, z, r * 0.8, M('gold', 4.4), thick=0.5, n=7)


def ghost_lamp(m, x, y, z=0.0, post=0.9, lit=True):
    """A spirit lamp on a stone post: the light the dead keep, the colour of the inside of a wave."""
    m.part(); m.turned(x, y, [(0.1, z), (0.06, z + 0.1), (0.05, z + post), (0.12, z + post + 0.06), (0.13, z + post + 0.14)], M('stone', 4.2), n=8, cap=M('bronze', 3.4))
    if lit:
        m.part(); m.blob(x, y, z + post + 0.24, 0.06, 0.06, 0.11, Mat(RAMPS['ghost'], 3.8, glow=True), n=6, rings=4)
        m.light(x, y, z + post + 0.3, 2.6, GHOST, 0.5)


def vault(m, xa, xb, ya, yb, z, rise, mat, gable, rim):
    """A barrel of tile from front to back, springing at z, and the round gable it shows the street."""
    R = (xb - xa) / 2; cx = (xa + xb) / 2
    ang = np.linspace(math.pi, 0, 11)
    grid = [[(cx + math.cos(a) * R, yy, z + math.sin(a) * rise) for a in ang] for yy in np.linspace(ya, yb, 4)]
    m.part(); m.sheet(grid, mat, two=False)
    m.part(); m.face([(cx - R, z), (cx + R, z)] + necro._arc(cx, z, R, rise, 11)[1:-1], ya, gable)
    arc_o = necro._arc(cx, z, R + 0.02, rise + 0.02, 11); arc_i = necro._arc(cx, z, R - 0.14, rise - 0.12, 11)
    m.part()
    for i in range(10):
        m.quad((arc_o[i][0], ya - 0.02, arc_o[i][1]), (arc_o[i + 1][0], ya - 0.02, arc_o[i + 1][1]),
               (arc_i[i + 1][0], ya - 0.02, arc_i[i + 1][1]), (arc_i[i][0], ya - 0.02, arc_i[i][1]), rim, two=True)


def door(m, mt, x, w=0.9, h=1.5, glow=True, ajar=0.34):
    """The door of a house of the dead: a frame of dressed stone, and if somebody is home, the light they keep."""
    fr = M('stone', 4.3, m_mottle(7, 0.3))
    m.part(); m.box(x - w / 2 - 0.16, -0.08, 0, x - w / 2, 0, h + 0.08, fr)
    m.box(x + w / 2, -0.08, 0, x + w / 2 + 0.16, 0, h + 0.08, fr)
    m.part(); m.box(x - w / 2 - 0.24, -0.1, h + 0.08, x + w / 2 + 0.24, 0, h + 0.26, M('stone', 4.8))
    m.part(); m.quad((x - w / 2, -0.02, 0), (x + w / 2, -0.02, 0), (x + w / 2, -0.02, h + 0.08), (x - w / 2, -0.02, h + 0.08), mt.dark)
    if glow:
        m.part(); m.quad((x - w / 2, -0.03, 0), (x + w / 2, -0.03, 0), (x + w / 2, -0.03, h * 0.55), (x - w / 2, -0.03, h * 0.55), Mat(RAMPS['ghost'], 1.6, glow=True))
        m.light(x, -0.4, 0.8, 2.4, GHOST, 0.45)
    if ajar:
        m.part(); m.quad((x - w / 2, -0.05, 0), (x - w / 2 + w * ajar, -0.05, 0), (x - w / 2 + w * ajar, -0.05, h), (x - w / 2, -0.05, h), M('cedar', 3.6, m_planks(3, 'v', knots=False)))
    m.part(); m.box(x - w / 2 - 0.2, -0.36, 0, x + w / 2 + 0.2, 0, 2 * PX, M('stone', 4.7, m_mottle(6, 0.25)))


def slit(m, mt, x, z, w=0.16, h=0.5, lit=True):
    """A window no wider than a hand: enough to see who it is."""
    m.part(); m.quad((x - w / 2, -0.02, z), (x + w / 2, -0.02, z), (x + w / 2, -0.02, z + h), (x - w / 2, -0.02, z + h), Mat(RAMPS['ghost'], 2.4, glow=True) if lit else mt.dark)
    m.part(); m.box(x - w / 2 - PX, -0.06, z - PX, x + w / 2 + PX, 0, z, mt.trim)


def base(m, mt, x0, x1, d, h, foot=0.3):
    shell(m, mt, x0, x1, d, h, plinth=stone(), foot=foot)


# ------------------------------------------------------------------ the road of the dead
def sweeper():
    """A brick vault with a moon over the door, and the cleanest step on the hill. She has had forty nights
    awake to get it nice, and three hundred years before that to work out where the dust comes from."""
    w, d, h = 5.5, 3.5, 1.9
    mt = Mats(71, 1); m = Model(); x0, x1 = -w / 2, w / 2
    base(m, mt, x0, x1, d, h)
    vault(m, x0 + 0.1, x1 - 0.1, 0.02, d - 0.05, h, 1.05, tile(), mt.wall_plain, mt.trim)
    moon(m, 0, 0.02, h + 0.5, 0.22)
    dx = -0.9
    door(m, mt, dx)
    slit(m, mt, 1.2, 0.9)
    # the step, wider than it need be and paler than anything else up here; the broom; the mat
    m.part(); m.box(dx - 1.0, -0.62, 0, dx + 1.0, 0, 3 * PX, M('alabaster', 5.2, m_mottle(8, 0.15)), top=M('alabaster', 5.6))
    m.part(); m.beam((dx + 0.9, -0.3, 0.1), (dx + 1.05, -0.06, 1.5), 1.1 * PX, M('wood', 4.4))
    m.part(); m.blob(dx + 0.88, -0.34, 0.14, 0.14, 0.08, 0.16, M('reed', 4.0, m_planks(2, 'v', knots=False)), n=7, rings=4)
    return Building('nr_sweeper', m, w, d, h, doors=[(dx, 'open')], tall=[(x0, x1, 1.1)], extra=[(dx + 0.7, -0.45, dx + 1.15, 0)])


def shepherd():
    """A long low tomb with his flock cut along the front of it, nose to tail, so that he would never be without
    them. He has been counting them since the god lay down. It does not work on the dead either."""
    w, d, h = 6.0, 3.5, 1.75
    mt = Mats(73, 1); m = Model(); x0, x1 = -w / 2, w / 2
    base(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h, h=0.2)
    merlons(m, mt.trim, x0 + 0.1, x1 - 0.1, 0, 3 * PX, h + 0.2, mw=0.3, mh=0.22)
    m.part(); m.box(x0 - PX, -0.5 * PX, h - 0.56, x1 + PX, 0, h - 0.12, M('lapis', 3.3, m_flock(9), ramp2='alabaster'))
    dx = -1.5
    door(m, mt, dx)
    # the count, scratched by the door, as far along the wall as an arm reaches
    m.part(); m.box(-0.6, -0.4 * PX, 0.42, 2.5, 0, 1.12, M('bone', 4.7, m_tally()))
    # his crook, where he left it
    m.part(); m.beam((2.72, -0.26, 0), (2.78, -0.05, 1.5), 1.0 * PX, M('wood', 4.5))
    m.part(); m.beam((2.78, -0.05, 1.5), (2.62, -0.08, 1.62), 1.0 * PX, M('wood', 4.5))
    return Building('nr_shepherd', m, w, d, h, doors=[(dx, 'open')])


def proud():
    """A stepped tomb, built a little taller than its neighbours on purpose. He had the door bricked up behind
    him so that nobody could come in and stand level. The steps up the front are for the neighbours to look at.
    The hatch in the roof is for the man who comes to sweep it, who has not been in four hundred years."""
    w, d, h = 5.0, 4.0, 1.25
    mt = Mats(75, 1); m = Model(); x0, x1 = -w / 2, w / 2
    niche = M('bone', 4.7, m_niches(6, 3))
    m.part(); m.box(x0, 0, 0, x1, d, h, niche, top=mt.roof)
    m.part(); m.box(x0 - PX, -PX, 0, x1 + PX, d, 0.3, stone(), top=mt.trim)
    m.part(); m.box(x0 - PX, -PX, h - PX, x1 + PX, PX, h, mt.trim)
    parapet(m, mt, x0, 0, x1, d, h, h=0.12, gap=(0.2, 1.0))
    t2 = (-2.1, 1.7, 0.9, 3.8, h + 1.1)
    m.part(); m.box(t2[0], t2[1], h, t2[2], t2[3], t2[4], niche, top=mt.roof)
    m.part(); m.box(t2[0] - PX, t2[1] - PX, t2[4] - PX, t2[2] + PX, t2[1] + PX, t2[4], mt.trim)
    t3 = (-1.5, 2.2, 0.3, 3.4, t2[4] + 0.85)
    m.part(); m.box(t3[0], t3[1], t2[4], t3[2], t3[3], t3[4], M('lapis', 3.7, m_glazed(8, 4)), top=mt.roof)
    m.part(); m.box(t3[0] - PX, t3[1] - PX, t3[4] - PX, t3[2] + PX, t3[1] + PX, t3[4], M('gold', 4.2))
    merlons(m, mt.trim, t3[0], t3[2], t3[1], t3[1] + 0.14, t3[4], mw=0.22, mh=0.16)
    # the doorway he had closed: a frame, and nothing in it but brick (the map hangs the brick in it)
    dx = -1.3
    door(m, mt, dx, glow=False, ajar=0)
    stairs(m, mt, 2.4, 0.5, 0, h)
    trapdoor(m, mt, 1.7, 2.6, h, open_=True)
    ghost_lamp(m, dx + 0.95, -0.3)
    return Building('nr_proud', m, w, d, h, doors=[(dx, 'locked')], stair=(2.4, 0.5), walk=(x0, x1), hatch=(1.7, 2.6),
                    tall=[(t2[0], t2[2], 1.95, 1.7)], leaves={0: ('bricked', 0.9, 1.5, 3)}, extra=[(dx + 0.8, -0.45, dx + 1.1, 0)])


def couple():
    """Two vaults under one roof line, a moon on each, and one door between them, bolted on the inside. They
    were married fifty years and buried side by side, and have spent every night since on whose side is whose."""
    w, d, h = 7.0, 3.5, 1.8
    mt = Mats(77, 1); m = Model(); x0, x1 = -w / 2, w / 2
    base(m, mt, x0, x1, d, h)
    for (a, b) in ((x0 + 0.1, -0.12), (0.12, x1 - 0.1)):
        vault(m, a, b, 0.02, d - 0.05, h, 0.9, tile(), mt.wall_plain, mt.trim)
        moon(m, (a + b) / 2, 0.02, h + 0.42, 0.18)
    door(m, mt, 0.0, glow=True, ajar=0)
    # a name either side of the door, each cut a little bigger than the other
    for sx, hh in ((-1.5, 0.5), (1.5, 0.58)):
        m.part(); m.box(sx - 0.5, -0.5 * PX, 0.8, sx + 0.5, 0, 0.8 + hh, M('stone', 4.5, m_cuneiform(4)), top=M('stone', 4.9))
    return Building('nr_couple', m, w, d, h, doors=[(0.0, 'held')], tall=[(x0, x1, 0.95)], leaves={0: ('barred', 0.9, 1.5, 3)})


# ------------------------------------------------------------------ the hilltop
def rich():
    """A rich man's tomb: piers down the front like the Temple's, a porch on two pillars of alabaster, a line of
    gold under the parapet, and both leaves of the door standing open. He is expecting company."""
    w, d, h = 8.5, 4.0, 2.4
    mt = Mats(79, 1); m = Model(); x0, x1 = -w / 2, w / 2
    base(m, mt, x0, x1, d, h, foot=0.5)
    houses.buttresses(m, mt.wall_plain, x0, -1.3, 0, h, 4, wd=0.5, out=0.14, top=mt.trim)
    houses.buttresses(m, mt.wall_plain, 1.3, x1, 0, h, 4, wd=0.5, out=0.14, top=mt.trim)
    parapet(m, mt, x0, 0, x1, d, h, h=0.22)
    merlons(m, mt.trim, x0 + 0.1, x1 - 0.1, 0, 3 * PX, h + 0.22, mw=0.4, mh=0.28)
    m.part(); m.box(x0 - PX, -0.16, h - 0.36, x1 + PX, 0, h - 0.28, M('gold', 4.2))
    ala = M('alabaster', 4.6, m_mottle(8, 0.2))
    for sx in (-1.2, 1.2):
        m.part(); m.turned(sx, -0.95, [(0.22, 0), (0.17, 0.12), (0.14, 1.86), (0.2, 1.96)], ala, n=10, cap=M('alabaster', 5.0))
    m.part(); m.box(-1.5, -1.2, 1.96, 1.5, 0, 2.16, ala, top=M('alabaster', 5.2))
    m.part(); m.box(-1.5, -1.22, 2.02, 1.5, -1.2, 2.1, M('gold', 4.2))
    big_door(m, mt, 0, 0, w=1.5, h=1.86, arch=False, bands=3, frame=M('stone', 4.4, m_mottle(7, 0.3)), ajar=True)
    m.part(); m.quad((-0.2, -0.03, 0), (0.75, -0.03, 0), (0.75, -0.03, 1.0), (-0.2, -0.03, 1.0), Mat(RAMPS['ghost'], 1.6, glow=True))
    m.light(0.2, -0.5, 0.9, 3.0, GHOST, 0.5)
    for sx in (-2.3, 2.3):
        ghost_lamp(m, sx, -0.4, post=1.1)
    return Building('np_rich', m, w, d, h, doors=[(0.0, 'open')], door_w=1.2,
                    extra=[(-1.42, -1.15, -0.98, -0.75), (0.98, -1.15, 1.42, -0.75), (-2.45, -0.55, -2.15, 0), (2.15, -0.55, 2.45, 0)])


def knocker():
    """A vault with a door of cedar under bronze, shut, and a gong for callers. From inside: knocking. He does
    not want to be let out. He wants to know that somebody is there."""
    w, d, h = 5.0, 3.5, 2.0
    mt = Mats(81, 1); m = Model(); x0, x1 = -w / 2, w / 2
    base(m, mt, x0, x1, d, h)
    vault(m, x0 + 0.1, x1 - 0.1, 0.02, d - 0.05, h, 1.0, tile(), mt.wall_plain, mt.trim)
    moon(m, 0, 0.02, h + 0.48, 0.2)
    dx = 0.7
    door(m, mt, dx, w=1.0, h=1.6, glow=True, ajar=0)
    slit(m, mt, -1.2, 0.9)
    return Building('np_knocker', m, w, d, h, doors=[(dx, 'gong')], tall=[(x0, x1, 1.05)], leaves={0: ('big', 1.0, 1.6, 2)})


def five():
    """A small stepped tomb with its door shut, and chalked on the door: BACK IN FIVE MINUTES. The dust on the
    chalk is forty nights deep."""
    w, d, h = 4.5, 3.5, 1.4
    mt = Mats(83, 1); m = Model(); x0, x1 = -w / 2, w / 2
    niche = M('bone', 4.7, m_niches(6, 3))
    m.part(); m.box(x0, 0, 0, x1, d, h, niche, top=mt.roof)
    m.part(); m.box(x0 - PX, -PX, 0, x1 + PX, d, 0.3, stone(), top=mt.trim)
    m.part(); m.box(x0 - PX, -PX, h - PX, x1 + PX, PX, h, mt.trim)
    m.part(); m.box(-1.5, 0.9, h, 1.5, d - 0.3, h + 0.8, niche, top=mt.roof)
    m.part(); m.box(-1.5 - PX, 0.9 - PX, h + 0.8 - PX, 1.5 + PX, 0.9 + PX, h + 0.8, mt.trim)
    merlons(m, mt.trim, -1.5, 1.5, 0.9, 1.04, h + 0.8, mw=0.24, mh=0.18)
    door(m, mt, 0.0, w=0.9, h=1.2, glow=False, ajar=0)
    ghost_lamp(m, 1.1, -0.3, lit=False)
    return Building('np_five', m, w, d, h, doors=[(0.0, 'bar')], tall=[(-1.6, 1.6, 0.9)], leaves={0: ('chalked', 0.9, 1.2, 3)}, extra=[(0.95, -0.45, 1.25, 0)])


def reader():
    """A scribe's tomb. He had his own work cut right round the house, where other men have a line of blue, and
    stopped the mason at tablet nine. From inside, somebody is reading aloud to somebody else. Neither of them is
    enjoying it."""
    w, d, h = 6.5, 3.5, 2.0
    mt = Mats(85, 1); m = Model(); x0, x1 = -w / 2, w / 2
    base(m, mt, x0, x1, d, h)
    parapet(m, mt, x0, 0, x1, d, h, h=0.2)
    m.part(); m.box(x0 - PX, -0.5 * PX, h - 0.9, x1 + PX, 0, h - 0.14, M('stone', 4.6, m_cuneiform(4)))
    dx = 1.6
    door(m, mt, dx)
    for wx in (-2.2, -1.2, -0.2):
        slit(m, mt, wx, 0.62, w=0.2, h=0.42)
    # tablets stacked by the door: the ones there was no room for inside
    for k in range(5):
        m.part(); m.box(dx - 1.3 + 0.03 * (k % 2), -0.36, 0.09 * k, dx - 0.82 + 0.03 * (k % 2), -0.06, 0.09 * k + 0.08, M('clay', 4.3 + 0.2 * (k % 2), m_cuneiform(3)))
    return Building('np_reader', m, w, d, h, doors=[(dx, 'open')], extra=[(dx - 1.35, -0.4, dx - 0.78, 0)])


def pillow():
    """A round tomb, the old kind: a drum of stone and a beehive over it. A night watchman's, by the rattle cut
    over the door. The lamp at the door has gone out, and whoever is inside will not open to the dark."""
    r = 2.4; h = 1.3
    mt = Mats(87, 1); m = Model()
    wall = M('bone', 4.9, m_mottle(24, 0.3))
    m.part(); m.turned(0, r, [(r, 0.0), (r, h)], wall, n=24)
    m.part(); m.turned(0, r, [(r + 0.05, 0.0), (r + 0.05, 0.3)], stone(), n=24, cap=mt.trim)
    m.part(); m.turned(0, r, [(r + 0.04, h - 0.06), (r + 0.04, h + 0.06)], mt.trim, n=24, cap=mt.trim)
    houses.dome(m, tile(), 0, r, r - 0.08, h + 0.06, rise=1.55, n=22, cap=M('gold', 4.2))
    m.part(); m.turned(0, r, [(0.1, h + 1.58), (0.13, h + 1.72), (0.05, h + 1.9)], M('gold', 4.2), n=8, cap=M('gold', 4.8))
    # the door is in the round of the wall: a porch of two jambs stands out to meet the street
    for sx in (-0.62, 0.62):
        m.part(); m.box(sx - 0.1, -0.1, 0, sx + 0.1, 0.34, 1.58, M('stone', 4.3, m_mottle(7, 0.3)), top=M('stone', 4.8))
    m.part(); m.box(-0.78, -0.12, 1.58, 0.78, 0.34, 1.78, M('stone', 4.8, m_cuneiform(4)), top=M('stone', 5.0))
    m.part(); m.quad((-0.52, -0.02, 0), (0.52, -0.02, 0), (0.52, -0.02, 1.58), (-0.52, -0.02, 1.58), mt.dark)
    m.part(); m.box(-0.72, -0.42, 0, 0.72, 0, 2 * PX, M('stone', 4.7, m_mottle(6, 0.25)))
    # (it is round: what the map is told is the part of it that meets the street, and then the rest of the drum, stepping back)
    up = r * 2 + h + 1.75
    return Building('np_pillow', m, 2.6, r * 2, h, doors=[(0.0, 'lit')], door_w=1.0, tall=[(-1.3, 1.3, 1.75)], leaves={0: ('plain', 1.0, 1.5, 3)},
                    extra=[(-1.9, 0.35, -1.3, up), (1.3, 0.35, 1.9, up), (-r, 0.9, -1.9, up), (1.9, 0.9, r, up)])


# ------------------------------------------------------------------ things that stand outside them
def stone_sheep(seed=0):
    """A sheep cut in stone, the size of a sheep. He had six made. People leave them a little grass, to be kind."""
    r = rnd(seed); m = Model()
    st = M('stone', 4.4, m_mottle(5, 0.35))
    m.part(); m.blob(0, 0.2, 0.34, 0.36, 0.2, 0.2, st, seed=seed, bump=0.05, n=9, rings=5)
    m.part(); m.blob(0.36, 0.16, 0.44, 0.13, 0.1, 0.11, M('stone', 3.9), n=7, rings=4)
    m.part()
    for (lx, ly) in ((-0.22, 0.12), (0.2, 0.12), (-0.22, 0.28), (0.2, 0.28)):
        m.box(lx - 0.04, ly - 0.04, 0, lx + 0.04, ly + 0.04, 0.2, M('stone', 3.8))
    return m


def name_stone(seed=0):
    """The stone by a door on this hill, that says who is behind it: low, square, and kept clean."""
    m = Model()
    st = M('stone', 4.5, m_cuneiform(4))
    m.part(); m.box(-0.34, 0.0, 0, 0.34, 0.16, 0.74, st, top=M('stone', 5.0))
    m.part(); m.box(-0.4, -0.04, 0, 0.4, 0.2, 0.1, M('stone', 3.8), top=M('stone', 4.4))
    return m


def thorn_tree(seed=0, s=1.0):
    """The tree the dead plant along their ways: bare, pale as a bone, and clipped to a round head all the same,
    because a hedge is a hedge. The same tree every time."""
    r = rnd(seed); m = Model()
    bark = M('bone', 3.6, m_mottle(5, 0.4))
    m.part(); m.limb([(0, 0.3, 0), (0.02, 0.3, 0.8 * s)], [0.16 * s, 0.1 * s], bark, n=7)
    m.part()
    for i in range(11):
        a = 2 * math.pi * i / 11 + float(r.uniform(-0.2, 0.2)); el = float(r.uniform(0.15, 1.25))
        tip = (math.cos(a) * math.cos(el) * 0.8 * s, 0.3 + math.sin(a) * math.cos(el) * 0.5 * s, (0.8 + math.sin(el) * 0.85) * s)
        mid = (tip[0] * 0.5, 0.3 + (tip[1] - 0.3) * 0.5, (0.8 + (tip[2] / s - 0.8) * 0.6) * s)
        m.limb([(0.02, 0.3, 0.8 * s), mid, tip], [0.07 * s, 0.045 * s, 0.02 * s], bark, n=5)
    return m


# ------------------------------------------------------------------ what they keep indoors
def stone_bed(l=2.2, w=1.0, seed=0, pillow=True):
    """A bed for somebody who will not be getting up: a slab on two blocks, its head to the west, and a pillow
    cut from the same stone, with the dent of a head worn into it."""
    m = Model()
    st = M('stone', 4.2, m_mottle(9, 0.3)); top = M('stone', 4.9, m_mottle(9, 0.25))
    m.part(); m.box(0.1, 0.08, 0, 0.5, w - 0.08, 0.3, M('stone', 3.6, m_ashlar(8, 6)))
    m.box(l - 0.5, 0.08, 0, l - 0.1, w - 0.08, 0.3, M('stone', 3.6, m_ashlar(8, 6)))
    m.part(); m.box(0, 0, 0.3, l, w, 0.42, st, top=top)
    if pillow:
        m.part(); m.box(0.08, 0.14, 0.42, 0.52, w - 0.14, 0.56, M('alabaster', 4.6), top=M('alabaster', 5.2))
        m.part(); m.box(0.2, w * 0.36, 0.55, 0.42, w * 0.64, 0.565, M('alabaster', 4.4))
    return m


def double_bed(l=2.2, w=2.3):
    """A bed for two, in one piece of stone, and down the middle of it every urn in the house, in a row. Neither
    of them will say who started that."""
    m = stone_bed(l, w, 3, pillow=False)
    for yy in (0.2, w - 0.66):
        m.part(); m.box(0.08, yy, 0.42, 0.52, yy + 0.46, 0.56, M('alabaster', 4.6), top=M('alabaster', 5.2))
    for k in range(6):
        x = 0.3 + k * (l - 0.5) / 5
        m.part(); m.turned(x, w / 2, [(0.07, 0.42), (0.11, 0.5), (0.1, 0.6), (0.05, 0.66)], M(('clay', 'tomb', 'clay')[k % 3], 4.2 + 0.2 * (k % 2)), n=7, cap=M('dark', 1.6))
    return m


def plinth(h=0.62):
    """A block of dressed stone to stand on. It is in his will."""
    m = Model()
    m.part(); m.box(-0.5, 0, 0, 0.5, 0.6, h, M('stone', 4.1, m_ashlar(8, 6)), top=M('stone', 4.9, m_mottle(6, 0.25)))
    m.part(); m.box(-0.56, -0.04, 0, 0.56, 0.64, 0.1, M('stone', 3.6), top=M('stone', 4.4))
    m.part(); m.box(-0.5, -0.5 * PX, h - 0.14, 0.5, 0, h - 0.06, M('gold', 4.2))
    return m


def banquet(w=5.0, d=1.0, h=0.5):
    """A table laid for twelve, forty nights ago and every night for two hundred years before that: bowls, cups,
    bread gone to stone, and at one end a place where somebody has actually been sitting."""
    m = Model()
    wood = M('cedar', 3.8, m_planks(4, 'h', knots=False))
    m.part()
    for x in (0.08, w - 0.2):
        for y in (0.08, d - 0.2):
            m.box(x, y, 0, x + 0.12, y + 0.12, h - 0.06, M('cedar', 3.2))
    m.part(); m.box(0, 0, h - 0.08, w, d, h, wood, top=M('cedar', 4.5, m_planks(4, 'h', knots=False)))
    m.part(); m.box(0.3, 0.3, h, w - 0.3, d - 0.3, h + 0.012, M('lapis', 3.0, m_mottle(8, 0.3), soft=True))            # a runner down the middle of it
    dust = M('bone', 4.6, m_mottle(4, 0.3))
    for k in range(6):
        x = 0.5 + k * (w - 1.0) / 5
        for y in (0.2, d - 0.2):
            m.part(); m.turned(x, y, [(0.04, h), (0.12, h + 0.04), (0.13, h + 0.06)], dust if k else M('gold', 4.3, gloss=0.03), n=8, cap=M('bone', 4.0) if k else M('fig', 3.2))
            m.part(); m.turned(x + 0.18, y, [(0.03, h), (0.045, h + 0.1)], dust if k else M('gold', 4.5, gloss=0.03), n=6, cap=M('dark', 1.6))
    for k, x in enumerate((w * 0.3, w * 0.5, w * 0.7)):
        m.part(); m.blob(x, d / 2, h + 0.08, 0.2, 0.14, 0.09, M('bone', 4.2, m_mottle(3, 0.5)), n=8, rings=4, seed=k)       # bread
    m.part(); m.turned(w * 0.5 + 0.5, d / 2, [(0.06, h), (0.12, h + 0.2), (0.08, h + 0.34), (0.05, h + 0.4)], M('bronze', 4.0, gloss=0.03), n=8, cap=M('dark', 1.4))
    return m


def sandal_row(n=4):
    """Sandals, in a row, toes to the wall. Other people's."""
    m = Model()
    for k in range(n):
        for sx in (0.0, 0.14):
            x = k * 0.42 + sx
            m.part(); m.box(x, 0.0, 0, x + 0.1, 0.28, 0.03, M(('wood', 'cedar', 'reed', 'wood')[k % 4], 4.0 + 0.2 * (k % 2)))
            m.part(); m.box(x, 0.16, 0.03, x + 0.1, 0.19, 0.05, M('red' if k == 2 else 'cedar', 3.4))
    return m


def broom_bucket():
    """A broom worn to a stump, and a bucket. The water in the bucket is cleaner than most people's cups."""
    m = Model()
    m.part(); m.beam((0.0, 0.3, 0.12), (0.12, 0.02, 1.5), 1.1 * PX, M('wood', 4.4))
    m.part(); m.blob(-0.02, 0.34, 0.12, 0.15, 0.08, 0.13, M('reed', 4.0, m_planks(2, 'v', knots=False)), n=7, rings=4)
    m.part(); m.turned(0.56, 0.24, [(0.15, 0), (0.19, 0.34)], M('wood', 4.2, m_planks(3, 'v', knots=False)), n=10, cap=Mat(RAMPS['water'], 3.4))
    m.part(); m.turned(0.56, 0.24, [(0.2, 0.26), (0.2, 0.3)], M('bronze', 3.8), n=10)
    return m


ALL = [sweeper, shepherd, proud, couple, rich, knocker, five, reader, pillow]
