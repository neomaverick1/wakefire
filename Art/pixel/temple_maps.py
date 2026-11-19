"""Beyond the Temple Gate: the yard before the ziggurat with its chasm (crossable only on a long
road of moonlight in the dream), then three floors inside: the hall of dream walls, the
gallery of the bull that breathes fire, and the summit where the god sleeps."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R, OUTLINE
import ashkel_art as A
import region_art as G
from mapkit import MapBuilder

CHEST = '/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'
C = 8


def chest(m, x, y, cid, what, layer=0):
    m.prop("chest" if layer == 0 else "chest_dream", lambda cv, ax, ay, fi: cv.blit(Canvas.load(CHEST), ax - 8, ay - 15), x, y, box=(-7, -6, 7, 0),
           size=(24, 24), pad=4, kind="chest", layer=layer, data={"id": cid, "text": what})


def pit_boxes(m, mask, layer):
    rows, cols = mask.shape
    for r in range(rows):
        c = 0
        while c < cols:
            if mask[r, c]:
                c0 = c
                while c < cols and mask[r, c]:
                    c += 1
                m.solid(c0 * C, r * C, c * C, (r + 1) * C, layer, "pit")
            else:
                c += 1


# ------------------------------------------------------------------ the temple yard
YARD_BRIDGE = [(440, 340), (440, 306), (180, 306), (180, 262), (440, 262), (440, 218), (320, 218), (320, 190)]


def temple_yard():
    TW, TH = 40, 36
    W, H = TW * 16, TH * 16
    m = MapBuilder("temple_yard", TW, TH, R['grass'][2], music="temple")
    g = m.ground
    A.grass(g, 0, 0, W, H, seed=71, dense=0.6)
    A.slabs(g, 32, 340, W - 64, H - 340, R['lime'], 16, 12, seed=72)
    A.slabs(g, 32, 60, W - 64, 140, R['lime'], 16, 12, seed=73)
    G.chasm(g, 0, 200, W, 140)
    # the ziggurat's lowest tier rises along the top
    A.city_wall(g, 0, 8, W, face_h=40, top_h=8, seed=74)
    m.solid(0, 0, W, 58)
    G.bronze_door(g, 320, 58, 34, 34, kind='lock')
    m.solid(0, 0, 32, H); m.solid(W - 32, 0, W, H)
    # the chasm: never walkable, except the road of moonlight, which only the dream has
    cols, rows = W // C, H // C
    pit = np.zeros((rows, cols), bool)
    road = np.zeros_like(pit)
    for r in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r * C + 4
            if 200 <= y < 340:
                pit[r, c] = True
    for (a, b) in zip(YARD_BRIDGE, YARD_BRIDGE[1:]):
        x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
        for r in range(rows):
            for c in range(cols):
                x, y = c * C + 4, r * C + 4
                if x0 - 10 <= x <= x1 + 10 and y0 - 10 <= y <= y1 + 10:
                    road[r, c] = True
    road &= pit
    # the old drawbridge in the middle (lowered from the far side once Azar has crossed)
    draw = np.zeros_like(pit)
    for r in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r * C + 4
            if 296 <= x < 344 and 200 <= y < 340:
                draw[r, c] = True
    pit_boxes(m, pit & ~road & ~draw, 0)
    pit_boxes(m, road & ~draw, 1)
    pit_boxes(m, draw & ~road, 0)
    pit_boxes(m, draw & road, 1)
    for (x0, y0, x1, y1) in ((296, 200, 344, 340),):
        m.marker("drawbridge", x0, y0, w=x1 - x0, h=y1 - y0)
    m.prop("drawbridge", lambda cv, ax, ay, fi: G.dock(cv, ax, ay, 48, 140), 296, 200, size=(48, 144), anchor=(0, 0), pad=0, kind="drawbridge")
    xs = [p[0] for p in YARD_BRIDGE]; ys = [p[1] for p in YARD_BRIDGE]
    bx0, by0, bx1, by1 = min(xs) - 12, min(ys) - 12, max(xs) + 12, max(ys) + 12
    def bridge_draw(cv, ax, ay, fi):
        G.moon_bridge(cv, [(p[0] - bx0, p[1] - by0) for p in YARD_BRIDGE], 16, fi)
    m.prop("moon_bridge_yard", bridge_draw, bx0, by0, layer=2, size=(bx1 - bx0, by1 - by0), anchor=(0, 0), pad=0)
    # guardians, fire, a sign
    lam = Canvas.load('/srv/Wakefire/Art/sprites/props/lamassu.png')
    m.prop("lamassu_yl", lambda cv, ax, ay, fi: cv.blit(lam, ax - 13, ay - 36), 250, 100, box=(-10, -8, 10, 0), size=(48, 56), pad=8)
    m.prop("lamassu_yr", lambda cv, ax, ay, fi: cv.blit(lam, ax - (lam.w - 13), ay - 36, flip=True), 390, 100, box=(-10, -8, 10, 0), size=(48, 56), pad=8)
    def braz(lit):
        return lambda cv, ax, ay, fi: A.brazier(cv, ax, ay, lit=lit, frame=fi)
    for i, (x, y) in enumerate(((120, 380), (520, 380), (120, 150), (520, 150))):
        m.prop("brazier_lit", braz(True), x, y, box=(-6, -4, 6, 0), size=(24, 40), pad=4, frames=4, kind="torch")
        m.light(x, y - 18, 5.0, (1.0, 0.70, 0.36), 0.85)
    m.prop("brazier_lit", braz(True), -100, -100, size=(24, 40), pad=4, frames=4)
    m.prop("sign_yard", lambda cv, ax, ay, fi: A.sign(cv, ax, ay), 360, 470, box=(-2, -2, 2, 0), size=(24, 24), pad=2, kind="sign",
           data={"text": "sign_yard"})
    m.light(320, 260, 7.0, (0.55, 0.62, 1.0), 0.45, flicker=False)
    m.marker("npc", 140, 500, who="goat_yard")
    m.spawn("south", 320, 552, "up")
    m.spawn("door", 320, 80, "down")
    m.exit(296, H - 8, 344, H, "ashkel", "gate")
    m.exit(306, 56, 334, 64, "zig_1", "south")
    m.solid(0, H - 4, 296, H); m.solid(344, H - 4, W, H)
    m.save()


# ------------------------------------------------------------------ inside
def room(m, W, H, wall_h=48, seed=80):
    g = m.ground
    G.tile_floor(g, 0, 0, W, H, seed=seed)
    G.floor_inlays(g, 24, wall_h, W - 48, H - wall_h - 16)
    G.glazed_wall(g, 0, 0, W, wall_h, seed=seed)
    for x in range(0, W):
        g.px(x, wall_h, OUTLINE)
    # side walls: thick, seen from above
    for (x0, x1) in ((0, 24), (W - 24, W)):
        for y in range(wall_h, H):
            for x in range(x0, x1):
                g.px(x, y, R['glaze'][1] if (x + y // 4) % 5 else R['glaze'][2])
        g.vline(x1 - 1 if x0 == 0 else x0, wall_h, H - 1, OUTLINE)
    g.rect(0, H - 16, W, 16, R['glaze'][1])
    g.hline(0, W - 1, H - 16, OUTLINE)
    m.solid(0, 0, W, wall_h - 4); m.solid(0, 0, 24, H); m.solid(W - 24, 0, W, H); m.solid(0, H - 14, W // 2 - 20, H); m.solid(W // 2 + 20, H - 14, W, H)


def torches(m, pts):
    def ptorch(cv, ax, ay, fi):
        A.pole_torch(cv, ax, ay, frame=fi)
    for (x, y) in pts:
        m.prop("pole_torch", ptorch, x, y, box=(-2, -2, 3, 0), size=(24, 40), pad=4, frames=4, kind="torch")
        m.light(x + 1, y - 24, 4.6, (1.0, 0.68, 0.34), 0.85)


def zig_1():
    TW, TH = 32, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("zig_1", TW, TH, R['brick'][2], music="dungeon")
    room(m, W, H, seed=81)
    g = m.ground
    G.carpet(g, 244, 208, 24, H - 224)
    G.carpet(g, 244, 120, 24, 56)
    G.cobweb(g, 26, 50); G.cobweb(g, W - 27, 50, flip=True)
    # a dividing wall with the locked door, and stairs up beyond it
    G.glazed_wall(g, 24, 176, W - 48, 32, seed=82, frieze=False)
    m.solid(24, 176, 236, 204); m.solid(276, 176, W - 24, 204)
    m.prop("lockdoor", lambda cv, ax, ay, fi: G.bronze_door(cv, ax, ay, 40, 30, 'lock'), 256, 206, box=(-20, -26, 20, 0), size=(48, 40), pad=4,
           kind="lockdoor", data={"id": "z1_door"})
    G.stairs_up(g, 256, 100, 40, 36)
    # the east alcove, closed off by a wall that only the waking world has
    m.prop("dreamwall", lambda cv, ax, ay, fi: G.glazed_wall(cv, ax - 8, ay - 122, 8, 122, seed=84, frieze=False), 400, 330,
           size=(16, 126), anchor=(8, 122), pad=0, layer=1)
    m.solid(392, 208, 400, 330, 1)
    chest(m, 450, 276, "z1_key", "key")
    # the west: a block, a plate, bars that lift
    m.prop("block", lambda cv, ax, ay, fi: G.block(cv, ax, ay), 172, 296, box=(-8, -12, 8, 0), size=(24, 24), pad=4, kind="block", data={"id": "z1_block"})
    m.prop("plate", lambda cv, ax, ay, fi: G.plate(cv, ax, ay - 6), 140, 296, size=(20, 16), pad=2, kind="plate", data={"id": "z1_plate"})
    chest(m, 66, 236, "z1_coins", "shekels:30")
    G.glazed_wall(g, 108, 204, 8, 54, seed=85, frieze=False)
    m.solid(108, 204, 116, 258)
    def bars(cv, ax, ay, fi):
        for k in range(-42, 43, 3):
            cv.vline(ax + k, ay - 22, ay - 1, R['bronze'][4] if k % 6 == 0 else R['bronze'][2])
        cv.hline(ax - 42, ax + 42, ay - 22, R['bronze'][4])
    m.prop("bars", bars, 66, 258, box=(-42, -6, 42, 0), size=(96, 30), pad=4, kind="bars", data={"id": "z1_bars"})
    for (x, y) in ((150, 120), (362, 120), (150, 330), (362, 330)):
        m.prop("pillar", lambda cv, ax, ay, fi: G.pillar(cv, ax, ay), x, y, box=(-7, -5, 7, 0), size=(24, 48), pad=4)
    torches(m, ((80, 160), (432, 160)))
    m.enemy("sentinel", 300, 280, "z1_s1", once=True)
    m.enemy("sentinel", 200, 120, "z1_s2", once=True)
    for i, (x, y) in enumerate(((180, 250), (330, 300), (256, 150))):
        m.enemy("moth", x, y, f"z1_m{i}")
    m.spawn("south", 256, H - 26, "up")
    m.spawn("top", 256, 124, "down")
    m.exit(236, H - 8, 276, H, "temple_yard", "door")
    m.exit(240, 64, 272, 80, "zig_2", "south")
    m.save()


def zig_2():
    TW, TH = 32, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("zig_2", TW, TH, R['brick'][2], music="dungeon")
    room(m, W, H, seed=91)
    g = m.ground
    G.carpet(g, 244, 290, 24, H - 306)
    G.carpet(g, 244, 84, 24, 64)
    G.cobweb(g, 26, 50); G.cobweb(g, W - 27, 50, flip=True)
    # the shield on its dais
    A.slabs(g, 216, 236, 80, 52, R['lime'], 16, 12, seed=92)
    chest(m, 256, 268, "z2_shield", "shield")
    # the bull's head that breathes fire across the way north
    G.glazed_wall(g, 24, 150, W - 48, 30, seed=93, frieze=False)
    m.solid(24, 150, 236, 176); m.solid(276, 150, W - 24, 176)
    m.prop("bullhead", lambda cv, ax, ay, fi: G.bull_statue(cv, ax, ay), 256, 178, box=(-20, -8, 20, 0), size=(44, 34), pad=4, kind="bullhead",
           data={"id": "z2_bull"})
    # beyond it: the bull key, and the great door up
    chest(m, 120, 110, "z2_bigkey", "bigkey")
    m.prop("bigdoor", lambda cv, ax, ay, fi: G.bronze_door(cv, ax, ay, 40, 32, 'bull'), 256, 76, box=(-20, -26, 20, 0), size=(48, 42), pad=4,
           kind="bigdoor", data={"id": "z2_bigdoor"})
    G.stairs_up(g, 256, 52, 40, 20)
    for (x, y) in ((120, 330), (392, 330)):
        m.prop("pillar", lambda cv, ax, ay, fi: G.pillar(cv, ax, ay), x, y, box=(-7, -5, 7, 0), size=(24, 48), pad=4)
    torches(m, ((80, 220), (432, 220), (80, 120), (432, 120)))
    m.enemy("sentinel", 150, 300, "z2_s1", once=True)
    m.enemy("sentinel", 360, 300, "z2_s2", once=True)
    m.enemy("sentinel", 380, 110, "z2_s3", once=True)
    m.spawn("south", 256, H - 26, "up")
    m.spawn("top", 256, 96, "down")
    m.exit(236, H - 8, 276, H, "zig_1", "top")
    m.exit(240, 44, 272, 58, "zig_3", "south", need="door_z2_bigdoor")
    m.save()


def zig_3():
    TW, TH = 30, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("zig_3", TW, TH, R['brick'][2], music="summit")
    room(m, W, H, wall_h=64, seed=101)
    g = m.ground
    G.carpet(g, W // 2 - 12, 262, 24, H - 278)
    # the summit floor, the altar, the god's bed beyond it
    A.slabs(g, 24, 64, W - 48, 70, R['lime'], 16, 12, seed=102)
    A.sigil(g, W // 2, 230, 26)
    m.marker("god", W // 2 - 10, 126)
    m.marker("altar", W // 2 + 64, 132)
    m.marker("boss", W // 2, 212)
    for (x, y) in ((110, 190), (W - 110, 190), (110, 300), (W - 110, 300)):
        m.prop("pillar", lambda cv, ax, ay, fi: G.pillar(cv, ax, ay), x, y, box=(-7, -5, 7, 0), size=(24, 48), pad=4, kind="pillar")
    torches(m, ((60, 150), (W - 60, 150), (60, 330), (W - 60, 330)))
    m.spawn("south", W // 2, H - 26, "up")
    m.exit(W // 2 - 20, H - 8, W // 2 + 20, H, "zig_2", "top")
    m.save()


if __name__ == "__main__":
    which = sys.argv[1:] or ["temple_yard", "zig_1", "zig_2", "zig_3"]
    for w in which:
        globals()[w]()
