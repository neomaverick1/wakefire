"""Beyond the Temple Gate: the yard before the ziggurat with its chasm (crossable only on a long
road of moonlight in the dream), then three floors inside: the hall of dream walls, the
gallery of the bull that breathes fire, and the summit where the god sleeps."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R, OUTLINE
import ashkel_art as A
import region_art as G
import town
import kit
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
    m = MapBuilder("temple_yard", TW, TH, (60, 44, 40, 255), music="temple")
    T = m.lay(seed=71)
    T.earth(T.all(), seed=1, base=3.6, ramp='dust')
    # two courts of pale stone, and between them the chasm
    courts = T.rect(32, 340, W - 64, H - 340) | T.rect(32, 58, W - 64, 142)
    T.slabs(courts, seed=72, rows=(12,), wmin=16, wmax=16, ramp='pale', base=4.0, jitter=0.9, crack=0.06, whole=False, wear=0.5, moss=0.05)
    # the way to the door: paler still, between two bands of glazed brick studded with gold
    way = T.rect(300, 58, 40, 142) | T.rect(300, 340, 40, H - 340)
    T.slabs(way, seed=73, rows=(12,), wmin=20, wmax=20, ramp='pale', base=4.8, jitter=0.5, crack=0.03, whole=False, wear=0.3)
    bands = (T.rect(296, 58, 4, 142) | T.rect(340, 58, 4, 142) | T.rect(296, 340, 4, H - 340) | T.rect(340, 340, 4, H - 340))
    T.bricks(bands, seed=74, bw=8, bh=4, ramp='lapis', base=3.3, jitter=0.7)
    stud = bands & ((T.yy % 16) >= 7) & ((T.yy % 16) <= 8) & (((T.xx - 296) % 44) >= 1) & (((T.xx - 296) % 44) <= 2)
    T.put(stud, 'gold', np.full((H, W), 4.0), 1.4)
    T.contact(0, 30, W, 58, reach=7, strength=1.6)
    g = m.bake()
    G.chasm(g, 0, 200, W, 140)
    m.ground_n[200:340, :] = (128, 128, 255, 1)
    # the precinct walls close the sides; the ziggurat's lowest tier rises along the top
    m.set_into_ground(town.precinct_side(H / 16.0), 0, H, seed=3)
    m.set_into_ground(town.precinct_side(H / 16.0), W - 32, H, seed=4)
    m.model("zig_tier", town.ziggurat_tier(W / 16.0, h=2.6, d=1.2, door_at=20.0), 0, 58, box=None)
    m.solid(0, 0, W, 58)
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
    for i, (x, y) in enumerate(((120, 380), (520, 380), (120, 150), (520, 150))):
        kit.brazier(m, x, y, lit=True)
    kit.brazier_frames(m)
    kit.sign(m, 360, 470, "sign_yard", "sign_yard")
    for (x, y, sd) in ((60, 560, 0), (580, 560, 1), (70, 420, 2), (570, 430, 3)):
        kit.palm(m, x, y, sd)
    for (x, y, sd) in ((180, 520, 1), (470, 540, 2), (200, 120, 3), (440, 126, 4)):
        m.model(f"planter_{sd}", town.planter(sd), x, y, box=(-14, -10, 14, 0))
    m.light(320, 260, 7.0, (0.55, 0.62, 1.0), 0.45, flicker=False, h=0.4)
    m.marker("npc", 140, 500, who="goat_yard")
    m.spawn("south", 320, 552, "up")
    m.spawn("door", 320, 80, "down")
    m.exit(296, H - 8, 344, H, "ashkel", "gate")
    m.exit(306, 56, 334, 64, "zig_1", "south")
    m.solid(0, H - 4, 296, H); m.solid(344, H - 4, W, H)
    m.save()


# ------------------------------------------------------------------ inside
def room(m, W, H, wall_h=48, seed=80, door=True):
    g = m.ground
    G.tile_floor(g, 0, 0, W, H, seed=seed)
    G.floor_inlays(g, 24, wall_h, W - 48, H - wall_h - 16)
    G.glazed_wall(g, 0, 0, W, wall_h, seed=seed)
    for x in range(0, W):
        g.px(x, wall_h, OUTLINE)
    # the north and west walls throw shade across the floor
    G.floor_shadow(g, 24, wall_h + 1, W - 48, 6, 'y+')
    G.floor_shadow(g, 24, wall_h + 1, 5, H - wall_h - 17, 'x+')
    # thick walls seen from above: capstones, gold coping on the inner edge
    G.wall_top(g, 0, wall_h, 24, H - wall_h, inner='right', seed=seed + 1)
    G.wall_top(g, W - 24, wall_h, 24, H - wall_h, inner='left', seed=seed + 2)
    G.wall_top(g, 24, H - 16, W - 48, 16, inner='up', seed=seed + 3)
    if door:
        G.doorway(g, W // 2, H, 40, 16)
    m.solid(0, 0, W, wall_h - 4); m.solid(0, 0, 24, H); m.solid(W - 24, 0, W, H); m.solid(0, H - 14, W // 2 - 20, H); m.solid(W // 2 + 20, H - 14, W, H)


def torches(m, pts):
    for (x, y) in pts:
        kit.torch(m, x, y, light=4.6)


def pillar(m, x, y, kind=None):
    m.model("pillar", town.pillar(2.2), x, y, box=(-7, -11, 7, 0), kind=kind)


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
    G.inner_wall(g, 24, 176, W - 48, 32, seed=82)
    m.solid(24, 176, 236, 204); m.solid(276, 176, W - 24, 204)
    m.model("lockdoor", town.bronze_door(2.5, 1.9, 'lock'), 256, 206, box=(-20, -26, 20, 0), kind="lockdoor", data={"id": "z1_door"})
    G.stairs_up(g, 256, 100, 40, 36)
    # the east alcove, closed off by a wall that only the waking world has
    m.prop("dreamwall", lambda cv, ax, ay, fi: G.inner_wall(cv, ax - 8, ay - 122, 8, 122, seed=84), 400, 330,
           size=(16, 126), anchor=(8, 122), pad=0, layer=1)
    m.solid(392, 208, 400, 330, 1)
    chest(m, 450, 276, "z1_key", "key")
    # the west: a block, a plate, bars that lift
    m.model("block", town.stone_block(), 172, 296, box=(-8, -12, 8, 0), kind="block", data={"id": "z1_block"})
    m.prop("plate", lambda cv, ax, ay, fi: G.plate(cv, ax, ay - 6), 140, 296, size=(20, 16), pad=2, kind="plate", data={"id": "z1_plate"})
    chest(m, 66, 236, "z1_coins", "shekels:30")
    G.inner_wall(g, 108, 204, 8, 54, seed=85)
    m.solid(108, 204, 116, 258)
    def bars(cv, ax, ay, fi):
        for k in range(-42, 43, 3):
            cv.vline(ax + k, ay - 22, ay - 1, R['bronze'][4] if k % 6 == 0 else R['bronze'][2])
        cv.hline(ax - 42, ax + 42, ay - 22, R['bronze'][4])
    m.prop("bars", bars, 66, 258, box=(-42, -6, 42, 0), size=(96, 30), pad=4, kind="bars", data={"id": "z1_bars"})
    for (x, y) in ((150, 120), (362, 120), (150, 330), (362, 330)):
        pillar(m, x, y)
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
    G.inner_wall(g, 24, 150, W - 48, 30, seed=93)
    m.solid(24, 150, 236, 176); m.solid(276, 150, W - 24, 176)
    m.prop("bullhead", lambda cv, ax, ay, fi: G.bull_statue(cv, ax, ay), 256, 178, box=(-20, -8, 20, 0), size=(44, 34), pad=4, kind="bullhead",
           data={"id": "z2_bull"})
    # beyond it: the bull key, and the great door up
    chest(m, 120, 110, "z2_bigkey", "bigkey")
    m.model("bigdoor", town.bronze_door(2.5, 2.0, 'bull'), 256, 76, box=(-20, -26, 20, 0), kind="bigdoor", data={"id": "z2_bigdoor"})
    G.stairs_up(g, 256, 52, 40, 20)
    for (x, y) in ((120, 330), (392, 330)):
        pillar(m, x, y)
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
    """The summit: an open platform at the top of the ziggurat, the sanctuary wall behind the
    sleeping god, low parapets on three sides and beyond them a long drop into the night, the
    city a scatter of embers far below."""
    TW, TH = 30, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("zig_3", TW, TH, R['brick'][2], music="summit")
    g = m.ground
    E, wall_h, P = 40, 64, 12          # drop beyond the edge, sanctuary wall height, parapet thickness
    G.night_drop(g, 0, 0, W, H, seed=111)
    # the platform
    A.marble(g, E, wall_h, W - 2 * E, H - wall_h - 24, 24, seed=102)
    G.glazed_wall(g, E, 0, W - 2 * E, wall_h, seed=101)
    for x in range(E, W - E):
        g.px(x, wall_h, OUTLINE)
    G.floor_shadow(g, E + P, wall_h + 1, W - 2 * E - 2 * P, 6, 'y+')
    G.floor_shadow(g, E + P, wall_h + 1, 4, H - wall_h - 24 - P - 1, 'x+')
    G.floor_inlays(g, E + P, wall_h + 2, W - 2 * E - 2 * P, H - wall_h - 24 - P - 2, inset=8, band=7)
    G.carpet(g, W // 2 - 12, 262, 24, H - 262 - 24)
    A.sigil(g, W // 2, 230, 26)
    # parapets, crenellated against the sky
    G.wall_top(g, E, wall_h, P, H - wall_h - 24, inner='right', seed=103, merlons=True)
    G.wall_top(g, W - E - P, wall_h, P, H - wall_h - 24, inner='left', seed=104, merlons=True)
    G.wall_top(g, E + P, H - 24 - P, W // 2 - 20 - E - P, P, inner='up', seed=105, merlons=True)
    G.wall_top(g, W // 2 + 20, H - 24 - P, W // 2 - 20 - E - P, P, inner='up', seed=106, merlons=True)
    # the stair down through the gap, falling away into the dark
    lime = R['lime']; gd = R['gold']
    for k in range(H - 24 - P, H):
        t = (k - (H - 24 - P)) / (24 + P)
        c = lime[3] if (k - (H - 24 - P)) % 4 == 0 else lime[2] if t < 0.45 else lime[1] if t < 0.8 else (14, 10, 24, 255)
        g.hline(W // 2 - 18, W // 2 + 17, k, c)
    for sx in (W // 2 - 20, W // 2 + 18):
        g.vline(sx, H - 24 - P, H - 1, gd[3]); g.vline(sx + 1, H - 24 - P, H - 1, gd[4] if sx < W // 2 else gd[2])
    # nothing walks off the summit
    m.solid(0, 0, W, wall_h - 4)
    m.solid(0, 0, E + P - 2, H); m.solid(W - E - P + 2, 0, W, H)
    m.solid(0, H - 24 - P + 2, W // 2 - 20, H); m.solid(W // 2 + 20, H - 24 - P + 2, W, H)
    m.marker("god", W // 2 - 10, 126)
    m.marker("altar", W // 2 + 64, 132)
    m.marker("boss", W // 2, 212)
    for (x, y) in ((118, 190), (W - 118, 190), (118, 300), (W - 118, 300)):
        pillar(m, x, y, kind="pillar")
    torches(m, ((72, 150), (W - 72, 150), (72, 318), (W - 72, 318)))
    m.light(W // 2, 120, 7.0, (0.62, 0.70, 1.0), 0.45, flicker=False)
    m.spawn("south", W // 2, H - 26, "up")
    m.exit(W // 2 - 20, H - 8, W // 2 + 20, H, "zig_2", "top")
    m.save()


if __name__ == "__main__":
    which = sys.argv[1:] or ["temple_yard", "zig_1", "zig_2", "zig_3"]
    for w in which:
        globals()[w]()
