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
from mapkit import MapBuilder
from forge import Model, M, m_ashlar, m_mottle, m_glazed

PX = 1 / 16.0
CW, CH = 416, 224             # a cell, in pixels
NW, SW, EW = 48, 16, 16       # the north wall's face, the south wall's top, a side wall's top
DOOR = 40                     # how wide a north or south doorway is
SIDE0, SIDE1 = 112, 144       # the rows an east or west doorway takes, measured from the top of its cell
PIT = 8                       # pits are boxed on a grid this fine
DW, DH = 2.5, 2.1             # a doorway through a north wall, in tiles


# ------------------------------------------------------------------ models
def wall(style, length, doors=(), h=2.75, d=0.25):
    """A room's north wall running east from the origin, with a dark doorway at each x in doors
    (tiles from its west end). 'temple' is glazed blue brick with gold bulls; 'tomb' is painted
    plaster on dark stone."""
    m = Model()

    def near(x, margin):
        return any(abs(x - dx) < DW / 2 + margin for dx in doors)

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


# ------------------------------------------------------------------ a floor of rooms
class Room:
    def __init__(self, floor, rid, c, r, cw, ch, name, opts):
        self.floor, self.id, self.c, self.r, self.cw, self.ch = floor, rid, c, r, cw, ch
        self.name, self.opts = name, opts
        self.ox, self.oy, self.w, self.h = c * CW, r * CH, cw * CW, ch * CH
        self.mark = ""                       # what the map scroll draws on it: 'boss', 'mini'

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
            if self.style == 'temple':
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
                gaps |= T.rect(self.door_x(l) - DOOR // 2, rm.oy + rm.h - SW, DOOR, SW)
            for l in self._west(rm):
                gaps |= T.rect(rm.ox, l["r"] * CH + SIDE0, EW, SIDE1 - SIDE0)
            for l in self._east(rm):
                gaps |= T.rect(rm.ox + rm.w - EW, l["r"] * CH + SIDE0, EW, SIDE1 - SIDE0)
            tops &= ~gaps
            if self.style == 'temple':
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

    # ---- walls, doors and everything that stands, after the bake
    def bake(self):
        m = self.m
        g = self.g = m.bake()
        for rm in self.rooms.values():
            north = self._north(rm)
            holes = [l for l in north if l["kind"] != 'wall']
            m.set_into_ground(wall(self.style, rm.w / 16.0, doors=[(self.door_x(l) - rm.ox) / 16.0 for l in holes]), rm.ox, rm.oy + NW)
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
            m.marker("room", rm.ox, rm.oy, w=rm.w, h=rm.h, id=rm.id, who=rm.opts, text=rm.name)
        for i, l in enumerate(self.links):
            self._door(i, l)
        return g

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
                    if l.get("door"):
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
            if kind == 'lock' or kind == 'big':
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
                m.model("bars_gap", town.bars(2.5, 1.2), dx, y - 3, box=(-20, -11, 20, 0), kind="bars", data=data)
        else:
            bx, gy = l["c"] * CW, l["r"] * CH
            if self.cells.get((l["c"], l["r"])) is None or self.cells.get((l["c"] - 1, l["r"])) is None:
                return
            self._overlay(f"{self.name}_jamb_{i}", bx - EW, gy + SIDE0 - 18, bx + EW, gy + SIDE0, gy + SIDE1 + 2)
            if kind == 'bars':
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

    # ---- furniture
    def chest(self, rm, x, y, uid, what, layer=0):
        X, Y = rm.p(x, y)
        kit.chest(self.m, X, Y, uid, what, layer=layer)
        self.chests.append({"id": uid, "room": rm.id, "big": what in ("shield", "sling", "stick", "bigkey")})

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

    def pit(self, rm, x0, y0, x1, y1, bridges=(), seed=5):
        """A drop inside a room (pixels from its corner). bridges: polylines of (x, y) that are roads
        of moonlight: there in the dream, a fall when awake."""
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
        for layer, mask in ((0, ~road), (1, road)):
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

    # ---- out
    def save(self):
        self.m.save()
        os.makedirs(f"{mapkit.RES}/Menu", exist_ok=True)
        path = f"{mapkit.RES}/Menu/dungeon_{self.dungeon}.json"
        data = json.load(open(path)) if os.path.exists(path) else {"floors": []}
        rooms = [{"id": rm.id, "c": rm.c, "r": rm.r, "cw": rm.cw, "ch": rm.ch, "name": rm.name, "mark": rm.mark} for rm in self.rooms.values()]
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
