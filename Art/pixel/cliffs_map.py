"""The sea cliffs east of town: a grassy clifftop, steps down to the beach, a pier where
Abu-Nur the fisherman sleeps in his boat, brine crabs everywhere, and across the water a
cove where the crabs keep what they steal. In the dream, moonlight lays a bridge over the sea."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R, OUTLINE
import ashkel_art as A
import region_art as G
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
    m = MapBuilder("cliffs", TW, TH, R['grass'][3], music="sea")
    g = m.ground
    water, dock, bridge = masks()
    A.grass(g, 0, 0, 520, 380, seed=21, dense=0.8, flowers=0.02)
    G.sand(g, 0, 380, 560, 148, seed=22)
    G.sand(g, 800, 100, 96, 230, seed=23)
    is_water = lambda x, y: 0 <= x < W and 0 <= y < H and water[min(H // C - 1, y // C), min(W // C - 1, x // C)]
    G.water(g, 560, 100, W - 560, H - 100, seed=24, deep_from=lambda x, y: (x - 560) / 300)
    G.water(g, 0, 528, 560, 48, seed=25, deep_from=lambda x, y: (y - 528) / 60)
    G.shore(g, is_water, 0, 96, W, H - 96)
    # cliffs: along the top east, and the drop from the clifftop to the beach
    G.cliff(g, 520, 0, W - 520, 100, seed=26)
    G.cliff(g, 0, 380, 240, 34, seed=27)
    G.cliff(g, 282, 380, 238, 34, seed=28)
    G.stone_steps(g, 242, 380, 38, 34, n=5)
    G.cliff(g, 800, 60, 96, 40, seed=29)
    m.solid(0, 380, 240, 414); m.solid(282, 380, 520, 414)
    m.solid(520, 0, W, 96)
    m.solid(520, 96, 560, 414)     # the clifftop ends at the sea
    # the pier
    G.dock(g, 496, 440, 144, 32)
    boxes(m, water & ~bridge, 0)
    boxes(m, bridge, 1)            # in the waking world the sea; in the dream, the bridge
    # boats
    m.prop("boat", lambda cv, ax, ay, fi: G.boat(cv, ax, ay - 6, 61), 600, 500, size=(48, 20), pad=2)
    m.prop("boat_b", lambda cv, ax, ay, fi: G.boat(cv, ax, ay - 6, 62), 440, 548, size=(48, 20), pad=2)
    # the moonlight bridge (dream only), laid flat so everyone walks on it
    x0 = min(p[0] for p in BRIDGE) - 10; y0 = min(p[1] for p in BRIDGE) - 10
    x1 = max(p[0] for p in BRIDGE) + 10; y1 = max(p[1] for p in BRIDGE) + 10
    def bridge_draw(cv, ax, ay, fi):
        pts = [(p[0] - x0, p[1] - y0) for p in BRIDGE]
        G.moon_bridge(cv, pts, 18, fi)
    m.prop("moon_bridge_cliffs", bridge_draw, x0, y0, layer=2, size=(x1 - x0, y1 - y0), anchor=(0, 0), pad=0)
    m.light(720, 380, 5.0, (0.6, 0.7, 1.0), 0.5, flicker=False)
    # pier torches
    def ptorch(cv, ax, ay, fi):
        A.pole_torch(cv, ax, ay, frame=fi)
    for x in (512, 628):
        m.prop("pole_torch", ptorch, x, 446, box=(-2, -2, 3, 0), size=(24, 40), pad=4, frames=4, kind="torch")
        m.light(x + 1, 422, 4.0, (1.0, 0.70, 0.36), 0.8)
    # clifftop dressing
    def olive(seed):
        return lambda cv, ax, ay, fi: A.olive_tree(cv, ax, ay, seed=seed)
    for (x, y, sd) in ((80, 120, 41), (200, 80, 42), (420, 160, 43), (120, 300, 44), (380, 320, 45)):
        m.prop(f"olive_{sd}", olive(sd), x, y, box=(-4, -4, 4, 0), size=(64, 64), pad=6)
        A.soft_shadow(g, x + 7, y + 1, 16, 5)
    def bush(seed, fl):
        return lambda cv, ax, ay, fi: A.bush(cv, ax, ay - 6, seed=seed, flowers=fl)
    for k, (x, y) in enumerate(((300, 200), (316, 210), (40, 220), (460, 250), (476, 262), (230, 340))):
        m.prop(f"bush_{k % 4}", bush(k % 4, k % 2 == 0), x, y, box=(-6, -5, 6, 0), size=(24, 24), pad=4, kind="bush")
    def rock(seed, r):
        return lambda cv, ax, ay, fi: G.blob(cv, ax, ay - r * 0.7, r, r * 0.75, R['rock'], seed=seed, lumps=3, dither=0.05)
    for (x, y, r, sd) in ((60, 470, 7, 1), (380, 440, 6, 2), (180, 520, 5, 3), (850, 150, 8, 4), (820, 320, 6, 5)):
        m.prop(f"rock_{sd}", rock(sd, r), x, y, box=(-r, -3, r, 0), size=(32, 28), pad=4)
    # the stolen oil, in the cove
    m.prop("chest", lambda cv, ax, ay, fi: cv.blit(Canvas.load('/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'), ax - 8, ay - 15),
           860, 140, box=(-7, -6, 7, 0), size=(24, 24), pad=4, kind="chest", data={"id": "cove_oil", "text": "oil"})
    # people and crabs
    m.marker("npc", 604, 476, who="abunur")
    for i, (x, y) in enumerate(((100, 470), (200, 500), (330, 470), (440, 500), (60, 430))):
        m.enemy("crab", x, y, f"cl_c{i}")
    for i, (x, y) in enumerate(((830, 200), (870, 250), (820, 300))):
        m.enemy("crab", x, y, f"cl_k{i}")
    m.marker("npc", 470, 120, who="goat_cliff")
    m.spawn("west", 22, 320, "right")
    m.exit(0, 296, 8, 344, "lowtown", "east")
    m.solid(0, 0, 4, 296); m.solid(0, 344, 4, H); m.solid(0, 0, 520, 4)
    m.save()


if __name__ == "__main__":
    build()
