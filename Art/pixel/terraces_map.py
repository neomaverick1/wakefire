"""The olive terraces west of town: hillside steps held up by dry-stone walls, olive trees in
rows, stairs that climb through the walls, jackals that hunt in pairs, and at the top an old
shrine whose offering only shows itself in the dream."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas
import town
import kit
from mapkit import MapBuilder

TW, TH = 52, 40
W, H = TW * 16, TH * 16
WALLS = [(520, 60, 104), (400, 100, 140), (280, 680, 720), (160, 360, 400)]   # (y, stair x0, stair x1)
CHEST = '/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'


def build():
    m = MapBuilder("terraces", TW, TH, (30, 60, 40, 255), music="hills")
    T = m.lay(seed=31)
    T.grass(T.all(), seed=1, flowers=0.008, tufts=0.03, fringe=0)
    # a worn path along each terrace, and up to each stair
    paths = T.none()
    for (y0, y1) in ((540, 600), (420, 500), (300, 380), (180, 260), (40, 140)):
        mid = y0 + (y1 - y0) // 2
        # each terrace's path stops short of the hedges at either end; only the one to town runs out
        paths |= T.stroke([(34, mid + 4), (200, mid - 3), (420, mid + 5), (640, mid - 2), (W if y0 == 300 else W - 34, mid + 3)], 15)
    for (y, s0, s1) in WALLS:
        cx = (s0 + s1) / 2
        paths |= T.stroke([(cx, y - 44), (cx, y + 64)], 22)
    paths = T.ragged(paths, 4, 9, seed=2)
    T.earth(paths, seed=3, base=4.1, ramp='dust', pebbles=0.01)
    # the shrine's old paving, grass thin and dry round it
    T.grass(T.ragged(T.disc(420, 70, 100, 30), 3, 8, seed=4) & ~paths, seed=5, ramp='dry', base=3.0, tufts=0.05)
    T.slabs(T.ragged(T.disc(410, 82, 74, 22), 3, 7, seed=6), seed=7, rows=(10, 11), wmin=10, wmax=17, base=3.8, moss=0.25, crack=0.15)
    for (y, s0, s1) in WALLS:
        T.contact(0, y, s0, y + 20, reach=6, strength=1.4); T.contact(s1, y, W, y + 20, reach=6, strength=1.4)
    m.bake()
    # the walls and the stairs through them, set into the ground
    for (y, s0, s1) in WALLS:
        m.set_into_ground(town.drystone(s0 / 16.0, seed=y), 0, y + 20, seed=y)
        m.set_into_ground(town.drystone((W - s1) / 16.0, seed=y + 1), s1, y + 20, seed=y + 1)
        m.set_into_ground(town.steps((s1 - s0) / 16.0, n=4, rise=0.6, run=0.65), s0, y + 20)
        m.solid(0, y, s0, y + 18); m.solid(s1, y, W, y + 18)
    # olive trees in their rows
    sd = 0
    for (row_y, xs) in ((120, (60, 180, 520, 640, 760)), (250, (40, 200, 330, 460, 600)), (370, (240, 380, 520, 760)),
                        (490, (200, 340, 470, 610, 740)), (620, (160, 300, 440, 580, 720))):
        for x in xs:
            kit.olive(m, x, row_y, sd); sd += 3
    for k, (x, y) in enumerate(((120, 330), (136, 340), (560, 210), (576, 220), (700, 470), (300, 600), (316, 610), (780, 90))):
        kit.bush(m, x, y, k)
    for (x, y, k) in ((60, 150, 0), (780, 250, 1), (90, 450, 2), (660, 560, 3), (520, 52, 4)):
        kit.rock(m, x, y, k)
    # ---------------------------------------------------------------- where the hillside stops
    # north: the hill goes on up as bare rock. West and east: cypress windbreaks, terrace by terrace.
    # South: the lowest terrace's own wall.
    m.set_into_ground(town.cliff(W / 16.0, h=1.6, seed=41), 0, 28, seed=41)
    m.solid(0, 0, W, 30)
    for i, (ya, yb) in enumerate(((46, 156), (196, 276), (316, 396), (436, 516), (556, 626))):
        kit.cypress_row(m, 8, ya, yb, seed=i)
        if ya == 316: kit.cypress_row(m, W - 8, 362, yb, seed=i + 2)
        else: kit.cypress_row(m, W - 8, ya, yb, seed=i + 2)
    m.model("tr_south", town.drystone(W / 16.0, h=0.7, seed=9), 0, H - 2, box=None)
    m.solid(0, H - 13, W, H)
    # the shrine at the top: an altar, and in the dream, what was offered on it
    m.model("altar", town.altar(), 420, 70, box=(-9, -12, 9, 0), kind="look", data={"id": "shrine_altar"})
    kit.lamassu(m, 352, 76, west=False)
    kit.chest(m, 452, 76, "shrine_lamp", "lamp", layer=2)
    # a vessel of flame, guarded, in the far corner of the lowest terrace
    kit.chest(m, 40, 620, "terrace_vessel", "vessel")
    for i, (x, y) in enumerate(((300, 340), (520, 350), (180, 220), (620, 230), (500, 100), (240, 470), (420, 600))):
        m.enemy("jackal", x, y, f"tr_j{i}")
    m.marker("npc", 600, 330, who="goat_terrace")
    m.spawn("east", W - 22, 320, "left")
    m.exit(W - 8, 296, W, 344, "lowtown", "west")
    m.solid(W - 4, 0, W, 296); m.solid(W - 4, 344, W, H); m.solid(0, 0, 4, H); m.solid(0, 0, W, 4); m.solid(0, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
