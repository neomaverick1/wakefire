"""The insides of houses. Every room is a cell of its own on a floor of rooms (dkit), so every
room is its own screen: a north wall with its face showing, plastered and painted the way that
house does it, the tops of the other three, and the dark of the rest of the building round it.
No two rooms get the same wall, the same floor or the same furniture."""
import math
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
import forge
from forge import Model, M, Mat, RAMPS, hash2, m_brick, m_ashlar, m_plaster, m_planks, m_mottle, m_stripes, m_reeds, fbm
import town
from town import Mats, PX, rnd, jar
import houses
import tombs
import hkit
import kit
import dkit
from dkit import Floor, CW, CH, NW, SW, EW, DW, DH

MT = Mats(0, 0)


# ------------------------------------------------------------------ the wall of a room
def house_wall(length, doors=(), clear=(), plaster=('limewash', 4.4), dado=('red', 3.4), band=None, foot='brick', hang=(), beams=True, h=2.75, d=0.25, seed=0, fresh=False):
    """A room's north wall, running east from the origin. plaster: its colour; dado: the painted
    lower part; band: a painted line of pattern under the ceiling ('zigzag', 'cones', 'lines', 'writing');
    hang: (x, what) = what is on it or let into it, x in tiles from its west end: 'window', 'niche' (a lamp,
    lit), 'shelf' / 'bread' / 'tablets' / 'cloth' / 'cups' (a shelf of them), 'herbs', 'net', 'rug', 'tools', 'shield'."""
    m = Model()
    r = rnd(seed)
    body = M(plaster[0], plaster[1], m_plaster(bricks=True, crack=True), ramp2='brick')
    if fresh:                       # a wall somebody keeps: no brick showing, not a crack in it
        body = M(plaster[0], plaster[1], m_mottle(24, 0.3))
    top = M(plaster[0], plaster[1] + 0.5, m_mottle(14, 0.3))
    m.part(); m.box(0, 0, 0, length, d, h, body, top=top)
    if foot == 'stone':
        m.part(); m.box(0, -PX, 0, length, d, 0.5, M('stone', 3.7, m_ashlar(12, 6)), top=M('stone', 4.5))
    else:
        m.part(); m.box(0, -PX, 0, length, d, 0.34, M('brick', 3.5, m_brick(8, 4, -1.0, 0.8)), top=M('brick', 4.3))
    z0 = 0.5 if foot == 'stone' else 0.34
    if dado:
        m.part(); m.quad((0, -0.5 * PX, z0), (length, -0.5 * PX, z0), (length, -0.5 * PX, 1.2), (0, -0.5 * PX, 1.2), M(dado[0], dado[1], m_mottle(12, 0.45)))
        m.part(); m.box(0, -0.7 * PX, 1.2, length, 0, 1.2 + PX, M(dado[0], dado[1] - 1.2))
    if band:
        mark = {'zigzag': houses.m_zigzag(8, 3, 2), 'cones': houses.m_cones(6, 3), 'lines': houses.m_band(((1, 1), (4, 1))), 'writing': town.m_cuneiform(5),
                'flock': tombs.m_flock(9)}[band[0]]
        m.part(); m.quad((0, -0.5 * PX, h - 0.78), (length, -0.5 * PX, h - 0.78), (length, -0.5 * PX, h - 0.42), (0, -0.5 * PX, h - 0.42), M(band[1], band[2], mark, ramp2=band[3] if len(band) > 3 else 'dark'))
    if beams:
        m.part()
        n = int(length / 0.9)
        for i in range(n + 1):
            x = (length - n * 0.9) / 2 + i * 0.9
            m.box(x - 1.5 * PX, -0.16, h - 0.3, x + 1.5 * PX, 0, h - 0.08, M('wood', 3.9))
    m.part(); m.box(0, -1.5 * PX, h - 0.1, length, d, h, M('wood', 3.4), top=top)

    def near(x, margin):
        return any(abs(x - dx) < DW / 2 + margin for dx in tuple(doors) + tuple(clear))
    for (x, what) in hang:
        if near(x, 0.3):
            continue
        if what == 'window':
            m.part(); m.box(x - 0.42, -0.05, 1.42, x + 0.42, 0, 2.16, M('wood', 3.6))
            m.part(); m.quad((x - 0.34, -0.06, 1.5), (x + 0.34, -0.06, 1.5), (x + 0.34, -0.06, 2.08), (x - 0.34, -0.06, 2.08), M('lapis', 1.6, m_mottle(5, 0.6)))
            m.part()
            for bx in (-0.12, 0.12):
                m.box(x + bx - PX / 2, -0.08, 1.5, x + bx + PX / 2, -0.06, 2.08, M('wood', 3.2))
            m.part(); m.box(x - 0.46, -0.12, 1.4, x + 0.46, 0, 1.46, M('wood', 4.4))
        elif what == 'niche':
            m.part(); m.box(x - 0.24, -0.03, 1.3, x + 0.24, 0, 1.78, M('dark', 1.8))
            m.part(); m.quad((x - 0.2, -0.035, 1.32), (x + 0.2, -0.035, 1.32), (x + 0.2, -0.035, 1.62), (x - 0.2, -0.035, 1.62), Mat(RAMPS['glow'], 0.9, glow=True))
            m.part(); m.blob(x, -0.06, 1.36, 0.1, 0.06, 0.05, M('clay', 4.4), n=7, rings=3)
            m.part(); m.blob(x + 0.07, -0.06, 1.45, 0.035, 0.03, 0.07, Mat(RAMPS['glow'], 2.6, glow=True), n=5, rings=3)
            m.part(); m.box(x - 0.28, -0.08, 1.24, x + 0.28, 0, 1.3, top)
        elif what == 'spirit':
            # a niche with one of the lamps the dead keep in it: the colour of the inside of a wave
            m.part(); m.box(x - 0.24, -0.03, 1.3, x + 0.24, 0, 1.78, M('dark', 1.8))
            m.part(); m.quad((x - 0.2, -0.035, 1.32), (x + 0.2, -0.035, 1.32), (x + 0.2, -0.035, 1.62), (x - 0.2, -0.035, 1.62), Mat(RAMPS['ghost'], 0.8, glow=True))
            m.part(); m.blob(x, -0.06, 1.36, 0.1, 0.06, 0.05, M('bronze', 3.6), n=7, rings=3)
            m.part(); m.blob(x + 0.07, -0.06, 1.45, 0.035, 0.03, 0.07, Mat(RAMPS['ghost'], 3.8, glow=True), n=5, rings=3)
            m.part(); m.box(x - 0.28, -0.08, 1.24, x + 0.28, 0, 1.3, top)
        elif what == 'moon':
            # the sign of the hill, let into the wall: a moon with its horns up
            m.part(); m.face([(x + 0.36 * math.cos(a), 1.74 + 0.36 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)], -0.04, M('lapis', 3.4))
            aa = np.linspace(math.radians(200), math.radians(340), 8)
            outer = [(x + math.cos(t) * 0.27, 1.74 + math.sin(t) * 0.27) for t in aa]
            inner = [(x + math.cos(t) * 0.265, 1.74 + 0.135 + math.sin(t) * 0.24) for t in aa]
            m.part()
            for i in range(7):
                m.quad((outer[i][0], -0.05, outer[i][1]), (outer[i + 1][0], -0.05, outer[i + 1][1]), (inner[i + 1][0], -0.05, inner[i + 1][1]), (inner[i][0], -0.05, inner[i][1]), M('gold', 4.4), two=True)
        elif what == 'falsedoor':
            # a door painted on the wall, for a spirit to come and go by: it has never needed to
            m.part(); m.box(x - 0.56, -0.05, z0, x + 0.56, 0, 2.06, M('stone', 4.4, m_mottle(8, 0.3)))
            m.part(); m.quad((x - 0.4, -0.06, z0), (x + 0.4, -0.06, z0), (x + 0.4, -0.06, 1.86), (x - 0.4, -0.06, 1.86), M('red', 2.6, m_planks(3, 'v', knots=False)))
            m.part(); m.box(x - 0.62, -0.08, 2.06, x + 0.62, 0, 2.18, M('stone', 4.9))
        elif what in ('shelf', 'bread', 'tablets', 'cloth', 'cups'):
            for z in (1.0, 1.62):
                m.part(); m.box(x - 0.8, -0.3, z - PX, x + 0.8, 0, z, M('wood', 4.5), top=M('wood', 4.9))
                m.part()
                for bx in (-0.72, 0.68):
                    m.box(x + bx, -0.28, z - 0.2, x + bx + PX, -0.02, z - PX, M('wood', 3.6))
                k = 0
                cx = x - 0.62
                while cx < x + 0.7:
                    if what == 'shelf':
                        jar(m, MT, cx, -0.15, z, s=0.42 + 0.1 * ((k * 5) % 3), kind=(0, 1, 0, 2)[k % 4], mat=(MT.pot, MT.pot2, M('clay', 4.0))[k % 3], n=7)
                        cx += 0.3
                    elif what == 'bread':
                        m.part(); m.blob(cx + 0.05, -0.15, z + 0.07, 0.16, 0.11, 0.075, M(('straw', 'wood', 'straw')[k % 3], (3.7, 4.6, 4.3)[k % 3], m_mottle(3, 0.5)), n=7, rings=4, seed=k)
                        cx += 0.36
                    elif what == 'tablets':
                        n = 2 + (k * 3) % 4
                        for q in range(n):
                            m.part(); m.box(cx - 0.02 + 0.01 * q, -0.26, z + q * 0.055, cx + 0.3, -0.04, z + (q + 1) * 0.055, M(('clay', 'sandstone', 'clay')[(k + q) % 3], 4.0 + 0.3 * ((k + q) % 2), m_mottle(4, 0.4)))
                        cx += 0.4
                    elif what == 'cloth':
                        m.part(); m.box(cx - 0.02, -0.27, z, cx + 0.3, -0.04, z + 0.12 + 0.05 * (k % 2), M(('red', 'blue', 'ochre', 'cream', 'fig', 'green')[k % 6], 4.0, m_stripes(3, 'u'), ramp2='linen', soft=True))
                        cx += 0.38
                    else:
                        m.part(); m.turned(cx + 0.04, -0.15, [(0.04, z), (0.06, z + 0.03), (0.03, z + 0.08), (0.09, z + 0.2)], M(('bronze', 'clay', 'clay')[k % 3], 4.4), n=7, cap=M('dark', 1.4))
                        cx += 0.26
                    k += 1
        elif what == 'herbs':
            m.part(); m.box(x - 0.7, -0.08, 2.0, x + 0.7, -0.04, 2.05, M('wood', 4.2))
            for k in range(5):
                cx = x - 0.56 + k * 0.28
                m.part(); m.blob(cx, -0.1, 1.76 - 0.04 * (k % 2), 0.09, 0.06, 0.2, M(('olive', 'green', 'straw', 'olive', 'red')[k], 3.6, m_mottle(3, 0.6), soft=True), n=6, rings=4, seed=k)
        elif what == 'net':
            g = np.zeros((6, 8, 3))
            for i in range(6):
                for q in range(8):
                    t, s = i / 5.0, q / 7.0
                    g[i, q] = (x - 0.9 + 1.8 * s, -0.06 - 0.1 * math.sin(math.pi * s) * t, 2.1 - 1.2 * t + 0.14 * math.sin(s * 9) * t)
            m.part(); m.sheet(g, M('straw', 3.9, houses.m_lattice(3), soft=True))
            m.part()
            for sx in (-0.9, 0.9):
                m.box(x + sx - PX, -0.1, 2.06, x + sx + PX, 0, 2.16, M('wood', 3.4))
        elif what == 'rug':
            m.part(); m.quad((x - 0.7, -0.05, 0.9), (x + 0.7, -0.05, 0.9), (x + 0.7, -0.05, 2.1), (x - 0.7, -0.05, 2.1), M('red', 3.5, houses.m_zigzag(8, 3, 2), ramp2='gold', soft=True))
            m.part(); m.box(x - 0.76, -0.08, 2.1, x + 0.76, 0, 2.16, M('wood', 4.2))
        elif what == 'tools':
            m.part(); m.box(x - 0.6, -0.08, 1.9, x + 0.6, -0.03, 1.96, M('wood', 4.2))
            for k, tx in enumerate((-0.45, -0.15, 0.15, 0.45)):
                m.part(); m.beam((x + tx, -0.08, 1.9), (x + tx, -0.06, 1.2 + 0.1 * (k % 2)), 0.8 * PX, M('wood', 4.6))
                m.part(); m.box(x + tx - 0.07, -0.09, 1.14 + 0.1 * (k % 2), x + tx + 0.07, -0.05, 1.26 + 0.1 * (k % 2), M(('bronze', 'iron', 'wood', 'bronze')[k], 4.2))
        elif what == 'shield':
            m.part(); m.face([(x + 0.36 * math.cos(a), 1.7 + 0.36 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)], -0.05, M('bronze', 4.2, gloss=0.03))
            m.part(); m.face([(x + 0.1 * math.cos(a), 1.7 + 0.1 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)], -0.07, M('bronze', 5.0, gloss=0.04))
    # doorways: a frame of cedar, a dark way through
    for dx in doors:
        a, b = dx - DW / 2, dx + DW / 2
        m.part(); m.box(a - 0.2, -0.2, 0, b + 0.2, 0, DH + 0.28, M(plaster[0], plaster[1] - 0.5, m_mottle(12, 0.4)), top=top)
        m.part(); m.quad((a, -0.21, 0), (b, -0.21, 0), (b, -0.21, DH), (a, -0.21, DH), M('dark', 1.1))
        m.part()
        for sx in (a - 0.1, b):
            m.box(sx, -0.24, 0, sx + 0.1, -0.2, DH + 0.1, M('cedar', 4.0, m_planks(3, 'v', knots=False)))
        m.box(a - 0.16, -0.25, DH, b + 0.16, -0.2, DH + 0.14, M('cedar', 4.3, m_planks(3, 'h', knots=False)))
    return m


# ------------------------------------------------------------------ furniture
def bed(seed=0, colour='red', w=1.0, l=1.9, made=True):
    """A bed: palm wood strung with rope, a mattress of reed, a blanket, somebody's shape still in it or not."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for x in (0.03, w - 0.12):
        for y in (0.03, l - 0.12):
            m.box(x, y, 0, x + 0.09, y + 0.09, 0.3, mt.beam)
    m.part(); m.box(0, 0, 0.2, w, l, 0.3, mt.wood_h, top=M('linen', 4.3, m_mottle(6, 0.3), soft=True))
    bl = M(colour, 3.7, m_stripes(5, 'v'), ramp2='cream', soft=True)
    if made:
        m.part(); m.box(0.02, 0.0, 0.3, w - 0.02, l * 0.64, 0.37, bl, top=M(colour, 4.1, m_stripes(5, 'v'), ramp2='cream', soft=True))
    else:
        m.part(); m.blob(w * 0.5, l * 0.3, 0.36, w * 0.5, l * 0.26, 0.1, bl, n=8, rings=4, seed=seed, bump=0.2)
    m.part(); m.blob(w / 2, l - 0.22, 0.36, w * 0.36, 0.15, 0.07, M('linen', 4.9, soft=True), n=8, rings=4)
    m.part(); m.box(0, l - 0.06, 0.3, w, l, 0.62, mt.wood_h, top=M('wood', 4.9))
    return m


def bed_h(seed=0, colour='red', l=2.2, w=0.95):
    """A bed set along a wall, for somebody to be asleep on: head to the west on the pillow, the blanket
    kicked down to the foot of it (it has been a warm forty nights)."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for x in (0.03, l - 0.12):
        for y in (0.03, w - 0.12):
            m.box(x, y, 0, x + 0.09, y + 0.09, 0.3, mt.beam)
    m.part(); m.box(0, 0, 0.2, l, w, 0.3, mt.wood_h, top=M('linen', 4.3, m_mottle(6, 0.3), soft=True))
    m.part(); m.box(0, 0, 0.3, 0.07, w, 0.6, mt.wood_h, top=M('wood', 4.9))
    m.part(); m.blob(0.3, w / 2, 0.36, 0.17, w * 0.34, 0.07, M('linen', 4.9, soft=True), n=8, rings=4)
    bl = M(colour, 3.7, m_stripes(5, 'u'), ramp2='cream', soft=True)
    m.part(); m.blob(l - 0.32, w / 2, 0.38, 0.24, w * 0.42, 0.09, bl, n=8, rings=4, seed=seed, bump=0.2)
    return m


def table(w=1.5, d=0.9, h=0.5, seed=0, things=None):
    """things: 'coins', 'cups', 'bread', 'scales', 'tablets', 'bones' (knuckle-bones: the oracle's), 'dough'."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for x in (0.05, w - 0.13):
        for y in (0.05, d - 0.13):
            m.box(x, y, 0, x + 0.08, y + 0.08, h - 0.06, mt.beam)
    m.part(); m.box(0, 0, h - 0.07, w, d, h, mt.wood_h, top=M('wood', 4.9, m_planks(4, 'h')))
    r = rnd(seed + 3)
    if things == 'coins':
        for k in range(5):
            cx, cy = float(r.uniform(0.2, w - 0.2)), float(r.uniform(0.2, d - 0.2))
            n = int(r.integers(2, 6))
            m.part(); m.cyl(cx, cy, h, h + 0.035 * n, 0.07, M('gold', 4.2, gloss=0.03), n=7, cap=M('gold', 5.0, gloss=0.04))
        m.part(); m.box(w - 0.5, 0.15, h, w - 0.14, 0.4, h + 0.05, M('clay', 4.2, town.m_cuneiform(4)))
    elif things == 'cups':
        for k in range(4):
            cx, cy = 0.25 + k * (w - 0.5) / 3, 0.25 + 0.3 * (k % 2)
            m.part(); m.turned(cx, cy, [(0.04, h), (0.065, h + 0.14)], mt.pot if k % 2 else mt.pot2, n=7, cap=mt.dark)
        jar(m, mt, w / 2, d / 2, h, s=0.5, kind=0, mat=mt.pot2)
    elif things == 'bread':
        for k in range(4):
            m.part(); m.blob(0.3 + k * (w - 0.6) / 3, 0.3 + 0.25 * (k % 2), h + 0.07, 0.17, 0.12, 0.08, M(('straw', 'wood')[k % 2], 4.0 + 0.4 * (k % 2), m_mottle(3, 0.5)), n=7, rings=4, seed=k)
    elif things == 'scales':
        cx, cy = w / 2, d / 2
        m.part(); m.box(cx - 0.03, cy - 0.03, h, cx + 0.03, cy + 0.03, h + 0.6, mt.bronze)
        m.part(); m.box(cx - 0.36, cy - PX / 2, h + 0.56, cx + 0.36, cy + PX / 2, h + 0.6, mt.bronze)
        for sx, dz in ((-0.34, -0.06), (0.34, 0.08)):
            m.part(); m.box(cx + sx - PX / 2, cy - PX / 2, h + 0.3 + dz, cx + sx + PX / 2, cy + PX / 2, h + 0.56, mt.rope)
            m.part(); m.turned(cx + sx, cy, [(0.02, h + 0.22 + dz), (0.14, h + 0.28 + dz), (0.15, h + 0.3 + dz)], mt.bronze, n=8, cap=M('bronze', 3.2))
        m.part(); m.cyl(cx - 0.34, cy, h + 0.24, h + 0.3, 0.06, M('gold', 4.4, gloss=0.03), n=6)
    elif things == 'tablets':
        for k in range(6):
            cx, cy = float(r.uniform(0.15, w - 0.45)), float(r.uniform(0.1, d - 0.4))
            m.part(); m.box(cx, cy, h + 0.05 * (k % 3), cx + 0.3, cy + 0.24, h + 0.05 * (k % 3) + 0.05, M(('clay', 'sandstone')[k % 2], 4.2, town.m_cuneiform(3)), top=M(('clay', 'sandstone')[k % 2], 4.6, town.m_cuneiform(3)))
    elif things == 'bones':
        m.part(); m.box(0.2, 0.15, h, w - 0.2, d - 0.15, h + 0.02, M('fig', 3.4, soft=True))
        for k in range(5):
            m.part(); m.blob(float(r.uniform(0.35, w - 0.35)), float(r.uniform(0.25, d - 0.25)), h + 0.05, 0.05, 0.035, 0.03, M('bone', 4.8), n=5, rings=3, seed=k)
    elif things == 'dough':
        m.part(); m.box(0.1, 0.1, h, w - 0.1, d - 0.1, h + 0.12, M('wood', 4.0, m_planks(4, 'h')), top=M('wood', 3.2))
        m.part(); m.blob(w / 2, d / 2, h + 0.3, w * 0.36, d * 0.3, 0.3, M('linen', 5.0, m_mottle(6, 0.3), soft=True), n=10, rings=6, bump=0.12)
    return m


def stool(seed=0):
    m = Model()
    m.part(); m.turned(0, 0.2, [(0.16, 0), (0.1, 0.12), (0.12, 0.24), (0.19, 0.3)], M('wood', 4.3), n=9, cap=M('reed', 4.5, m_reeds(2)))
    return m


def counter(w=3.0, d=0.6, h=0.66, seed=0, plaster=1):
    """A shop's counter: mud brick, plastered, a top of palm planks worn pale by elbows."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(0, 0, 0, w, d, h, mt.wall_plain, top=M('wood', 4.8, m_planks(4, 'h')))
    m.part(); m.box(-PX, -PX, h - 0.07, w + PX, d + PX, h, M('wood', 4.4, m_planks(4, 'h')), top=M('wood', 4.9, m_planks(4, 'h')))
    m.part(); m.box(-PX / 2, -PX / 2, 0, w + PX / 2, d, 0.14, mt.plinth, top=mt.trim)
    return m


def rack(w=1.6, what='jars', seed=0, rows=2):
    """Shelves standing on their own feet, with what the house keeps on them."""
    m = Model(); mt = Mats(seed, 0)
    h = 0.55 + 0.6 * rows
    m.part()
    for x in (0, w - 0.08):
        m.box(x, 0, 0, x + 0.08, 0.4, h, mt.beam)
    for k in range(rows + 1):
        z = 0.12 + k * 0.6
        m.part(); m.box(0, 0, z - 0.05, w, 0.4, z, mt.wood_h, top=M('wood', 4.8))
        if k == rows:
            break
        cx = 0.2; q = 0
        while cx < w - 0.15:
            if what == 'jars':
                jar(m, mt, cx, 0.2, z, s=0.5 + 0.12 * ((q * 5 + k) % 3), kind=(0, 1, 3, 0)[(q + k) % 4] if q % 3 else 0, mat=(mt.pot, mt.pot2, M('clay', 4.0))[(q + k) % 3], n=8)
                cx += 0.34
            elif what == 'cloth':
                m.part(); m.box(cx - 0.12, 0.04, z, cx + 0.2, 0.36, z + 0.16 + 0.06 * (q % 2), M(('red', 'blue', 'ochre', 'cream', 'fig', 'green')[(q + k * 2) % 6], 4.0, m_stripes(3, 'u'), ramp2='linen', soft=True))
                cx += 0.38
            elif what == 'tablets':
                n = 2 + (q * 3 + k) % 4
                for j in range(n):
                    m.part(); m.box(cx - 0.1, 0.06, z + j * 0.06, cx + 0.22, 0.34, z + (j + 1) * 0.06, M(('clay', 'sandstone', 'clay')[(q + j) % 3], 4.0 + 0.3 * ((q + j) % 2), m_mottle(4, 0.4)))
                cx += 0.4
            else:
                m.part(); m.blob(cx + 0.04, 0.2, z + 0.08, 0.17, 0.12, 0.08, M(('straw', 'wood', 'straw')[(q + k) % 3], (3.7, 4.6, 4.3)[(q + k) % 3], m_mottle(3, 0.5)), n=7, rings=4, seed=q)
                cx += 0.38
            q += 1
    return m


def loom(seed=0, colours=('red', 'cream'), done=0.45):
    """An upright loom: two posts, the cloth beam over them, the warp hung with clay weights, and as much cloth as
    she had woven when she stopped."""
    m = Model(); mt = Mats(seed, 0)
    w, h = 1.5, 1.7
    m.part()
    for x in (0, w - 0.1):
        m.box(x, 0.1, 0, x + 0.1, 0.22, h, mt.beam)
    m.box(-0.06, 0.08, h - 0.1, w + 0.06, 0.24, h, M('wood', 4.8))
    z1 = h - 0.1; zc = z1 - (z1 - 0.3) * done
    m.part(); m.quad((0.12, 0.1, 0.3), (w - 0.12, 0.1, 0.3), (w - 0.12, 0.1, zc), (0.12, 0.1, zc), M('linen', 4.3, m_stripes(2, 'u'), ramp2='straw', soft=True), two=True)
    m.part(); m.quad((0.12, 0.09, zc), (w - 0.12, 0.09, zc), (w - 0.12, 0.09, z1), (0.12, 0.09, z1), M(colours[0], 4.0, m_stripes(4, 'v'), ramp2=colours[1], soft=True), two=True)
    m.part()
    for k in range(7):
        m.blob(0.2 + k * (w - 0.4) / 6, 0.1, 0.22, 0.05, 0.05, 0.07, M('clay', 4.0), n=5, rings=3)
    m.part(); m.box(0.1, 0.06, zc - 0.03, w - 0.1, 0.12, zc + 0.02, M('wood', 4.9))
    return m


def hearth(frame=0, seed=0):
    """A hearth on the floor: a ring of fired clay, coals, and a fire that nobody has fed in forty nights and that has
    not noticed."""
    m = Model()
    m.part(); m.turned(0, 0.4, [(0.42, 0), (0.46, 0.12), (0.36, 0.16), (0.3, 0.1)], M('clay', 3.6, m_mottle(5, 0.5)), n=12, cap=Mat(RAMPS['glow'], 1.6, town.m_coals(), glow=True), squash=0.8)
    town.flame(m, 0, 0.4, 0.12, s=0.8, frame=frame, seed=seed)
    m.light(0, 0.0, 0.4, 4.2, (1.0, 0.66, 0.32), 0.8)
    return m


def big_jars(n=3, seed=0, straws=False):
    """Storage jars shoulder to shoulder."""
    m = Model(); mt = Mats(seed, 0)
    r = rnd(seed)
    for k in range(n):
        x = k * 0.62
        s = float(r.uniform(0.92, 1.1))
        jar(m, mt, x, 0.3, 0, s=s, kind=3, mat=mt.pot2 if k % 2 else mt.pot, n=10)
        if straws:
            m.part(); m.beam((x + 0.05, 0.3, 0.92 * s), (x + 0.3, 0.16, 1.4 * s), 0.6 * PX, M('straw', 4.6))
    return m


def cradle(seed=0):
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.box(0, 0, 0.1, 0.9, 0.5, 0.36, M('reed', 4.2, m_reeds(2)), top=M('linen', 4.6, soft=True))
    m.part(); m.blob(0.45, 0.25, 0.4, 0.26, 0.14, 0.08, M('blue', 4.0, soft=True), n=7, rings=4)
    m.part()
    for x in (0.05, 0.8):
        m.box(x, -0.04, 0, x + 0.05, 0.54, 0.1, mt.beam)
    return m


def net_heap(seed=0):
    m = Model()
    m.part(); m.blob(0, 0.4, 0.2, 0.7, 0.42, 0.26, M('straw', 3.8, houses.m_lattice(3), soft=True), n=10, rings=6, seed=seed, bump=0.22)
    m.part()
    for k in range(4):
        m.blob(-0.4 + k * 0.3, 0.16 + 0.1 * (k % 2), 0.16, 0.09, 0.09, 0.09, M('cedar', 3.8), n=6, rings=3, seed=k)
    return m


def boat_frame(seed=0):
    """A skiff on trestles with half its planks off: the job he was going to finish in the morning."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for x in (0.5, 2.3):
        m.box(x, 0.05, 0, x + 0.1, 0.85, 0.36, mt.beam)
    for i in range(9):
        t0, t1 = i / 9.0, (i + 1) / 9.0
        xa, xb = 3.0 * t0 - 0.1, 3.0 * t1 - 0.1
        ra = math.sin(math.pi * (t0 + t1) / 2) ** 0.6
        hw = 0.46 * ra; hz = 0.42 * ra
        prof = [(-hw, hz), (-hw * 0.8, hz * 0.3), (0, 0.0), (hw * 0.8, hz * 0.3), (hw, hz)]
        m.part()
        for q, ((ya, za), (yb, zb)) in enumerate(zip(prof[:-1], prof[1:])):
            if i in (3, 4, 5) and q == 0:
                continue                                   # the planks that are off
            m.quad((xa, 0.45 + ya, 0.36 + za), (xb, 0.45 + ya, 0.36 + za), (xb, 0.45 + yb, 0.36 + zb), (xa, 0.45 + yb, 0.36 + zb), M('wood', 4.0, m_planks(3, 'h')), two=True)
    return m


def chewed_table(seed=0):
    """Three legs, and the place where the fourth was eaten."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for (x, y) in ((0.05, 0.05), (1.17, 0.05), (0.05, 0.67)):
        m.box(x, y, 0, x + 0.08, y + 0.08, 0.44, mt.beam)
    m.box(1.17, 0.67, 0.3, 1.25, 0.75, 0.44, mt.beam)
    m.part(); m.box(0, 0, 0.44, 1.3, 0.8, 0.5, mt.wood_h, top=M('wood', 4.8, m_planks(4, 'h')))
    m.part(); m.blob(1.0, 0.5, 0.56, 0.16, 0.12, 0.06, M('cedar', 3.8, soft=True), n=6, rings=3)       # what is left of a sandal
    return m


def door_bar(w=2.6):
    """Two planks across a doorway from inside, in iron hooks."""
    m = Model(); mt = Mats(0, 0)
    for z in (0.34, 0.86):
        m.part(); m.box(-w / 2, 0.02, z, w / 2, 0.12, z + 0.16, M('wood', 4.5, m_planks(3, 'h')), top=M('wood', 4.9))
    m.part()
    for sx in (-w / 2 + 0.1, w / 2 - 0.2):
        m.box(sx, 0.0, 0.26, sx + 0.1, 0.14, 1.1, mt.iron)
    return m


def money_pile(seed=0):
    m = Model(); r = rnd(seed)
    g = M('gold', 4.2, gloss=0.03)
    m.part()
    for k in range(9):
        cx, cy = float(r.uniform(-0.3, 0.3)), 0.3 + float(r.uniform(-0.18, 0.18))
        m.cyl(cx, cy, 0, 0.05 + 0.04 * int(r.integers(1, 5)), 0.07, g, n=7, cap=M('gold', 5.0, gloss=0.04))
    return m


def cushion(colour='fig', seed=0):
    m = Model()
    m.part(); m.blob(0, 0.25, 0.09, 0.3, 0.24, 0.09, M(colour, 3.9, m_stripes(4, 'u'), ramp2='gold', soft=True), n=8, rings=4, seed=seed)
    return m


def censer_stand(frame=0):
    """A bronze bowl on three legs, and what she burns in it."""
    m = Model()
    m.part()
    for a in (0.5, 2.6, 4.7):
        m.beam((math.cos(a) * 0.18, 0.2 + math.sin(a) * 0.1, 0), (0, 0.2, 0.5), PX, M('bronze', 3.8))
    m.part(); m.turned(0, 0.2, [(0.05, 0.46), (0.2, 0.54), (0.22, 0.62)], M('bronze', 4.4, gloss=0.03), n=9, cap=Mat(RAMPS['fig'], 3.2 + 0.5 * (frame % 2), glow=True))
    m.light(0, 0.0, 0.7, 2.6, (0.78, 0.55, 1.0), 0.6)
    return m


def basket(seed=0, full=None):
    """A basket of reed, and whatever is in it: 'wool', 'bread', 'fish', 'onions'."""
    m = Model()
    m.part(); m.turned(0, 0.25, [(0.16, 0), (0.24, 0.16), (0.26, 0.3), (0.23, 0.32)], M('reed', 4.0, m_reeds(2)), n=10, cap=M('dark', 1.6), squash=0.85)
    if full:
        col = {'wool': ('linen', 4.9), 'bread': ('straw', 4.0), 'fish': ('bronze', 4.4), 'onions': ('ochre', 4.4), 'figs': ('fig', 3.4)}[full]
        m.part()
        for k in range(5):
            a = k * 1.3 + seed
            m.blob(math.cos(a) * 0.1, 0.25 + math.sin(a) * 0.07, 0.32 + 0.02 * (k % 2), 0.09, 0.08, 0.07, M(col[0], col[1], m_mottle(3, 0.4), soft=True), n=6, rings=3, seed=k)
    return m


def water_stand(seed=0):
    """A water jar in its stand, with the dipper hung on it."""
    m = Model(); mt = Mats(seed, 0)
    m.part()
    for a in (0.6, 2.7, 4.8):
        m.beam((math.cos(a) * 0.22, 0.25 + math.sin(a) * 0.14, 0), (math.cos(a) * 0.14, 0.25 + math.sin(a) * 0.1, 0.34), 1.2 * PX, mt.beam)
    jar(m, mt, 0, 0.25, 0.26, s=0.9, kind=0, mat=mt.pot2, n=10)
    m.part(); m.beam((0.2, 0.2, 0.74), (0.34, 0.14, 0.5), 0.7 * PX, M('wood', 4.6))
    return m


def lamp_stand(frame=0, h=1.3):
    """A lamp on a tall bronze stand: what a house that can afford the oil reads by."""
    m = Model()
    m.part(); m.turned(0, 0.2, [(0.14, 0), (0.05, 0.08), (0.03, h - 0.1), (0.1, h - 0.04), (0.13, h)], M('bronze', 4.2, gloss=0.03), n=8, cap=M('bronze', 3.4))
    m.part(); m.blob(0.04, 0.2, h + 0.08 + 0.01 * frame, 0.045, 0.04, 0.09 + 0.01 * (frame % 2), Mat(RAMPS['glow'], 2.8, glow=True), n=5, rings=3)
    m.light(0, 0.0, h + 0.1, 4.4, (1.0, 0.74, 0.42), 0.75)
    return m


def cloth_bolts(seed=0, n=5):
    """Cloth in the bolt, stacked as it came off the loom."""
    m = Model(); r = rnd(seed)
    cols = ('red', 'blue', 'ochre', 'cream', 'fig', 'green', 'linen')
    k = 0
    for row in range(2):
        for i in range(n - row):
            x = i * 0.34 + row * 0.17
            m.part(); m.limb([(x, 0.05, 0.12 + row * 0.2), (x, 0.75, 0.12 + row * 0.2)], [0.12, 0.12], M(cols[(k + seed) % len(cols)], 4.0, m_stripes(3, 'u'), ramp2='linen', soft=True), n=7)
            k += 1
    return m


def partition(length, seed=0, plaster=1, h=1.5, d=0.375):
    """A wall inside a house that does not go to the roof: a room made into two."""
    m = Model(); mt = Mats(seed, plaster)
    m.part(); m.box(0, 0, 0, length, d, h, mt.wall_plain, top=mt.trim)
    m.part(); m.box(-PX / 2, -PX / 2, 0, length + PX / 2, d, 0.2, mt.plinth, top=mt.trim)
    m.part(); m.box(-PX, -PX, h, length + PX, d + PX, h + 0.08, M('wood', 4.2), top=M('wood', 4.8))
    return m


def tablet_chest(seed=0):
    """A box of tablets nobody has had the heart to file."""
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.box(0, 0, 0, 0.9, 0.55, 0.4, mt.wood_h, top=M('dark', 1.8))
    r = rnd(seed)
    for k in range(6):
        x = 0.08 + k * 0.13
        m.part(); m.box(x, 0.06, 0.2, x + 0.09, 0.5, 0.46 + float(r.uniform(0, 0.08)), M(('clay', 'sandstone')[k % 2], 4.2, town.m_cuneiform(3)))
    return m


def flour_bin(seed=0):
    """A bin of palm planks with a lid, white with what is in it. It slides, if a man puts his shoulder to it."""
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.box(-0.5, 0.0, 0, 0.5, 0.75, 0.62, M('wood', 4.1, m_planks(4, 'v')), top=M('wood', 4.7, m_planks(4, 'h')))
    m.part()
    for z in (0.12, 0.46):
        m.box(-0.52, -0.02, z, 0.52, 0.77, z + 0.07, M('wood', 3.2))
    m.part(); m.box(-0.54, -0.04, 0.62, 0.54, 0.79, 0.7, M('wood', 4.4, m_planks(4, 'h')), top=M('linen', 4.9, m_mottle(5, 0.4)))
    m.part(); m.blob(0.2, 0.4, 0.74, 0.2, 0.16, 0.05, M('linen', 5.2, soft=True), n=7, rings=3)
    return m


def cellar_door(open_=True):
    """Two leaves of plank let into the ground, with a ring."""
    m = Model(); mt = Mats(0, 0)
    m.part(); m.box(-0.7, 0, 0, 0.7, 1.0, 0.08, mt.beam, top=mt.dark if open_ else M('wood', 4.2, m_planks(4, 'v')))
    if open_:
        m.part(); m.quad((-0.7, 1.0, 0.08), (0.7, 1.0, 0.08), (0.7, 1.12, 0.9), (-0.7, 1.12, 0.9), M('wood', 4.2, m_planks(4, 'v')), two=True)
        m.part()
        for k in range(3):
            m.box(-0.56, 0.12 + k * 0.26, 0.0, 0.56, 0.2 + k * 0.26, 0.05 - 0.01 * k, M('stone', 4.2 - 0.9 * k))
    return m


def table_with(w=1.5, d=0.9, h=0.5, seed=0, things='game'):
    """A table and what is on it: 'game' (the game of twenty squares, half played), 'figs' (two bowls, two cups, set
    for two), 'lamps' (a dozen for sale, three of them burning), 'toys' (what was taken off the boys)."""
    m = table(w, d, h, seed, None)
    mt = Mats(seed, 0)
    if things == 'game':
        m.part(); m.box(w / 2 - 0.42, d / 2 - 0.16, h, w / 2 + 0.42, d / 2 + 0.16, h + 0.04, M('wood', 3.4), top=M('lapis', 3.4, m_ashlar(3, 3), ramp2='bone'))
        for k, (px, py, col) in enumerate(((-0.3, 0.0, 'bone'), (-0.1, 0.06, 'dark'), (0.12, -0.04, 'bone'), (0.3, 0.05, 'dark'), (0.56, 0.2, 'bone'), (-0.58, -0.22, 'dark'))):
            m.part(); m.cyl(w / 2 + px, d / 2 + py, h + (0.04 if abs(px) < 0.42 else 0), h + (0.08 if abs(px) < 0.42 else 0.04), 0.04, M(col, 4.6 if col == 'bone' else 1.8), n=6)
        for k in range(3):
            m.part(); m.blob(0.2 + 0.1 * k, d - 0.22, h + 0.03, 0.035, 0.035, 0.03, M('bone', 4.8), n=4, rings=3, seed=k)
    elif things == 'figs':
        for sx in (0.3, w - 0.3):
            m.part(); m.turned(sx, d / 2, [(0.05, h), (0.15, h + 0.06), (0.16, h + 0.08)], mt.pot2, n=8, cap=M('fig', 3.0))
            for k in range(3):
                m.part(); m.blob(sx + 0.06 * math.cos(k * 2.1), d / 2 + 0.05 * math.sin(k * 2.1), h + 0.11, 0.05, 0.045, 0.05, M('fig', 3.4, soft=True), n=5, rings=3, seed=k)
            m.part(); m.turned(sx + (0.2 if sx < w / 2 else -0.2), d / 2 - 0.2, [(0.03, h), (0.05, h + 0.11)], mt.pot, n=6, cap=mt.dark)
        jar(m, mt, w / 2, d / 2 + 0.12, h, s=0.46, kind=1, mat=mt.pot2)
    elif things == 'lamps':
        k = 0
        for ly in (0.2, d - 0.22):
            for lx in np.arange(0.2, w - 0.1, 0.26):
                m.part(); m.blob(lx, ly, h + 0.04, 0.085, 0.06, 0.045, mt.pot if k % 2 else mt.pot2, n=7, rings=3)
                if k % 4 == 1:
                    m.part(); m.blob(lx + 0.07, ly, h + 0.13, 0.035, 0.03, 0.06, Mat(RAMPS['glow'], 2.6, glow=True), n=5, rings=3)
                k += 1
        m.light(w / 2, d / 2 - 0.3, h + 0.3, 3.2, (1.0, 0.74, 0.42), 0.6)
    elif things == 'toys':
        m.part(); m.blob(0.3, 0.3, h + 0.08, 0.09, 0.09, 0.09, M('red', 3.6, m_stripes(2, 'u'), ramp2='cream', soft=True), n=7, rings=4)      # a ball
        m.part(); m.beam((0.5, 0.2, h + 0.03), (1.1, 0.5, h + 0.03), PX, M('wood', 4.6)); m.box(0.56, 0.16, h, 0.62, 0.32, h + 0.05, M('wood', 4.0))      # a wooden sword
        m.part(); m.beam((0.9, 0.62, h + 0.02), (1.3, 0.7, h + 0.02), 0.5 * PX, M('straw', 4.4)); m.blob(1.3, 0.7, h + 0.03, 0.06, 0.04, 0.02, M('cedar', 3.6, soft=True), n=5, rings=3)   # a sling
        for k in range(4):
            m.part(); m.blob(0.2 + 0.09 * k, d - 0.18, h + 0.03, 0.035, 0.035, 0.03, M('bone', 4.8), n=4, rings=3, seed=k)                              # knuckle-bones
    return m


def keys_peg():
    """A board on the wall with pegs in it, and on one of them a ring of keys."""
    m = Model()
    m.part(); m.box(-0.4, -0.05, 1.3, 0.4, 0, 1.5, M('wood', 4.0, m_planks(3, 'h')))
    m.part()
    for px in (-0.26, 0.0, 0.26):
        m.box(px - PX / 2, -0.14, 1.38, px + PX / 2, -0.05, 1.42, M('wood', 4.8))
    m.part(); m.face([(0.0 + 0.1 * math.cos(a), 1.26 + 0.1 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9, endpoint=False)], -0.13, M('bronze', 4.4, gloss=0.03))
    m.part(); m.face([(0.0 + 0.06 * math.cos(a), 1.26 + 0.06 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 7, endpoint=False)], -0.135, M('wood', 4.0, m_planks(3, 'h')))
    m.part()
    for k, kx in enumerate((-0.06, 0.02, 0.09)):
        m.box(kx - PX / 2, -0.14, 0.98 - 0.03 * k, kx + PX / 2, -0.13, 1.18, M('bronze', 4.6, gloss=0.03))
    return m


def bolt():
    """A bolt of bronze on the inside of a door that does not look like a door from the other side."""
    m = Model()
    m.part(); m.box(-0.3, -0.05, 0.9, 0.3, 0, 1.1, M('wood', 3.6, m_planks(3, 'h')))
    m.part(); m.box(-0.36, -0.1, 0.96, 0.2, -0.05, 1.04, M('bronze', 4.4, gloss=0.03))
    m.part(); m.box(0.06, -0.16, 0.94, 0.12, -0.1, 1.06, M('bronze', 5.0, gloss=0.04))
    return m


def strongbox(seed=0):
    """A chest of cedar under bands of bronze, the size of a bed. He sits on it. He has sat on it so long it has a dip."""
    m = Model(); mt = Mats(seed, 0)
    m.part(); m.box(-0.8, 0, 0, 0.8, 0.8, 0.6, M('cedar', 3.9, m_planks(4, 'h')), top=M('cedar', 4.4, m_planks(4, 'h')))
    m.part()
    for bx in (-0.6, 0.0, 0.52):
        m.box(bx, -PX / 2, 0, bx + 0.08, 0.8 + PX / 2, 0.62, M('bronze', 4.2, gloss=0.03))
    m.part(); m.box(-0.08, -0.03, 0.26, 0.08, 0, 0.44, M('bronze', 4.8, gloss=0.04))
    m.part(); m.box(-0.84, -0.03, 0.56, 0.84, 0.83, 0.62, M('bronze', 3.8, gloss=0.03), top=M('cedar', 4.5, m_planks(4, 'h')))
    return m


def logs(n=5, seed=0, l=1.6):
    """Cedar in the log, stacked: what the house was built on, in every sense."""
    m = Model(); r = rnd(seed)
    k = 0
    for row in range(3):
        for i in range(n - row):
            x = i * 0.36 + row * 0.18
            rad = 0.17 + float(r.uniform(-0.02, 0.02))
            m.part(); m.limb([(x, 0.05, 0.17 + row * 0.3), (x, 0.05 + l, 0.17 + row * 0.3)], [rad, rad], M('cedar', 3.6 + 0.3 * (k % 2), m_planks(3, 'u', knots=False)), n=8)
            m.part(); m.face([(x + rad * math.cos(a), 0.17 + row * 0.3 + rad * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9, endpoint=False)], 0.04, M('wood', 4.8, town.m_rings(2)))
            k += 1
    return m


def lamp_rack(frame=0, w=1.6, seed=0):
    """Shelves of lamps, every one burning. It is the brightest thing in Ashkel after the god."""
    m = Model(); mt = Mats(seed, 0)
    h = 1.75
    m.part()
    for x in (0, w - 0.08):
        m.box(x, 0, 0, x + 0.08, 0.4, h, mt.beam)
    q = 0
    for k in range(3):
        z = 0.2 + k * 0.6
        m.part(); m.box(0, 0, z - 0.05, w, 0.4, z, mt.wood_h, top=M('wood', 4.8))
        cx = 0.22
        while cx < w - 0.15:
            m.part(); m.blob(cx, 0.2, z + 0.045, 0.085, 0.06, 0.045, mt.pot if q % 2 else mt.pot2, n=7, rings=3)
            m.part(); m.blob(cx + 0.07, 0.2, z + 0.13 + 0.01 * ((frame + q) % 2), 0.035, 0.03, 0.06 + 0.01 * ((frame + q) % 2), Mat(RAMPS['glow'], 2.6, glow=True), n=5, rings=3)
            cx += 0.3; q += 1
    m.light(w / 2, -0.2, 1.0, 4.2, (1.0, 0.74, 0.42), 0.7)
    return m


def frog_jar():
    """A jar with a cloth tied over it, and holes in the cloth."""
    m = Model(); mt = Mats(3, 0)
    jar(m, mt, 0, 0.2, 0, s=0.7, kind=0, mat=mt.pot2, n=9)
    m.part(); m.blob(0, 0.2, 0.5, 0.13, 0.11, 0.04, M('linen', 4.8, soft=True), n=7, rings=3)
    return m


def sandals():
    """A pair of sandals, side by side, toes to the door."""
    m = Model()
    for sx in (-0.1, 0.1):
        m.part(); m.box(sx - 0.07, 0.05, 0, sx + 0.07, 0.4, 0.03, M('cedar', 3.6, soft=True), top=M('cedar', 4.2, soft=True))
        m.part(); m.box(sx - 0.07, 0.24, 0.03, sx + 0.07, 0.28, 0.08, M('cedar', 3.0))
    return m


def lesson():
    """The lesson: a slab of clay the height of a boy, on a frame, with today's line on it in the master's hand."""
    m = Model(); mt = Mats(5, 0)
    m.part()
    for sx in (-0.5, 0.5):
        m.beam((sx, 0.3, 0), (sx * 0.8, 0.1, 1.5), 1.2 * PX, mt.beam)
    m.part(); m.box(-0.6, 0.06, 0.5, 0.6, 0.14, 1.46, M('clay', 4.2, town.m_cuneiform(5)), top=M('clay', 4.8))
    m.part(); m.box(-0.64, 0.04, 0.44, 0.64, 0.16, 0.5, M('wood', 4.2))
    return m


def tray_stand():
    """A folding stand with a tray on it: cups, a jug, and dates that are forty nights past their best."""
    m = Model(); mt = Mats(7, 0)
    m.part()
    for (a, b) in (((-0.3, 0.1), (0.3, 0.4)), ((0.3, 0.1), (-0.3, 0.4))):
        m.beam((a[0], a[1], 0), (b[0], b[1], 0.6), PX, mt.beam)
    m.part(); m.turned(0, 0.25, [(0.3, 0.6), (0.34, 0.64)], M('bronze', 4.4, gloss=0.03), n=10, cap=M('bronze', 3.6))
    jar(m, mt, 0.0, 0.25, 0.62, s=0.4, kind=1, mat=M('bronze', 4.4, gloss=0.03))
    for k, cx in enumerate((-0.18, 0.18)):
        m.part(); m.turned(cx, 0.2, [(0.03, 0.62), (0.05, 0.72)], M('bronze', 4.6, gloss=0.03), n=6, cap=M('dark', 1.4))
    return m


# ------------------------------------------------------------------ a floor of house rooms
class House(Floor):
    """The rooms of a town's houses. style 'house'; no plan is written for the map page: a house is not a dungeon."""

    def __init__(self, name, cols, rows, music="town", seed=0):
        super().__init__(name, cols, rows, 'house', None, "", 0, music, seed)

    def chamber(self, rid, c, r, name, x0, x1, y0=NW, y1=CH - SW, opts="lamp", more=(), **look):
        """A room whose floor is the box x0..x1, y0..y1 of its cell (pixels), plus any `more` boxes."""
        snug = x0 >= 48 and x1 <= CW - 48
        rm = self.room(rid, c, r, name=name, opts=(opts + (" snug" if snug else "")).strip())
        self.shape(rm, [(x0, y0, x1, y1)] + list(more))
        rm.look = look
        rm.box = (x0, y0, x1, y1)
        return rm

    # ---- looks
    def wall_model(self, rm, length, doors, clear=()):
        L = rm.look
        # (a face that reaches the side of the cell is carried on to its edge: measure from where it really starts)
        start = 0 if rm.box[0] <= EW else rm.box[0]
        end = CW if rm.box[2] >= CW - EW else rm.box[2]
        main = abs(length * 16 - (end - start)) < 2
        hang = [(hx - start / 16.0, what) for (hx, what) in L.get('hang', ()) if 0.6 < hx - start / 16.0 < length - 0.6] if main else ()
        return house_wall(length, doors, clear, plaster=L.get('plaster', ('limewash', 4.4)), dado=L.get('dado', ('red', 3.4)), band=L.get('band'),
                          foot=L.get('foot', 'brick'), hang=hang, beams=L.get('beams', True), seed=self.seed + rm.c * 7 + rm.r, fresh=L.get('fresh', False))

    def floor_look(self, T, rm, sd, whole, fx, fy, fw, fh):
        kind = rm.look.get('floor', 'earth')
        H, W = self.H, self.W
        if kind == 'earth':
            hkit.calm(T, whole, 'dust', base=3.7, seed=sd, amp=0.2, pebbles=0.0006)
        elif kind == 'plank':
            T.planks(whole, seed=sd, w=7, along='x', base=3.5, ramp='plank')
        elif kind == 'flag':
            T.slabs(whole, seed=sd, rows=(12, 14, 11), wmin=13, wmax=22, ramp='flag', base=3.3, jitter=1.0, crack=0.14, whole=False, wear=0.6, moss=0.05)
        elif kind == 'tile':
            T.tiles(whole, seed=sd, size=16, ramp='tile', base=3.7, inlay='lapis', every=3)
        elif kind == 'brick':
            T.bricks(whole, seed=sd, bw=8, bh=4, ramp='tile', base=3.3, jitter=0.9, herring=True)
        elif kind == 'sand':
            hkit.calm(T, whole, 'sand', base=3.2, seed=sd, amp=0.2, pebbles=0.0004)
        return True

    def tops_look(self, T, rm, sd, tops, gaps):
        T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='plank', base=3.4, whole=False, crack=0)
        if rm is None:
            return True                      # (the sill of a doorway, painted on its own)
        fm = self._floor_mask(rm) if rm.floor else None
        if fm is None:
            T.walltop(tops, seed=sd + 1, ramp='wall', base=3.6)
            return True
        band = tops & T.grow(fm, 12)
        T.walltop(band, seed=sd + 1, ramp='wall', base=3.5, bw=20, bh=12)
        T.put(tops & ~band, 'basalt', np.full((self.H, self.W), 0.0), 0.0)
        return True

    # ---- a floor above the floor, in a house: a gallery of planks on posts
    def top_look(self, T, rm, sd, mask):
        T.planks(mask, seed=sd, w=6, along='y', base=4.0, ramp='plank')
        T.border(mask, 'plank', 2.4, 1, 0.8)

    def face_model(self, length, h):
        m = Model()
        m.part(); m.box(0, 0, 0, length, PX, h, M('dark', 1.4))
        m.part()
        n = max(2, int(length / 1.5))
        for i in range(n + 1):
            x = min(length - 0.12, i * length / n)
            m.box(x, -PX, 0, x + 0.12, PX, h, M('wood', 3.9, m_planks(3, 'v', knots=False)))
        m.part(); m.box(0, -1.5 * PX, h - 3 * PX, length, PX, h, M('wood', 4.6, m_planks(4, 'h', knots=False)))
        return m

    def flight_model(self, w, rise, run):
        n = max(2, int(round(rise * 16 / 4)))
        m = Model()
        for i in range(n):
            m.part(); m.box(0, run * i / n, 0, w, run, rise * (i + 1) / n, M('wood', 3.4, m_planks(4, 'h', knots=False)), top=M('wood', 4.7, m_planks(4, 'h', knots=False)))
        return m

    # ---- things on the floor, painted before the bake
    def mat(self, rm, x, y, w, h, seed=1, ramp='dry'):
        """A mat of reed."""
        T = self.T
        area = T.rect(rm.ox + x, rm.oy + y, w, h)
        T.planks(area, seed=self.seed + seed, w=3, along='y', base=3.8, ramp=ramp)
        T.border(area, ramp='soil', tone=2.6, width=1, hgt=0.6)

    def rug(self, rm, x, y, w, h, ramp='carpet', seed=1, edge='gold'):
        T = self.T
        area = T.rect(rm.ox + x, rm.oy + y, w, h)
        T.carpet(area, seed=self.seed + seed, ramp=ramp)
        T.border(area, ramp=edge, tone=3.4, width=1, hgt=0.8)
        inner = T.rect(rm.ox + x + 4, rm.oy + y + 4, w - 8, h - 8)
        T.border(inner, ramp=edge, tone=2.8, width=1, hgt=0.8)

    def line(self, rm, x, y0, y1, ramp='pale', tone=5.0):
        """A line drawn down a floor in chalk."""
        T = self.T
        area = T.rect(rm.ox + x, rm.oy + y0, 1, y1 - y0) & ((T.yy % 7) != 3)
        T.put(area, ramp, np.full((self.H, self.W), float(tone)), 0.2)

    # ---- things standing in a room, after the bake
    def put(self, key, model, rm, x, y, box='foot', **kw):
        X, Y = rm.p(x, y)
        return self.m.model(key, model, X, Y, box=box, **kw)

    def say(self, key, model, rm, x, y, box, text, **kw):
        X, Y = rm.p(x, y)
        return self.m.model(key, model, X, Y, box=box, kind="look", data={"id": "say", "text": text}, **kw)

    def pot(self, rm, x, y, big=False):
        X, Y = rm.p(x, y)
        kit.pot(self.m, X, Y, big)

    def who(self, rm, x, y, name):
        X, Y = rm.p(x, y)
        self.m.marker("npc", X, Y, who=name)

    def lamp(self, rm, x, strength=0.6, radius=3.4, colour=(1.0, 0.72, 0.4)):
        """The light of a lamp in a niche of the north wall, x pixels from the room's west side."""
        X, Y = rm.p(x, rm.box[1])
        self.m.light(X, Y - 20, radius, colour, strength, h=1.4)

    def moon(self, rm, x, radius=2.6):
        """Moonlight through a window in the north wall, lying on the floor under it."""
        X, Y = rm.p(x, rm.box[1])
        self.m.light(X, Y + 18, radius, (0.62, 0.72, 1.0), 0.45, flicker=False, h=0.2)

    def lights(self, rm):
        """A lamp's light for every lit niche in the room's wall, and the moon for every window."""
        for (hx, what) in rm.look.get('hang', ()):
            if what == 'niche': self.lamp(rm, int(hx * 16))
            if what == 'spirit': self.lamp(rm, int(hx * 16), strength=0.55, radius=3.6, colour=(0.45, 1.0, 0.85))
            if what == 'window': self.moon(rm, int(hx * 16))

    def bar(self, rm, uid, say=None, text=None):
        """The planks across the inside of the street door (the gap in the south wall). Lifted off, they stay off,
        and whatever outside answers to "on:" + uid is open too."""
        X, Y = rm.p(CW // 2, CH - SW)
        data = {"id": uid}
        if say: data["say"] = say
        self.m.model("door_bar", door_bar(2.6), X, Y + 2, box=(-21, -6, 21, 2), kind="latch", data=data, shadow=False)

    def wall(self, rm, x0, x1, y, seed=0, plaster=1, h=1.5):
        """A partition across part of a room, its south face at y (pixels from the room's corner)."""
        L = x1 - x0
        X, Y = rm.p(x0, y)
        self.m.model(f"in_part_{L}_{seed}_{plaster}", partition(L / 16.0, seed, plaster, h), X, Y, box=(0, -6, L, 0))

    def porch(self, y1):
        """The short way in from the street door, for a room that stops short of the south wall of its cell."""
        return (CW // 2 - 24, y1, CW // 2 + 24, CH - SW)

    def save(self):
        self.m.save()
