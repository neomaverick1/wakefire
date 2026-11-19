"""The olive terraces west of town: hillside steps held up by dry-stone walls, olive trees in
rows, stairs that zigzag up, jackals that hunt in pairs, and at the top an old shrine whose
offering only shows itself in the dream."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas, R, OUTLINE
import ashkel_art as A
import region_art as G
from mapkit import MapBuilder

TW, TH = 52, 40
W, H = TW * 16, TH * 16
WALLS = [(520, 60, 104), (400, 100, 140), (280, 680, 720), (160, 360, 400)]   # (y, stair x0, stair x1)
CHEST = '/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'


def build():
    m = MapBuilder("terraces", TW, TH, R['grass'][3], music="hills")
    g = m.ground
    A.grass(g, 0, 0, W, H, seed=31, dense=1.0, flowers=0.03)
    # a worn path along each terrace
    for (y0, y1) in ((540, 600), (420, 500), (300, 380), (180, 260), (40, 140)):
        G.dirt(g, 0, y0 + (y1 - y0) // 2 - 10, W, 20, seed=y0)
    for (y, s0, s1) in WALLS:
        G.drystone_wall(g, 0, y, s0, 20, seed=y)
        G.drystone_wall(g, s1, y, W - s1, 20, seed=y + 1)
        G.stone_steps(g, s0, y, s1 - s0, 20, n=4)
        m.solid(0, y, s0, y + 18); m.solid(s1, y, W, y + 18)
    # olive trees in their rows
    def olive(seed):
        return lambda cv, ax, ay, fi: A.olive_tree(cv, ax, ay, seed=seed)
    sd = 50
    for (row_y, xs) in ((120, (60, 180, 520, 640, 760)), (250, (40, 200, 330, 460, 600)), (370, (240, 380, 520, 760)),
                        (490, (200, 340, 470, 610, 740)), (620, (160, 300, 440, 580, 720))):
        for x in xs:
            m.prop(f"olive_{sd}", olive(sd), x, row_y, box=(-4, -4, 4, 0), size=(64, 64), pad=6)
            A.soft_shadow(g, x + 7, row_y + 1, 16, 5)
            sd += 1
    def bush(seed, fl):
        return lambda cv, ax, ay, fi: A.bush(cv, ax, ay - 6, seed=seed, flowers=fl)
    for k, (x, y) in enumerate(((120, 330), (136, 340), (560, 210), (576, 220), (700, 470), (300, 600), (316, 610), (780, 90))):
        m.prop(f"bush_{k % 4}", bush(k % 4, k % 3 == 0), x, y, box=(-6, -5, 6, 0), size=(24, 24), pad=4, kind="bush")
    # the shrine at the top: an altar, and in the dream, what was offered on it
    m.prop("altar", lambda cv, ax, ay, fi: G.block(cv, ax, ay), 420, 70, box=(-8, -6, 8, 0), size=(24, 24), pad=2, kind="look",
           data={"id": "shrine_altar"})
    m.prop("lamassu_t", lambda cv, ax, ay, fi: cv.blit(Canvas.load('/srv/Wakefire/Art/sprites/props/lamassu.png'), ax - 13, ay - 36),
           360, 70, box=(-10, -8, 10, 0), size=(48, 56), pad=8)
    m.prop("chest_dream", lambda cv, ax, ay, fi: cv.blit(Canvas.load(CHEST), ax - 8, ay - 15), 452, 76, box=(-7, -6, 7, 0), size=(24, 24), pad=4,
           kind="chest", layer=2, data={"id": "shrine_lamp", "text": "lamp"})
    # a vessel of flame, guarded, in the far corner of the lowest terrace
    m.prop("chest", lambda cv, ax, ay, fi: cv.blit(Canvas.load(CHEST), ax - 8, ay - 15), 40, 620, box=(-7, -6, 7, 0), size=(24, 24), pad=4,
           kind="chest", data={"id": "terrace_vessel", "text": "vessel"})
    for i, (x, y) in enumerate(((300, 340), (520, 350), (180, 220), (620, 230), (500, 100), (240, 470), (420, 600))):
        m.enemy("jackal", x, y, f"tr_j{i}")
    m.marker("npc", 600, 330, who="goat_terrace")
    m.spawn("east", W - 22, 320, "left")
    m.exit(W - 8, 296, W, 344, "lowtown", "west")
    m.solid(W - 4, 0, W, 296); m.solid(W - 4, 344, W, H); m.solid(0, 0, 4, H); m.solid(0, 0, W, 4); m.solid(0, H - 4, W, H)
    m.save()


if __name__ == "__main__":
    build()
