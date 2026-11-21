"""Ashkel, first district: the square before the Temple Gate. The precinct wall and its glazed
gate close the north side; the processional way runs up to it between rows of houses on the
west and the night market on the east. Builds the ground, the props, collision, lights and
markers for Unity."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas
import ashkel_art as A
import town
import kit
from forge import Model, M, m_ashlar, m_mottle
from mapkit import MapBuilder

TW, TH = 60, 30
W, H = TW * 16, TH * 16

HOUSES = [
    # west of the square: two rows with a lane between
    ('ak_w1a', 72, 176, 7.0, 3.0, 2.75, dict(seed=4, plaster=0, door_x=-1.4, upper=(0.0, 3.5, 1.75, 1.9))),
    ('ak_w1b', 188, 176, 7.5, 3.0, 2.5, dict(seed=7, plaster=1, door_x=1.6)),
    ('ak_w1c', 308, 176, 7.5, 3.0, 2.75, dict(seed=9, plaster=2, door_x=-1.8, stair='r')),
    ('ak_w2a', 52, 340, 6.5, 3.0, 2.5, dict(seed=13, plaster=3, door_x=1.0)),
    ('ak_w2b', 168, 340, 8.0, 3.0, 2.75, dict(seed=14, plaster=4, door_x=-2.0, upper=(0.5, 4.0, 1.75, 2.0))),
    ('ak_w2c', 306, 340, 7.25, 3.0, 2.5, dict(seed=15, plaster=0, door_x=1.5)),
    # east: one house against the wall, a row along the south of the market
    ('ak_e1a', 884, 176, 8.0, 3.0, 2.75, dict(seed=16, plaster=1, door_x=-2.2, upper=(0.0, 4.0, 1.75, 2.0))),
    ('ak_e2a', 668, 424, 8.0, 3.0, 2.75, dict(seed=17, plaster=2, door_x=1.8, upper=(-4.0, -0.5, 1.75, 1.9))),
    ('ak_e2b', 804, 424, 8.5, 3.0, 2.5, dict(seed=18, plaster=0, door_x=-1.0)),
    ('ak_e2c', 920, 424, 5.5, 3.0, 2.75, dict(seed=19, plaster=3, door_x=-0.6)),
]


def terrace():
    """The low platform before the gate, with three steps down into the square."""
    m = Model()
    face = M('sandstone', 4.2, m_ashlar(16, 8)); top = M('sandstone', 4.5, m_ashlar(16, 12, 5))
    d, h = 34 / 16.0, 0.5
    m.part(); m.box(0, 0, 0, 4.75, d, h, face, top=top)
    m.part(); m.box(7.75, 0, 0, 12.5, d, h, face, top=top)
    for i in range(3):
        m.part(); m.box(4.75, 0.19 * i, 0, 7.75, d, h * (i + 1) / 3, face, top=top)
    return m


def build():
    m = MapBuilder("ashkel", TW, TH, (60, 44, 40, 255), music="town")
    T = m.lay(seed=3)
    # ---------------------------------------------------------------- the ground
    T.earth(T.all(), seed=1, grain='h', base=3.4)
    market = T.ragged(T.rect(592, 60, 220, 272), 5, 12, seed=2)
    T.earth(market, seed=3, base=3.9, ramp='dust', pebbles=0.006)
    court = T.ragged(T.rect(0, 344, 440, 136), 5, 12, seed=4)
    T.earth(court, seed=5, base=3.8, ramp='dust', pebbles=0.006)
    green = T.ragged(T.rect(0, 440, 300, 40) | T.disc(40, 420, 50, 40) | T.disc(340, 440, 44, 30) | T.rect(560, 452, 400, 28) | T.disc(930, 290, 34, 40) | T.disc(596, 452, 30, 20), 5, 10, seed=6)
    T.grass(green, seed=7, flowers=0.008)
    T.grass(T.ragged(T.disc(700, 300, 60, 16) | T.disc(160, 400, 60, 14) | T.disc(780, 90, 40, 12), 4, 8, seed=8) & ~green, seed=9, ramp='dry', base=3.0, tufts=0.05)
    # the square: cut stone, with flagstones running out into the market and the lanes
    square = T.rect(380, 92, 200, 216)
    T.slabs(square | T.rect(376, 58, 208, 40), seed=12, moss=0.06)
    T.slabs(T.ragged(T.disc(640, 290, 46, 20) | T.disc(700, 150, 70, 26) | T.disc(720, 240, 50, 16) | T.disc(200, 196, 150, 12) | T.disc(160, 350, 120, 9), 3, 7, seed=10),
            seed=14, rows=(9, 10), wmin=9, wmax=15, base=4.0)
    # the processional way: pale slabs between two bands of glazed blue brick studded with gold
    way = T.rect(448, 92, 64, 388)
    T.slabs(way, seed=41, rows=(12,), wmin=16, wmax=16, ramp='pale', base=4.3, jitter=0.8, crack=0.05, whole=False, wear=0.4)
    bands = T.rect(444, 92, 4, 388) | T.rect(512, 92, 4, 388)
    T.bricks(bands, seed=42, bw=8, bh=4, ramp='lapis', base=3.3, jitter=0.7)
    stud = bands & ((T.yy % 16) >= 7) & ((T.yy % 16) <= 8) & (((T.xx - 444) % 68) >= 1) & (((T.xx - 444) % 68) <= 2)
    T.put(stud, 'gold', np.full((H, W), 4.0), 1.4)
    # a garden behind the last house, in rows
    for (x, y, w, h) in ((20, 372, 84, 40), (236, 380, 60, 36)):
        bed = T.rect(x, y, w, h)
        T.soil(bed, seed=x)
        T.grass(bed & ((T.yy % 5) == 2) & (((T.xx + T.yy // 5 * 3) % 7) < 4), seed=x + 1, base=3.6, tufts=0.0, fringe=0)
    for (key, cx, y, w, d, h, kw) in HOUSES:
        T.contact(cx - w * 8, y - d * 16, cx + w * 8, y, reach=5, strength=1.5)
    T.contact(0, 30, 392, 58, reach=6, strength=1.6); T.contact(568, 30, W, 58, reach=6, strength=1.6)
    g = m.bake()
    A.sigil(g, 480, 186, 22)
    m.set_into_ground(terrace(), 380, 92)
    m.solid(380, 84, 456, 92); m.solid(504, 84, 580, 92)
    m.solid(374, 58, 380, 92); m.solid(580, 58, 586, 92)

    # ---------------------------------------------------------------- the wall and the gate
    m.model("wall_temple", town.city_wall(60.0, h=2.2, d=1.2, gate_at=30.0, gate_w=2.9), 0, 58, box=None)
    m.solid(0, 0, 457, 58); m.solid(503, 0, W, 58); m.solid(416, 58, 457, 66); m.solid(503, 58, 544, 66)
    m.model("banner", town.banner, 305, 59, box=None, frames=4, kind="banner")
    for bx in (184, 655, 776):
        m.model("banner", town.banner, bx, 59, box=None, frames=4, kind="banner")
    m.model("gate_temple", town.gate_doors(False), 480, 59, box=(-23, -14, 23, 0), kind="gate", data={"id": "temple_gate"})
    m.model("gate_temple_open", town.gate_doors(True), -100, -100, box=None, lights=False)
    for x in (364, 596):
        m.model("wall_torch", town.wall_torch, x, 67, box=None, frames=4, kind="torch")
        m.light(x, 67 - 49, 4.5, (1.0, 0.72, 0.38), 0.9, h=2.95)

    # ---------------------------------------------------------------- houses
    for (key, cx, y, w, d, h, kw) in HOUSES:
        m.model(key, town.house(w, d, h, **kw), cx, y, box=(-w * 8, -(d + h) * 16, w * 8, 0))
        if kw.get('stair') == 'r': m.solid(cx + w * 8 - 37, y, cx + w * 8, y + 9)
        if kw.get('stair') == 'l': m.solid(cx - w * 8, y, cx - w * 8 + 37, y + 9)
    for (x, y, big) in ((122, 180, True), (252, 180, False), (226, 344, True), (112, 344, False), (600, 428, True), (742, 428, False), (930, 180, True), (30, 180, False)):
        kit.pot(m, x, y, big)

    # ---------------------------------------------------------------- trees and hedges
    for (x, y, sd) in ((340, 436, 4), (40, 440, 5), (150, 452, 6), (590, 456, 7), (926, 300, 0)):
        kit.olive(m, x, y, sd)
    for (x, y, sd) in ((600, 150, 2), (806, 270, 3), (372, 472, 4)):
        kit.palm(m, x, y, sd)
    kit.cypress(m, 810, 110, 2)
    k = 0
    for x in range(392, 440, 16):
        for y in (330, 350):
            kit.bush(m, x, y, k); k += 1
    for x in range(536, 584, 16):
        for y in (330, 350):
            kit.bush(m, x, y, k); k += 1
    for (x, y) in ((20, 466), (70, 470), (300, 466), (716, 470), (760, 466), (930, 470), (912, 466), (700, 306)):
        kit.bush(m, x, y, k); k += 1
    for (x, y, sd) in ((398, 134, 1), (562, 134, 2), (398, 286, 3), (562, 286, 4)):
        m.model(f"planter_{sd}", town.planter(sd), x, y, box=(-14, -10, 14, 0))

    # ---------------------------------------------------------------- the night market, a well
    for (x, y, sd) in ((680, 124, 1), (760, 124, 2), (720, 234, 3)):
        m.stall(f"stall_{sd}", sd, x, y, town)
    m.model("well", town.well(), 640, 284, box=(-14, -26, 14, 0), kind="well")
    kit.sign(m, 440, 300, "sign_gate", "sign_temple")
    m.model("amphorae", town.amphorae(31), 628, 128)
    m.model("sacks", town.sacks(32), 764, 244)
    m.model("amphorae_b", town.amphorae(33), 618, 250)
    m.model("crates", town.crates(0), 808, 130)
    m.model("cart", town.cart(3), 770, 316, box=(-16, -16, 30, 0))

    # braziers in the square, dark until the Wakefire touches them
    for i, (x, y) in enumerate(((412, 176), (548, 176), (480, 250))):
        kit.brazier(m, x, y, False, f"square_{i}")
    kit.brazier_frames(m)

    # guardians of the gate: winged bulls with crowned men's heads, facing each other across the steps
    kit.lamassu(m, 418, 88, west=False)
    kit.lamassu(m, 542, 88, west=True)
    # standing torches at the foot of the steps, and where the lanes meet the square
    for (x, y) in ((442, 108), (518, 108), (600, 336), (366, 250), (628, 64)):
        kit.torch(m, x, y)

    # ---------------------------------------------------------------- where the district stops
    # west: the alley behind the first house is walled off, and the street ends at the dyers' wall
    kit.wall_ew(m, 0, 16, 176, seed=5, plaster=0)
    kit.wall_ns(m, 0, 174, 250, seed=6, plaster=2)
    kit.say(m, "cart_wreck", town.cart_wreck(2), 50, 238, (-26, -12, 28, 0),
            "A handcart, on its side where its owner lay down.^Past the wall is the Dyers' Quarter, snoring in three colours.")
    m.model("amphorae_w", town.amphorae(35), 24, 196)
    kit.cypress_row(m, 8, 356, 462, seed=1)
    # east: the market backs onto the coppersmiths' wall
    kit.wall_ew(m, 948, W, 176, seed=7, plaster=1)
    kit.wall_ns(m, W - 10, 174, 334, seed=8, plaster=3)
    kit.say(m, "crates_e", town.crates(1), 934, 300, (-12, -10, 12, 0),
            "Crates of copper pots, stacked against the Coppersmiths' wall.^Not one of them has been hammered in forty nights. The quiet is unnatural.")
    m.model("amphorae_e", town.amphorae(36), 936, 222)
    kit.cypress_row(m, W - 8, 438, 462, seed=2)
    # south: the terrace's own wall, either side of the way down to the lower town
    m.model("south_wall_w", town.drystone(446 / 16.0, h=0.7, seed=3), 0, H - 2, box=None)
    m.model("south_wall_e", town.drystone((W - 514) / 16.0, h=0.7, seed=4), 514, H - 2, box=None)
    m.solid(0, H - 13, 446, H); m.solid(514, H - 13, W, H)

    m.marker("spawn", 480, 220)
    m.spawn("south", 480, 456, "up")
    m.spawn("gate", 480, 72, "down")
    m.exit(448, 472, 512, 480, "lowtown", "north")
    m.exit(462, 30, 498, 46, "temple_yard", "south", need="gate_open")
    m.marker("npc", 466, 84, who="captain")
    m.marker("npc", 398, 222, who="goat")
    m.marker("npc", 552, 226, who="dreamer")
    m.marker("npc", 604, 300, who="walker")
    m.marker("npc", 680, 110, who="merchant")
    m.solid(0, 0, 4, H); m.solid(W - 4, 0, W, H); m.solid(0, H - 4, 448, H); m.solid(512, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
