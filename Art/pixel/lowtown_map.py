"""Lower Ashkel: where the road from the Temple Gate comes down into the streets. The bakery
(Hesha), the potter's yard (Kesh), the oracle's house (Ummi), a night market, and the goat,
which is somehow on a roof. Exits: north to the gate, west to the olive terraces, east to the
sea cliffs."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R, OUTLINE
import ashkel_art as A
import region_art as G
from mapkit import MapBuilder

TW, TH = 60, 36
W, H = TW * 16, TH * 16


def build():
    m = MapBuilder("lowtown", TW, TH, R['grass'][3], music="town")
    g = m.ground
    A.grass(g, 0, 0, W, H, seed=11, dense=0.9)
    main = (448, 0, 64, 312)
    cross = (0, 296, W, 48)
    south = (452, 344, 56, 232)
    G.path(g, [(480, 330), (482, 420), (476, 500), (480, 580)], 40, seed=14)
    G.path(g, [(470, 352), (380, 372), (320, 410), (300, 470)], 22, seed=15)      # lane to the bakery
    G.path(g, [(500, 352), (600, 372), (660, 420), (700, 470)], 22, seed=16)      # lane to the potter
    G.path(g, [(860, 340), (880, 420), (900, 470)], 18, seed=17)
    G.path(g, [(120, 340), (100, 420), (90, 470)], 18, seed=18)
    A.pavers(g, *main, seed=12)
    A.pavers(g, *cross, seed=13)
    inside = lambda x, y: (main[0] <= x < main[0] + main[2] and y < main[1] + main[3]) or (cross[1] <= y < cross[1] + cross[3])
    A.edge_line(g, inside, 0, 0, W, H, R['grass'][1])
    G.laundry(g, 288, 330, 92, seed=1)
    G.laundry(g, 636, 680, 96, seed=2)

    def house(seed, w, ladder=False, door=True):
        return lambda cv, ax, ay, fi: A.mud_house(cv, ax - w // 2, ay - 60, w, 26, 34, seed=seed, ladder=ladder, door=door)
    houses = [(370, 140, 84, 21, True), (250, 152, 72, 22, False), (370, 268, 84, 23, False), (150, 268, 80, 24, True),
              (590, 140, 80, 25, False), (720, 152, 76, 26, True), (860, 140, 72, 27, False),
              (250, 470, 96, 28, False), (700, 470, 88, 29, True), (880, 470, 70, 30, False), (90, 470, 70, 31, True)]
    for (x, y, w, sd, lad) in houses:
        m.prop(f"lt_house_{sd}", house(sd, w, lad), x, y, box=(-w // 2, -58, w // 2, 0), size=(w + 8, 70), pad=4)
        A.soft_shadow(g, x + w // 2 + 3, y - 18, 6, 18)
        m.light(x - w // 2 + 9, y - 22, 2.4, (1.0, 0.74, 0.4), 0.55, tag="window")

    # the bakery: an oven still glowing after forty nights, and sacks of flour
    m.prop("oven", lambda cv, ax, ay, fi: G.oven(cv, ax, ay, fi), 318, 512, box=(-12, -6, 12, 0), size=(40, 36), pad=4, frames=3)
    m.light(318, 504, 3.6, (1.0, 0.6, 0.3), 0.9)
    m.prop("lt_sacks", lambda cv, ax, ay, fi: A.sacks(cv, ax, ay, 40), 196, 508, box=(-8, -5, 8, 0), size=(28, 22), pad=4)
    # the potter's yard: kiln, wheel, rows of drying jars
    m.prop("kiln", lambda cv, ax, ay, fi: G.kiln(cv, ax, ay, fi), 780, 520, box=(-11, -8, 11, 0), size=(36, 34), pad=4, frames=2)
    m.light(780, 508, 3.0, (1.0, 0.55, 0.28), 0.8)
    m.prop("wheel", lambda cv, ax, ay, fi: G.potters_wheel(cv, ax, ay), 640, 516, box=(-6, -3, 6, 0), size=(20, 18), pad=4)
    def pot(big, seed):
        return lambda cv, ax, ay, fi: A.pot(cv, ax, ay, seed=seed, big=big)
    for i, x in enumerate(range(600, 690, 13)):
        m.prop("pot_big" if i % 2 else "pot", pot(i % 2 == 1, x), x, 552, box=(-4, -4, 4, 0), size=(24, 30), pad=6, kind="pot")
    # the oracle's house: a purple awning, incense smoke, her chair
    m.prop("oracle_awning", lambda cv, ax, ay, fi: G.awning(cv, ax - 36, ay - 10, 72, R['lapis'][3], R['red'][2]), 860, 168, size=(80, 24), pad=2)
    m.light(860, 170, 3.0, (0.75, 0.6, 1.0), 0.6)
    # market on the cross street
    def stall(seed):
        return lambda cv, ax, ay, fi: A.stall(cv, ax - 22, ay - 34, 44, seed=seed)
    for (x, y, sd) in ((170, 292, 4), (300, 292, 5), (700, 292, 6), (820, 292, 7)):
        m.prop(f"stall_{sd}", stall(sd), x, y, box=(-22, -8, 22, 0), size=(60, 50), pad=4)
        A.soft_shadow(g, x + 6, y, 24, 4)
    m.prop("lt_amph", lambda cv, ax, ay, fi: A.amphorae(cv, ax, ay, 41), 240, 296, box=(-8, -4, 8, 0), size=(32, 28), pad=4)
    m.prop("well", lambda cv, ax, ay, fi: A.well(cv, ax, ay - 9), 560, 250, box=(-13, -12, 13, 0), size=(40, 44), pad=4, kind="well")
    # trees, bushes
    def olive(seed):
        return lambda cv, ax, ay, fi: A.olive_tree(cv, ax, ay, seed=seed)
    for (x, y, sd) in ((60, 140, 31), (40, 400, 32), (930, 380, 33), (520, 420, 34), (420, 560, 35)):
        m.prop(f"olive_{sd}", olive(sd), x, y, box=(-4, -4, 4, 0), size=(64, 64), pad=6)
        A.soft_shadow(g, x + 7, y + 1, 16, 5)
    def cyp(seed, h):
        return lambda cv, ax, ay, fi: A.cypress(cv, ax, ay, h, seed=seed)
    for (x, y, h, sd) in ((430, 60, 44, 31), (530, 60, 44, 32), (930, 230, 46, 33)):
        m.prop(f"cypress_{sd}", cyp(sd, h), x, y, box=(-3, -3, 3, 0), size=(24, 64), pad=4)
    def bush(seed, fl):
        return lambda cv, ax, ay, fi: A.bush(cv, ax, ay - 6, seed=seed, flowers=fl)
    k = 0
    for (x, y) in ((120, 200), (136, 208), (430, 190), (530, 200), (546, 190), (800, 210), (816, 220), (40, 300), (920, 560),
                   (470, 400), (490, 410), (130, 560), (146, 566), (560, 470), (576, 478)):
        m.prop(f"bush_{k % 4}", bush(k % 4, k % 3 == 0), x, y, box=(-6, -5, 6, 0), size=(24, 24), pad=4, kind="bush")
        k += 1
    # palms, carts, crates
    for (x, y, sd) in ((96, 236, 1), (604, 236, 2), (900, 330, 3), (420, 440, 4), (560, 560, 5), (20, 520, 6)):
        m.prop(f"palm_{sd}", lambda cv, ax, ay, fi, sd=sd: G.palm(cv, ax, ay, 40 + sd % 3 * 4, seed=sd), x, y, box=(-2, -2, 2, 0), size=(48, 64), pad=4)
        A.soft_shadow(g, x + 8, y, 12, 4)
    m.prop("cart", lambda cv, ax, ay, fi: G.cart(cv, ax, ay, 3), 560, 300, box=(-14, -6, 14, 0), size=(48, 30), pad=4)
    m.prop("crates", lambda cv, ax, ay, fi: G.crates(cv, ax, ay), 262, 300, box=(-11, -6, 11, 0), size=(30, 26), pad=4)
    m.prop("crates_b", lambda cv, ax, ay, fi: G.crates(cv, ax, ay), 772, 306, box=(-11, -6, 11, 0), size=(30, 26), pad=4)
    # a sign at the crossing
    m.prop("sign_lt", lambda cv, ax, ay, fi: A.sign(cv, ax, ay), 528, 290, box=(-2, -2, 2, 0), size=(24, 24), pad=2, kind="sign", data={"text": "sign_lowtown"})
    # a chest at the end of the alley behind the potter
    m.prop("chest", lambda cv, ax, ay, fi: cv.blit(Canvas.load('/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'), ax - 8, ay - 15),
           936, 520, box=(-7, -6, 7, 0), size=(24, 24), pad=4, kind="chest", data={"id": "lt_alley", "text": "shekels:20"})

    # people
    m.marker("npc", 300, 518, who="hesha")
    m.marker("npc", 650, 524, who="kesh")
    m.marker("npc", 858, 186, who="ummi")
    m.marker("npc", 370, 100, who="goat_roof")
    m.marker("npc", 522, 330, who="taxman")
    m.marker("npc", 178, 512, who="flourboy")
    m.marker("npc", 700, 170, who="lover")
    m.marker("npc", 604, 262, who="dog")
    # the dream has its own residents here
    for (x, y, uid) in ((200, 420, "lt_m1"), (720, 400, "lt_m2"), (480, 520, "lt_m3")):
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


if __name__ == "__main__":
    build()
