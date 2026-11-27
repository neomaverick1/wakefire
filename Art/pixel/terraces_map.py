"""The olive terraces west of town: hillside steps held up by dry-stone walls, olive trees in
rows, stairs that climb through the walls, jackals that hunt in pairs, and at the top the old
shrine of the First Watch: an altar whose offering only shows itself in the dream, and behind it
the door in the rock that goes down to the watch's crypt."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas
import town
import necro
import kit
import hkit
import dprops
from mapkit import MapBuilder

TW, TH = 52, 40
W, H = TW * 16, TH * 16
WALLS = [(520, 60, 104), (400, 100, 140), (280, 680, 720), (160, 360, 400)]   # (y, stair x0, stair x1)
HILL = 700                               # where the gate to the Hill of Sleepers stands in the top cliff
CRYPT = 420                              # and the door of the crypt, behind the shrine's altar
CHEST = '/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'


def build():
    m = MapBuilder("terraces", TW, TH, (30, 60, 40, 255), music="hills")
    T = m.lay(seed=31)
    hkit.green(T, T.all(), seed=1)
    # a path along each terrace, and up to each stair
    paths = T.none()
    for (y0, y1) in ((540, 600), (420, 500), (300, 380), (180, 260), (40, 140)):
        mid = y0 + (y1 - y0) // 2
        # each terrace's path stops short of the hedges at either end; only the one to town runs out
        paths |= T.stroke([(34, mid + 4), (200, mid - 3), (420, mid + 5), (640, mid - 2), (W if y0 == 300 else W - 34, mid + 3)], 15)
    for (y, s0, s1) in WALLS:
        cx = (s0 + s1) / 2
        paths |= T.stroke([(cx, y - 44), (cx, y + 64)], 22)
    paths |= T.stroke([(HILL, 96), (HILL, 30)], 20)           # up to the gate of the Hill of Sleepers
    hkit.track(T, paths, seed=3)
    # the shrine's paving: old, pale, and kept
    hkit.streets(T, [(T.rect(336, 60, 168, 44) | T.rect(CRYPT - 13, 26, 26, 44), 7, 10, 17)], base=4.0, ramp='pale', kerb=('flag', 2.8))
    # flowers, where somebody planted them: at the foot of every stair, and round the shrine
    for (x, y, k) in ((48, 512, 'w'), (112, 512, 'w'), (88, 392, 'y'), (150, 392, 'y'), (668, 272, 'r'), (730, 272, 'r'), (348, 152, 'w'), (410, 152, 'w'),
                      (320, 112, 'r'), (510, 112, 'r'), (660, 60, 'w'), (736, 60, 'w'), (780, 300, 'y'), (780, 352, 'y'), (220, 600, 'r'), (520, 610, 'y'), (640, 480, 'w')):
        hkit.flowers(T, x, y, k)
    for (y, s0, s1) in WALLS:
        T.contact(0, y, s0, y + 20, reach=6, strength=1.4); T.contact(s1, y, W, y + 20, reach=6, strength=1.4)
    m.bake()
    # the walls and the stairs through them, set into the ground
    for (y, s0, s1) in WALLS:
        m.set_into_ground(town.cliff(s0 / 16.0, h=1.15, seed=y), 0, y + 20, seed=y)
        m.set_into_ground(town.cliff((W - s1) / 16.0, h=1.15, seed=y + 1), s1, y + 20, seed=y + 1)
        m.set_into_ground(town.steps((s1 - s0) / 16.0, n=5, rise=1.0, run=1.1), s0, y + 20)
        m.solid(0, y, s0, y + 18); m.solid(s1, y, W, y + 18)
    # olive trees in their rows
    # (one tree, the same in every row)
    for (row_y, xs) in ((120, (60, 180, 520, 640, 760)), (250, (40, 200, 330, 460, 600)), (370, (240, 380, 520, 760)),
                        (490, (200, 340, 470, 610, 740)), (620, (160, 300, 440, 580, 720))):
        for x in xs:
            kit.olive(m, x, row_y, 0)
    for (x0, y0) in ((120, 330), (560, 210), (700, 470), (300, 600)):                # myrtle, in blocks of four
        for dx in (0, 16):
            for dy in (0, 12):
                kit.bush(m, x0 + dx, y0 + dy, 1)
    # what the boards say
    hkit.name_post(m, 790, 290, "tr_name", "{g}THE OLIVE TERRACES.{/}^{t}PICK NOTHING. THE TEMPLE COUNTS THEM.{/}| Under it, in chalk: {t}THE TEMPLE IS ASLEEP.{/}")
    hkit.name_post(m, HILL - 44, 104, "tr_hill", "{g}THE HILL OF SLEEPERS.{/}^{t}DO NOT WAKE THE DEAD.{/}| Somebody has. It was not you. It is a comfort, of a kind.")
    for (x, y, k) in ((60, 150, 0), (780, 250, 1), (90, 450, 2), (660, 560, 3), (520, 52, 4)):
        kit.rock(m, x, y, k)
    # ---------------------------------------------------------------- where the hillside stops
    # north: the hill goes on up as bare rock. West and east: cypress windbreaks, terrace by terrace.
    # South: the lowest terrace's own wall.
    m.set_into_ground(town.cliff(W / 16.0, h=1.6, seed=41), 0, 28, seed=41)
    m.solid(0, 0, CRYPT - 12, 30); m.solid(CRYPT + 12, 0, HILL - 14, 30); m.solid(HILL + 14, 0, W, 30)
    m.solid(HILL - 14, 0, HILL + 14, 12); m.solid(CRYPT - 12, 0, CRYPT + 12, 12)
    # the gate of the Hill of Sleepers, in the rock: shut until someone comes with the temple's key
    m.model("hill_gate", necro.hill_gate(False), HILL, 30, box=(-14, -6, 14, 0), kind="gate", data={"id": "hill_gate"}, shadow=False)
    m.model("hill_gate_open", necro.hill_gate(True), -100, -100, box=None, lights=False, shadow=False)
    kit.spirit_lamp(m, HILL - 30, 44, light=3.0); kit.spirit_lamp(m, HILL + 30, 44, light=3.0)
    # the way down to the Crypt of the First Watch, in the rock behind the altar
    m.model("crypt_door", dprops.crypt_door(), CRYPT, 30, box=None, shadow=False)
    m.light(CRYPT, 8, 2.2, (1.0, 0.70, 0.36), 0.5, h=1.4)
    for i, (ya, yb) in enumerate(((46, 156), (196, 276), (316, 396), (436, 516), (556, 626))):
        kit.cypress_row(m, 8, ya, yb, seed=i)
        if ya == 316: kit.cypress_row(m, W - 8, 362, yb, seed=i + 2)
        else: kit.cypress_row(m, W - 8, ya, yb, seed=i + 2)
    hkit.wall_ew(m, 0, W, H - 2, 9, 1)                         # the lowest terrace's own wall: the town's, lime-washed
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
    m.spawn("hill", HILL, 52, "down")
    m.spawn("crypt", CRYPT, 46, "down")
    m.exit(CRYPT - 10, 14, CRYPT + 10, 26, "crypt", "south")
    m.exit(HILL - 12, 14, HILL + 12, 27, "necro_road", "south", need="hill_gate")
    m.exit(W - 8, 296, W, 344, "lowtown", "west")
    m.solid(W - 4, 0, W, 296); m.solid(W - 4, 344, W, H); m.solid(0, 0, 4, H); m.solid(0, 0, W, 4); m.solid(0, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
