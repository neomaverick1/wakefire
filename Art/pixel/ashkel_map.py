"""Ashkel, first district: the Temple Gate square with houses to the west and the night market
to the east. Builds the ground, the props, collision, lights and markers for Unity."""
import numpy as np
from px import Canvas, R, OUTLINE
import ashkel_art as A
from mapkit import MapBuilder

TW, TH = 60, 30
W, H = TW * 16, TH * 16


def build():
    m = MapBuilder("ashkel", TW, TH, R['grass'][3], music="town")
    g = m.ground
    A.grass(g, 0, 0, W, H, seed=3, dense=0.8)
    # the square: a terrace before the gate, a kerbed plaza, a processional way of pale slabs
    # running from the road to the steps, and Ninhal's sun-and-moon set into the paving
    sq = (380, 92, 200, 216)
    road = (452, 300, 56, 180)
    walk = (448, 92, 64, 388)
    A.pavers(g, *sq)
    A.pavers(g, *road, seed=5)
    A.kerb(g, *sq)
    A.slabs(g, walk[0], walk[1], walk[2], walk[3], R['lime'], 16, 12, seed=41)
    A.sigil(g, 480, 186, 22)
    A.terrace(g, 392, 58, 176, 26, 8, 456, 48)
    inside = lambda x, y: (sq[0] <= x < sq[0] + sq[2] and sq[1] <= y < sq[1] + sq[3]) or \
                          (road[0] <= x < road[0] + road[2] and road[1] <= y < road[1] + road[3]) or \
                          (392 <= x < 568 and 58 <= y < 92)
    A.edge_line(g, inside, 370, 50, 220, 440, R['grass'][1])
    m.solid(392, 84, 456, 92); m.solid(504, 84, 568, 92)
    m.solid(386, 58, 392, 92); m.solid(568, 58, 574, 92)

    # precinct wall with the Temple Gate (one big prop) and its solid band
    def wall(cv, ax, ay, fi):
        A.city_wall(cv, 0, ay - 46, W, face_h=34, top_h=10)
        A.tower(cv, 436, ay - 58, 38, 60, seed=11)
        A.tower(cv, 486, ay - 58, 38, 60, seed=12)
        A.torch_bracket(cv, 454, ay - 30, 0)
        A.torch_bracket(cv, 505, ay - 30, 2)

    m.prop("wall_temple", wall, 0, 58, size=(W, 120), anchor=(0, 100), pad=0)
    def banner(cv, ax, ay, fi):
        A.banner(cv, ax - 5, ay - 35, 10, 28, frame=fi)
    for bx in (300, 404, 546, 650):
        m.prop("banner", banner, bx + 5, 59, size=(24, 40), pad=2, frames=4, kind="banner")
    m.solid(0, 0, 457, 58)
    m.solid(503, 0, W, 58)
    def gate_doors(open_):
        return lambda cv, ax, ay, fi: A.gate(cv, ax, ay - 40, 46, 40, open_=open_)
    m.prop("gate_temple", gate_doors(False), 480, 59, box=(-23, -14, 23, 0), size=(80, 80), kind="gate", data={"id": "temple_gate"})
    m.prop("gate_temple_open", gate_doors(True), -100, -100, size=(80, 80))
    for (x, y) in ((455, 28), (506, 28)):
        m.light(x, y, 4.5, (1.0, 0.72, 0.38), 0.9)

    # west: houses, a garden, pots
    def house(seed, w, ladder=False, door=True):
        def f(cv, ax, ay, fi):
            A.mud_house(cv, ax - w // 2, ay - 60, w, 26, 34, seed=seed, ladder=ladder, door=door)
        return f
    for (x, y, w, seed, lad) in ((120, 150, 80, 4, True), (250, 140, 72, 7, False), (70, 300, 76, 9, False), (220, 330, 84, 13, True)):
        m.prop(f"house_{seed}", house(seed, w, lad), x, y, box=(-w // 2, -58, w // 2, 0), size=(w + 8, 70), pad=4)
        A.soft_shadow(g, x + w // 2 + 3, y - 18, 6, 18)
        m.light(x - w // 2 + 9, y - 22, 2.4, (1.0, 0.74, 0.4), 0.55, tag="window")
    # garden in front of the first house
    A.flower_bed(g, 90, 176, 48, 16, seed=3)
    A.flower_bed(g, 230, 360, 40, 14, seed=4)

    def pot(big, seed):
        return lambda cv, ax, ay, fi: A.pot(cv, ax, ay, seed=seed, big=big)
    for (x, y, big) in ((168, 152, True), (177, 154, False), (300, 142, False), (110, 302, True), (276, 334, True), (285, 336, False)):
        m.prop("pot_big" if big else "pot", pot(big, x), x, y, box=(-4, -4, 4, 0), size=(24, 30), pad=6, kind="pot")
        A.soft_shadow(g, x + 3, y, 6, 2)

    # trees
    def olive(seed):
        return lambda cv, ax, ay, fi: A.olive_tree(cv, ax, ay, seed=seed)
    for (x, y, seed) in ((330, 200, 5), (40, 420, 6), (340, 430, 7), (610, 400, 8), (900, 300, 9)):
        m.prop(f"olive_{seed}", olive(seed), x, y, box=(-4, -4, 4, 0), size=(64, 64), pad=6)
        A.soft_shadow(g, x + 7, y + 1, 16, 5)
    def cyp(seed, h):
        return lambda cv, ax, ay, fi: A.cypress(cv, ax, ay, h, seed=seed)
    for (x, y, h, seed) in ((600, 140, 46, 3), (860, 120, 50, 4), (940, 190, 44, 5), (360, 120, 40, 6), (20, 160, 44, 7)):
        m.prop(f"cypress_{seed}", cyp(seed, h), x, y, box=(-3, -3, 3, 0), size=(24, 64), pad=4)
        A.soft_shadow(g, x + 5, y, 8, 3)

    # bushes along the square, LttP-style rows that can be cut
    def bush(seed, fl):
        return lambda cv, ax, ay, fi: A.bush(cv, ax, ay - 6, seed=seed, flowers=fl)
    k = 0
    for x in range(392, 440, 16):
        for y in (330, 350):
            m.prop(f"bush_{k % 4}", bush(k % 4, k % 3 == 0), x, y, box=(-6, -5, 6, 0), size=(24, 24), pad=4, kind="bush")
            A.soft_shadow(g, x + 3, y, 8, 2.5)
            k += 1
    for x in range(536, 584, 16):
        for y in (330, 350):
            m.prop(f"bush_{k % 4}", bush(k % 4, k % 3 == 0), x, y, box=(-6, -5, 6, 0), size=(24, 24), pad=4, kind="bush")
            A.soft_shadow(g, x + 3, y, 8, 2.5)
            k += 1
    for (x, y) in ((40, 210), (56, 218), (30, 236), (700, 300), (716, 310), (930, 420), (912, 440)):
        m.prop(f"bush_{k % 4}", bush(k % 4, k % 3 == 0), x, y, box=(-6, -5, 6, 0), size=(24, 24), pad=4, kind="bush")
        A.soft_shadow(g, x + 3, y, 8, 2.5)
        k += 1

    # east: the night market, a well
    def stall(seed):
        return lambda cv, ax, ay, fi: A.stall(cv, ax - 22, ay - 34, 44, seed=seed)
    for (x, y, seed) in ((680, 120, 1), (760, 120, 2), (720, 220, 3)):
        m.prop(f"stall_{seed}", stall(seed), x, y, box=(-22, -8, 22, 0), size=(60, 50), pad=4)
        A.soft_shadow(g, x + 6, y, 24, 4)
    m.prop("well", lambda cv, ax, ay, fi: A.well(cv, ax, ay - 9), 640, 280, box=(-13, -12, 13, 0), size=(40, 44), pad=4, kind="well")
    A.soft_shadow(g, 645, 281, 15, 4)
    m.prop("sign_gate", lambda cv, ax, ay, fi: A.sign(cv, ax, ay), 440, 300, box=(-2, -2, 2, 0), size=(24, 24), pad=2, kind="sign",
           data={"text": "sign_temple"})

    # braziers in the square, dark until the Wakefire touches them
    def braz(lit):
        return lambda cv, ax, ay, fi: A.brazier(cv, ax, ay, lit=lit, frame=fi)
    for i, (x, y) in enumerate(((412, 176), (548, 176), (480, 250))):
        m.prop("brazier", braz(False), x, y, box=(-6, -4, 6, 0), size=(24, 34), pad=4, kind="brazier", data={"id": f"square_{i}"})
        A.soft_shadow(g, x + 4, y, 8, 2.5)
    m.prop("brazier_lit", braz(True), -100, -100, size=(24, 40), pad=4, frames=4)

    # guardians of the gate: winged bulls with crowned men's heads
    from px import Canvas as _C
    import json as _json
    lam = _C.load("/srv/Wakefire/Art/sprites/props/lamassu.png")
    lbx, lby = _json.load(open("/srv/Wakefire/Art/sprites/props/lamassu.json"))["base"]
    def lamassu(flip):
        return lambda cv, ax, ay, fi: cv.blit(lam, ax - (lam.w - lbx if flip else lbx), ay - lby, flip=flip)
    m.prop("lamassu_l", lamassu(False), 420, 82, box=(-10, -8, 10, 0), size=(48, 56), pad=8)
    m.prop("lamassu_r", lamassu(True), 540, 82, box=(-10, -8, 10, 0), size=(48, 56), pad=8)
    # standing torches at the foot of the steps
    def ptorch(cv, ax, ay, fi):
        A.pole_torch(cv, ax, ay, frame=fi)
    for x in (442, 518):
        m.prop("pole_torch", ptorch, x, 104, box=(-2, -2, 3, 0), size=(24, 40), pad=4, frames=4, kind="torch")
        A.soft_shadow(g, x + 3, 104, 5, 2)
        m.light(x + 1, 80, 4.2, (1.0, 0.70, 0.36), 0.85)
    # planters with clipped myrtle along the square
    def plant(seed):
        return lambda cv, ax, ay, fi: A.planter(cv, ax, ay, 28, 9, 12, seed=seed)
    for (x, y, sd) in ((398, 134, 1), (562, 134, 2), (398, 286, 3), (562, 286, 4)):
        m.prop(f"planter_{sd}", plant(sd), x, y, box=(-14, -10, 14, 0), size=(40, 36), pad=4)
        A.soft_shadow(g, x + 5, y, 15, 3)
    # market clutter
    m.prop("amphorae", lambda cv, ax, ay, fi: A.amphorae(cv, ax, ay, 31), 700, 132, box=(-8, -4, 8, 0), size=(32, 28), pad=4)
    m.prop("sacks", lambda cv, ax, ay, fi: A.sacks(cv, ax, ay, 32), 744, 236, box=(-8, -5, 8, 0), size=(28, 22), pad=4)
    m.prop("amphorae_b", lambda cv, ax, ay, fi: A.amphorae(cv, ax, ay, 33), 618, 262, box=(-8, -4, 8, 0), size=(32, 28), pad=4)

    m.marker("spawn", 480, 220)
    m.spawn("south", 480, 456, "up")
    m.spawn("gate", 480, 72, "down")
    m.exit(448, 472, 512, 480, "lowtown", "north")
    m.exit(462, 30, 498, 46, "temple_yard", "south", need="gate_open")
    m.marker("npc", 452, 80, who="captain")
    m.marker("npc", 398, 222, who="goat")
    m.marker("npc", 552, 226, who="dreamer")
    m.marker("npc", 604, 300, who="walker")
    m.marker("npc", 680, 112, who="merchant")
    m.solid(0, 0, 4, H); m.solid(W - 4, 0, W, H); m.solid(0, H - 4, 448, H); m.solid(512, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
