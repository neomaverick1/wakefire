"""Lower Ashkel: where the road from the Temple Gate comes down into the streets. Rows of
mud-brick houses under flat roofs, a paved main street crossing a market street, the bakery
(Hesha) and the potter's yard (Kesh) to the south, the oracle's house (Ummi) to the north-east,
a well court with a dog in it, and the goat, which is somehow on a roof.
Exits: north to the gate, west to the olive terraces, east to the sea cliffs."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas
import town
import kit
from mapkit import MapBuilder

TW, TH = 60, 36
W, H = TW * 16, TH * 16

# (key, centre x, front y, width, depth, height, extras) in tiles for the last three
ROW1, ROW2, ROW3 = 132, 276, 470
HOUSES = [
    # the north row, backs to the old inner wall
    ('lt_a1', 72, ROW1, 6.0, 3.0, 2.5, dict(seed=21, plaster=2, door_x=0.6, stair='l')),
    ('lt_a2', 192, ROW1, 7.0, 3.0, 2.75, dict(seed=22, plaster=0, upper=(-3.5, 0.5, 1.75, 2.0), door_x=1.9)),
    ('lt_a3', 350, ROW1, 9.0, 3.0, 2.75, dict(seed=23, plaster=3, door_x=2.2)),
    ('lt_b1', 588, ROW1, 7.0, 3.0, 2.75, dict(seed=25, plaster=1, door_x=-1.6, upper=(0.0, 3.5, 1.75, 1.9))),
    ('lt_b2', 720, ROW1, 7.5, 3.0, 2.5, dict(seed=26, plaster=4, door_x=1.4)),
    ('lt_b3', 860, ROW1, 8.0, 3.0, 2.75, dict(seed=27, plaster=2, door_x=-2.4, skip=[(-1.4, 1.6)], upper=(-4.0, -0.5, 1.5, 1.75))),
    # the row along the market street
    ('lt_c1', 80, ROW2, 7.5, 3.0, 2.75, dict(seed=31, plaster=1, door_x=-2.4, skip=[(0.0, 3.0)])),
    ('lt_c2', 232, ROW2, 7.5, 3.0, 2.5, dict(seed=32, plaster=3, door_x=2.3, skip=[(-1.4, 1.5)], upper=(-3.75, -0.5, 1.5, 1.9))),
    ('lt_c3', 368, ROW2, 8.5, 3.0, 2.75, dict(seed=33, plaster=0, door_x=-1.5, stair='r')),
    ('lt_d1', 728, ROW2, 8.0, 3.0, 2.75, dict(seed=34, plaster=2, door_x=2.6, skip=[(-2.0, 1.2)])),
    ('lt_d2', 884, ROW2, 7.5, 3.0, 2.5, dict(seed=35, plaster=0, door_x=-2.4, skip=[(-1.2, 2.0)], upper=(0.25, 3.75, 1.5, 2.0))),
    # south of the street: the bakery, the potter and their neighbours
    ('lt_e1', 96, ROW3, 7.0, 3.0, 2.5, dict(seed=41, plaster=4, door_x=1.5)),
    ('lt_e2', 254, ROW3, 8.0, 3.0, 2.75, dict(seed=42, plaster=1, door_x=1.2, upper=(-4.0, -0.75, 1.75, 1.9))),
    ('lt_e3', 654, ROW3, 8.0, 3.0, 2.75, dict(seed=43, plaster=2, door_x=-0.8, stair='r')),
    ('lt_e4', 888, ROW3, 6.5, 3.0, 2.5, dict(seed=44, plaster=3, door_x=-1.2)),
]


def build():
    m = MapBuilder("lowtown", TW, TH, (60, 44, 40, 255), music="town")
    T = m.lay(seed=11)
    # ---------------------------------------------------------------- the ground
    T.earth(T.all(), seed=1, grain='h', base=3.4)
    # the yards south of the houses are drier and paler
    yards = T.ragged(T.rect(0, 472, W, 104), 5, 14, seed=2)
    T.earth(yards, seed=3, base=3.9, ramp='dust', pebbles=0.006)
    # grass creeps in along the map's edges and behind the last houses
    green = T.ragged(T.rect(0, 540, 180, 40) | T.rect(770, 548, 190, 30) | T.rect(0, 348, 36, 30) | T.rect(930, 348, 30, 30) |
                     T.disc(420, 556, 54, 30) | T.disc(560, 566, 60, 20) | T.disc(36, 420, 30, 60) | T.disc(940, 420, 26, 50), 5, 10, seed=4)
    T.grass(green, seed=5, flowers=0.008)
    dry = T.ragged(T.disc(330, 420, 70, 26) | T.disc(560, 400, 44, 22) | T.disc(780, 420, 50, 24) | T.disc(160, 356, 60, 10) | T.disc(820, 362, 70, 10), 4, 8, seed=6)
    T.grass(dry & ~green, seed=7, ramp='dry', base=3.0, tufts=0.05)
    # the paved streets: stones laid whole, so their edges wander
    main = T.rect(444, 0, 72, 300)
    cross = T.rect(0, 292, W, 56)
    T.slabs(main | cross, seed=12, moss=0.10)
    # a drain down the middle of the main street, a darker course of stone
    T.slabs(T.rect(476, 0, 8, 292), seed=13, rows=(8, 9), wmin=7, wmax=8, ramp='cobble', base=3.2, jitter=0.6, crack=0, whole=False)
    # the paths south: trodden earth, paler than the street dirt, with flagstones dropped where it gets muddy
    lanes = T.stroke([(480, 344), (482, 420), (476, 500), (480, 580)], 38) | T.stroke([(470, 352), (380, 372), (330, 420), (310, 490)], 20) | \
            T.stroke([(500, 352), (560, 372), (590, 440), (600, 500)], 20) | T.stroke([(730, 348), (760, 400), (770, 480)], 18) | T.stroke([(170, 348), (166, 420), (170, 490)], 18)
    T.earth(T.ragged(lanes, 3, 7, seed=8) & ~(main | cross), seed=9, base=4.3, ramp='dust', pebbles=0.008)
    T.slabs(T.disc(482, 372, 20, 14) | T.disc(478, 452, 16, 12), seed=15, rows=(9, 10), wmin=9, wmax=15, base=3.5)
    # the lane between the two north rows: a few worn flagstones where feet turn in at the doors
    T.slabs(T.ragged(T.disc(200, 152, 40, 9) | T.disc(360, 150, 30, 8) | T.disc(600, 152, 34, 9) | T.disc(868, 156, 46, 12), 2, 6, seed=10), seed=16, rows=(9, 10), wmin=9, wmax=15, base=3.4)
    # the well court is paved
    T.slabs(T.rect(522, 190, 136, 104), seed=17, rows=(10, 12, 11), base=3.9)
    # garden plots behind the south row
    for (x, y, w, h) in ((332, 384, 96, 40), (536, 384, 40, 56), (728, 388, 96, 44)):
        bed = T.rect(x, y, w, h)
        T.soil(bed, seed=x)
        T.grass(bed & ((T.yy % 5) == 2) & (((T.xx + T.yy // 5 * 3) % 7) < 4), seed=x + 1, base=3.6, tufts=0.0, fringe=0)
    # where each house stands: the dark where wall meets street
    for (key, cx, y, w, d, h, kw) in HOUSES:
        T.contact(cx - w * 8, y - d * 16, cx + w * 8, y, reach=5, strength=1.5)
    m.bake()

    # ---------------------------------------------------------------- the houses
    for (key, cx, y, w, d, h, kw) in HOUSES:
        m.model(key, town.house(w, d, h, **kw), cx, y, box=(-w * 8, -(d + h) * 16, w * 8, 0))
        if kw.get('stair') == 'r': m.solid(cx + w * 8 - 37, y, cx + w * 8, y + 9)
        if kw.get('stair') == 'l': m.solid(cx - w * 8, y, cx - w * 8 + 37, y + 9)
    # the old inner wall closes the north side, either side of the road up to the gate
    m.model("lt_wall_w", town.city_wall(27.0, h=2.2, d=1.0, buttress=6.0), 0, 40, box=(0, -36, 432, 0))
    m.model("lt_wall_e", town.city_wall(27.0, h=2.2, d=1.0, buttress=6.0, seed=2), 528, 40, box=(0, -36, 432, 0))
    m.solid(0, 0, 444, 40); m.solid(516, 0, W, 40)

    # the oracle's house: a purple awning, her chair under it
    m.model("oracle_awning", town.awning(3.0, 1.1, colors=('fig', 'blue')), 868, ROW1 + 18, box=None)
    m.light(868, ROW1 + 4, 3.0, (0.75, 0.6, 1.0), 0.6, h=1.2)
    # the bakery yard: an oven still glowing after forty nights, and sacks of flour
    m.prop("oven", lambda cv, ax, ay, fi: G.oven(cv, ax, ay, fi), 318, 512, box=(-12, -6, 12, 0), size=(40, 36), pad=4, frames=3)
    m.light(318, 504, 3.6, (1.0, 0.6, 0.3), 0.9, h=0.6)
    m.model("lt_sacks", town.sacks(40), 196, 508, kind=None)
    m.model("lt_sacks_b", town.sacks(41), 226, 494)
    # the potter's yard: kiln, wheel, rows of drying jars
    m.prop("kiln", lambda cv, ax, ay, fi: G.kiln(cv, ax, ay, fi), 780, 520, box=(-11, -8, 11, 0), size=(36, 34), pad=4, frames=2)
    m.light(780, 508, 3.0, (1.0, 0.55, 0.28), 0.8, h=0.6)
    m.prop("wheel", lambda cv, ax, ay, fi: G.potters_wheel(cv, ax, ay), 640, 516, box=(-6, -3, 6, 0), size=(20, 18), pad=4)
    for i, x in enumerate(range(600, 690, 13)):
        kit.pot(m, x, 552, i % 2 == 1)
    for (x, y, big) in ((116, 136, True), (240, 137, False), (668, 136, False), (790, 137, True), (300, 280, True), (60, 474, False), (910, 474, True), (700, 474, False)):
        kit.pot(m, x, y, big)

    # the market on the cross street
    for (x, sd) in ((104, 4), (236, 5), (716, 6), (892, 7)):
        m.stall(f"stall_{sd}", sd, x, 302, town)
    m.model("lt_amph", town.amphorae(41), 134, 296)
    m.model("crates", town.crates(0), 304, 296)
    m.model("crates_b", town.crates(1), 930, 296)
    m.model("cart", town.cart(3), 610, 296, box=(-16, -16, 30, 0))
    m.model("well", town.well(), 560, 240, box=(-14, -26, 14, 0), kind="well")
    kit.sign(m, 528, 290, "sign_lt", "sign_lowtown")
    for (x, y) in ((438, 290), (444, 352), (166, 352), (812, 352), (438, 170), (522, 170)):
        kit.torch(m, x, y)

    # trees and bushes
    for (x, y, sd) in ((420, 560, 3), (40, 536, 0), (936, 420, 1), (372, 430, 2)):
        kit.olive(m, x, y, sd)
    for (x, y, sd) in ((434, 62, 0), (526, 62, 1)):
        kit.cypress(m, x, y, sd)
    for (x, y, sd) in ((536, 200, 1), (646, 204, 0), (560, 440, 3), (566, 566, 4), (20, 420, 5), (800, 470, 2)):
        kit.palm(m, x, y, sd)
    for k, (x, y) in enumerate(((40, 556), (60, 562), (130, 560), (146, 566), (920, 562), (840, 566), (470, 566), (350, 440), (400, 446), (772, 440), (540, 560))):
        kit.bush(m, x, y, k)
    for (x, y, sd) in ((196, 548, 0), (742, 560, 1), (16, 356, 2)):
        kit.rock(m, x, y, sd)

    # a chest at the end of the alley behind the potter
    m.prop("chest", lambda cv, ax, ay, fi: cv.blit(Canvas.load('/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'), ax - 8, ay - 15),
           936, 520, box=(-7, -6, 7, 0), size=(24, 24), pad=4, kind="chest", data={"id": "lt_alley", "text": "shekels:20"})

    # people
    m.marker("npc", 300, 518, who="hesha")
    m.marker("npc", 650, 524, who="kesh")
    m.marker("npc", 858, 186, who="ummi")
    m.marker("npc", 350, 72, who="goat_roof")
    m.marker("npc", 522, 330, who="taxman")
    m.marker("npc", 178, 512, who="flourboy")
    m.marker("npc", 700, 170, who="lover")
    m.marker("npc", 604, 262, who="dog")
    # the dream has its own residents here
    for (x, y, uid) in ((150, 524, "lt_m1"), (760, 544, "lt_m2"), (480, 500, "lt_m3")):
        m.enemy("moth", x, y, uid)
    # ways out
    m.spawn("north", 480, 26, "down")
    m.spawn("west", 22, 320, "right")
    m.spawn("east", W - 22, 320, "left")
    m.spawn("start", 480, 26, "down")
    m.exit(448, 0, 512, 8, "ashkel", "south")
    m.exit(0, 296, 8, 344, "terraces", "east")
    m.exit(W - 8, 296, W, 344, "cliffs", "west")
    m.solid(0, 0, 4, 296); m.solid(0, 344, 4, H); m.solid(W - 4, 0, W, 296); m.solid(W - 4, 344, W, H)
    m.solid(0, 0, 448, 4); m.solid(512, 0, W, 4); m.solid(0, H - 4, W, H)
    m.save()


import region_art as G

if __name__ == "__main__":
    build()
