"""Beyond the Temple Gate: the yard before the ziggurat with its chasm (crossable only on a long
road of moonlight in the dream), then three floors inside: the hall of dream walls, the
gallery of the bull that breathes fire, and the summit where the god sleeps."""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from px import Canvas, R, OUTLINE
import ashkel_art as A
import region_art as G
import town
import kit
import hkit
from mapkit import MapBuilder

CHEST = '/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png'
C = 8


def chest(m, x, y, cid, what, layer=0):
    kit.chest(m, x, y, cid, what, layer=layer)


def pit_boxes(m, mask, layer):
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


# ------------------------------------------------------------------ the temple yard
YARD_BRIDGE = [(440, 340), (440, 306), (180, 306), (180, 262), (440, 262), (440, 218), (320, 218), (320, 190)]


def temple_yard():
    TW, TH = 40, 36
    W, H = TW * 16, TH * 16
    m = MapBuilder("temple_yard", TW, TH, (60, 44, 40, 255), music="temple")
    T = m.lay(seed=71)
    T.earth(T.all(), seed=1, base=3.6, ramp='dust')
    # two courts of pale stone, and between them the chasm
    courts = T.rect(32, 340, W - 64, H - 340) | T.rect(32, 58, W - 64, 142)
    T.slabs(courts, seed=72, rows=(12,), wmin=16, wmax=16, ramp='pale', base=4.0, jitter=0.9, crack=0.06, whole=False, wear=0.5, moss=0.05)
    # the temple's gardens: a lawn either side of the way in each court, kept, with a kerb of pale stone
    for k, (x, y, w, h) in enumerate(((60, 372, 204, 164), (376, 372, 204, 164), (60, 92, 180, 92), (400, 92, 180, 92))):
        lawn = T.rect(x, y, w, h)
        hkit.green(T, lawn, seed=5 + k)
        T.border(lawn, ramp='pale', tone=4.9, width=2, hgt=1.2)
        for (fx, fy, kind) in ((x + 8, y + 8, 'w'), (x + w - 22, y + 8, 'r'), (x + 8, y + h - 22, 'y'), (x + w - 22, y + h - 22, 'w')):
            hkit.flowers(T, fx, fy, kind)
    # the way to the door: paler still, between two bands of glazed brick studded with gold
    way = T.rect(300, 58, 40, 142) | T.rect(300, 340, 40, H - 340)
    T.slabs(way, seed=73, rows=(12,), wmin=20, wmax=20, ramp='pale', base=4.8, jitter=0.5, crack=0.03, whole=False, wear=0.3)
    bands = (T.rect(296, 58, 4, 142) | T.rect(340, 58, 4, 142) | T.rect(296, 340, 4, H - 340) | T.rect(340, 340, 4, H - 340))
    T.bricks(bands, seed=74, bw=8, bh=4, ramp='lapis', base=3.3, jitter=0.7)
    stud = bands & ((T.yy % 16) >= 7) & ((T.yy % 16) <= 8) & (((T.xx - 296) % 44) >= 1) & (((T.xx - 296) % 44) <= 2)
    T.put(stud, 'gold', np.full((H, W), 4.0), 1.4)
    T.contact(0, 30, W, 58, reach=7, strength=1.6)
    g = m.bake()
    G.chasm(g, 0, 200, W, 140)
    m.ground_n[200:340, :] = (128, 128, 255, 1)
    # the precinct walls close the sides; the ziggurat's lowest tier rises along the top
    m.set_into_ground(town.precinct_side(H / 16.0), 0, H, seed=3)
    m.set_into_ground(town.precinct_side(H / 16.0), W - 32, H, seed=4)
    m.model("zig_tier", town.ziggurat_tier(W / 16.0, h=2.6, d=1.2, door_at=20.0), 0, 58, box=None)
    m.solid(0, 0, W, 58)
    m.solid(0, 0, 32, H); m.solid(W - 32, 0, W, H)
    # the chasm: never walkable, except the road of moonlight, which only the dream has
    cols, rows = W // C, H // C
    pit = np.zeros((rows, cols), bool)
    road = np.zeros_like(pit)
    for r in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r * C + 4
            if 200 <= y < 340:
                pit[r, c] = True
    for (a, b) in zip(YARD_BRIDGE, YARD_BRIDGE[1:]):
        x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
        for r in range(rows):
            for c in range(cols):
                x, y = c * C + 4, r * C + 4
                if x0 - 10 <= x <= x1 + 10 and y0 - 10 <= y <= y1 + 10:
                    road[r, c] = True
    road &= pit
    # the old drawbridge in the middle (lowered from the far side once Azar has crossed)
    draw = np.zeros_like(pit)
    for r in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r * C + 4
            if 296 <= x < 344 and 200 <= y < 340:
                draw[r, c] = True
    pit_boxes(m, pit & ~road & ~draw, 0)
    pit_boxes(m, road & ~draw, 1)
    pit_boxes(m, draw & ~road, 0)
    pit_boxes(m, draw & road, 1)
    for (x0, y0, x1, y1) in ((296, 200, 344, 340),):
        m.marker("drawbridge", x0, y0, w=x1 - x0, h=y1 - y0)
    m.model("drawbridge", town.bridge_deck(3.0, 8.75), 296, 200, box=None, kind="drawbridge", shadow=False)
    xs = [p[0] for p in YARD_BRIDGE]; ys = [p[1] for p in YARD_BRIDGE]
    bx0, by0, bx1, by1 = min(xs) - 12, min(ys) - 12, max(xs) + 12, max(ys) + 12
    def bridge_draw(cv, ax, ay, fi):
        G.moon_bridge(cv, [(p[0] - bx0, p[1] - by0) for p in YARD_BRIDGE], 16, fi)
    m.prop("moon_bridge_yard", bridge_draw, bx0, by0, layer=2, size=(bx1 - bx0, by1 - by0), anchor=(0, 0), pad=0)
    # guardians, fire, a sign
    kit.lamassu(m, 246, 104, west=False)
    kit.lamassu(m, 394, 104, west=True)
    for i, (x, y) in enumerate(((120, 380), (520, 380), (120, 150), (520, 150))):
        kit.brazier(m, x, y, lit=True)
    kit.brazier_frames(m)
    kit.sign(m, 360, 470, "sign_yard", "sign_yard")
    for (x, y) in ((76, 552), (564, 552), (76, 420), (564, 420)):          # (one palm, the same at every corner)
        kit.palm(m, x, y, 0)
    for (x, y, sd) in ((180, 520, 1), (470, 540, 2), (176, 122, 3), (464, 122, 4)):
        m.model(f"planter_{sd}", town.planter(sd), x, y, box=(-14, -10, 14, 0))
    m.light(320, 260, 7.0, (0.55, 0.62, 1.0), 0.45, flicker=False, h=0.4)
    m.marker("npc", 140, 500, who="goat_yard")
    # the temple's own seal, the size of a barrel, rolling the way between the gate and the bridge and sealing the ground
    m.marker("enemy", 320, 384, who="seal", id="ty_seal", text="once beat:320,384;320,500")
    m.spawn("south", 320, 552, "up")
    m.spawn("door", 320, 80, "down")
    m.exit(296, H - 8, 344, H, "ashkel", "gate")
    m.exit(306, 56, 334, 64, "zig_1", "south")
    # the south wall, seen from inside: its walk and merlons either side of the gate passage
    m.model("yard_south_w", town.parapet_ew((296 - 32) / 16.0), 32, H - 2, box=None)
    m.model("yard_south_e", town.parapet_ew((W - 32 - 344) / 16.0), 344, H - 2, box=None)
    m.solid(0, H - 14, 296, H); m.solid(344, H - 14, W, H)
    m.save()


# ------------------------------------------------------------------ inside
def floor(m, W, H, wall_h=48, seed=80, door=True):
    """Lays a hall's floor: fired tiles with a blue lozenge here and there, an inlaid band round the
    room, the tops of the thick side walls. Returns the Terrain so carpets and daises can go on
    before it is baked."""
    T = m.lay(seed=seed)
    T.tiles(T.all(), seed=seed, size=16, ramp='tile', base=3.5, inlay='lapis', every=5)
    band = T.rect(36, wall_h + 14, W - 72, H - wall_h - 44) & ~T.rect(39, wall_h + 17, W - 78, H - wall_h - 50)
    T.put(band, 'lapis', np.full((H, W), 3.2) + ((T.xx + T.yy) % 6 < 3) * 0.8, 1.2)
    corner = band & (((T.xx - 36) % (W - 75) < 3) & ((T.yy - wall_h - 14) % (H - wall_h - 47) < 3))
    T.put(corner, 'gold', np.full((H, W), 4.0), 1.5)
    tops = T.rect(0, wall_h, 24, H - wall_h) | T.rect(W - 24, wall_h, 24, H - wall_h) | T.rect(24, H - 16, W - 48, 16)
    if door:
        gap = T.rect(W // 2 - 20, H - 16, 40, 16)
        tops &= ~gap
        T.slabs(gap, seed=seed + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=4.0, whole=False, crack=0)
    T.walltop(tops, seed=seed + 1)
    coping = (T.rect(22, wall_h, 2, H - wall_h - 16) | T.rect(W - 24, wall_h, 2, H - wall_h - 16) | T.rect(24, H - 16, W - 48, 2)) & tops
    T.put(coping, 'gold', np.full((H, W), 3.6), 3.4)
    # the north and west walls shade the floor at their feet
    T.contact(0, 0, W, wall_h, reach=7, strength=1.6)
    T.contact(0, wall_h, 24, H, reach=5, strength=1.0)
    return T


def walls(m, W, H, wall_h=48, portal=None, steps_to=None, door=True):
    """The sanctuary wall along the north side (with a doorway and steps up to it, if asked) and the collision of the hall."""
    m.set_into_ground(town.temple_wall(W / 16.0, h=wall_h / 16.0 - 0.25, d=0.25, door_at=None if portal is None else portal / 16.0), 0, wall_h)
    if portal is not None and steps_to:
        run = (steps_to - wall_h) / 16.0
        rise = min(1.25, run * 0.42)
        m.set_into_ground(town.steps(2.5, n=6, rise=rise, run=run - rise), portal - 20, steps_to)
    m.solid(0, 0, W, wall_h - 4); m.solid(0, 0, 24, H); m.solid(W - 24, 0, W, H)
    if door:
        m.solid(0, H - 14, W // 2 - 20, H); m.solid(W // 2 + 20, H - 14, W, H)


def torches(m, pts):
    for (x, y) in pts:
        kit.torch(m, x, y, light=4.6)


def pillar(m, x, y, kind=None):
    m.model("pillar", town.pillar(2.2), x, y, box=(-7, -11, 7, 0), kind=kind)


# (the ziggurat's three floors of rooms are in zig_maps.py; the summit is the only hall left here)


def zig_3():
    """The summit: an open platform at the top of the ziggurat, the sanctuary wall behind the
    sleeping god, low parapets on three sides and beyond them a long drop into the night, the
    city a scatter of embers far below."""
    TW, TH = 30, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("zig_3", TW, TH, (36, 22, 32, 255), music="summit")
    E, wall_h, P = 40, 64, 12          # drop beyond the edge, sanctuary wall height, parapet thickness
    T = m.lay(seed=101)
    plat = T.rect(E, wall_h, W - 2 * E, H - wall_h - 24)
    # the sky god's floor is the sky: deep glazed blue, gold stars let into it
    T.tiles(T.all(), seed=102, size=24, ramp='night', base=3.3, jitter=0.9)
    T.stars(T.all(), seed=103, size=24, density=0.42)
    band = T.rect(E + P + 8, wall_h + 10, W - 2 * E - 2 * P - 16, H - wall_h - 24 - P - 18) & ~T.rect(E + P + 12, wall_h + 14, W - 2 * E - 2 * P - 24, H - wall_h - 24 - P - 26)
    T.put(band, 'gold', np.full((H, W), 3.4) + ((T.xx + T.yy) % 8 < 4) * 0.8, 1.3)
    T.carpet(T.rect(W // 2 - 12, 262, 24, H - 262 - 24), seed=3)
    T.contact(E, 0, W - E, wall_h, reach=7, strength=1.6)
    g = m.bake()
    # beyond the platform: the night, and the city far below
    sky = Canvas(W, H)
    G.night_drop(sky, 0, 0, W, H, seed=111)
    out = np.ones((H, W), bool); out[0:H - 24, E:W - E] = False
    g.a[out] = sky.a[out]
    m.ground_n[out] = (128, 128, 255, 1)
    A.sigil(g, W // 2, 230, 26)
    m.set_into_ground(town.temple_wall((W - 2 * E) / 16.0, h=wall_h / 16.0 - 0.25, d=0.25), E, wall_h)
    # parapets, crenellated against the sky
    m.set_into_ground(town.parapet_ns((H - wall_h - 24) / 16.0, inner='right'), E, H - 24)
    m.set_into_ground(town.parapet_ns((H - wall_h - 24) / 16.0, inner='left'), W - E - P, H - 24)
    m.set_into_ground(town.parapet_ew((W // 2 - 20 - E - P) / 16.0), E + P, H - 24)
    m.set_into_ground(town.parapet_ew((W // 2 - 20 - E - P) / 16.0), W // 2 + 20, H - 24)
    # the stair down through the gap, falling away into the dark
    lime = R['lime']; gd = R['gold']
    for k in range(H - 24 - P, H):
        t = (k - (H - 24 - P)) / (24 + P)
        c = lime[3] if (k - (H - 24 - P)) % 4 == 0 else lime[2] if t < 0.45 else lime[1] if t < 0.8 else (14, 10, 24, 255)
        g.hline(W // 2 - 18, W // 2 + 17, k, c)
    for sx in (W // 2 - 20, W // 2 + 18):
        g.vline(sx, H - 24 - P, H - 1, gd[3]); g.vline(sx + 1, H - 24 - P, H - 1, gd[4] if sx < W // 2 else gd[2])
    # nothing walks off the summit
    m.solid(0, 0, W, wall_h - 4)
    m.solid(0, 0, E + P - 2, H); m.solid(W - E - P + 2, 0, W, H)
    m.solid(0, H - 24 - P + 2, W // 2 - 20, H); m.solid(W // 2 + 20, H - 24 - P + 2, W, H)
    m.marker("god", W // 2 - 10, 126)
    m.marker("altar", W // 2 + 64, 132)
    m.marker("boss", W // 2, 212)
    for (x, y) in ((118, 190), (W - 118, 190), (118, 300), (W - 118, 300)):
        pillar(m, x, y, kind="pillar")
    torches(m, ((72, 150), (W - 72, 150), (72, 318), (W - 72, 318)))
    m.light(W // 2, 120, 7.0, (0.62, 0.70, 1.0), 0.45, flicker=False)
    m.spawn("south", W // 2, H - 26, "up")
    m.exit(W // 2 - 20, H - 8, W // 2 + 20, H, "zig_hi", "top")
    m.save()


if __name__ == "__main__":
    which = sys.argv[1:] or ["temple_yard", "zig_3"]
    for w in which:
        globals()[w]()
