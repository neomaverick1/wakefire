"""Ashkel, first district: the square before the Temple Gate. The precinct wall and its glazed gate close the
north side; the processional way runs up to it. Five houses stand round it, no two alike, each on its own
ground: the watch house and its drill yard under the wall; Ilu-Bani the cedar merchant's, with its walled
garden and its pool; the lamp seller's, lit from top to bottom; the tablet house, and Widow Ilta's with the
fig tree she planted the week her husband went out for figs. The night market keeps the east side."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas
import ashkel_art as A
import town
import kit
import houses
import hkit
import dprops
from forge import Model, M, m_ashlar, m_mottle
from mapkit import MapBuilder

TW, TH = 60, 30
W, H = TW * 16, TH * 16
IN = "ashkel_in"
FN, FS, FM = 196, 436, 430          # the fronts: the row under the wall, the row south of the market, the merchant's
LANE = (216, 248)                   # the lane west of the square
PATH = (446, 462)                   # the path along the south: to the merchant's porch, to the tablet house and Ilta's

PLACES = [
    (houses.watch_house, 100, FN), (houses.lamp_house, 884, FN),
    (houses.merchant_house, 120, FM), (houses.tablet_house, 648, FS), (houses.ilta_house, 868, FS),
]
SAY = {
    'ak_merchant': {0: "Barred from inside, by a man who has been robbed before and liked it less each time.^"
                       "The house of Ilu-Bani, cedar merchant to the Temple. There is no bell. People who call on Ilu-Bani are expected.| "
                       "The watch have always said his cellar is a good deal nearer their lock-up than he would like.",
                    ('open', 0): "The bar lifts out of its hooks.^The front door of the richest house in Ashkel stands open, and nobody in it minds."},
    'ak_lamps': {0: "Shut. A tablet hangs on the door: {g}OPEN WHEN THE SIGN IS LIT.{/}^"
                    "The sign is the fire bowl beside it. It is out. It is the only flame on the whole front of the house that is.",
                 ('open', 0): "The lamp seller's sign burns, and inside a bolt slides back.^He built it to work whether he was awake or not. He is a man who thinks ahead."},
}


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
    B = [(f(), x, y) for (f, x, y) in PLACES]
    # ================================================================ the ground
    hkit.calm(T, T.all(), 'sand', base=3.2, seed=1, amp=0.3, pebbles=0.002)
    green = (T.rect(392, 316, 52, 124) | T.rect(520, 316, 40, 20) | T.rect(816, 232, 134, 100) | T.rect(222, 274, 144, 164) |
             T.rect(732, 344, 80, 94) | T.rect(528, 344, 38, 94) | T.rect(920, 344, 30, 120) | T.rect(10, 262, 22, 200))
    hkit.lawn(T, green, seed=5, flowers=0.012)
    # the yards: paler, drier, kept
    yards = T.rect(184, 62, 188, 150)
    hkit.calm(T, yards, 'sand', base=3.9, seed=3, amp=0.3, pebbles=0.001)
    # the drill square in the watch's yard: a floor of beaten earth with a line round it
    drill = T.rect(208, 100, 144, 84)
    hkit.calm(T, drill, 'dust', base=3.6, seed=4, amp=0.2, pebbles=0.0)
    T.border(drill, ramp='pale', tone=4.4, width=1, hgt=0.6)
    # the lane, and the path along the south
    lane = T.rect(10, LANE[0], 370, LANE[1] - LANE[0])
    path = T.rect(100, PATH[0], 348, PATH[1] - PATH[0]) | T.rect(512, PATH[0], 420, PATH[1] - PATH[0])
    hkit.paved(T, lane | path, seed=12, rows=(8,), wmin=11, wmax=17)
    # the market: brick laid herringbone, a kerb round it, and the well in a court of tiles
    market = T.rect(592, 62, 224, 270)
    T.bricks(market, seed=21, bw=8, bh=4, ramp='flag', base=3.9, jitter=0.4, herring=True)
    T.border(market, ramp='pale', tone=4.3, width=2, hgt=1.2)
    court = T.rect(608, 252, 64, 64)
    T.tiles(court, seed=17, size=16, ramp='tile', base=3.9, checker='flag')
    T.border(court, ramp='pale', tone=4.4, width=2, hgt=1.2)
    # the square: cut stone
    square = T.rect(380, 92, 200, 216)
    T.slabs(square | T.rect(376, 58, 208, 40), seed=12, moss=0.06)
    # the processional way: pale slabs between two bands of glazed blue brick studded with gold
    way = T.rect(448, 92, 64, 388)
    T.slabs(way, seed=41, rows=(12,), wmin=16, wmax=16, ramp='pale', base=4.3, jitter=0.8, crack=0.05, whole=False, wear=0.4)
    bands = T.rect(444, 92, 4, 388) | T.rect(512, 92, 4, 388)
    T.bricks(bands, seed=42, bw=8, bh=4, ramp='lapis', base=3.3, jitter=0.7)
    stud = bands & ((T.yy % 16) >= 7) & ((T.yy % 16) <= 8) & (((T.xx - 444) % 68) >= 1) & (((T.xx - 444) % 68) <= 2)
    T.put(stud, 'gold', np.full((H, W), 4.0), 1.4)
    # a paved path from every door to the street it belongs to
    paths = (T.rect(111, FN, 16, LANE[0] - FN) |                          # the watch house
             T.rect(268, 212, 16, 4) |                                    # the yard gate
             T.rect(112, FM, 16, PATH[0] - FM) |                          # the merchant's porch
             T.rect(288, 438, 16, 8) |                                    # his garden gate
             T.rect(678, FS, 16, PATH[0] - FS) | T.rect(844, FS, 16, PATH[0] - FS) | T.rect(764, 438, 16, 8) |      # the tablet house, Ilta's, her garden
             T.rect(902, FN, 16, 36) | T.rect(816, 216, 102, 16))        # the lamp seller's, and round to the market
    hkit.paved(T, paths, seed=19, rows=(8,), wmin=8, wmax=12, base=4.0)
    # ---- the merchant's garden: a pool in a surround of tiles
    surround = T.rect(242, 314, 104, 72)
    T.tiles(surround, seed=23, size=8, ramp='tile', base=4.0, checker='flag')
    T.border(surround, ramp='pale', tone=4.5, width=2, hgt=1.2)
    pool = T.rect(250, 322, 88, 56)
    T.water(pool, seed=24, deep=10.0)
    T.border(pool, ramp='lapis', tone=3.4, width=2, hgt=1.0)
    hkit.paved(T, T.rect(288, 386, 16, 52), seed=25, rows=(8,), wmin=8, wmax=12, base=4.0)
    # ---- garden beds
    for (x, y, w, h, sd, crop) in ((230, 282, 48, 20, 1, 'grass'), (310, 282, 48, 20, 2, 'grass'), (230, 404, 40, 26, 3, 'grass'), (322, 404, 36, 26, 4, 'grass'),      # Ilu-Bani's
                                   (738, 352, 26, 40, 5, 'grass'), (784, 352, 24, 28, 6, 'dry'),                                                                        # Ilta's
                                   (532, 356, 28, 64, 7, 'grass')):                                                                                                     # the tablet house's leeks
        hkit.bed(T, x, y, w, h, seed=sd, crop=crop)
    for (b, x, y) in B:
        hkit.contact(T, b, x, y)
    T.contact(0, 30, 392, 58, reach=6, strength=1.6); T.contact(568, 30, W, 58, reach=6, strength=1.6)
    g = m.bake()
    A.sigil(g, 480, 186, 22)
    m.set_into_ground(terrace(), 380, 92)
    m.solid(380, 84, 456, 92); m.solid(504, 84, 580, 92)
    m.solid(374, 58, 380, 92); m.solid(580, 58, 586, 92)
    m.solid(250, 322, 338, 378)                                           # the pool

    # ================================================================ the wall and the gate
    m.model("wall_temple", town.city_wall(60.0, h=2.2, d=1.2, gate_at=30.0, gate_w=2.9), 0, 58, box=None)
    m.solid(0, 0, 457, 58); m.solid(503, 0, W, 58); m.solid(416, 58, 457, 66); m.solid(503, 58, 544, 66)
    m.model("banner", town.banner, 305, 59, box=None, frames=4, kind="banner")
    for bx in (220, 655, 776):
        m.model("banner", town.banner, bx, 59, box=None, frames=4, kind="banner")
    m.model("gate_temple", town.gate_doors(False), 480, 59, box=(-23, -14, 23, 0), kind="gate", data={"id": "temple_gate"})
    m.model("gate_temple_open", town.gate_doors(True), -100, -100, box=None, lights=False)
    for x in (364, 596):
        m.model("wall_torch", town.wall_torch, x, 67, box=None, frames=4, kind="torch")
        m.light(x, 67 - 49, 4.5, (1.0, 0.72, 0.38), 0.9, h=2.95)

    # ================================================================ the houses
    for (b, x, y) in B:
        hkit.place(m, b, x, y, inside=IN, say=SAY.get(b.key))
    # nobody walks round the back of one: the wall is behind the north row, and what is behind the others is theirs
    m.solid(10, 58, 184, 86)                                              # behind the watch house
    m.solid(824, 58, W, 94)                                               # behind the lamp seller's
    m.solid(10, 262, 216, 312)                                            # behind Ilu-Bani's
    m.solid(10, 312, 32, 462); m.solid(208, 312, 216, 444)                # and either side of it
    m.solid(728, 340, 732, FS); m.solid(812, 340, 816, FS); m.solid(566, 340, 568, FS)
    kit.brazier(m, 934, FN + 12, False, "ak_lamps_sign")                  # the lamp seller's sign
    kit.say(m, "ak_rules", town.stele(1.4, 5), 300, 222, (-5, -5, 5, 0),
            "The rules of the night watch, on a stone of their own, for men who say they never saw the ones over the door.^"
            "{g}IF THE CITY WILL NOT WAKE, GO TO THE FIRST WATCH.{/}| Under it, smaller, in another hand: {t}WAKE THE CAPTAIN FIRST.{/}| "
            "Under that, scratched with a spear point: {t}YOU WAKE HIM.{/}")

    # ================================================================ the plots
    hkit.plot(m, 184, 62, 372, 212, gates=[('s', 264, 288), ('e', 140, 172)], sides='se', seed=1, plaster=3, lamp=[('s', 0)])     # the drill yard
    hkit.plot(m, 216, 262, 372, 444, gates=[('s', 284, 308)], sides='nse', seed=7, plaster=1, lamp=[('s', 0)])                  # Ilu-Bani's garden
    hkit.hedge_ew(m, 16, 212, 262, 1, flowers='red')                                                                            # the back of his house, on the lane
    hkit.wall_ew(m, 732, 756, 438, 13, 1); hkit.wall_ew(m, 788, 812, 438, 14, 1)                                                # Ilta's garden
    for x in (756, 788):
        hkit.gate_pier(m, x, 439, 5, 1, lamp=(x == 756))
    hkit.hedge_ew(m, 528, 740, 338, 2); hkit.hedge_ew(m, 740, 944, 338, 3, flowers='fig')                                       # the south side of the market
    hkit.wall_ns(m, 522, 344, 438, 15, 0)                                                                                       # the tablet house's plot, on the way

    # ================================================================ what stands in them
    # ---- the drill yard
    kit.say(m, "ak_pell", houses.pell(0), 248, 150, (-3, -4, 3, 0),
            "The pell. The watch hits it instead of each other.^It has never once hit back, and it still has the better record.")
    m.model("ak_pell", houses.pell(0), 312, 150, box=(-3, -4, 3, 0))
    kit.say(m, "ak_butt", houses.butt(0), 340, 84, (-8, -5, 8, 0),
            "The archery butt. There are three arrows in it.^There are forty in the wall behind it, and one in the bench.")
    m.model("spear_rack", dprops.spear_rack(), 228, 78, box=(-12, -4, 12, 0))
    m.model("bench_1", hkit.bench(1.5, 1), 268, 80, box=(0, -6, 24, 0))
    for k, (x, y) in enumerate(((196, 204), (356, 204))):
        m.model(f"tub_olive_{k}", hkit.tub_tree(k, 'olive'), x, y, box=(-5, -8, 5, 0))
    kit.pot(m, 196, 78, True); kit.pot(m, 356, 88, False)
    # ---- Ilu-Bani's garden
    for k, (x, y) in enumerate(((240, 318), (348, 318), (240, 390), (348, 390))):
        m.model(f"tub_palm_{k % 2}", hkit.tub_tree(k % 2, 'palm'), x, y, box=(-5, -8, 5, 0))
    hkit.hedge_ew(m, 224, 364, 306, 4, flowers='cream')
    m.model("bench_0", hkit.bench(1.5, 0), 258, 402, box=(0, -6, 24, 0))
    kit.say(m, "ak_tortoise", houses.tortoise(0), 318, 398, (-4, -4, 4, 0),
            "A tortoise, by the pool.^It was not asleep before. It is not asleep now. Nobody has ever been able to tell, and it has never been in a hurry to say.")
    kit.palm(m, 232, 432, 2); kit.palm(m, 356, 300, 4)
    kit.cypress_row(m, 20, 330, 440, seed=1)
    # ---- the market, the well
    for (x, y, sd) in ((680, 124, 1), (760, 124, 2), (720, 234, 3)):
        m.stall(f"stall_{sd}", sd, x, y, town)
    m.model("well", town.well(), 640, 284, box=(-14, -26, 14, 0), kind="well")
    m.model("amphorae", town.amphorae(31), 628, 128)
    m.model("sacks", town.sacks(32), 764, 244)
    m.model("amphorae_b", town.amphorae(33), 618, 236)
    m.model("crates", town.crates(0), 800, 128)
    m.model("cart", town.cart(3), 770, 316, box=(-16, -16, 30, 0))
    for k, (x, y) in enumerate(((600, 76), (808, 76), (600, 324), (808, 324))):
        m.model("lt_bollard", town.post(0.7), x, y, box=(-2, -3, 2, 0))
    kit.palm(m, 604, 180, 2)
    # ---- the lamp seller's oil yard
    for k, x in enumerate((838, 870, 902)):
        m.model("lt_amph" if k % 2 == 0 else "lt_amph_w", town.amphorae(41 + k % 2), x, 262)
    kit.say(m, "crates_e", town.crates(1), 934, 300, (-12, -10, 12, 0),
            "Crates of copper pots, stacked against the Coppersmiths' wall.^Not one of them has been hammered in forty nights. The quiet is unnatural.")
    kit.olive(m, 852, 310, 0); kit.palm(m, 826, 290, 3)
    hkit.hedge_ew(m, 824, 900, 240, 5, flowers='ochre')
    # ---- Widow Ilta's: the fig, the hens, her beds
    kit.say(m, "ak_fig", houses.fig_tree(1), 772, 424, (-4, -6, 4, 0),
            "A fig tree, forty years old, heavy with fruit.^Widow Ilta planted it the week her husband went out for figs. To save him the trip.")
    m.model("coop_0", hkit.coop(0), 738, 432, box=(0, -11, 16, 0))
    m.model("washing_ilta", hkit.washing(1, 2.0, ('cream', 'blue', 'linen')), 934, 420, box=(0, -3, 3, 0))
    kit.pot(m, 826, FS + 6, False); kit.pot(m, 892, FS + 6, True)
    # ---- the tablet house's plot
    kit.olive(m, 546, 438, 3)
    kit.say(m, "ak_slate", town.stele(1.1, 3), 566, FS + 12, (-4, -4, 4, 0),
            "The tablet house's notice stone. Today's line, for copying:^{g}THE DILIGENT BOY RISES BEFORE THE SUN.{/}| Somebody has added, lower down and not very straight: {t}the sun has not come up.{/}")
    # ---- the square
    for (x, y, sd) in ((398, 134, 1), (562, 134, 2), (398, 286, 3), (562, 286, 4)):
        m.model(f"planter_{sd}", town.planter(sd), x, y, box=(-14, -10, 14, 0))
    kit.sign(m, 440, 300, "sign_gate", "sign_temple")
    kit.bush(m, 568, 216, 2)                                              # the fishmonger's palace
    for i, (x, y) in enumerate(((412, 176), (548, 176), (480, 250))):
        kit.brazier(m, x, y, False, f"square_{i}")
    kit.brazier_frames(m)
    kit.lamassu(m, 418, 88, west=False)
    kit.lamassu(m, 542, 88, west=True)
    k = 0
    for x in range(400, 440, 16):
        for y in (334, 356):
            kit.bush(m, x, y, k); k += 1
    kit.olive(m, 420, 420, 4); kit.olive(m, 540, 330, 5)
    # ---- light: torches where ways meet
    for (x, y) in ((442, 108), (518, 108), (374, LANE[0] - 2), (374, LANE[1] + 8), (588, 108), (588, 324), (442, PATH[0] - 4), (518, PATH[0] - 4), (628, 64)):
        kit.torch(m, x, y)

    # ================================================================ where the district stops
    kit.wall_ns(m, 0, 58, LANE[0] + 34, seed=6, plaster=2)
    kit.say(m, "cart_wreck", town.cart_wreck(2), 50, 240, (-26, -12, 28, 0),
            "A handcart, on its side where its owner lay down.^Past the wall is the Dyers' Quarter, snoring in three colours.")
    kit.wall_ns(m, 0, LANE[0] + 34, 462, seed=5, plaster=0)
    kit.wall_ns(m, W - 10, 58, 462, seed=8, plaster=3)
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
    m.marker("npc", 844, 362, who="cat_roof")                              # on Widow Ilta's bed, on Widow Ilta's roof
    m.marker("smoke", 44, 76)                                              # the watch fire
    m.solid(0, 0, 4, H); m.solid(W - 4, 0, W, H); m.solid(0, H - 4, 448, H); m.solid(512, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
