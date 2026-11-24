"""Dungeon floors: rooms on a grid of cells, joined by doorways, built with the same floors,
walls and furniture as the single halls they replace.

A cell is 26 x 14 tiles. A room takes one cell or a block of them, and keeps its own four walls:
the tall north wall with its face showing, the tops of the side walls and of the south wall.
Doorways go through the middle of a cell's side. The game shows one room at a time and slides
the picture across when Azar walks through a doorway (Scripts/World/Rooms.cs), so each room is
laid out as if it were alone on the screen.

Stairs are a doorway in a north wall with steps up to it, or a gap in a south wall; both carry
Azar to another floor, which is another map.

A floor also writes its plan into Resources/Menu/dungeon_<name>.json for the map page."""
import sys
import os
import json
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R
import region_art as G
import town
import kit
import mapkit
import forge
from PIL import Image
from mapkit import MapBuilder
from ground import Terrain
from forge import Model, M, m_ashlar, m_mottle, m_glazed, m_brick

PX = 1 / 16.0
CW, CH = 416, 224             # a cell, in pixels
NW, SW, EW = 48, 16, 16       # the north wall's face, the south wall's top, a side wall's top
DOOR = 40                     # how wide a north or south doorway is
SIDE0, SIDE1 = 112, 144       # the rows an east or west doorway takes, measured from the top of its cell
PIT = 8                       # pits are boxed on a grid this fine
DW, DH = 2.5, 2.1             # a doorway through a north wall, in tiles
SECRET = ('crack', 'dream')   # doorways the wall does not show: one walled up (a heavy blow brings it down), one only a dreamer has


# ------------------------------------------------------------------ models
def wall(style, length, doors=(), h=2.75, d=0.25, clear=()):
    """A room's north wall running east from the origin, with a dark doorway at each x in doors
    (tiles from its west end). 'temple' is glazed blue brick with gold bulls; 'tomb' is painted
    plaster on dark stone. clear: places kept free of pilasters and panels as a doorway would be,
    with no doorway cut (a way through that the wall is not telling anybody about)."""
    m = Model()

    def near(x, margin):
        return any(abs(x - dx) < DW / 2 + margin for dx in tuple(doors) + tuple(clear))

    if style == 'temple':
        w = town.wall_mats()
        m.part(); m.box(0, 0, 0, length, d, h, w.lapis, top=w.top)
        m.part(); m.box(0, -PX, 0, length, d, 0.5, w.base, top=w.top)
        m.part(); m.box(0, -0.5 * PX, h - 0.75, length, d, h - 0.3, w.frieze)
        for zz in (h - 0.3, h - 0.81):
            m.part(); m.box(0, -PX, zz, length, d, zz + PX, w.gold)
        m.part(); m.box(0, -1.5 * PX, h - 0.12, length, d, h, w.gold, top=w.top)
        x = 2.0
        while x < length - 1.5:
            if not near(x + 0.4, 0.9):
                m.part(); m.box(x, -0.14, 0, x + 0.8, 0, h - 0.82, M('lapis', 3.6, m_glazed(8, 4)), top=w.gold)
                m.part(); m.box(x - PX, -0.14 - PX, 0, x + 0.8 + PX, 0, 0.5, w.base, top=w.top)
            x += 4.0
        x = 3.2
        while x < length - 2.6:
            if not near(x + 0.8, 1.2):
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
        foot, top, dark, trim = w.base, w.top, w.dark, w.gold
    elif style == 'crypt':
        # squared sandstone gone dark with age, a row of niches with a dead watchman's helmet or his
        # lamp in each, and one line of writing under the coping
        foot = M('sandstone', 3.1, m_ashlar(16, 8))
        body = M('sandstone', 3.6, m_ashlar(14, 7))
        top = M('sandstone', 4.4, m_mottle(14, 0.4))
        m.part(); m.box(0, 0, 0, length, d, h, body, top=top)
        m.part(); m.box(0, -PX, 0, length, d, 0.5, foot, top=top)
        m.part(); m.box(0, -0.5 * PX, h - 0.62, length, d, h - 0.3, M('sandstone', 4.0, town.m_cuneiform(5)))
        m.part(); m.box(0, -1.5 * PX, h - 0.14, length, d, h, M('sandstone', 4.3), top=top)
        x = 1.6; k = 0
        while x < length - 1.2:
            if not near(x + 0.3, 0.7):
                m.part(); m.box(x, -0.02, 0.72, x + 0.6, 0, 1.5, M('dark', 1.5))
                if k % 3 == 2:
                    m.part(); m.turned(x + 0.3, -0.07, [(0.1, 0.72), (0.15, 0.8), (0.07, 0.9)], M('clay', 3.9), n=7, cap=M('dark', 1.4), squash=0.5)
                else:
                    m.part(); m.blob(x + 0.3, -0.05, 0.86, 0.17, 0.08, 0.15, M('bronze', 3.3 + (k % 2) * 0.5), n=8, rings=5)
                    m.part(); m.box(x + 0.28, -0.07, 0.98, x + 0.32, -0.03, 1.12, M('red', 2.6))
            x += 2.0; k += 1
        dark, trim = M('dark', 1.1), M('bronze', 4.0)
    else:
        foot = M('stone', 3.3, m_ashlar(16, 8))
        plaster = M('ochre', 4.3, m_mottle(16, 0.5))
        paint = M('ochre', 4.3, town.m_procession(22, 14), ramp2='red')
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
            if not near(x + 0.4, 0.9):
                m.part(); m.box(x, -0.14, 0, x + 0.8, 0, h - 0.82, M('stone', 3.8, m_ashlar(10, 6)), top=M('stone', 4.6))
            x += 4.0
        dark, trim = M('dark', 1.2), M('gold', 3.9)
    for dx in doors:
        a, b = dx - DW / 2, dx + DW / 2
        m.part(); m.box(a - 0.25, -0.2, 0, b + 0.25, 0, DH + 0.3, foot, top=top)
        m.part(); m.quad((a, -0.21, 0), (b, -0.21, 0), (b, -0.21, DH), (a, -0.21, DH), dark)
        m.part()
        if style == 'temple':
            for sx in (a - 0.07, b):
                m.box(sx, -0.24, 0, sx + 0.07, -0.2, DH + 0.07, trim)
            m.box(a - 0.07, -0.24, DH, b + 0.07, -0.2, DH + 0.07, trim)
        else:
            m.box(a - 0.1, -0.24, DH, b + 0.1, -0.2, DH + 0.1, trim)
    return m


def bars_ns(depth=2.0, h=1.4):
    """A grille of bronze bars across an east or west doorway: the same bars as town.bars, seen
    end on, running north from the origin."""
    m = Model()
    brz = M('bronze', 4.3, gloss=0.03); dk = M('bronze', 3.2)
    n = int(depth / 0.25)
    m.part()
    for i in range(n + 1):
        y = depth * i / n
        m.box(-PX / 2, y - PX / 2, 0, PX / 2, y + PX / 2, h, brz if i % 2 == 0 else dk)
    m.part(); m.box(-PX, 0, h - 0.08, PX, depth, h, brz)
    m.part(); m.box(-PX, 0, 0.3, PX, depth, 0.36, dk)
    return m


def low_door(w=2.5, h=0.9):
    """The back of a bronze door, as much of it as shows over the top of a south wall."""
    m = Model()
    plate = M('bronze', 3.4, town.m_planks(8, 'v', knots=False))
    m.part(); m.box(-w / 2, 0, 0, w / 2, 0.12, h, plate, top=M('bronze', 4.4))
    m.part()
    for z in (0.16, h - 0.2):
        m.box(-w / 2, -0.02, z, w / 2, 0, z + 2 * PX, M('bronze', 4.6, gloss=0.03))
    return m


def crack_face(seed=0, h=1.9):
    """What a walled-up doorway cannot help showing: two cracks up the face of the wall, and the
    bits they have dropped at the foot of it. Its origin is the middle of the doorway's foot."""
    m = Model()
    rng = np.random.default_rng(seed + 11)
    dark = M('dark', 0.6)
    for (x, z1) in ((-0.55, h), (0.5, h * 0.6)):
        z = 0.22
        m.part()
        while z < z1:
            dz = rng.uniform(0.14, 0.3); dx = rng.uniform(-0.2, 0.2)
            m.box(x - PX / 2, -3.3 * PX, z, x + PX / 2, -3 * PX, min(z1, z + dz), dark)
            z += dz
            if z < z1:
                xa, xb = sorted((x, x + dx))
                m.box(xa - PX / 2, -3.3 * PX, z - PX / 2, xb + PX / 2, -3 * PX, z + PX / 2, dark)
                x += dx
    st = M('stone', 3.6)
    m.part()
    for k in range(5):
        m.blob(rng.uniform(-1.0, 1.0), -0.3 - rng.uniform(0, 0.3), 0.04, 0.075, 0.06, 0.05, st, n=6, rings=3)
    return m


def crack_top(span=1.0, across='ns', seed=0):
    """The same, seen from above: cracks across the top of a wall `span` tiles thick. across 'ns':
    the wall runs east-west and the cracks cross it northwards from the origin; 'ew': the wall
    runs north-south, the origin is the middle of its south end, and they cross it sideways."""
    m = Model()
    rng = np.random.default_rng(seed + 23)
    dark = M('dark', 0.6)
    for k, off in enumerate((-0.5, 0.42)):
        m.part()
        if across == 'ns':
            x, y = off, 0.1
            while y < span - 0.1:
                dy = rng.uniform(0.12, 0.26); dx = rng.uniform(-0.16, 0.16)
                m.box(x - PX / 2, y, 0, x + PX / 2, min(span - 0.1, y + dy), 0.3 * PX, dark)
                y += dy
                if y < span - 0.1:
                    xa, xb = sorted((x, x + dx))
                    m.box(xa - PX / 2, y - PX / 2, 0, xb + PX / 2, y + PX / 2, 0.3 * PX, dark)
                    x += dx
        else:
            x, y = -span + 0.1, 1.0 + off * 1.1
            while x < span - 0.1:
                dx = rng.uniform(0.14, 0.3); dy = rng.uniform(-0.16, 0.16)
                m.box(x, y - PX / 2, 0, min(span - 0.1, x + dx), y + PX / 2, 0.3 * PX, dark)
                x += dx
                if x < span - 0.1:
                    ya, yb = sorted((y, y + dy))
                    m.box(x - PX / 2, ya - PX / 2, 0, x + PX / 2, yb + PX / 2, 0.3 * PX, dark)
                    y += dy
    return m


def burrow_mouth():
    """A hole something has dug through the foot of a wall: black, low, and not made by a mason.
    Its origin is the middle of the hole's foot, on the face of the wall."""
    m = Model()
    rng = np.random.default_rng(5)
    dark = M('dark', 0.0)
    pts = [(-0.7, 0), (0.7, 0), (0.78, 0.36), (0.66, 0.74), (0.4, 0.98), (0.08, 1.1), (-0.3, 1.04), (-0.6, 0.8), (-0.8, 0.4)]
    m.part(); m.face(pts, -3.4 * PX, dark)
    # the courses it broke through, standing proud round the edge of it
    st = [M('sandstone', 3.0), M('sandstone', 3.8), M('sandstone', 2.5)]
    for k, (x, z, w, h) in enumerate(((-0.92, 0.14, 0.2, 0.2), (-0.86, 0.5, 0.18, 0.2), (-0.7, 0.86, 0.2, 0.16), (-0.4, 1.1, 0.24, 0.14), (0.02, 1.18, 0.26, 0.14),
                                      (0.4, 1.06, 0.22, 0.16), (0.68, 0.8, 0.2, 0.2), (0.82, 0.44, 0.18, 0.2), (0.84, 0.1, 0.2, 0.2))):
        m.part(); m.box(x - w / 2, -0.24, z - h / 2, x + w / 2, -0.2, z + h / 2, st[k % 3])
    # what was dug out, trodden into a fan across the floor in front
    earth = [M('mud', 2.4), M('mud', 3.0)]
    m.part()
    for k in range(16):
        a = rng.uniform(-1.25, 1.25); y = -0.3 - rng.uniform(0, 0.75) * (1 - abs(a) / 1.6)
        if abs(a) < 0.42 and y > -0.7:
            continue                                   # (the middle of it is worn flat by whatever uses it)
        m.blob(a, y, 0.03, rng.uniform(0.1, 0.19), 0.1, rng.uniform(0.04, 0.09), earth[k % 2], n=6, rings=3, seed=k)
    return m


def ladder(h=2.5, w=0.7):
    """A ladder of cedar poles leaning on a wall, its foot a little out from it: the origin is the middle
    of its foot."""
    m = Model()
    rail, rung = M('cedar', 3.6), M('wood', 4.2)
    lean = 0.32
    m.part()
    for sx in (-w / 2, w / 2):
        m.beam((sx, 0, 0), (sx, lean, h), 1.3 * PX, rail)
    m.part()
    n = int(h / 0.32)
    for i in range(1, n + 1):
        t = i / (n + 1.0)
        m.beam((-w / 2 - PX, lean * t - PX * 0.5, h * t), (w / 2 + PX, lean * t - PX * 0.5, h * t), PX, rung)
    return m


def burrow_hole():
    """The other end: a hole come up through a floor, and the heap of what came out of it."""
    m = Model()
    rng = np.random.default_rng(8)
    dark = M('dark', 0.2)
    m.part(); m.turned(0, 0, [(0.46, 0.0), (0.46, 0.02)], dark, n=14, cap=dark, squash=0.6)
    earth = M('mud', 2.7)
    m.part()
    for k in range(13):
        a = k / 13.0 * 6.283
        if 3.6 < a < 5.8:
            continue                                   # the side he climbs out of is trodden flat
        r = 0.52 + rng.uniform(0, 0.12)
        m.blob(r * np.cos(a), r * 0.6 * np.sin(a), 0.05, rng.uniform(0.1, 0.16), 0.09, rng.uniform(0.06, 0.11), earth, n=6, rings=3, seed=k)
    m.part()
    for k in range(6):
        m.blob(0.7 + rng.uniform(-0.2, 0.25), 0.2 + rng.uniform(-0.15, 0.2), 0.08 + rng.uniform(0, 0.1), rng.uniform(0.14, 0.22), 0.14, rng.uniform(0.1, 0.16), earth, n=7, rings=4, seed=20 + k)
    return m


def stairwell(cv, w, d, style):
    """Steps going down out of sight through a floor, seen from above (drawn on cv from its top left):
    a kerb round three sides, the top step at the south edge in the light, the rest going into the dark
    to the north."""
    if style == 'temple':
        kerb, kerb_d = (214, 198, 150, 255), (150, 132, 100, 255)
        tones = [(196, 178, 132, 255), (160, 142, 110, 255), (122, 106, 92, 255), (86, 74, 78, 255), (54, 46, 62, 255), (30, 24, 44, 255)]
    elif style == 'barrow':
        kerb, kerb_d = (176, 136, 96, 255), (112, 80, 66, 255)
        tones = [(160, 122, 88, 255), (128, 94, 74, 255), (98, 70, 62, 255), (70, 50, 54, 255), (46, 34, 46, 255), (26, 20, 36, 255)]
    else:
        kerb, kerb_d = (150, 150, 172, 255), (92, 90, 112, 255)
        tones = [(132, 130, 150, 255), (104, 100, 122, 255), (78, 74, 98, 255), (56, 52, 76, 255), (38, 34, 56, 255), (22, 18, 36, 255)]
    dark = (12, 9, 22, 255)
    cv.rect(0, 0, w, d, dark)
    n = len(tones)
    step = max(2, (d - 4) // n)
    y = d
    for k in range(n):
        y0 = max(2, y - step)
        cv.rect(2, y0, w - 4, y - y0, tones[k])
        # each tread's far edge is its nosing, and catches what light there is; the next one down starts in its shade
        if k > 0:
            cv.hline(2, w - 3, y - 1, tuple(int(c * 0.6) for c in tones[k][:3]) + (255,))
        if y0 > 2 and y - y0 >= 2:
            cv.hline(2, w - 3, y0, tuple(min(255, int(c * 1.25)) for c in tones[k][:3]) + (255,))
        y = y0
        if y <= 2:
            break
    # the kerb: north, west and east
    cv.rect(0, 0, w, 2, kerb); cv.hline(0, w - 1, 1, kerb_d)
    cv.rect(0, 0, 2, d, kerb); cv.vline(1, 2, d - 1, kerb_d)
    cv.rect(w - 2, 0, 2, d, kerb); cv.vline(w - 2, 2, d - 1, kerb_d)


# ------------------------------------------------------------------ a floor of rooms
class Room:
    def __init__(self, floor, rid, c, r, cw, ch, name, opts):
        self.floor, self.id, self.c, self.r, self.cw, self.ch = floor, rid, c, r, cw, ch
        self.name, self.opts = name, opts
        self.ox, self.oy, self.w, self.h = c * CW, r * CH, cw * CW, ch * CH
        self.mark = ""                       # what the map scroll draws on it: 'boss', 'mini'
        self.passage = False                 # a way between rooms rather than a room (a tuning fork listens through it)
        self.secret = False                  # on no plan: the map page draws it only once Azar has stood in it
        self._faces = []                     # the north-wall faces it was given: (x, y of the foot, length, [doors' x]) in map pixels
        self.floor = None                    # None: floor from wall to wall. Or [(x0, y0, x1, y1)...] in pixels from the
                                             # room's corner: where there is floor (everything else in it is rock)

    # places inside the room, in pixels from its top-left corner
    def p(self, x, y):
        return self.ox + x, self.oy + y

    @property
    def fx0(self): return self.ox + EW
    @property
    def fy0(self): return self.oy + NW
    @property
    def fx1(self): return self.ox + self.w - EW
    @property
    def fy1(self): return self.oy + self.h - SW
    @property
    def cx(self): return self.ox + self.w // 2
    @property
    def cy(self): return (self.fy0 + self.fy1) // 2


class Floor:
    """One floor of a dungeon. style is 'temple' or 'tomb'."""

    def __init__(self, name, cols, rows, style, dungeon, label, order, music, seed=0):
        self.name, self.cols, self.rows, self.style = name, cols, rows, style
        self.dungeon, self.label, self.order, self.seed = dungeon, label, order, seed
        fill = (10, 7, 14, 255) if style == 'temple' else (6, 5, 10, 255) if style == 'tomb' else (8, 6, 9, 255)
        self.m = MapBuilder(name, cols * CW // 16, rows * CH // 16, fill, music=music)
        self.W, self.H = cols * CW, rows * CH
        self.rooms = {}
        self.cells = {}
        self.links = []
        self.chests = []
        self.platforms = []
        self.burrows = []
        self.T = None
        self.g = None

    # ---- the plan
    def room(self, rid, c, r, cw=1, ch=1, name="", opts=""):
        rm = Room(self, rid, c, r, cw, ch, name, opts)
        self.rooms[rid] = rm
        for i in range(cw):
            for j in range(ch):
                self.cells[(c + i, r + j)] = rm
        return rm

    def shape(self, rm, rects):
        """Give a room a floor that is not a box: a union of rectangles (pixels from the room's corner,
        inside its walls). Whatever they leave is solid rock. Doorways still go through the middle of a
        cell's side, so a rectangle has to reach the wall wherever there is one. Call before lay()."""
        x1m, y1m = rm.w - EW, rm.h - SW
        rm.floor = [(max(EW, int(a)), max(NW, int(b)), min(x1m, int(c)), min(y1m, int(d))) for (a, b, c, d) in rects]
        return rm

    def corners(self, rm, n=32, which='nw ne sw se'):
        """Cut a room's corners off (n pixels each way): an eight-sided hall instead of a box."""
        x0, y0, x1, y1 = EW, NW, rm.w - EW, rm.h - SW
        w = which.split()
        rects = [(x0 + n, y0, x1 - n, y1), (x0, y0 + n, x1, y1 - n)]
        if 'nw' not in w: rects.append((x0, y0, x0 + n, y0 + n))
        if 'ne' not in w: rects.append((x1 - n, y0, x1, y0 + n))
        if 'sw' not in w: rects.append((x0, y1 - n, x0 + n, y1))
        if 'se' not in w: rects.append((x1 - n, y1 - n, x1, y1))
        return self.shape(rm, rects)

    def passage(self, rm, along='ew', wide=80, stubs=''):
        """Make a one-cell room a passage: a strip of floor `wide` pixels across, running east-west through
        the side doors or north-south through the end doors. stubs: sides ('n', 's', 'e', 'w') that
        also have a doorway, reached by a short arm off the passage."""
        x0, y0, x1, y1 = EW, NW, rm.w - EW, rm.h - SW
        cx, cy = rm.w // 2, (SIDE0 + SIDE1) // 2
        if along == 'ew':
            rects = [(x0, cy - wide // 2, x1, cy + wide // 2)]
        else:
            rects = [(cx - wide // 2, y0, cx + wide // 2, y1)]
        for sd in stubs.split():
            if sd == 'n': rects.append((cx - 36, y0, cx + 36, cy))
            if sd == 's': rects.append((cx - 36, cy, cx + 36, y1))
            if sd == 'w': rects.append((x0, cy - 28, cx, cy + 28))
            if sd == 'e': rects.append((cx, cy - 28, x1, cy + 28))
        rm.passage = True
        return self.shape(rm, rects)

    def _floor_mask(self, rm):
        fm = self.T.none()
        for (x0, y0, x1, y1) in rm.floor:
            fm |= self.T.rect(rm.ox + x0, rm.oy + y0, x1 - x0, y1 - y0)
        return fm

    def _covered(self, rm, x, y):
        return any(x0 <= x < x1 and y0 <= y < y1 for (x0, y0, x1, y1) in rm.floor)

    def link(self, c, r, side, kind='open', **data):
        """A doorway in side 'n', 's', 'e' or 'w' of cell (c, r). kind: 'open', 'lock' (a small key),
        'big' (the big key), 'bars' (a grille that a flag lifts), 'stairs' (to=map, spawn=name: to
        another floor; a spawn named `name` is put where Azar arrives), 'out' (the way out)."""
        if side == 's':
            c, r, side = c, r + 1, 'n'
        elif side == 'e':
            c, r, side = c + 1, r, 'w'
        ln = {"c": c, "r": r, "side": side, "kind": kind}
        ln.update(data)
        self.links.append(ln)
        return ln

    def _north(self, rm):
        return [l for l in self.links if l["side"] == 'n' and self.cells.get((l["c"], l["r"])) is rm]

    def _south(self, rm):
        return [l for l in self.links if l["side"] == 'n' and self.cells.get((l["c"], l["r"] - 1)) is rm]

    def _west(self, rm):
        return [l for l in self.links if l["side"] == 'w' and self.cells.get((l["c"], l["r"])) is rm]

    def _east(self, rm):
        return [l for l in self.links if l["side"] == 'w' and self.cells.get((l["c"] - 1, l["r"])) is rm]

    @staticmethod
    def door_x(l):
        return l["c"] * CW + CW // 2

    @staticmethod
    def door_y(l):
        return l["r"] * CH + (SIDE0 + SIDE1) // 2

    # ---- the ground, before it is baked
    def lay(self):
        T = self.T = self.m.lay(seed=self.seed)
        W, H = self.W, self.H
        T.put(T.all(), 'basalt', np.full((H, W), 0.0), 0.0)
        for k, rm in enumerate(self.rooms.values()):
            sd = self.seed + 3 * k
            whole = T.rect(rm.ox, rm.oy, rm.w, rm.h)
            fx, fy, fw, fh = rm.fx0, rm.fy0, rm.w - 2 * EW, rm.h - NW - SW
            fm = self._floor_mask(rm) if rm.floor else None
            if self.floor_look(T, rm, sd, whole, fx, fy, fw, fh):
                pass
            elif fm is not None and self.style == 'temple':
                T.tiles(whole, seed=sd, size=16, ramp='tile', base=3.5, inlay='lapis', every=5)
            elif fm is not None and self.style == 'crypt':
                T.slabs(whole, seed=sd, rows=(14, 12, 15), wmin=14, wmax=26, ramp='flag', base=3.3, jitter=1.2, crack=0.22, whole=False, wear=0.7, moss=0.06)
            elif fm is not None:
                T.slabs(whole, seed=sd, rows=(16,), wmin=20, wmax=28, ramp='basalt', base=4.0, jitter=1.0, crack=0.14, whole=False, wear=0.6)
            elif self.style == 'temple':
                T.tiles(whole, seed=sd, size=16, ramp='tile', base=3.5, inlay='lapis', every=5)
                band = T.rect(fx + 12, fy + 14, fw - 24, fh - 28) & ~T.rect(fx + 15, fy + 17, fw - 30, fh - 34)
                T.put(band, 'lapis', np.full((H, W), 3.2) + ((T.xx + T.yy) % 6 < 3) * 0.8, 1.2)
                corner = band & (((T.xx - fx - 12) % (fw - 27) < 3) & ((T.yy - fy - 14) % (fh - 31) < 3))
                T.put(corner, 'gold', np.full((H, W), 4.0), 1.5)
            elif self.style == 'crypt':
                T.slabs(whole, seed=sd, rows=(14, 12, 15), wmin=14, wmax=26, ramp='flag', base=3.3, jitter=1.2, crack=0.22, whole=False, wear=0.7, moss=0.06)
                line = T.rect(fx + 10, fy + 12, fw - 20, fh - 24) & ~T.rect(fx + 12, fy + 14, fw - 24, fh - 28)
                T.put(line, 'flag', np.full((H, W), 2.0), 0.6)
            else:
                T.slabs(whole, seed=sd, rows=(16,), wmin=20, wmax=28, ramp='basalt', base=4.0, jitter=1.0, crack=0.14, whole=False, wear=0.6)
                line = T.rect(fx + 10, fy + 12, fw - 20, fh - 24) & ~T.rect(fx + 12, fy + 14, fw - 24, fh - 28)
                T.put(line, 'gold', np.full((H, W), 2.6), 1.2)
                line2 = T.rect(fx + 14, fy + 16, fw - 28, fh - 32) & ~T.rect(fx + 17, fy + 19, fw - 34, fh - 38)
                T.put(line2, 'lapis', np.full((H, W), 2.4) + ((T.xx + T.yy) % 6 < 3) * 0.8, 1.1)
            tops = (T.rect(rm.ox, rm.oy + NW, EW, rm.h - NW) | T.rect(rm.ox + rm.w - EW, rm.oy + NW, EW, rm.h - NW)
                    | T.rect(rm.ox + EW, rm.oy + rm.h - SW, rm.w - 2 * EW, SW))
            gaps = T.none()
            for l in self._south(rm):
                if l["kind"] not in SECRET:
                    gaps |= T.rect(self.door_x(l) - DOOR // 2, rm.oy + rm.h - SW, DOOR, SW)
            for l in self._west(rm):
                if l["kind"] not in SECRET:
                    gaps |= T.rect(rm.ox, l["r"] * CH + SIDE0, EW, SIDE1 - SIDE0)
            for l in self._east(rm):
                if l["kind"] not in SECRET:
                    gaps |= T.rect(rm.ox + rm.w - EW, l["r"] * CH + SIDE0, EW, SIDE1 - SIDE0)
            if fm is not None:
                tops = whole & ~fm                 # everything in the room that is not floor is the top of a wall
            tops &= ~gaps
            rm._sd = sd
            if self.tops_look(T, rm, sd, tops, gaps):
                pass
            elif self.style == 'temple':
                T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=4.0, whole=False, crack=0)
                T.walltop(tops, seed=sd + 1)
                coping = (T.rect(rm.ox + EW - 2, rm.oy + NW, 2, rm.h - NW - SW) | T.rect(rm.ox + rm.w - EW, rm.oy + NW, 2, rm.h - NW - SW)
                          | T.rect(rm.ox + EW, rm.oy + rm.h - SW, rm.w - 2 * EW, 2)) & tops
                T.put(coping, 'gold', np.full((H, W), 3.6), 3.4)
            elif self.style == 'crypt':
                T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='flag', base=3.9, whole=False, crack=0.1)
                T.walltop(tops, seed=sd + 1, ramp='wall', base=3.0)
            else:
                T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=3.2, whole=False, crack=0)
                T.walltop(tops, seed=sd + 1, ramp='flag', base=3.6)
            if fm is not None:
                # an inlaid line round the edge of the rock, and its shade on the floor at the foot of every face
                edge = tops & T.grow(fm, 2)
                T.put(edge, 'gold' if self.style in ('temple', 'tomb') else 'flag', np.full((H, W), 3.4 if self.style in ('temple', 'tomb') else 2.2), 3.0)
                for (x0, y0, x1, y1) in rm.floor:
                    if not self._covered(rm, (x0 + x1) // 2, y0 - 2):
                        T.contact(rm.ox + x0, rm.oy + y0 - 8, rm.ox + x1, rm.oy + y0, reach=7, strength=1.6)
                    if not self._covered(rm, x0 - 2, (y0 + y1) // 2):
                        T.contact(rm.ox + x0 - 8, rm.oy + y0, rm.ox + x0, rm.oy + y1, reach=5, strength=1.0)
                continue
            # the north and west walls shade the floor at their feet
            T.contact(rm.ox, rm.oy, rm.ox + rm.w, rm.oy + NW, reach=7, strength=1.6)
            T.contact(rm.ox, rm.oy + NW, rm.ox + EW, rm.oy + rm.h - SW, reach=5, strength=1.0)
        return T

    def carpet(self, rm, x, y, w, h, seed=1):
        """A runner on a room's floor (pixels from the room's corner), before the bake."""
        if self.style == 'temple':
            self.T.carpet(self.T.rect(rm.ox + x, rm.oy + y, w, h), seed=seed)
        else:
            T = self.T
            mask = T.rect(rm.ox + x, rm.oy + y, w, h)
            tone = 2.6 + ((T.yy // 2) % 2) * 0.5 + ((T.xx // 3 + T.yy // 2) % 2) * 0.3
            T.put(mask, 'carpet', tone, np.full(tone.shape, 1.4))
            T.border(mask, 'gold', 3.0, 2, 1.5)

    def dais(self, rm, x, y, w, h, seed=2):
        """A low platform of pale stone edged in gold."""
        T = self.T
        mask = T.rect(rm.ox + x, rm.oy + y, w, h)
        T.slabs(mask, seed=seed, rows=(13,), wmin=16, wmax=16, ramp='pale', base=4.4 if self.style == 'temple' else 3.4, jitter=0.6, whole=False, crack=0.04)
        T.border(mask, 'gold', 3.6, 2, 1.5)

    def wall_model(self, rm, length, doors, clear=()):
        """A room's north wall (a floor with a look of its own builds its own)."""
        return wall(self.style, length, doors=doors, clear=clear)

    def floor_look(self, T, rm, sd, whole, fx, fy, fw, fh):
        """A floor with a look of its own paves a room here and returns True."""
        return False

    def tops_look(self, T, rm, sd, tops, gaps):
        """...and gives its wall tops and doorway sills their own stone."""
        return False

    # ---- walls, doors and everything that stands, after the bake
    def bake(self):
        m = self.m
        g = self.g = m.bake()
        for rm in self.rooms.values():
            north = self._north(rm)
            holes = [l for l in north if l["kind"] != 'wall']
            if rm.floor:
                self._bake_shaped(rm, holes)
                self._mark(rm)
                continue
            shown = [self.door_x(l) for l in holes if l["kind"] not in SECRET]
            hidden = [self.door_x(l) for l in holes if l["kind"] in SECRET] + [rm.ox + b["x"] for b in self.burrows if b["rm"] is rm]
            m.set_into_ground(self.wall_model(rm, rm.w / 16.0, [(x - rm.ox) / 16.0 for x in shown], clear=[(x - rm.ox) / 16.0 for x in hidden]), rm.ox, rm.oy + NW)
            rm._faces.append((rm.ox, rm.oy + NW, rm.w, shown))
            G.cobweb(g, rm.ox + EW + 2, rm.oy + NW + 4); G.cobweb(g, rm.ox + rm.w - EW - 3, rm.oy + NW + 4, flip=True)
            # the north wall, solid but for its doorways (a stair is climbed to its foot, not walked through)
            x = rm.ox
            for l in sorted(holes, key=self.door_x):
                dx = self.door_x(l)
                if l["kind"] == 'stairs':
                    continue
                m.solid(x, rm.oy, dx - 17, rm.oy + NW - 4)
                x = dx + 17
            m.solid(x, rm.oy, rm.ox + rm.w, rm.oy + NW - 4)
            # the south wall and its gaps
            x = rm.ox
            for l in sorted(self._south(rm), key=self.door_x):
                dx = self.door_x(l)
                m.solid(x, rm.oy + rm.h - SW + 2, dx - 18, rm.oy + rm.h)
                x = dx + 18
            m.solid(x, rm.oy + rm.h - SW + 2, rm.ox + rm.w, rm.oy + rm.h)
            # the side walls and theirs
            for side, links, x0 in (('w', self._west(rm), rm.ox), ('e', self._east(rm), rm.ox + rm.w - EW)):
                y = rm.oy
                for l in sorted(links, key=lambda q: q["r"]):
                    gy = l["r"] * CH
                    m.solid(x0, y, x0 + EW, gy + SIDE0)
                    y = gy + SIDE1
                m.solid(x0, y, x0 + EW, rm.oy + rm.h)
            self._mark(rm)
        for i, l in enumerate(self.links):
            self._door(i, l)
        for pf in self.platforms:
            self._raise(pf)
        for b in self.burrows:
            X, Y = b["rm"].p(b["x"], NW)
            m.model("burrow_mouth", burrow_mouth(), X, Y + 1, box=None, shadow=False, lights=False)
            m.marker("warp", X - 8, Y - 8, w=16, h=8, id="burrow", text=b["to"])
            m.spawn(b["name"], X, Y + 12, "down")
        return g

    def _mark(self, rm):
        opts = (rm.opts + " secret").strip() if rm.secret else rm.opts
        self.m.marker("room", rm.ox, rm.oy, w=rm.w, h=rm.h, id=rm.id, who=opts, text=rm.name)

    def _bake_shaped(self, rm, holes):
        """The walls of a room whose floor is a union of rectangles: a wall's face along every stretch
        where rock stands north of floor (its doorways, where that stretch is the room's own north
        wall), and everything that is not floor or a doorway made solid."""
        m = self.m
        faces = []
        for (x0, y0, x1, y1) in rm.floor:
            # the parts of this rectangle's top edge that have rock above them
            xs = [x0, x1]
            for (a0, b0, a1, b1) in rm.floor:
                if b0 <= y0 - 1 < b1:
                    xs += [max(x0, min(x1, a0)), max(x0, min(x1, a1))]
            xs = sorted(set(xs))
            run = None
            for xa, xb in zip(xs, xs[1:]):
                rock = not self._covered(rm, (xa + xb) // 2, y0 - 1)
                if rock and run is not None and run[1] == xa:
                    run[1] = xb
                elif rock:
                    run = [xa, xb]; faces.append((y0, run))
        for y0, (xa, xb) in sorted(faces, key=lambda q: q[0]):
            if xb - xa < 8:
                continue
            if xa <= EW: xa = 0
            if xb >= rm.w - EW: xb = rm.w
            here = [l for l in holes if y0 <= NW and xa <= self.door_x(l) - rm.ox <= xb]
            shown = [self.door_x(l) for l in here if l["kind"] not in SECRET]
            hidden = [self.door_x(l) for l in here if l["kind"] in SECRET]
            m.set_into_ground(self.wall_model(rm, (xb - xa) / 16.0, [(x - rm.ox - xa) / 16.0 for x in shown],
                                              clear=[(x - rm.ox - xa) / 16.0 for x in hidden]), rm.ox + xa, rm.oy + y0)
            rm._faces.append((rm.ox + xa, rm.oy + y0, xb - xa, shown))
            for l in holes:
                if y0 <= NW and xa <= self.door_x(l) - rm.ox <= xb:
                    l["_faced"] = True
        for l in holes:
            if not l.pop("_faced", False):
                print(f"  !! {self.name}/{rm.id}: the doorway in its north wall at x={self.door_x(l) - rm.ox} has no floor under it")
        # where a man may stand: the floor (a little under the foot of each face, as under the north wall), and the doorways
        free = np.zeros((rm.h, rm.w), bool)
        for (x0, y0, x1, y1) in rm.floor:
            free[max(0, y0 - 4):min(rm.h, y1 + 2), x0:x1] = True
        for l in holes:
            if l["kind"] == 'stairs' or l["kind"] == 'out':
                continue
            dx = self.door_x(l) - rm.ox
            free[0:NW, dx - 17:dx + 17] = True
        for l in self._south(rm):
            dx = self.door_x(l) - rm.ox
            free[rm.h - SW - 2:rm.h, dx - 18:dx + 18] = True
        for l in self._west(rm):
            gy = l["r"] * CH - rm.oy
            free[gy + SIDE0:gy + SIDE1, 0:EW] = True
        for l in self._east(rm):
            gy = l["r"] * CH - rm.oy
            free[gy + SIDE0:gy + SIDE1, rm.w - EW:rm.w] = True
        # rock, as few boxes as will do: runs along each row, stacked while they stay the same
        open_runs = {}
        for y in range(rm.h):
            row = ~free[y]
            edges = np.flatnonzero(np.diff(np.concatenate(([0], row.view(np.int8), [0]))))
            runs = [(int(a), int(b)) for a, b in zip(edges[::2], edges[1::2])]
            nxt = {}
            for run in runs:
                if run in open_runs:
                    nxt[run] = open_runs.pop(run)
                else:
                    nxt[run] = y
            for (a, b), y_from in open_runs.items():
                m.solid(rm.ox + a, rm.oy + y_from, rm.ox + b, rm.oy + y)
            open_runs = nxt
        for (a, b), y_from in open_runs.items():
            m.solid(rm.ox + a, rm.oy + y_from, rm.ox + b, rm.oy + rm.h)

    def _overlay(self, key, x0, y0, x1, y1, base_y):
        """What stands over a doorway (its lintel, the wall top beside a side door) as a prop of its
        own, cut from the ground picture, so Azar passes under it."""
        m = self.m
        crop = m.ground.a[y0:y1, x0:x1].copy()

        def draw(cv, ax, ay, fi):
            cv.a[0:y1 - y0, 0:x1 - x0] = crop
        o = m.prop(key, draw, x0, base_y, size=(x1 - x0, y1 - y0), anchor=(0, base_y - y0), pad=0)
        # lit exactly as the wall it was cut from
        from PIL import Image
        Image.fromarray(m.ground_n[y0:y1, x0:x1].copy()).save(f"{mapkit.RES}/Objects/{key}_lin.png")
        o["n"] = 1

    def _door(self, i, l):
        m = self.m
        kind = l["kind"]
        uid = l.get("id") or f"{self.name}_d{i}"
        if l["side"] == 'n':
            dx, y = self.door_x(l), l["r"] * CH             # y: the top of the lower room = the foot of the upper one
            lower = self.cells.get((l["c"], l["r"]))
            upper = self.cells.get((l["c"], l["r"] - 1))
            if kind == 'stairs' or kind == 'out':
                if lower is not None and upper is None:
                    # up the steps into the doorway
                    run = 32 / 16.0
                    rise = min(1.25, run * 0.42)
                    m.set_into_ground(town.steps(2.5, n=6, rise=rise, run=run - rise), dx - 20, y + NW + 32)
                    m.exit(dx - 16, y + NW - 4, dx + 16, y + NW + 10, l["to"], l["spawn"], need=l.get("need"))
                    m.spawn(l["name"], dx, y + NW + 44, "down")
                    if l.get("door") == 'sun':
                        # the king's own door: a bronze sun that only the story opens (a 'gate', by its id)
                        m.model("sealdoor", town.bronze_door(2.5, 2.0, 'sun'), dx, y + NW + 34, box=(-20, -26, 20, 0), kind="gate", data={"id": uid})
                    elif l.get("door") == 'ghost':
                        # the king's own door, which only the Ghost Key opens
                        m.model("ghostdoor", town.bronze_door(2.5, 2.0, 'ghost'), dx, y + NW + 34, box=(-20, -26, 20, 0), kind="bigdoor", data={"id": uid})
                    elif l.get("door"):
                        # a door standing at the foot of the steps: 'big' or 'lock'
                        dk = l["door"]
                        m.model("bigdoor" if dk == 'big' else "lockdoor", town.bronze_door(2.5, 2.0 if dk == 'big' else 1.9, 'bull' if dk == 'big' else 'lock'),
                                dx, y + NW + 34, box=(-20, -26, 20, 0), kind="bigdoor" if dk == 'big' else "lockdoor", data={"id": uid})
                elif upper is not None and lower is None:
                    # down through the gap in the south wall
                    self._steps_down(dx, y)
                    m.exit(dx - 20, y - 8, dx + 20, y, l["to"], l["spawn"], need=l.get("need"))
                    m.spawn(l["name"], dx, y - 26, "up")
                return
            if lower is None or upper is None:
                return
            # the lintel hangs over whoever walks through
            self._overlay(f"{self.name}_lintel_{i}", dx - 26, y, dx + 26, y + NW - 33, y + NW)
            if kind in SECRET:
                self._secret_n(i, l, lower, upper, uid)
            elif kind == 'lock' or kind == 'big':
                big = kind == 'big'
                # (a doorway's door is taller than the ones at the foot of a stair: its own name, its own picture)
                m.model("bigdoor_n" if big else "lockdoor_n", town.bronze_door(2.5, 2.1, 'bull' if big else 'lock'), dx, y + NW + 3,
                        box=(-20, -8, 20, 0), kind="bigdoor" if big else "lockdoor", data={"id": uid})
                m.model("lowdoor", low_door(), dx, y - 2, box=(-20, -12, 20, 0), kind="bigdoor" if big else "lockdoor", data={"id": uid})
            elif kind == 'bars':
                data = {"id": uid, "text": l.get("when", ""), "who": l.get("opts", "")}
                if l.get("say"):
                    data["say"] = l["say"]
                m.model("bars_door", town.bars(2.5, 2.0), dx, y + NW + 3, box=(-20, -7, 20, 0), kind="bars", data=data)
                far = l.get("far")
                if far:
                    # 'far': what the grille on the upper room's side answers to, when it is not the same thing
                    data = {"id": far["id"], "text": far.get("when", ""), "who": far.get("opts", "")}
                m.model("bars_gap", town.bars(2.5, 1.2), dx, y - 3, box=(-20, -11, 20, 0), kind="bars", data=data)
        else:
            bx, gy = l["c"] * CW, l["r"] * CH
            if self.cells.get((l["c"], l["r"])) is None or self.cells.get((l["c"] - 1, l["r"])) is None:
                return
            self._overlay(f"{self.name}_jamb_{i}", bx - EW, gy + SIDE0 - 18, bx + EW, gy + SIDE0, gy + SIDE1 + 2)
            if kind in SECRET:
                self._secret_w(i, l, uid)
            elif kind == 'bars':
                data = {"id": uid, "text": l.get("when", ""), "who": l.get("opts", "")}
                if l.get("say"):
                    data["say"] = l["say"]
                # 'far': what the grille at the west end answers to, when it is not the same thing
                far = dict(l["far"]) if l.get("far") else None
                for sx in (bx - EW + 3, bx + EW - 3):
                    dd = data
                    if far and sx < bx:
                        dd = {"id": far["id"], "text": far.get("when", ""), "who": far.get("opts", "")}
                    m.model("bars_ns", bars_ns(2.0, 1.4), sx, gy + SIDE1, box=(-3, -(SIDE1 - SIDE0), 3, 0), kind="bars", data=dd)

    def _steps_down(self, dx, y):
        """Steps going out of sight through a south gap: down to the yard from the temple, up to the
        night from anything dug into a hill."""
        g = self.g
        if self.style == 'temple':
            lime = R['lime']; gd = R['gold']
            edge, tread, deep, far, side0, side1, side2 = lime[3], lime[2], lime[1], (14, 10, 24, 255), gd[3], gd[4], gd[2]
        else:
            # worn stone, and moonlight coming down it from outside
            edge, tread, deep, far = (150, 150, 178, 255), (96, 92, 118, 255), (62, 58, 80, 255), (120, 124, 160, 255)
            side0, side1, side2 = (60, 52, 66, 255), (84, 72, 84, 255), (40, 34, 46, 255)
        for k in range(y - SW, y):
            t = (k - (y - SW)) / SW
            c = edge if (k - (y - SW)) % 4 == 0 else tread if t < 0.45 else deep if t < 0.8 else far
            g.hline(dx - 18, dx + 17, k, c)
        for sx in (dx - 20, dx + 18):
            g.vline(sx, y - SW, y - 1, side0); g.vline(sx + 1, y - SW, y - 1, side1 if sx < dx else side2)

    # ---- ways the wall does not show
    def _raw(self, key, rgba, nm, x, y, px, py, layer=0, kind=None, data=None, box=None):
        """A picture made here (not by the forge) as a prop of its own, its pivot (px, py) put at map (x, y)."""
        Image.fromarray(rgba).save(f"{mapkit.RES}/Objects/{key}.png")
        o = {"s": key, "x": int(x), "y": int(y), "px": int(px), "py": int(py), "w": int(rgba.shape[1]), "h": int(rgba.shape[0]), "layer": layer}
        if nm is not None:
            Image.fromarray(nm).save(f"{mapkit.RES}/Objects/{key}_lin.png")
            o["n"] = 1
        if box:
            o["box"] = [int(b) for b in box]
        if kind:
            o["kind"] = kind
        if data:
            o.update(data)
        self.m.objects.append(o)
        return o

    def _sill(self, w, h, sd):
        """The floor of a doorway through a wall top, w by h pixels, as this floor paves them."""
        T = Terrain(w, h, sd)
        gaps = T.all()
        if self.tops_look(T, None, sd, T.none(), gaps):
            pass
        elif self.style == 'temple':
            T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=4.0, whole=False, crack=0)
        elif self.style == 'crypt':
            T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='flag', base=3.9, whole=False, crack=0.1)
        else:
            T.slabs(gaps, seed=sd + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=3.2, whole=False, crack=0)
        rgb, nm = T.render()
        rgba = np.zeros((h, w, 4), np.uint8); rgba[..., :3] = rgb; rgba[..., 3] = 255
        # the foot of the wall either side of it, in shade
        for x in (0, w - 1):
            rgba[:, x, :3] = (rgba[:, x, :3] * 0.45).astype(np.uint8)
        return rgba, nm

    def _secret_n(self, i, l, lower, upper, uid):
        """A doorway between a room and the one north of it that the wall does not show. The ground has
        the wall whole. The doorway is a picture of its own, laid over the wall when it is found (a
        'crack': flag door_<id>) or for a dreamer only (a 'dream'); until then what stands there is solid."""
        m = self.m
        kind = l["kind"]
        dx, y = self.door_x(l), l["r"] * CH
        layer = 2 if kind == 'dream' else 0
        show = None if kind == 'dream' else "breach"
        face = next((f for f in lower._faces if f[0] <= dx <= f[0] + f[2] and f[1] == y + NW), None)
        if face is None:
            print(f"  !! {self.name}: the hidden way {uid} has no wall to be hidden in")
            return
        X, Y, L, doors = face
        d = forge.draw(self.wall_model(lower, L / 16.0, [(q - X) / 16.0 for q in doors + [dx]]), seed=0, shadow=False)
        c0 = d.ax + (dx - X) - 26
        self._raw(f"{self.name}_way_{i}", d.rgba[:, c0:c0 + 52].copy(), d.normal[:, c0:c0 + 52].copy(), dx - 26, y, 0, d.ay - NW,
                  layer=layer, kind=show, data={"id": uid})
        # ...and the same doorway from the room above: its floor, across the top of that room's south wall
        rgba, nm = self._sill(DOOR, SW, upper._sd)
        self._raw(f"{self.name}_way_{i}_s", rgba, nm, dx - DOOR // 2, y - SW, 0, 0, layer=layer, kind=show, data={"id": uid})
        if kind == 'crack':
            data = {"id": uid, "text": l.get("text", "")}
            m.model(f"{self.style}_crack_n", crack_face(self.seed), dx, y + NW + 1, box=(-20, -NW - 1, 20, -5), kind="crack", data=data, shadow=False, lights=False)
            m.model(f"{self.style}_crack_s", crack_top(1.0, 'ns', self.seed), dx, y, box=(-20, -SW + 2, 20, 0), kind="crack", data=data, shadow=False, lights=False)
        else:
            m.solid(dx - 20, y - SW + 2, dx + 20, y + NW - 4, 1)

    def _secret_w(self, i, l, uid):
        """The same between a room and the one west of it: the doorway's floor is laid across the two wall
        tops when it is found, or for a dreamer."""
        m = self.m
        kind = l["kind"]
        bx, gy = l["c"] * CW, l["r"] * CH
        layer = 2 if kind == 'dream' else 0
        west = self.cells.get((l["c"] - 1, l["r"]))
        rgba, nm = self._sill(2 * EW, SIDE1 - SIDE0, west._sd)
        self._raw(f"{self.name}_way_{i}", rgba, nm, bx - EW, gy + SIDE0, 0, 0, layer=layer, kind=None if kind == 'dream' else "breach", data={"id": uid})
        if kind == 'crack':
            m.model(f"{self.style}_crack_w", crack_top(1.0, 'ew', self.seed), bx, gy + SIDE1, box=(-EW, -(SIDE1 - SIDE0), EW, 0), kind="crack",
                    data={"id": uid, "text": l.get("text", "")}, shadow=False, lights=False)
        else:
            m.solid(bx - EW, gy + SIDE0, bx + EW, gy + SIDE1, 1)

    def hatch(self, rm, x, y, uid, to, spawn, name, when=None, say=None, w=28, d=22):
        """A stair going down through the floor: (x, y) is the middle of its head, where Azar steps onto
        it; it goes down northwards from there. to/spawn: where it comes out; a spawn `name` is put at
        its head for whoever comes up it. when: what has to hold before there is a stair there at all
        (the same language the grilles answer to); say: what the game tells the player when it opens."""
        X, Y = rm.p(x, y)
        key = f"stairwell_{self.style}_{w}_{d}"
        data = {"id": uid, "text": when or "", "who": name}
        if say:
            data["say"] = say
        self.m.prop(key, lambda cv, ax, ay, fi: stairwell(cv, w, d, self.style), X - w // 2, Y - d, size=(w, d), anchor=(0, 0), pad=0, kind="hatch", data=data)
        self.m.exit(X - w // 2 + 5, Y - d + 3, X + w // 2 - 5, Y - 6, to, spawn, need=f"open_{uid}" if when else None)
        self.m.spawn(name, X, Y + 9, "down")

    def burrow(self, rm, x, name, to):
        """A hole dug through the foot of a room's north wall, x pixels from its west side (say so before
        the bake: the wall keeps its niches clear of it): Azar goes in on his hands and knees and comes
        out at the spawn `to` of this same floor (the other end of it, as a rule). A spawn `name` is
        put in front of it for whoever comes the other way."""
        self.burrows.append({"rm": rm, "x": x, "name": name, "to": to})

    def burrow_floor(self, rm, x, y, name, to):
        """The other end of one: a hole come up through the floor at (x, y)."""
        X, Y = rm.p(x, y)
        o = self.m.model("burrow_hole", burrow_hole(), X, Y, box=None, shadow=False, lights=False)
        # it lies on the floor: whoever stands by it is drawn over it
        o["y"] -= 14; o["py"] -= 14
        self.m.marker("warp", X - 6, Y - 6, w=12, h=8, id="burrow", text=to)
        self.m.spawn(name, X, Y + 12, "down")

    def drop(self, rm, x0, y0, x1, y1, to, spawn, seed=5, glow=(1.0, 0.72, 0.4), **pit):
        """A hole in the floor that has a floor under it: whoever goes in comes down at `spawn` of the
        map `to` (the floor below; or this one, for a hole into a room of its own). Azar, leaning on
        its edge, jumps. glow: the colour of whatever light is coming up it. pit: what Floor.pit takes."""
        self.pit(rm, x0, y0, x1, y1, seed=seed, **pit)
        X0, Y0 = rm.p(x0, y0)
        self.m.marker("drop", X0, Y0, w=x1 - x0, h=y1 - y0, id=to, text=spawn)
        if glow:
            self.m.light(X0 + (x1 - x0) // 2, Y0 + (y1 - y0) // 2, 2.6, glow, 0.5, flicker=True, h=0.1)

    def ladder(self, rm, x, name, to, h=2.5):
        """A ladder up a room's north wall, x pixels from its west side, into the dark over the room:
        whoever climbs it comes out at the spawn `to` of this floor. A spawn `name` is put at its foot."""
        X, Y = rm.p(x, NW)
        self.m.model(f"ladder_{int(h * 10)}", ladder(h), X, Y + 5, box=None, shadow=False, lights=False)
        self.m.marker("warp", X - 7, Y - 6, w=14, h=10, id="ladder", text=to)
        self.m.spawn(name, X, Y + 16, "down")

    def landing(self, rm, x, y, name):
        """Where somebody who came down a hole comes down."""
        X, Y = rm.p(x, y)
        self.m.markers.append({"kind": "spawn", "x": int(X), "y": int(Y), "who": name, "text": "down", "id": "fall"})

    # ---- height: floors above the floor
    def top_look(self, T, rm, sd, mask):
        """What a raised floor is paved with (a floor with a look of its own paves its own)."""
        H, W = self.H, self.W
        if self.style == 'temple':
            T.tiles(mask, seed=sd, size=16, ramp='tile', base=4.1, inlay='lapis', every=3)
            T.border(mask, 'gold', 3.6, 2, 1.5)
        elif self.style == 'crypt':
            T.slabs(mask, seed=sd, rows=(12, 14), wmin=14, wmax=24, ramp='flag', base=4.0, jitter=1.0, crack=0.12, whole=False, wear=0.5)
            T.border(mask, 'flag', 4.9, 2, 1.2)
        elif self.style == 'barrow':
            T.bricks(mask, seed=sd, bw=8, bh=4, ramp='tile', base=3.5, jitter=0.9)
            T.border(mask, 'pale', 3.4, 2, 1.2)
        else:
            T.slabs(mask, seed=sd, rows=(16,), wmin=20, wmax=28, ramp='basalt', base=4.7, jitter=0.9, crack=0.08, whole=False, wear=0.4)
            T.border(mask, 'gold', 3.2, 2, 1.4)

    def face_model(self, length, h):
        """The front of a raised floor, running east from the origin: `length` tiles long, `h` high."""
        m = Model()
        if self.style == 'temple':
            w = town.wall_mats(); body, cope = w.base, w.gold
        elif self.style == 'crypt':
            body, cope = M('sandstone', 3.3, m_ashlar(16, 8)), M('sandstone', 4.5)
        elif self.style == 'barrow':
            body, cope = M('mud', 3.3, m_brick(8, 4)), M('mud', 4.5)
        else:
            body, cope = M('stone', 3.2, m_ashlar(16, 8)), M('gold', 3.8)
        m.part(); m.box(0, 0, 0, length, PX, h, body)
        m.part(); m.box(0, -PX, h - 2 * PX, length, PX, h, cope)
        return m

    def flight_model(self, w, rise, run):
        """Steps up the front of a raised floor, climbing north from the origin."""
        n = max(2, int(round(rise * 16 / 4)))
        if self.style == 'temple':
            tread, riser = M('sandstone', 4.9, m_mottle(9, 0.3)), M('sandstone', 3.7, m_mottle(6, 0.4))
        elif self.style == 'crypt':
            tread, riser = M('sandstone', 4.3, m_mottle(9, 0.3)), M('sandstone', 3.0, m_mottle(6, 0.4))
        elif self.style == 'barrow':
            tread, riser = M('mud', 4.4, m_mottle(9, 0.3)), M('mud', 3.0, m_brick(8, 4))
        else:
            tread, riser = M('stone', 4.6, m_mottle(9, 0.3)), M('stone', 3.0, m_mottle(6, 0.4))
        m = Model()
        for i in range(n):
            m.part(); m.box(0, run * i / n, 0, w, run, rise * (i + 1) / n, riser, top=tread)
        return m

    def platform(self, rm, x0, y0, x1, y1, h=12, steps=(), run=12, hop='sew', back=True):
        """A raised floor inside a room, between lay() and bake(): (x0, y0)-(x1, y1), in pixels from the
        room's corner, is its top as it is drawn and walked on; its front, h pixels high, shows below
        y1. steps: (xa, xb) flights up its front. Its open edges are ledges: nobody walks off or on, but
        Azar, leaning on one from above, hops down (hop: which of the south, east and west ones let him).
        back=False: nothing along its north edge (a higher one stands there: say the lower one first)."""
        T = self.T
        X0, Y0 = rm.p(x0, y0)
        w, d = x1 - x0, y1 - y0
        top = T.rect(X0, Y0, w, d)
        face = T.rect(X0, Y0 + d, w, h)
        if rm.floor:
            # (in a room that is not a box, it is raised floor only where there was floor)
            fm = self._floor_mask(rm)
            top &= fm; face &= fm
        sd = self.seed + 7 * x0 + y0 + 31 * list(self.rooms).index(rm.id)
        self.top_look(T, rm, sd, top)
        T.hgt[top] += 3.0
        T.put(face, 'basalt', np.full((self.H, self.W), 1.0), 0.0)
        # its own shade on the floor below, and the north wall's on it
        T.contact(X0, Y0, X0 + w, Y0 + d + h, reach=7, strength=1.3)
        if y0 <= NW + 2:
            T.contact(rm.ox, rm.oy, rm.ox + rm.w, rm.oy + NW, reach=7, strength=1.6)
        self.platforms.append({"rm": rm, "x0": x0, "y0": y0, "x1": x1, "y1": y1, "h": h, "steps": [tuple(q) for q in steps], "run": run, "hop": hop, "back": back})

    def _raise(self, pf):
        """After the bake: the front of a raised floor, its flights of steps, and its edges."""
        m = self.m
        rm, x0, y0, x1, y1, h, run = pf["rm"], pf["x0"], pf["y0"], pf["x1"], pf["y1"], pf["h"], pf["run"]
        X0, Y0 = rm.p(x0, y0); X1, Y1 = rm.p(x1, y1)
        m.set_into_ground(self.face_model((x1 - x0) / 16.0, h / 16.0), X0, Y1 + h, seed=self.seed + x0)
        for (xa, xb) in pf["steps"]:
            m.set_into_ground(self.flight_model((xb - xa) / 16.0, h / 16.0, run / 16.0), rm.ox + xa, Y1 + h + run, seed=self.seed + xa)
        # the front: a ledge but for the flights
        x = x0
        for (xa, xb) in sorted(pf["steps"]) + [(x1, x1)]:
            if xa > x:
                m.solid(rm.ox + x, Y1 - 1, rm.ox + xa, Y1 + h, 0, f"ledge_s:{h}" if 's' in pf["hop"] else f"ledge_x:{h}")
            x = xb
        # the sides, where they do not run into a wall
        if x1 < rm.w - EW - 2:
            m.solid(X1 - 1, Y0, X1 + 3, Y1 + h, 0, f"ledge_e:{h}" if 'e' in pf["hop"] else f"ledge_x:{h}")
        if x0 > EW + 2:
            m.solid(X0 - 3, Y0, X0 + 1, Y1 + h, 0, f"ledge_w:{h}" if 'w' in pf["hop"] else f"ledge_x:{h}")
        if y0 > NW + 2 and pf["back"]:
            # (its far edge: nobody goes over that one, there being nothing to show where he would land)
            m.solid(X0 - 3, Y0 - 2, X1 + 3, Y0 + 1, 0, f"ledge_x:{h}")

    # ---- furniture
    def chest(self, rm, x, y, uid, what, layer=0, ghost=False):
        """ghost: a chest that died with its keeper. The colour of old ice, and (like the rest of the dead)
        there for a waking man and not for a dreamer."""
        X, Y = rm.p(x, y)
        if ghost:
            self.m.model("ghostchest", lambda fi: town.chest(fi == 1, ghost=True), X, Y, box=(-9, -10, 9, 0), frames=2, names=["ghostchest", "ghostchest_open"],
                         still=True, kind="chest", layer=1, data={"id": uid, "text": what})
        else:
            kit.chest(self.m, X, Y, uid, what, layer=layer)
        self.chests.append({"id": uid, "room": rm.id, "big": what in ("shield", "bigkey", "ghostkey")})

    def bigchest(self, rm, x, y, uid, what):
        """A great chest, for a main item."""
        import dprops
        X, Y = rm.p(x, y)
        self.m.model("bigchest", lambda fi: dprops.bigchest(fi == 1), X, Y, box=(-16, -18, 16, -1), frames=2, names=["bigchest", "bigchest_open"], still=True,
                     kind="bigchest", data={"id": uid, "text": what}, lights=False)
        self.chests.append({"id": uid, "room": rm.id, "big": True})

    def plaque(self, rm, x, text):
        """Writing on a room's north wall, x pixels from its west side."""
        import dprops
        X, Y = rm.p(x, NW)
        self.m.model("plaque", dprops.plaque(), X, Y + 1, box=(-10, -4, 10, 0), kind="look", data={"id": "say", "text": text}, shadow=False)

    def look(self, key, model, rm, x, y, box, text, **kw):
        """Something to walk up to and look at."""
        X, Y = rm.p(x, y)
        return self.m.model(key, model, X, Y, box=box, kind="look", data={"id": "say", "text": text}, **kw)

    def bullhead(self, rm, x, y, uid, straight=False, phase=None, herd=False):
        """A bull's head of bronze in a block of wall, facing south, its mouth a furnace door. It breathes
        fire at whoever stands in front of it; straight=True breathes straight ahead on a beat of its
        own (a row of them is lanes of fire to cross), phase = how far into the beat it starts. Only
        its own fire, thrown back off the mirror shield, breaks it (flag = uid)."""
        X, Y = rm.p(x, y)
        data = {"id": uid}
        if straight:
            data["who"] = "straight"
        if herd:
            data["who"] = "herd"                 # one of the Herdsman's own: it breathes when he tells it to
        if phase is not None:
            data["text"] = str(phase)
        self.m.model("bullhead", town.bull_statue(), X, Y, box=(-20, -8, 20, 0), kind="bullhead", data=data)

    def disc(self, rm, x, uid):
        """A sun disc on a room's north wall, x pixels from the room's west side: lit by the light off
        a raised mirror shield."""
        import dprops
        X, Y = rm.p(x, NW)
        self.m.model("sun_disc", lambda fi: dprops.sun_disc(fi == 1), X, Y + 1, box=None, frames=2, names=["sun_disc", "sun_disc_lit"], still=True,
                     kind="disc", data={"id": uid}, lights=False, shadow=False)

    def pool(self, rm, x, y, r=13):
        """Moonlight come down through a hole in the roof and lying on the floor in a pool: the one
        place a mirror has something to throw. Its middle at (x, y)."""
        m, g = self.m, self.g
        X, Y = rm.p(x, y)
        a = g.a
        ry = int(r * 0.62)
        for yy in range(Y - ry, Y + ry + 1):
            for xx in range(X - r, X + r + 1):
                d = ((xx - X) / r) ** 2 + ((yy - Y) / ry) ** 2
                if d > 1.0:
                    continue
                k = 0.62 if d < 0.5 else 0.42 if d < 0.85 else 0.22
                if ((xx + yy) % 2 == 0) and 0.5 <= d < 0.58:
                    k = 0.42                                   # a broken edge between the tones, not a ring
                c = a[yy, xx].astype(float)
                c[:3] = c[:3] * (1 - k) + np.array([196, 214, 255.0]) * k
                a[yy, xx] = c.astype(np.uint8)
        m.light(X, Y, 2.3, (0.72, 0.82, 1.0), 0.75, flicker=False, h=0.3)
        m.marker("pool", X - r, Y - ry, w=2 * r, h=2 * ry)

    def pillar(self, rm, x, y, kind=None):
        X, Y = rm.p(x, y)
        if self.style == 'crypt':
            import dprops
            self.m.model("pier", dprops.pier(), X, Y, box=(-8, -11, 8, 0), kind=kind)
        else:
            self.m.model("pillar", town.pillar(2.2), X, Y, box=(-7, -11, 7, 0), kind=kind)

    def roots(self, rm, x0, x1, y, uid, text, depth=27):
        """Roots grown across a gap in a wall that runs east-west (its face at y), from x0 to x1. The
        blade cuts them; text is what looking at them says before that. depth: how much of the way
        through the wall they stop."""
        import dprops
        X, Y = rm.p(x0, y)
        self.m.model(f"roots_{x1 - x0}", dprops.roots((x1 - x0) / 16.0), X, Y, box=(0, -depth, x1 - x0, 0), kind="roots", data={"id": uid, "text": text})

    def torch(self, rm, x, y, light=4.6):
        X, Y = rm.p(x, y)
        if self.style == 'tomb':
            kit.spirit_lamp(self.m, X, Y, light=light - 0.2)
        else:
            kit.torch(self.m, X, Y, light=light)

    def brazier(self, rm, x, y, uid=None, lit=False):
        X, Y = rm.p(x, y)
        kit.brazier(self.m, X, Y, lit, uid)

    def enemy(self, rm, kind, x, y, uid=None, once=False):
        X, Y = rm.p(x, y)
        self.m.enemy(kind, X, Y, uid, once=once)

    def block(self, rm, x, y, uid):
        X, Y = rm.p(x, y)
        self.m.model("block", town.stone_block(), X, Y, box=(-8, -12, 8, 0), kind="block", data={"id": uid})

    def plate(self, rm, x, y, uid):
        X, Y = rm.p(x, y)
        self.m.model("plate", town.plate(), X, Y, box=None, kind="plate", data={"id": uid}, shadow=False)

    def bars(self, rm, x, y, uid, when, w=5.25, opts="", say=None):
        """A grille across part of a room, running east-west, its middle at (x, y). say: what the game
        tells the player the first time it lifts."""
        X, Y = rm.p(x, y)
        data = {"id": uid, "text": when, "who": opts}
        if say:
            data["say"] = say
        self.m.model(f"bars_{int(w * 16)}", town.bars(w, 1.4), X, Y, box=(-int(w * 8), -6, int(w * 8), 0), kind="bars", data=data)

    def partition(self, rm, x0, x1, y, h=1.5, layer=0):
        """A lower wall inside a room, running east from x0 to x1, its face at y. layer 1: only the
        waking world has it (a dreamer walks through); layer 2: only the dream."""
        import dprops
        m = self.m
        build = town.partition if self.style == 'temple' else town.tomb_partition if self.style == 'tomb' else dprops.crypt_partition
        if layer and self.style == 'crypt':
            build = lambda L, h: dprops.crypt_partition(L, h=h, brick=True)       # a way bricked up: only the waking world believes it
        if layer:
            # a thing of its own, drawn in front of or behind whoever is near it: only its foot is solid
            m.model(f"{self.style}_dreamwall_ew_{x1 - x0}_{int(h * 10)}", build((x1 - x0) / 16.0, h=h), rm.ox + x0, rm.oy + y, box=None, layer=layer)
            m.solid(rm.ox + x0, rm.oy + y - 10, rm.ox + x1, rm.oy + y - 1, layer)
        else:
            # painted into the floor: nobody may stand where its face and its top are drawn
            m.set_into_ground(build((x1 - x0) / 16.0, h=h), rm.ox + x0, rm.oy + y, seed=self.seed + x0 + y)
            m.solid(rm.ox + x0, rm.oy + y - int(h * 16) - 8, rm.ox + x1, rm.oy + y - 4)

    def partition_ns(self, rm, x, y0, y1, h=1.5, layer=0):
        """The same kind of wall running north from y1 up to y0, 8 pixels thick at x."""
        import dprops
        m = self.m
        build = town.partition_ns if self.style == 'temple' else town.tomb_partition_ns if self.style == 'tomb' else dprops.crypt_partition_ns
        if layer and self.style == 'crypt':
            build = lambda dp, **kw: dprops.crypt_partition_ns(dp, brick=True, **kw)
        if layer:
            m.model(f"{self.style}_dreamwall_{y1 - y0}", build((y1 - y0) / 16.0), rm.ox + x, rm.oy + y1, box=None, layer=layer)
        elif y0 > NW + 4:
            # it starts out on the floor, not at the north wall: its top is drawn over ground somebody can
            # stand on (a gap above it, most of all), so it is a thing of its own and he passes behind it
            m.model(f"{self.style}_wall_ns_{y1 - y0}_{int(h * 10)}", build((y1 - y0) / 16.0, h=h), rm.ox + x, rm.oy + y1, box=None)
        else:
            m.set_into_ground(build((y1 - y0) / 16.0, h=h), rm.ox + x, rm.oy + y1, seed=self.seed + x)
        m.solid(rm.ox + x, rm.oy + y0, rm.ox + x + 8, rm.oy + y1, layer)

    def pit(self, rm, x0, y0, x1, y1, bridges=(), seed=5, planks=()):
        """A drop inside a room (pixels from its corner). bridges: polylines of (x, y) that are roads
        of moonlight: there in the dream, a fall when awake. planks: (a, b) spans along x (or
        ('y', a, b) along y) whose part of the drop is boxed on its own, so a plank laid there
        (Floor.plank) can switch exactly that much of it off."""
        m, g = self.m, self.g
        X0, Y0 = rm.p(x0, y0); w, h = x1 - x0, y1 - y0
        G.chasm(g, X0, Y0, w, h, seed=seed)
        m.ground_n[Y0:Y0 + h, X0:X0 + w] = (128, 128, 255, 1)
        cols, rows = w // PIT, h // PIT
        road = np.zeros((rows, cols), bool)
        for bi, pts in enumerate(bridges):
            for (a, b) in zip(pts, pts[1:]):
                ax0, ax1 = sorted((a[0], b[0])); ay0, ay1 = sorted((a[1], b[1]))
                for r_ in range(rows):
                    for c_ in range(cols):
                        px, py = x0 + c_ * PIT + PIT // 2, y0 + r_ * PIT + PIT // 2
                        if ax0 - 10 <= px <= ax1 + 10 and ay0 - 10 <= py <= ay1 + 10:
                            road[r_, c_] = True
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            bx0, by0, bx1, by1 = min(xs) - 12, min(ys) - 12, max(xs) + 12, max(ys) + 12

            def draw(cv, ax, ay, fi, pts=pts, bx0=bx0, by0=by0):
                G.moon_bridge(cv, [(q[0] - bx0, q[1] - by0) for q in pts], 16, fi)
            m.prop(f"{self.name}_{rm.id}_moon_{bi}", draw, rm.ox + bx0, rm.oy + by0, layer=2, size=(bx1 - bx0, by1 - by0), anchor=(0, 0), pad=0)
        strip = np.zeros((rows, cols), bool)
        for pk in planks:
            along_y = pk[0] == 'y'
            a, b = pk[-2], pk[-1]
            for r_ in range(rows):
                for c_ in range(cols):
                    q = (y0 + r_ * PIT + PIT // 2) if along_y else (x0 + c_ * PIT + PIT // 2)
                    if a <= q < b:
                        strip[r_, c_] = True
        for layer, mask in ((0, ~road & ~strip), (1, road & ~strip), (0, strip)):
            for r_ in range(rows):
                c_ = 0
                while c_ < cols:
                    if mask[r_, c_]:
                        c0 = c_
                        while c_ < cols and mask[r_, c_]:
                            c_ += 1
                        m.solid(X0 + c0 * PIT, Y0 + r_ * PIT, X0 + c_ * PIT, Y0 + (r_ + 1) * PIT, layer, "pit")
                    else:
                        c_ += 1

    # ---- Nod's Pocket: what only the dream has, and what in the waking world it is for
    def dreamthing(self, rm, x, y, uid, what, key, build, box=None, source=False, frames=None, wall=False):
        """Something only the dream has, small enough to pocket (what = the Pocket's name for it: key,
        plank, flame...). source: there is always another. wall: it hangs on the north wall at x."""
        X, Y = rm.p(x, NW + 1) if wall else rm.p(x, y)
        data = {"id": uid, "text": what}
        if source:
            data["who"] = "source"
        return self.m.model(key, build, X, Y, box=box, layer=2, kind="dreamthing", data=data, frames=frames, lights=False, shadow=False)

    def dreamlock(self, rm, x, y, uid, w=3.0):
        """A grille across part of a room whose lock only a key out of a dream fits (its middle at (x, y))."""
        import bprops
        X, Y = rm.p(x, y)
        self.m.model(f"lockgrille_{int(w * 16)}", bprops.lock_grille(w), X, Y, box=(-int(w * 8), -6, int(w * 8), 0), kind="dreamlock", data={"id": uid})

    def bluelamp(self, rm, x, y, uid):
        """A cold lamp of the dead: only a flame out of a dream lights it (then lit:uid holds)."""
        import bprops
        X, Y = rm.p(x, y)
        self.m.model("bluelamp", lambda fi: bprops.blue_lamp(fi), X, Y, box=(-4, -5, 4, 0), frames=4,
                     names=["bluelamp", "bluelamp_lit_0", "bluelamp_lit_1", "bluelamp_lit_2"], still=True, kind="bluelamp", data={"id": uid}, lights=False)

    def plank(self, rm, x, y0, y1, uid, half=12):
        """Two brackets either side of a drop that lies between y0 and y1, at x: where a plank of moonlight
        can be laid. The pit must have been made with planks=[(x - half, x + half)]."""
        import bprops
        m = self.m
        X, Yn = rm.p(x, y0)
        _, Ys = rm.p(x, y1)
        m.model("brackets", bprops.brackets(), X, Ys + 4, box=None, kind="plankgap", data={"id": uid}, shadow=False)
        m.model("brackets", bprops.brackets(), X, Yn - 2, box=None, kind="plankgap", data={"id": uid}, shadow=False)
        m.model(f"moonplank_{y1 - y0}", bprops.moon_plank((y1 - y0 + 10) / 16.0, half / 16.0 - 0.1), X, Yn - 5, box=None, kind="plank",
                data={"id": uid, "text": f"{X - half},{Yn},{X + half},{Ys}"}, lights=False, shadow=False)

    def standard(self, rm, x, y, side, uid):
        """A general's standard: hauled down with the action button (flag = uid)."""
        import bprops
        X, Y = rm.p(x, y)
        self.m.model(f"standard_{side}", lambda fi: bprops.standard(side, fi == 1), X, Y, box=(-4, -6, 4, 0), frames=2,
                     names=[f"standard_{side}", f"standard_{side}_down"], still=True, kind="standard", data={"id": uid, "text": side}, lights=False)

    # ---- out
    def save(self):
        self.m.save()
        os.makedirs(f"{mapkit.RES}/Menu", exist_ok=True)
        path = f"{mapkit.RES}/Menu/dungeon_{self.dungeon}.json"
        data = json.load(open(path)) if os.path.exists(path) else {"floors": []}
        rooms = []
        for rm in self.rooms.values():
            q = {"id": rm.id, "c": rm.c, "r": rm.r, "cw": rm.cw, "ch": rm.ch, "name": rm.name, "mark": rm.mark}
            if rm.passage:
                q["pass"] = True
            if rm.secret:
                q["secret"] = True
            if rm.floor:
                # each rectangle of its floor as fractions of the space inside the room's walls, for the map page: x0, y0, x1, y1, ...
                iw, ih = rm.w - 2 * EW, rm.h - NW - SW
                q["shape"] = [round(v, 3) for (x0, y0, x1, y1) in rm.floor for v in ((x0 - EW) / iw, (y0 - NW) / ih, (x1 - EW) / iw, (y1 - NW) / ih)]
            rooms.append(q)
        links = []
        for i, l in enumerate(self.links):
            lower = self.cells.get((l["c"], l["r"]))
            other = self.cells.get((l["c"], l["r"] - 1)) if l["side"] == 'n' else self.cells.get((l["c"] - 1, l["r"]))
            links.append({"c": l["c"], "r": l["r"], "side": l["side"], "kind": l["kind"], "to": l.get("to", ""), "id": l.get("id", ""),
                          "a": lower.id if lower else "", "b": other.id if other else ""})
        floor = {"map": self.name, "label": self.label, "order": self.order, "cols": self.cols, "rows": self.rows,
                 "rooms": rooms, "links": links, "chests": self.chests}
        data["floors"] = sorted([f for f in data["floors"] if f["map"] != self.name] + [floor], key=lambda f: -f["order"])
        json.dump(data, open(path, "w"))
