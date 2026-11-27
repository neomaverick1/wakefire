"""The sea cliffs east of town: a grassy clifftop, steps down to the beach, a pier where
Abu-Nur the fisherman sleeps in his boat, nets left out on the sand (one or two of which have
gone on fishing without him), and across the water a cove where a net keeps what it has caught. In the dream, moonlight lays a bridge over the sea."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R
import region_art as G
import town
import kit
import hkit
from mapkit import MapBuilder

TW, TH = 56, 36
W, H = TW * 16, TH * 16
C = 8   # mask cell size

# bridge of moonlight: dock end -> east -> north -> east into the cove
BRIDGE = [(640, 456), (720, 456), (720, 292), (800, 292)]


def masks():
    cols, rows = W // C, H // C
    water = np.zeros((rows, cols), bool)
    for r in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r * C + 4
            if y >= 528 or (x >= 560 and y >= 100 and not (x >= 800 and y < 330)):
                water[r, c] = True
    dock = np.zeros_like(water)
    for r in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r * C + 4
            if 496 <= x < 640 and 440 <= y < 472:
                dock[r, c] = True
    bridge = np.zeros_like(water)
    for (a, b) in zip(BRIDGE, BRIDGE[1:]):
        x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
        for r in range(rows):
            for c in range(cols):
                x, y = c * C + 4, r * C + 4
                if x0 - 12 <= x <= x1 + 12 and y0 - 12 <= y <= y1 + 12:
                    bridge[r, c] = True
    water &= ~dock
    return water, dock, bridge & water


def boxes(m, mask, layer):
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


def build():
    m = MapBuilder("cliffs", TW, TH, (30, 60, 40, 255), music="sea")
    water, dock, bridge = masks()
    T = m.lay(seed=21)
    big = lambda mask: np.kron(mask, np.ones((C, C), bool))
    sea = big(water)
    # the clifftop
    hkit.green(T, T.all(), seed=1)
    hkit.track(T, T.stroke([(0, 320), (120, 318), (200, 350), (258, 372), (262, 400)], 20) | T.stroke([(120, 318), (300, 250), (440, 150), (470, 120)], 14), seed=3)
    # the rocky rim where the clifftop ends above the sea
    T.rock(T.ragged(T.rect(508, 96, 56, 322), 4, 8, seed=4) | T.rect(520, 96, 40, 318), seed=5)
    # the beach, the cove across the water
    T.sand(T.rect(0, 380, 560, 150) | T.rect(800, 96, 96, 236), seed=6)
    T.water(T.ragged(sea, 3, 11, seed=9), seed=7, deep=46.0)
    # flowers on the clifftop, where somebody planted them; and on the sand, what the sea leaves, in threes
    for (x, y) in ((30, 290), (30, 350), (150, 290), (232, 340), (330, 226), (420, 130), (60, 60), (300, 60), (480, 300), (200, 200)):
        hkit.flowers(T, x, y, 'wyr'[(x + y) % 3])
    for (x, y) in ((60, 500), (150, 440), (300, 506), (420, 450), (500, 506), (830, 240), (850, 300)):
        hkit.flowers(T, x, y, 'w', leaf='sand')
    # the pier
    pier = T.rect(496, 440, 144, 32)
    T.planks(pier, seed=8, w=6, along='x')
    T.contact(0, 380, 240, 414, reach=6, strength=1.3); T.contact(282, 380, 520, 414, reach=6, strength=1.3)
    m.bake()
    # the rock faces: the tall cliff over the sea, the drop from the clifftop to the beach
    m.set_into_ground(town.cliff((W - 520) / 16.0, h=5.6, seed=26, grass=True), 520, 100, seed=26)
    m.set_into_ground(town.cliff(15.0, h=1.85, seed=27), 0, 414, seed=27)
    m.set_into_ground(town.cliff(238 / 16.0, h=1.85, seed=28), 282, 414, seed=28)
    m.set_into_ground(town.steps(38 / 16.0, n=5, rise=1.0, run=1.1), 242, 414)
    # (a hole at the foot of the low cliff: the way the tide gets under the town, and so can a man on his knees)
    m.solid(0, 380, 112, 414); m.solid(128, 380, 240, 414); m.solid(112, 380, 128, 404); m.solid(282, 380, 520, 414)
    m.model("cave_mouth", hkit.cave_mouth(3), 120, 415, box=None, shadow=False, lights=False)
    m.exit(114, 404, 126, 411, "lowtown_in", "beer_cave_in")
    m.spawn("beer_cave", 120, 428, "down")
    m.solid(520, 0, W, 96)
    m.solid(520, 96, 560, 414)     # the clifftop ends at the sea
    boxes(m, water & ~bridge, 0)
    boxes(m, bridge, 1)            # in the waking world the sea; in the dream, the bridge
    for (x, y) in ((498, 474), (638, 474), (498, 442), (638, 442), (568, 474)):
        m.model("post", town.post(0.8), x, y, box=None)
    # boats
    m.model("boat", town.boat(1), 600, 478, box=None)
    m.model("boat_b", town.boat(2), 440, 540, box=None)
    # the moonlight bridge (dream only), laid flat so everyone walks on it
    x0 = min(p[0] for p in BRIDGE) - 10; y0 = min(p[1] for p in BRIDGE) - 10
    x1 = max(p[0] for p in BRIDGE) + 10; y1 = max(p[1] for p in BRIDGE) + 10
    def bridge_draw(cv, ax, ay, fi):
        pts = [(p[0] - x0, p[1] - y0) for p in BRIDGE]
        G.moon_bridge(cv, pts, 18, fi)
    m.prop("moon_bridge_cliffs", bridge_draw, x0, y0, layer=2, size=(x1 - x0, y1 - y0), anchor=(0, 0), pad=0)
    m.light(720, 380, 5.0, (0.6, 0.7, 1.0), 0.5, flicker=False, h=0.3)
    # pier torches
    for x in (512, 628):
        kit.torch(m, x, 446, light=4.0)
    # clifftop dressing
    # the town's own tree, in a row along the way out to the point, and three more back from the road
    for (x, y) in ((80, 120), (200, 96), (320, 150), (120, 284), (380, 330), (60, 220)):
        hkit.tree(m, x, y)
    for (x0, y0) in ((296, 200), (456, 250)):                                     # myrtle, in blocks of four
        for dx in (0, 16):
            for dy in (0, 12):
                kit.bush(m, x0 + dx, y0 + dy, 1)
    hkit.name_post(m, 226, 362, "cl_name", "{g}THE SEA CLIFFS.{/}^{t}NO BATHING. NO FISHING AFTER DARK. TAKE YOUR NETS IN.{/}| Somebody did not take a net in. It has been dark for forty nights.")
    for (x, y, sd) in ((60, 470, 1), (380, 440, 2), (180, 520, 0), (840, 190, 3), (820, 320, 1), (340, 70, 4)):
        kit.rock(m, x, y, sd)
    # ---------------------------------------------------------------- where the clifftop and the beaches stop
    # north: the land climbs on as bare rock. West: a cypress windbreak either side of the road to town.
    # The beach ends in a fall of boulders at each end, and so does the cove.
    m.set_into_ground(town.cliff(520 / 16.0, h=1.5, seed=31), 0, 26, seed=31)
    m.solid(0, 0, 520, 28)
    kit.cypress_row(m, 8, 46, 284, seed=5)
    kit.cypress_row(m, 8, 356, 372, seed=6, step=14)
    kit.boulders(m, ((10, 436), (16, 462), (8, 488), (16, 514)), seed=1)
    kit.boulders(m, ((884, 126), (889, 166), (883, 206), (889, 246), (884, 286), (888, 322)), seed=2)

    # the stolen oil, in the cove
    kit.chest(m, 860, 140, "cove_oil", "oil")
    # people, and nets: most of them are nets. The ones with money in them are not.
    m.marker("npc", 604, 487, who="abunur")
    for i, (x, y) in enumerate(((204, 494), (428, 498))):
        m.enemy("dragnet", x, y, f"cl_n{i}", once=True)
    m.enemy("dragnet", 838, 232, "cl_n2", once=True)                # ...and the one that keeps the cove
    for i, (x, y) in enumerate(((108, 474), (322, 478), (62, 438), (866, 292))):
        m.marker("npc", x, y, who=f"net_{i}")
    m.marker("npc", 470, 120, who="goat_cliff")
    m.spawn("west", 22, 320, "right")
    m.exit(0, 296, 8, 344, "lowtown", "east")
    m.solid(0, 0, 4, 296); m.solid(0, 344, 4, H); m.solid(0, 0, 520, 4)
    m.save()


if __name__ == "__main__":
    build()
