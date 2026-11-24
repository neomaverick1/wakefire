"""Lower Ashkel: where the road from the Temple Gate comes down into the streets. Eight houses,
no two alike, each on its own plot: the house the goat stands on and Ummi the oracle's under the
old wall; the Seven Jars, the weavers' and the counting house on the market street; Hesha's
bakery and Kesh's pottery behind it with their yards; the net loft on the quay. Every door has
its path, every plot its wall, and the roofs are places: up the stair or the ladder, and down
again by whichever edge is nearest.
Exits: north to the gate, west to the olive terraces, east to the sea cliffs."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas
import town
import kit
import houses
import hkit
from mapkit import MapBuilder

TW, TH = 60, 45
W, H = TW * 16, TH * 16
IN = "lowtown_in"

FN, FM, FS = 176, 384, 608          # where the fronts of the three rows stand
QUAY = 688                          # the top of the water
MAIN = (448, 512)                   # the main street, west and east kerb
STREET = (384, 448)                 # the market street, north and south kerb
LANE = (216, 240)                   # the lane behind the market row

# (builder, centre x, front y)
PLACES = [
    (houses.goat_house, 352, FN), (houses.oracle_house, 852, FN),
    (houses.beer_house, 128, FM), (houses.weavers, 336, FM), (houses.tax_office, 588, FM),
    (houses.bakery, 160, FS), (houses.pottery, 672, FS), (houses.net_loft, 856, 644),
]
SAY = {
    'lt_weavers': {0: "Bolted. The sisters who weave here have not spoken to each other in nine years, or to the street in ten.^"
                      "There is a ladder at the east end. The cats use it."},
    'lt_goat': {0: "Barred from inside, with two planks and a spite.^Nobody has lived here since before the sleep. Somebody keeps the roof very tidy.",
                ('open', 0): "The bar comes off. The door of the goat's house stands open.^The goat does not use it. The goat has never needed a door."},
    'lt_tax': {0: "The door of the counting house. There is more bronze on it than on a shield.^"
                  "It opens to the gong, for people who have come to pay. Nobody has rung it in forty nights. Nobody rang it much before.",
               ('open', 0): "The gong sings, and somewhere inside a bolt remembers its duty.^The counting house is open for business. It is the only thing in Ashkel that is."},
}


def plot(m, x0, y0, x1, y1, gates=(), sides='swe', seed=0, plaster=1, lamp=()):
    """Low walls round a plot (x0, y0)-(x1, y1), with a way through wherever a path goes in.
    gates: (side, a, b) = the opening, along that side. lamp: which gates have a lit pier."""
    g = {s: sorted((a, b) for (sd, a, b) in gates if sd == s) for s in 'nswe'}
    k = [0]

    def run(a, b, cuts):
        out = []
        for (ca, cb) in cuts:
            if ca > a: out.append((a, ca))
            a = max(a, cb)
        if a < b: out.append((a, b))
        return out
    if 's' in sides:
        for (a, b) in run(x0, x1, g['s']):
            hkit.wall_ew(m, a, b, y1, seed + k[0], plaster); k[0] += 1
        for i, (a, b) in enumerate(g['s']):
            hkit.gate_pier(m, a - 4, y1 + 1, seed, plaster, lamp=('s', i) in lamp)
            hkit.gate_pier(m, b + 4, y1 + 1, seed + 1, plaster, lamp=('s', i) in lamp)
    if 'n' in sides:
        for (a, b) in run(x0, x1, g['n']):
            hkit.wall_ew(m, a, b, y0 + 6, seed + k[0], plaster); k[0] += 1
        for i, (a, b) in enumerate(g['n']):
            hkit.gate_pier(m, a - 4, y0 + 7, seed, plaster)
            hkit.gate_pier(m, b + 4, y0 + 7, seed + 1, plaster)
    ya = y0 + (6 if 'n' in sides else 0); yb = y1 - (6 if 's' in sides else 0)
    for sd, x in (('w', x0), ('e', x1 - 6)):
        if sd not in sides: continue
        for (a, b) in run(ya, yb, g[sd]):
            hkit.wall_ns(m, x, a, b, seed + k[0], plaster); k[0] += 1
        for i, (a, b) in enumerate(g[sd]):
            hkit.gate_pier(m, x + 3, a, seed, plaster, lamp=(sd, i) in lamp)
            hkit.gate_pier(m, x + 3, b + 8, seed + 1, plaster, lamp=(sd, i) in lamp)


def build():
    m = MapBuilder("lowtown", TW, TH, (60, 44, 40, 255), music="town")
    T = m.lay(seed=11)
    B = [(f(), x, y) for (f, x, y) in PLACES]
    # ================================================================ the ground
    # the town's own earth, swept; grass where the town stops
    hkit.calm(T, T.all(), 'sand', base=3.2, seed=1, amp=0.3, pebbles=0.002)
    green = T.rect(0, 456, 24, 210) | T.rect(936, 456, 24, 210) | T.rect(16, 48, 232, 164) | T.rect(752, 48, 200, 164) | T.rect(772, 456, 172, 96)
    hkit.lawn(T, green, seed=5, flowers=0.012)
    # the yards: paler, drier, kept
    yards = T.rect(256, 48, 184, 164) | T.rect(24, 456, 416, 206) | T.rect(528, 456, 240, 206) | T.rect(672, 248, 272, 136) | T.rect(780, 552, 164, 114)
    hkit.calm(T, yards, 'sand', base=3.9, seed=3, amp=0.3, pebbles=0.001)
    # the streets
    main = T.rect(MAIN[0], 0, MAIN[1] - MAIN[0], STREET[0])
    street = T.rect(0, STREET[0], W, STREET[1] - STREET[0])
    lane = T.rect(16, LANE[0], 928, LANE[1] - LANE[0])
    south = T.rect(464, STREET[1], 32, 666 - STREET[1])
    hkit.paved(T, main | street | lane | south, seed=12, rows=(8,), wmin=11, wmax=17)
    # a drain down the middle of the main street, a darker course of stone
    T.slabs(T.rect(476, 0, 8, STREET[0]), seed=13, rows=(8, 9), wmin=7, wmax=8, ramp='cobble', base=3.2, jitter=0.6, crack=0, whole=False)
    # where the two streets cross: a square of bigger stones, lapis let into it
    cross = T.rect(MAIN[0] - 16, STREET[0], MAIN[1] - MAIN[0] + 32, STREET[1] - STREET[0])
    T.tiles(cross, seed=14, size=16, ramp='flag', base=4.0, inlay='lapis', every=2)
    T.border(cross, ramp='pale', tone=4.4, width=2, hgt=1.2)
    # the well court: tiles, a border, the well in the middle of it
    court = T.rect(528, 56, 208, 156)
    T.tiles(court, seed=17, size=16, ramp='tile', base=3.9, checker='flag')
    T.border(court, ramp='pale', tone=4.4, width=2, hgt=1.2)
    hkit.paved(T, T.rect(512, 120, 16, 32) | T.rect(616, 212, 32, 4), seed=18)
    # a paved path from every door to the street it belongs to
    paths = (T.rect(331, FN, 16, LANE[0] - FN) | T.rect(844, FN, 16, LANE[0] - FN) |                       # the goat's house, the oracle's
             T.rect(112, 176, 16, 40) |                                                                        # into the orchard
             T.rect(173, FS, 16, 40) | T.rect(173, 632, 291, 16) |                                             # the bakery: door, then east to the lane
             T.rect(715, FS, 16, 24) | T.rect(496, 616, 235, 16) |                                             # the pottery: door, then west to the lane
             T.rect(829, 644, 16, 24) | T.rect(648, 240, 24, 144) | T.rect(220, 240, 40, 144))                  # the net loft; the two alleys
    hkit.paved(T, paths, seed=19, rows=(8,), wmin=8, wmax=12, base=4.0)
    # ---- gardens
    for (x, y, w, h, sd) in ((272, 472, 64, 32, 1), (352, 472, 64, 32, 2), (28, 480, 40, 48, 3), (28, 540, 40, 40, 4),      # the bakery's
                             (40, 64, 72, 28, 5), (152, 64, 72, 28, 6), (40, 180, 56, 24, 7), (168, 180, 56, 24, 8),        # the orchard's
                             (768, 184, 56, 24, 9), (880, 184, 56, 24, 10),                                                 # the oracle's
                             (264, 56, 40, 100, 11), (416, 60, 20, 60, 12)):                                                # the goat's (eaten)
        hkit.bed(T, x, y, w, h, seed=sd, crop='dry' if sd >= 11 else 'grass')
    # the quay: the town stops at a kerb of big stones, and past it the sea
    T.slabs(T.rect(0, QUAY - 22, W, 22), seed=18, rows=(11,), wmin=14, wmax=22, base=3.7, moss=0.04, whole=False)
    T.border(T.rect(0, QUAY - 22, W, 22), ramp='pale', tone=4.2, width=2, hgt=1.2)
    for (b, x, y) in B:
        hkit.contact(T, b, x, y)
    T.water(T.rect(0, QUAY, W, H - QUAY), seed=19, deep=30.0)
    m.bake()
    m.set_into_ground(town.quay(W / 16.0), 0, QUAY, seed=20)
    m.solid(0, QUAY - 8, W, H)

    # ================================================================ the houses
    for (b, x, y) in B:
        hkit.place(m, b, x, y, inside=IN, say=SAY.get(b.key))
    # the old inner wall closes the north side, either side of the road up to the gate
    m.model("lt_wall_w", town.city_wall(27.0, h=2.2, d=1.0, buttress=6.0), 0, 40, box=(0, -36, 432, 0))
    m.model("lt_wall_e", town.city_wall(27.0, h=2.2, d=1.0, buttress=6.0, seed=2), 528, 40, box=(0, -36, 432, 0))
    m.solid(0, 0, 444, 40); m.solid(516, 0, W, 40)
    hkit.gong(m, 552, FM + 10, "lt_tax_gong")

    # ================================================================ the plots
    # under the wall: the orchard, the goat's house, the well court, the oracle's
    plot(m, 16, 48, 248, 212, gates=[('s', 108, 132)], sides='se', seed=1, plaster=1, lamp=[('s', 0)])
    plot(m, 256, 48, 440, 212, gates=[('s', 327, 351)], sides='swe', seed=5, plaster=3, lamp=[('s', 0)])
    plot(m, 752, 48, 952, 212, gates=[('s', 840, 864)], sides='sw', seed=9, plaster=1, lamp=[('s', 0)])
    for (x, y) in ((528, 216), (736, 216)):                       # the court is open to the lane: piers and nothing between
        hkit.gate_pier(m, x, y, 3, 2, lamp=True)
    for (x, y) in ((528, 64), (736, 64)):
        hkit.gate_pier(m, x, y, 4, 2)
    hkit.wall_ns(m, 520, 48, 116, 13, 2); hkit.wall_ns(m, 520, 156, 212, 14, 2)
    hkit.wall_ns(m, 738, 48, 212, 15, 2)
    # the market row: a wall shuts the west end; the caravan yard has its own
    hkit.wall_ew(m, 10, 36, FM, 17, 4)
    plot(m, 672, 248, 944, 384, gates=[('w', 296, 328)], sides='nw', seed=21, plaster=4, lamp=[('w', 0)])
    # behind the market street: the bakery's and the pottery's, each with a gate on the lane to the quay
    plot(m, 24, 450, 446, 668, gates=[('e', 624, 656)], sides='nse', seed=25, plaster=2, lamp=[('e', 0)])
    plot(m, 520, 450, 768, 668, gates=[('w', 608, 640)], sides='nsw', seed=31, plaster=0, lamp=[('w', 0)])
    hkit.wall_ns(m, 762, 456, 662, 37, 0)

    # ================================================================ what stands in them
    # ---- the orchard: olives in rows, clipped myrtle, a bench
    for i, (x, y) in enumerate(((60, 132), (132, 128), (204, 132), (96, 172), (168, 170))):
        kit.olive(m, x, y, i + 1)
    hkit.hedge_ew(m, 24, 104, 204, 1, flowers='red'); hkit.hedge_ew(m, 136, 240, 204, 2, flowers='red')
    hkit.hedge_sn(m, 24, 56, 196, 3)
    m.model("bench_0", hkit.bench(1.5, 0), 108, 108, box=(0, -6, 24, 0))
    # ---- the goat's house: a trough, a fence it has eaten a hole in
    m.model("trough_0", hkit.trough(0), 392, 204, box=(0, -8, 22, 0))
    hkit.fence_ew(m, 264, 304, 164, 1)
    kit.pot(m, 420, 190, True); kit.pot(m, 300, 190, False)
    # ---- the well court
    m.model("well", town.well(), 632, 144, box=(-14, -26, 14, 0), kind="well")
    for k, (x, y) in enumerate(((548, 84), (716, 84), (548, 200), (716, 200))):
        m.model(f"tub_palm_{k % 2}", hkit.tub_tree(k % 2, 'palm'), x, y, box=(-5, -8, 5, 0))
    m.model("bench_1", hkit.bench(1.5, 1), 580, 76, box=(0, -6, 24, 0))
    m.model("bench_1", hkit.bench(1.5, 1), 660, 76, box=(0, -6, 24, 0))
    # ---- the oracle's: figs in flower along the wall, a tub either side of her door
    hkit.hedge_ew(m, 760, 836, 204, 5, flowers='fig'); hkit.hedge_ew(m, 868, 944, 204, 6, flowers='fig')
    for k, x in enumerate((822, 882)):
        m.model(f"tub_olive_{k}", hkit.tub_tree(k, 'olive'), x, FN + 10, box=(-5, -8, 5, 0))
    kit.cypress(m, 772, 120, 1); kit.cypress(m, 934, 124, 2)
    # ---- the market: three stalls in a row before the caravan yard, and what the caravan left in it
    for (x, sd) in ((716, 4), (796, 5), (876, 6)):
        m.stall(f"stall_{sd}", sd, x, FM + 14, town)
    m.model("cart", town.cart(3), 730, 300, box=(-16, -16, 30, 0))
    for k, x in enumerate((790, 822, 854)):
        m.model("crates" if k != 1 else "crates_b", town.crates(k % 2), x, 276)
    for k, x in enumerate((790, 822, 854, 886)):
        m.model("lt_amph" if k % 2 == 0 else "lt_amph_w", town.amphorae(41 + k % 2), x, 318)
    m.model("trough_0", hkit.trough(0), 900, 290, box=(0, -8, 22, 0))
    kit.palm(m, 924, 356, 2)
    # ---- the Seven Jars and the weavers: what the houses have not already got in front of them
    m.model("washing_0", hkit.washing(0, 2.2), 222, 300, box=(0, -3, 3, 0))
    m.model("tub_palm_0", hkit.tub_tree(0, 'palm'), 232, FM + 8, box=(-5, -8, 5, 0))            # a palm in a tub at the mouth of the alley
    m.model("bench_0", hkit.bench(1.5, 0), 532, 398, box=(0, -6, 24, 0))                 # where people wait to pay; nobody is waiting
    for k, (x, y) in enumerate(((444, 376), (516, 376), (444, 456), (516, 456))):         # the four stones at the crossing
        m.model("lt_bollard", town.post(0.7), x, y, box=(-2, -3, 2, 0))
    kit.pot(m, 228, 372, True); kit.pot(m, 252, 262, False)
    kit.sign(m, 520, FM + 12, "sign_lt", "sign_lowtown")
    # the cellar door of the Seven Jars, in the alley: two leaves let into the ground, one of them up
    import hin
    o = m.model("cellar_door", hin.cellar_door(True), 240, 334, box=None, shadow=False, lights=False)
    o["y"] -= 18; o["py"] -= 18
    m.solid(229, 314, 232, 334); m.solid(248, 314, 251, 334); m.solid(229, 312, 251, 316)
    m.exit(233, 318, 247, 328, IN, "lt_beer_cellar_in")
    m.spawn("lt_beer_cellar", 240, 344, "down")
    # ---- the bakery: the oven and its yard, herbs, the hen house, the washing
    m.model("oven", town.oven, 296, 600, box=(-14, -22, 14, 0), frames=3)
    m.model("lt_sacks", town.sacks(40), 344, 612, kind=None)
    m.model("lt_sacks_b", town.sacks(41), 370, 600)
    m.model("coop_0", hkit.coop(0), 30, 612, box=(0, -11, 16, 0))
    hkit.fence_sn(m, 72, 560, 628, 2)
    m.model("washing_1", hkit.washing(1, 2.6, ('cream', 'linen', 'cream', 'red')), 384, 540, box=(0, -3, 3, 0))
    for k, x in enumerate((264, 280)):
        kit.pot(m, x, 660, k == 0)
    kit.palm(m, 420, 560, 3)
    m.model("bench_0", hkit.bench(1.5, 0), 392, 630, box=(0, -6, 24, 0))
    hkit.hedge_ew(m, 264, 424, 520, 7, flowers='cream')
    kit.olive(m, 52, 520, 4)
    # ---- the pottery: kiln, wheel, and the jars set out to be counted, which is how he sleeps
    m.model("kiln", town.kiln, 556, 604, box=(-10, -18, 10, 0), frames=2)
    m.model("wheel", town.potters_wheel(), 560, 652, box=(-6, -8, 6, 0))
    for j, y in enumerate((646, 660)):
        for i, x in enumerate(range(616, 756, 16)):
            kit.pot(m, x, y, (i + j) % 3 == 0)
    kit.pot(m, 540, 480, True); kit.pot(m, 556, 484, False); kit.pot(m, 574, 480, True)
    kit.palm(m, 548, 548, 4)
    hkit.hedge_ew(m, 600, 752, 476, 8, flowers='ochre')
    # ---- the net loft and the quay
    for x in (238, 418, 540, 668, 736):
        m.model("post", town.post(0.8), x, QUAY - 6, box=(-2, -3, 2, 0))
    kit.say(m, "lt_mooring", town.post(0.8), 302, QUAY - 6, (-3, -4, 3, 0),
            "The fishing boats, all in, tied up tight.^Forty nights, and nobody has asked the fish how they feel about it.")
    m.model("lt_boat", town.boat(1), 270, QUAY - 2, box=None, shadow=False)
    m.model("lt_boat_b", town.boat(2), 702, QUAY - 1, box=None, shadow=False)
    kit.say(m, "lt_nets", town.sacks(44), 452, QUAY - 26, (-10, -8, 10, 0),
            "Nets, folded for a morning that hasn't come yet.^The road ends here. So does the land.")
    m.model("washing_2", hkit.washing(2, 2.6, ('straw', 'straw', 'linen')), 800, 534, box=(0, -3, 3, 0))
    m.model("crates", town.crates(0), 800, 668); m.model("lt_amph", town.amphorae(41), 760, 664)
    for k, (x, y) in enumerate(((800, 500), (880, 488), (920, 512))):
        kit.bush(m, x, y, k + 1)
    kit.olive(m, 852, 492, 6)
    kit.chest(m, 936, 640, "lt_alley", "shekels:20")
    # ---- light: a torch at every corner where two ways meet, and down the main street in pairs
    for (x, y) in ((440, FM - 2), (520, FM - 2), (440, STREET[1] + 6), (520, STREET[1] + 6), (440, 100), (520, 100), (440, LANE[0] - 2), (520, LANE[1] + 6),
                   (168, STREET[1] + 6), (812, STREET[1] + 6), (40, LANE[1] + 6), (920, LANE[1] + 6)):
        kit.torch(m, x, y)
    for (x, y, sd) in ((434, 62, 0), (526, 62, 1)):
        kit.cypress(m, x, y, sd)

    # ================================================================ where the town stops
    kit.wall_ns(m, 0, 40, STREET[0], seed=11, plaster=1)
    kit.wall_ns(m, W - 10, 40, STREET[0], seed=12, plaster=4)
    kit.cypress_row(m, 8, 472, 650, seed=3)
    kit.cypress_row(m, W - 8, 472, 520, seed=4)

    # people
    m.marker("npc", 316, 628, who="hesha")
    m.marker("npc", 592, 652, who="kesh")
    m.marker("npc", 884, 196, who="ummi")
    m.marker("npc", 330, 112, who="goat_roof")
    m.marker("npc", 624, 412, who="taxman")
    m.marker("npc", 352, 622, who="flourboy")
    m.marker("npc", 272, 396, who="lover")
    m.marker("npc", 600, 188, who="dog")
    m.marker("npc", 172, 316, who="roof_drinker")                   # on the roof of the Seven Jars, where the benches are
    # smoke: the bakery's chimney, the kiln, and whatever Ummi burns
    m.marker("smoke", 202, 488)
    m.marker("smoke", 556, 576)
    m.marker("smoke", 852, 62, who="fig")
    # the dream has its own residents here
    for (x, y, uid) in ((120, 640, "lt_m1"), (700, 640, "lt_m2"), (480, 560, "lt_m3")):
        m.enemy("moth", x, y, uid)
    # ways out
    m.spawn("north", 480, 26, "down")
    m.spawn("west", 22, 424, "right")
    m.spawn("east", W - 22, 424, "left")
    m.spawn("start", 480, 26, "down")
    m.exit(448, 0, 512, 8, "ashkel", "south")
    m.exit(0, 400, 8, 448, "terraces", "east")
    m.exit(W - 8, 400, W, 448, "cliffs", "west")
    m.solid(0, 0, 4, 400); m.solid(0, 448, 4, H); m.solid(W - 4, 0, W, 400); m.solid(W - 4, 448, W, H)
    m.solid(0, 0, 448, 4); m.solid(512, 0, W, 4); m.solid(0, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
