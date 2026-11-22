"""Chapter two: the Hill of Sleepers. The road of the dead climbing from the hill gate past the
small tombs, the hilltop where the great tombs stand round the king's, and the three halls of
the tomb of Kurashtar, who has not slept in four hundred years.
  python3 necro_maps.py [map ...]"""
import sys, math
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from scipy import ndimage
from px import Canvas, R
from forge import hash2, fbm
import region_art as G
import town
import necro
import kit
from mapkit import MapBuilder

C = 8
BLANK = "~~In the dream the stone is smooth and blank.^Nobody is under it to say otherwise."
EPITAPHS = [
    "The stone reads:^{g}'HE ROSE EVERY DAY OF HIS LIFE. NOT TODAY.'{/}",
    "The stone reads:^{g}'ENBI-ISHTAR. OWED NOTHING. OWNED LESS.'{/}",
    "The stone reads:^{g}'TO MY HUSBAND. I TOLD YOU SO.'{/}",
    "The stone reads:^{g}'SHE KNEW WHERE EVERYTHING WAS.'{/}| Under it, in another hand: {g}'NOW NOBODY DOES.'{/}",
    "The stone begins, in a careful hand: {g}'KUBABA, BELOVED...'{/}^The rest has been eaten. There are tooth marks.",
    "The stone reads:^{g}'PLOT RESERVED. DO NOT BE BURIED HERE.'{/}",
    "The stone reads:^{g}'HE COLLECTED TAXES. HE IS STILL OWED.'{/}",
    "The stone reads:^{g}'SHE SAID SHE WOULD ONLY BE A MINUTE.'{/}",
    "The stone reads:^{g}'A NIGHT WATCHMAN. HE NEVER ONCE SLEPT ON DUTY.'{/}| {g}'HE IS MAKING UP FOR IT.'{/}",
    "The stone reads:^{g}'I WAS NOT TIRED.'{/}",
    "The stone reads:^{g}'ASK ME ABOUT MY SONS.'{/}| Lower down, smaller: {g}'ON SECOND THOUGHT, DON'T.'{/}",
    "The stone reads:^{g}'LUGAL-ME, WHO WAS RIGHT ABOUT THE WELL.'{/}",
]


def epitaph(i):
    return EPITAPHS[i % len(EPITAPHS)] + BLANK


# what a man hears with his ear to a tomb door: awake ~~ in the dream ~~ after the dawn
QUIET = "~~In the dream there is nobody behind the door.^The dead don't dream. Asleep, the hill is very quiet."
SNORE = "~~Snoring.^From behind every door on the hill, at last: snoring."
DOORS = [
    "A brick vault with a moon over the door.^Inside, somebody is sweeping. They have had forty nights to get it nice.",
    "Through the door, very faintly: counting.| {g}'...nine thousand and six. Nine thousand and seven.'{/}^Sheep, probably.",
    "A stepped tomb, built a little taller than its neighbours on purpose.^The neighbours have noticed.",
    "From inside: an argument, in whispers, about whose turn it is to lie on the left.",
    "Quiet. Either nobody is in, or somebody in there is managing it.^You resent them a little.",
    "A rich man's tomb. The offering table is laid for one.^Nobody has had the heart to tell him.",
    "Knocking, from inside. Not to be let out.^Just checking that somebody is there.",
    "On the door, in chalk: {g}'BACK IN FIVE MINUTES.'{/}^The dust on it is forty nights deep.",
    "Inside, somebody is reading aloud to somebody else.^Neither of them is enjoying it.",
    "A small sound behind the door, over and over.^Somebody is plumping a pillow that has been stone for three hundred years.",
    "Behind the door, a long sigh.| Then, after a while, another one, from someone else, as if in answer.",
]
BARROWS_SAY = [
    "The barrow of the house of Dur. The door has been kicked open from the inside.",
    "A barrow. Somebody has scratched on the lintel: {g}'DO NOT KNOCK. I AM TRYING.'{/}",
    "A great round barrow. From deep inside, a slow tune, hummed flat.^It might be a lullaby. It isn't working.",
    "A small barrow, grass gone to straw. From inside: the click of someone counting on their fingers, and losing count.",
]
COFFIN = ("A stone coffin, lid on.^From inside, the sound of fingers drumming."
          "~~In the dream it is only a stone box.~~A stone coffin, lid on.^From inside: nothing at all. Bliss.")
COFFIN_OPEN = ("An empty coffin, the lid pushed off.^Its owner has gone for a walk. Forty nights ago."
               "~~In the dream it is only a stone box.~~The lid is back on.^Somebody came home.")


def door(i):
    return DOORS[i % len(DOORS)] + QUIET + SNORE


def barrow(i):
    return BARROWS_SAY[i % len(BARROWS_SAY)] + QUIET + SNORE


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


def cells(mask):
    """A pixel mask as collision cells: a cell is taken when most of it is."""
    H, W = mask.shape
    return mask.reshape(H // C, C, W // C, C).mean((1, 3)) > 0.5


# ------------------------------------------------------------------ the fall from the hill
def hill_fall(W, H, seed):
    """What lies off the edge of the hill: night all the way down, mist lying in it in banks,
    the fires of the sleeping city a long way under."""
    yy, xx = np.mgrid[0:H, 0:W]
    v = fbm(xx / 74.0, yy / 30.0, seed, 3) * 0.72 + fbm(xx / 21.0 + 9.1, yy / 9.0, seed + 5, 2) * 0.28
    cols = np.array([(6, 8, 20), (9, 12, 28), (14, 18, 40), (22, 27, 56), (33, 40, 76), (47, 56, 98)], float)
    lv = np.clip((v - 0.33) / 0.36, 0, 0.999) * len(cols)
    rgb = cols[np.floor(lv).astype(int)]
    h = hash2(xx, yy, seed + 9)
    clear = v < 0.44
    rgb[clear & (h > 0.9972)] = (255, 176, 84)
    rgb[clear & (h > 0.9945) & (h <= 0.9972)] = (168, 100, 60)
    out = np.zeros((H, W, 4), np.uint8); out[..., :3] = rgb; out[..., 3] = 255
    return out


def coast(T, land, seed=0, width=9):
    """The lip of the hill: bare rock where the ground gives out."""
    d = ndimage.distance_transform_edt(land)
    band = land & (d < width + (fbm(T.xx / 14.0, T.yy / 14.0, seed, 2) - 0.5) * 9)
    T.rock(band, seed=seed + 1, base=3.3)
    return band


def fall(m, g, land, seed, face=15):
    """Everything off the land becomes the fall; under every edge that faces us, the rock of the
    hill going down into it."""
    H, W = land.shape
    void = ~land
    g.a[void] = hill_fall(W, H, seed)[void]
    yy, xx = np.mgrid[0:H, 0:W]
    depth = np.zeros((H, W), int)
    for k in range(1, face + 1):
        sh = np.zeros_like(land); sh[k:] = land[:-k]
        hit = sh & void & (depth == 0)
        depth[hit] = k
    stop = face - 8 + (hash2(xx // 2, xx * 0, seed + 4) * 5).astype(int) + (fbm(xx / 9.0, xx * 0.0, seed + 8, 2) * 6).astype(int)
    on = (depth > 0) & (depth <= stop)
    rock = np.array([(86, 86, 104), (64, 65, 84), (48, 49, 68), (35, 36, 54), (25, 26, 42), (17, 18, 31)], float)
    lv = np.clip((depth - 1) * len(rock) // face + (hash2(xx // 4, depth // 4, seed + 3) > 0.6), 0, len(rock) - 1)
    g.a[on, :3] = rock[lv[on]]
    seam = on & (hash2(xx // 5, xx * 0, seed + 6) > 0.72) & (hash2(xx // 5 + 1, xx * 0, seed + 6) <= 0.72) & (depth > 1)
    g.a[seam, :3] = (16, 16, 28)
    # a dark line where land meets nothing, so the edge reads
    rim = land & ndimage.binary_dilation(void)
    g.a[rim, :3] = (g.a[rim, :3] * 0.5).astype(np.uint8)
    m.ground_n[void] = (128, 128, 255, 1)
    return void


def plot(T, x, y, w, h, seed=0):
    """Turned earth where the plain graves are: darker than the hill round it."""
    mask = T.ragged(T.rect(x, y, w, h), 3, 9, seed=seed)
    T.earth(mask, seed=seed + 1, base=2.7, ramp='ash', pebbles=0.02)
    return mask


# ------------------------------------------------------------------ the road of the dead
ROAD = [(320, 704), (316, 600), (250, 520), (200, 450), (230, 372), (420, 330), (452, 250), (400, 170), (320, 110), (320, 0)]


def necro_road():
    TW, TH = 40, 44
    W, H = TW * 16, TH * 16
    m = MapBuilder("necro_road", TW, TH, (10, 12, 28, 255), music="hill")
    T = m.lay(seed=201)
    land = T.ragged(T.rect(52, 70, W - 104, H), 15, 52, seed=31) | T.ragged(T.rect(-30, -30, W + 60, 126), 9, 34, seed=30) | T.rect(40, H - 26, W - 80, 26)
    land &= ~T.ragged(T.disc(0, 400, 86, 70) | T.disc(W, 560, 78, 80), 6, 18, seed=32)
    T.earth(T.all(), seed=1, base=3.3, ramp='ash', pebbles=0.014)
    T.grass(T.ragged(T.disc(170, 560, 80, 44) | T.disc(500, 400, 60, 30) | T.disc(250, 200, 84, 34) | T.disc(520, 120, 54, 40) | T.disc(110, 330, 50, 40), 5, 10, seed=4),
            seed=5, ramp='sere', base=2.7, tufts=0.07)
    T.rock(T.ragged(T.disc(112, 246, 54, 40), 5, 12, seed=2), seed=3, base=3.3)
    coast(T, land, seed=33)
    road = T.ragged(T.stroke(ROAD, 30), 3, 8, seed=6)
    T.slabs(road, seed=7, rows=(10, 11), wmin=10, wmax=18, ramp='pale', base=3.3, jitter=1.0, crack=0.12, moss=0.0, wear=0.6)
    side = T.ragged(T.stroke([(230, 372), (160, 320), (118, 268)], 15) | T.stroke([(420, 330), (480, 400), (500, 440)], 15), 3, 7, seed=8)
    T.earth(side & ~road, seed=9, base=4.2, ramp='ash', pebbles=0.01)
    plots = ((176, 544, 96, 62, 41), (410, 500, 74, 84, 42), (286, 396, 70, 44, 43), (236, 170, 100, 60, 44), (60, 120, 62, 70, 45))
    for (x, y, w, h, sd) in plots:
        plot(T, x, y, w, h, sd)
    TOMBS = [('vault', 122, 640, 5.0, 2.8, 1.5, 0, True), ('flat', 508, 652, 5.5, 2.8, 1.6, 1, False), ('step', 548, 520, 4.5, 2.8, 1.4, 2, False),
             ('vault', 176, 150, 5.5, 2.8, 1.6, 6, True), ('flat', 490, 132, 4.5, 2.4, 1.4, 7, False)]
    BARROWS = [(104, 476, 2.0, 3, True), (540, 268, 2.2, 4, False)]
    for (st, x, y, w, d, h, sd, lamp) in TOMBS:
        T.contact(x - w * 8, y - d * 16, x + w * 8, y, reach=5, strength=1.4)
    for (x, y, r, sd, lamp) in BARROWS:
        T.contact(x - r * 14, y - r * 30, x + r * 14, y - 4, reach=6, strength=1.3)
    g = m.bake()
    void = fall(m, g, land, 203)
    pit_boxes(m, cells(void), 0)
    # the rock the hilltop stands on, across the top, and the way up through it
    m.set_into_ground(town.cliff(286 / 16.0, h=2.2, seed=51, grass=False, rock='stone'), 0, 60, seed=51)
    m.set_into_ground(town.cliff((W - 354) / 16.0, h=2.2, seed=52, grass=False, rock='stone'), 354, 60, seed=52)
    m.solid(0, 0, 286, 62); m.solid(354, 0, W, 62)
    kit.standard(m, 278, 84); kit.standard(m, 362, 84)
    for i, (st, x, y, w, d, h, sd, lamp) in enumerate(TOMBS):
        kit.tomb(m, x, y, w, d, h, sd, st, lamp, text=door(i))
    for i, (x, y, r, sd, lamp) in enumerate(BARROWS):
        kit.tumulus(m, x, y, r, sd, lamp, text=barrow(i))
    # the wall the queue stands in the gap of: field stone right across the hill
    m.model("nr_wall_w", town.drystone((394 - 44) / 16.0, h=1.1, seed=11), 44, 300, box=None)
    m.model("nr_wall_e", town.drystone((W - 44 - 446) / 16.0, h=1.1, seed=12), 446, 300, box=None)
    m.solid(0, 290, 394, 300); m.solid(446, 290, W, 300)
    m.solid(394, 286, 446, 300, 1)            # the dead in the gap: there in the waking world, not in the dream
    kit.standard(m, 386, 308); kit.standard(m, 454, 308)
    # the plain graves
    kit.graves(m, 186, 566, 4, 2, seed=1); kit.graves(m, 420, 524, 3, 3, seed=2); kit.graves(m, 296, 418, 3, 1, seed=3)
    kit.graves(m, 246, 192, 4, 2, seed=4); kit.graves(m, 70, 144, 2, 2, seed=5)
    # stones with things to say
    kit.stele(m, 112, 244, 0, uid="stele_kur", text="stele")
    kit.standard(m, 88, 250)
    for i, (x, y) in enumerate(((270, 620), (368, 530), (160, 420), (476, 290), (364, 150), (270, 104))):
        kit.stele(m, x, y, i + 1, text=epitaph(i))
    for (x, y) in ((286, 650), (350, 566), (226, 476), (252, 336), (474, 232), (372, 126)):
        kit.spirit_lamp(m, x, y)
    for i, (x, y) in enumerate(((84, 560), (566, 590), (96, 384), (572, 430), (236, 262), (420, 76), (206, 76), (572, 160), (76, 196))):
        kit.dead_tree(m, x, y, i)
    for sd, (x, y) in enumerate(((204, 676), (436, 600), (150, 306), (510, 550), (414, 226), (96, 110))):
        kit.rock(m, x, y, sd)
    for i, (x, y) in enumerate(((240, 650), (470, 470), (130, 400), (556, 348), (310, 250), (200, 110), (530, 84), (382, 440))):
        kit.thorn(m, x, y, i)
    for i, (x, y) in enumerate(((158, 646), (468, 660), (90, 500), (300, 470), (510, 200), (214, 160), (450, 140))):
        kit.urn(m, x, y, i)
    for i, (x, y) in enumerate(((400, 640), (150, 350), (340, 216), (560, 400))):
        kit.bones(m, x, y, i)
    m.model("offer_a", town.offering_table(1), 156, 500, box=(-12, -10, 12, 0))
    m.model("offer_b", town.offering_table(2, food=False), 486, 452, box=(-12, -10, 12, 0))
    # the gate from the terraces: two posts and a wall of field stone along the foot of the hill
    kit.gate_post(m, 284, H - 4); kit.gate_post(m, 356, H - 4)
    m.model("nr_foot_w", town.drystone((272 - 44) / 16.0, h=0.9, seed=13), 44, H - 2, box=None)
    m.model("nr_foot_e", town.drystone((W - 44 - 368) / 16.0, h=0.9, seed=14), 368, H - 2, box=None)
    m.solid(0, H - 12, 296, H); m.solid(344, H - 12, W, H)
    m.marker("npc", 350, 640, who="namtar")
    m.marker("npc", 148, 512, who="gran_dur")
    m.marker("npc", 504, 462, who="belu")
    m.marker("npc", 520, 300, who="goat_tomb")
    for i, x in enumerate((402, 414, 426, 438)):
        m.marker("npc", x, 296, who=f"queue_{i}")
    for i, (x, y) in enumerate(((150, 270), (96, 330), (300, 224), (520, 180))):
        m.enemy("unremembered", x, y, f"nr_u{i}")
    for i, (x, y) in enumerate(((420, 470), (220, 520), (330, 262))):
        m.enemy("scarab", x, y, f"nr_s{i}")
    m.spawn("south", 320, H - 30, "up")
    m.spawn("north", 320, 86, "down")
    m.exit(296, H - 8, 344, H, "terraces", "hill")
    m.exit(296, 44, 344, 58, "necropolis", "south")
    m.save()


# ------------------------------------------------------------------ the hilltop
HILL_BRIDGE = [(540, 256), (584, 256), (628, 256)]


def necropolis():
    TW, TH = 48, 40
    W, H = TW * 16, TH * 16
    m = MapBuilder("necropolis", TW, TH, (10, 12, 28, 255), music="hill")
    T = m.lay(seed=211)
    land = T.ragged(T.rect(46, 60, W - 92, H), 14, 56, seed=35) | T.ragged(T.rect(-30, -30, W + 60, 174), 9, 34, seed=34) | T.rect(40, H - 26, W - 80, 26)
    cleft = T.ragged(T.disc(664, 256, 112, 96) | T.rect(690, 176, 90, 160), 7, 22, seed=36)
    isle = T.ragged(T.disc(664, 262, 34, 50), 3, 10, seed=37)
    land = (land & ~cleft) | isle
    T.earth(T.all(), seed=1, base=3.3, ramp='ash', pebbles=0.014)
    T.grass(T.ragged(T.disc(130, 190, 104, 66) | T.disc(660, 540, 76, 56) | T.disc(100, 540, 66, 50) | T.disc(430, 250, 44, 30), 5, 12, seed=2),
            seed=3, ramp='sere', base=2.7, tufts=0.07)
    coast(T, land, seed=38)
    T.rock(isle, seed=39, base=3.5)
    # the avenue from the gate up to the king's door, and the court in front of it
    avenue = T.rect(364, 188, 40, H - 188)
    court = T.rect(272, 118, 224, 74)
    T.slabs(avenue | court, seed=4, rows=(12,), wmin=16, wmax=20, ramp='pale', base=3.4, jitter=0.9, crack=0.1, whole=False, wear=0.6)
    T.border(court, 'lapis', 3.0, 2, 1.2)
    # the court of the game, east of the avenue
    game = T.rect(474, 400, 144, 92)
    T.slabs(game, seed=5, rows=(10, 11), wmin=12, wmax=18, ramp='flag', base=3.3, moss=0.0, whole=False)
    T.border(game, 'pale', 4.2, 1, 1.1)
    for (x, y, w, h, sd) in ((56, 372, 84, 78, 46), (612, 500, 98, 62, 47), (420, 214, 66, 58, 48)):
        plot(T, x, y, w, h, sd)
    TOMBS = [('flat', 190, 338, 6.5, 3.0, 1.8, 11, True), ('vault', 176, 482, 6.0, 2.8, 1.7, 12, False), ('step', 300, 612, 4.5, 2.8, 1.4, 14, False),
             ('vault', 566, 612, 6.0, 2.8, 1.7, 15, True), ('step', 690, 448, 4.5, 2.8, 1.4, 17, False), ('flat', 480, 330, 5.0, 2.6, 1.6, 16, False)]
    BARROWS = [(150, 598, 2.4, 13, True), (276, 440, 1.8, 18, True)]
    for (st, x, y, w, d, h, sd, lamp) in TOMBS:
        T.contact(x - w * 8, y - d * 16, x + w * 8, y, reach=5, strength=1.4)
    for (x, y, r, sd, lamp) in BARROWS:
        T.contact(x - r * 14, y - r * 30, x + r * 14, y - 4, reach=6, strength=1.3)
    T.contact(0, 0, W, 108, reach=9, strength=1.7)
    g = m.bake()
    void = fall(m, g, land, 213)
    vc = cells(void)
    cols, rows = W // C, H // C
    road = np.zeros_like(vc)
    for r_ in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r_ * C + 4
            if HILL_BRIDGE[0][0] - 8 <= x <= HILL_BRIDGE[-1][0] + 8 and abs(y - HILL_BRIDGE[0][1]) <= 10:
                road[r_, c] = True
    road &= vc
    pit_boxes(m, vc & ~road, 0)
    pit_boxes(m, road, 1)
    xs = [p[0] for p in HILL_BRIDGE]; ys = [p[1] for p in HILL_BRIDGE]
    bx0, by0, bx1, by1 = min(xs) - 12, min(ys) - 12, max(xs) + 12, max(ys) + 12
    def bridge_draw(cv, ax, ay, fi):
        G.moon_bridge(cv, [(p[0] - bx0, p[1] - by0) for p in HILL_BRIDGE], 16, fi)
    m.prop("moon_bridge_hill", bridge_draw, bx0, by0, layer=2, size=(bx1 - bx0, by1 - by0), anchor=(0, 0), pad=0)
    m.light(584, 256, 5.0, (0.55, 0.62, 1.0), 0.45, flicker=False, h=0.4)
    # the rock the king's tomb is cut into, right across the top, and the front of it in the middle
    m.set_into_ground(town.cliff(304 / 16.0, h=4.2, seed=61, grass=False, rock='stone'), 0, 108, seed=61)
    m.set_into_ground(town.cliff((W - 464) / 16.0, h=4.2, seed=62, grass=False, rock='stone'), 464, 108, seed=62)
    m.set_into_ground(necro.royal_front(10.0, 4.6), 384, 110, seed=63)
    m.solid(0, 0, 352, 104); m.solid(416, 0, W, 104); m.solid(352, 0, 416, 86)      # the doorway itself is the door's to close
    m.solid(304, 104, 352, 114); m.solid(416, 104, 464, 114)
    m.model("king_door", necro.king_door(), 384, 110, box=(-34, -8, 34, 0), kind="gate", data={"id": "king_door"}, shadow=False)
    m.model("king_door_open", necro.king_door(open_=True), -100, -100, box=None, lights=False, shadow=False)
    m.light(384, 92, 4.0, (1.0, 0.8, 0.42), 0.35, flicker=False, h=2.6)
    m.model("lamassu_w", town.lamassu(False, 1.25), 252, 156, box=(-30, -20, 30, 0))
    m.model("lamassu_e", town.lamassu(True, 1.25), 516, 156, box=(-30, -20, 30, 0))
    kit.spirit_bowl(m, 316, 148); kit.spirit_bowl(m, 452, 148)
    kit.standard(m, 348, 200); kit.standard(m, 420, 200)
    # the gate from the road: two posts and a wall of field stone
    kit.gate_post(m, 348, H - 4); kit.gate_post(m, 420, H - 4)
    m.model("np_wall_w", town.drystone((336 - 44) / 16.0, h=0.9, seed=21), 44, H - 2, box=None)
    m.model("np_wall_e", town.drystone((W - 44 - 432) / 16.0, h=0.9, seed=22), 432, H - 2, box=None)
    m.solid(0, H - 12, 360, H); m.solid(408, H - 12, W, H)
    for i, (st, x, y, w, d, h, sd, lamp) in enumerate(TOMBS):
        kit.tomb(m, x, y, w, d, h, sd, st, lamp, text=door(i + 5))
    for i, (x, y, r, sd, lamp) in enumerate(BARROWS):
        kit.tumulus(m, x, y, r, sd, lamp, text=barrow(i + 2))
    # the garden of the dead: bare trees, two fire altars that have gone out, and the stone they used to light
    for i, (x, y) in enumerate(((70, 168), (116, 224), (200, 152), (236, 232), (66, 262), (156, 280))):
        kit.dead_tree(m, x, y, i + 2)
    kit.stele(m, 134, 182, 1, uid="stele_tar", text="stele")
    kit.brazier(m, 104, 194, False, "garden_0")
    kit.brazier(m, 164, 194, False, "garden_1")
    kit.brazier_frames(m)
    # the stone on the island, and what somebody left with it
    kit.stele(m, 664, 240, 2, uid="stele_ash", text="stele")
    kit.chest(m, 664, 290, "isle_vessel", "vessel")
    # graves, stones, lamps along the avenue
    kit.graves(m, 66, 392, 3, 2, seed=6); kit.graves(m, 622, 520, 4, 2, seed=7); kit.graves(m, 430, 234, 2, 1, seed=8)
    for i, (x, y) in enumerate(((330, 560), (438, 560), (330, 440), (438, 440), (330, 320), (438, 320), (330, 240), (438, 240))):
        if i % 2 == 0: kit.spirit_lamp(m, x, y)
        else: kit.stele(m, x, y, i, text=epitaph(6 + i // 2))
    # the court of the game: four columns that held a roof once, the board, two seats
    for i, (x, y) in enumerate(((484, 416), (606, 416), (484, 488), (606, 488))):
        m.model(f"col_{i % 2}", necro.broken_column(1.4 - 0.5 * (i % 2), i, fallen=(i == 1)), x, y, box=(-5, -9, 5, -1))
    m.model("game_board", town.game_board(), 546, 452, box=(-8, -10, 8, 0), kind="look", data={"id": "game_board"})
    m.model("stone_seat", necro.stone_seat(), 520, 452, box=(-5, -8, 5, 0))
    m.model("stone_seat", necro.stone_seat(), 572, 452, box=(-5, -8, 5, 0))
    m.model("offer_c", town.offering_table(3), 262, 352, box=(-12, -10, 12, 0))
    m.model("offer_d", town.offering_table(4, food=False), 640, 624, box=(-12, -10, 12, 0))
    for sd, (x, y) in enumerate(((66, 330), (700, 356), (440, 620), (604, 146))):
        kit.rock(m, x, y, sd + 3)
    for i, (x, y) in enumerate(((704, 560), (60, 590), (520, 560), (560, 172))):
        kit.dead_tree(m, x, y, i)
    for i, (x, y) in enumerate(((240, 290), (104, 470), (520, 250), (620, 380), (230, 560), (470, 590), (86, 300), (590, 200))):
        kit.thorn(m, x, y, i)
    for i, (x, y) in enumerate(((236, 346), (120, 492), (444, 344), (620, 624), (340, 624), (724, 460), (512, 512))):
        kit.urn(m, x, y, i)
    for i, (x, y) in enumerate(((300, 270), (580, 340), (90, 470))):
        kit.bones(m, x, y, i)
    m.marker("npc", 527, 453, who="general_a")
    m.marker("npc", 565, 453, who="general_b")
    m.marker("npc", 250, 530, who="poet")
    m.marker("npc", 300, 172, who="doorman")
    m.marker("npc", 420, 590, who="goat_hill")
    for i, (x, y) in enumerate(((110, 300), (240, 400), (640, 580), (540, 230), (90, 300), (210, 290))):
        m.enemy("unremembered", x, y, f"np_u{i}")
    for i, (x, y) in enumerate(((560, 540), (310, 500), (110, 440))):
        m.enemy("scarab", x, y, f"np_s{i}")
    m.spawn("south", 384, H - 30, "up")
    m.spawn("door", 384, 138, "down")
    m.exit(360, H - 8, 408, H, "necro_road", "north")
    m.exit(366, 88, 402, 106, "tomb_1", "south", need="king_door")
    m.save()


# ------------------------------------------------------------------ inside the tomb
def floor(m, W, H, wall_h=48, seed=300, door=True):
    """A hall of the tomb: black flags worn grey down the middle, a line of gold and blue let in
    round the edge, the tops of the walls round it."""
    T = m.lay(seed=seed)
    T.slabs(T.all(), seed=seed, rows=(16,), wmin=20, wmax=28, ramp='basalt', base=4.0, jitter=1.0, crack=0.14, whole=False, wear=0.6)
    inner = T.rect(34, wall_h + 12, W - 68, H - wall_h - 40)
    line = inner & ~T.rect(36, wall_h + 14, W - 72, H - wall_h - 44)
    T.put(line, 'gold', np.full((H, W), 2.6), 1.2)
    line2 = T.rect(38, wall_h + 16, W - 76, H - wall_h - 48) & ~T.rect(41, wall_h + 19, W - 82, H - wall_h - 54)
    T.put(line2, 'lapis', np.full((H, W), 2.4) + ((T.xx + T.yy) % 6 < 3) * 0.8, 1.1)
    tops = T.rect(0, wall_h, 24, H - wall_h) | T.rect(W - 24, wall_h, 24, H - wall_h) | T.rect(24, H - 16, W - 48, 16)
    if door:
        gap = T.rect(W // 2 - 20, H - 16, 40, 16)
        tops &= ~gap
        T.slabs(gap, seed=seed + 7, rows=(8,), wmin=20, wmax=20, ramp='pale', base=3.2, whole=False, crack=0)
    T.walltop(tops, seed=seed + 1, ramp='flag', base=3.6)
    T.contact(0, 0, W, wall_h, reach=7, strength=1.6)
    T.contact(0, wall_h, 24, H, reach=5, strength=1.0)
    return T


def runner(T, x, y, w, h):
    """A runner of red wool with a gold edge, laid for a procession that came once."""
    mask = T.rect(x, y, w, h)
    tone = 2.6 + ((T.yy // 2) % 2) * 0.5 + ((T.xx // 3 + T.yy // 2) % 2) * 0.3
    T.put(mask, 'carpet', tone, np.full(tone.shape, 1.4))
    T.border(mask, 'gold', 3.0, 2, 1.5)


def walls(m, W, H, wall_h=48, portal=None, steps_to=None, door=True):
    m.set_into_ground(town.tomb_wall(W / 16.0, h=wall_h / 16.0 - 0.25, d=0.25, door_at=None if portal is None else portal / 16.0), 0, wall_h)
    if portal is not None and steps_to:
        run = (steps_to - wall_h) / 16.0
        rise = min(1.25, run * 0.42)
        m.set_into_ground(town.steps(2.5, n=6, rise=rise, run=run - rise), portal - 20, steps_to)
    m.solid(0, 0, W, wall_h - 4); m.solid(0, 0, 24, H); m.solid(W - 24, 0, W, H)
    if door:
        m.solid(0, H - 14, W // 2 - 20, H); m.solid(W // 2 + 20, H - 14, W, H)


def trench(m, g, W, H, y0, h, seed, bridge_x=None):
    """A cut right across a hall that the dead filled with dark: lays the fall, its far wall, and
    the collision (the strip under bridge_x is solid only when awake)."""
    sky = hill_fall(W, H, seed)
    box = np.zeros((H, W), bool); box[y0:y0 + h, 24:W - 24] = True
    g.a[box] = sky[box]
    yy, xx = np.mgrid[0:H, 0:W]
    face = box & (yy < y0 + 9)
    rock = np.array([(58, 54, 66), (46, 43, 56), (36, 33, 46), (27, 25, 37), (20, 18, 29), (14, 13, 22)], float)
    lv = np.clip((yy - y0) * len(rock) // 9, 0, len(rock) - 1)
    g.a[face, :3] = rock[lv[face]]
    joint = face & ((xx + ((yy - y0) // 3) * 9) % 18 == 0)
    g.a[joint, :3] = (14, 13, 22)
    g.a[y0 - 1, 24:W - 24, :3] = (g.a[y0 - 1, 24:W - 24, :3] * 0.55).astype(np.uint8)
    g.a[y0 + h, 24:W - 24, :3] = np.minimum(255, g.a[y0 + h, 24:W - 24, :3].astype(int) + 34).astype(np.uint8)
    m.ground_n[box] = (128, 128, 255, 1)
    cols, rows = W // C, H // C
    pit = np.zeros((rows, cols), bool); road = np.zeros_like(pit)
    for r_ in range(rows):
        for c in range(cols):
            x, y = c * C + 4, r_ * C + 4
            if 24 <= x < W - 24 and y0 <= y < y0 + h:
                pit[r_, c] = True
                if bridge_x is not None and abs(x - bridge_x) <= 12:
                    road[r_, c] = True
    pit_boxes(m, pit & ~road, 0)
    pit_boxes(m, road, 1)


def lamps(m, pts):
    for (x, y) in pts:
        kit.spirit_lamp(m, x, y, light=4.4)


def tomb_1():
    """The hall of servants: the king's clay soldiers in their niches, the robbers asleep where
    the sleep caught them, a wall the dead put up that only the waking world has, and the key
    on the far side of it."""
    TW, TH = 32, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("tomb_1", TW, TH, (12, 10, 18, 255), music="tomb")
    T = floor(m, W, H, seed=301)
    runner(T, 244, 210, 24, H - 226)
    runner(T, 244, 104, 24, 72)
    T.contact(24, 176, 236, 208, reach=5, strength=1.3); T.contact(276, 176, W - 24, 208, reach=5, strength=1.3)
    g = m.bake()
    walls(m, W, H, portal=256, steps_to=100)
    G.cobweb(g, 26, 52); G.cobweb(g, W - 27, 52, flip=True)
    m.set_into_ground(town.tomb_partition((236 - 24) / 16.0), 24, 208, seed=302)
    m.set_into_ground(town.tomb_partition((W - 24 - 276) / 16.0), 276, 208, seed=303)
    m.solid(24, 176, 236, 204); m.solid(276, 176, W - 24, 204)
    m.model("lockdoor", town.bronze_door(2.5, 1.9, 'lock'), 256, 206, box=(-20, -26, 20, 0), kind="lockdoor", data={"id": "t1_door"})
    # east: a walled bay, the key inside it, and in the one way through three of the king's servants,
    # dead and on duty, shoulder to shoulder. They are there in the waking world and not in the dream
    m.set_into_ground(town.tomb_partition_ns(92 / 16.0, h=0.9), 400, 300, seed=304)
    m.set_into_ground(town.tomb_partition(20 / 16.0, h=0.9), 408, 300, seed=305)
    m.set_into_ground(town.tomb_partition(20 / 16.0, h=0.9), 468, 300, seed=306)
    m.solid(400, 208, 408, 300); m.solid(408, 292, 428, 300); m.solid(468, 292, 488, 300)
    for i, x in enumerate((436, 448, 460)):
        m.marker("npc", x, 300, who=f"servant_{i}")
    m.solid(428, 290, 468, 302, 1)
    kit.chest(m, 448, 250, "t1_key", "key")
    # west: the robbers, asleep on their sacks
    m.model("loot", necro.treasure(1), 96, 300, box=(-12, -8, 12, 0), kind="look",
            data={"id": "say", "text": "Grave goods, bagged and ready to go.^They got this far forty nights ago. They have not got any further."})
    for (x, y) in ((70, 212), (176, 212), (336, 212)):
        m.model("sentinel_niche", necro.sentinel_niche(), x, y, box=None)
    lamps(m, ((150, 334), (362, 334), (150, 120), (362, 120)))
    lamps(m, ((420, 228), (476, 228)))
    m.model("sarcophagus", necro.sarcophagus(1), 180, 344, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": COFFIN})
    m.model("sarcophagus_open", necro.sarcophagus(2, True), 326, 290, box=(-16, -14, 16, 0), kind="look", data={"id": "say", "text": COFFIN_OPEN})
    m.model("sarcophagus", necro.sarcophagus(1), 110, 140, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": COFFIN})
    m.model("sarcophagus", necro.sarcophagus(1), 420, 140, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": COFFIN})
    for i, (x, y) in enumerate(((44, 250), (474, 340), (44, 110), (474, 108), (300, 236))):
        kit.urn(m, x, y, i)
    m.marker("npc", 70, 326, who="robber_a")
    m.marker("npc", 124, 334, who="robber_b")
    m.enemy("ushabti", 300, 320, "t1_g1", once=True)
    m.enemy("ushabti", 200, 140, "t1_g2", once=True)
    for i, (x, y) in enumerate(((200, 280), (350, 340))):
        m.enemy("scarab", x, y, f"t1_s{i}")
    m.spawn("south", 256, H - 26, "up")
    m.spawn("top", 256, 124, "down")
    m.exit(236, H - 8, 276, H, "necropolis", "door")
    m.exit(240, 64, 272, 80, "tomb_2", "south")
    m.save()


def tomb_2():
    """The hall of the lyre: a trench cut right across it that the dead filled with dark, four fire
    altars to light, the queen's lyre, and beyond them the door to the king."""
    TW, TH = 32, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("tomb_2", TW, TH, (12, 10, 18, 255), music="tomb")
    T = floor(m, W, H, seed=311)
    runner(T, 244, 262, 24, H - 278)
    runner(T, 244, 84, 24, 90)
    g = m.bake()
    py_, ph = 196, 44
    trench(m, g, W, H, py_, ph, 313, bridge_x=180)
    bx0, by0, bx1, by1 = 168, py_ - 10, 192, py_ + ph + 10
    def bridge_draw(cv, ax, ay, fi):
        G.moon_bridge(cv, [(12, 6), (12, by1 - by0 - 6)], 16, fi)
    m.prop("moon_bridge_tomb", bridge_draw, bx0, by0, layer=2, size=(bx1 - bx0, by1 - by0), anchor=(0, 0), pad=0)
    walls(m, W, H, portal=256, steps_to=76)
    G.cobweb(g, 26, 52); G.cobweb(g, W - 27, 52, flip=True)
    # four fire altars for the dead, out: two this side of the trench, two the other
    for i, (x, y) in enumerate(((120, 300), (392, 300), (120, 150), (392, 150))):
        kit.brazier(m, x, y, False, f"lyre_{i}")
    kit.brazier_frames(m)
    m.model("lyre", town.lyre(), 330, 156, box=(-10, -8, 12, 0), kind="look", data={"id": "lyre"})
    m.model("sealdoor", town.bronze_door(2.5, 2.0, 'sun'), 256, 76, box=(-20, -26, 20, 0), kind="gate", data={"id": "t2_seal"})
    kit.chest(m, 420, 336, "t2_coins", "shekels:40")
    m.model("sarcophagus", necro.sarcophagus(1), 84, 344, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": COFFIN})
    m.model("sarcophagus", necro.sarcophagus(1), 440, 116, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": COFFIN})
    m.model("treasure_3", necro.treasure(3), 76, 116, box=(-12, -8, 12, 0))
    lamps(m, ((60, 262), (452, 262), (200, 110), (312, 110)))
    for i, (x, y) in enumerate(((44, 300), (470, 300), (44, 150), (300, 330))):
        kit.urn(m, x, y, i + 1)
    m.marker("npc", 404, 300, who="robber_c")
    m.enemy("ushabti", 150, 330, "t2_g1", once=True)
    m.enemy("ushabti", 360, 120, "t2_g2", once=True)
    m.enemy("ushabti", 150, 120, "t2_g3", once=True)
    m.spawn("south", 256, H - 26, "up")
    m.spawn("top", 256, 96, "down")
    m.exit(236, H - 8, 276, H, "tomb_1", "top")
    m.exit(240, 44, 272, 58, "tomb_3", "south", need="door_t2_seal")
    m.save()


def sun_floor(T, cx, cy, r, sq=1.16):
    """The sun let into the floor of the king's chamber in gold, blue and red stone: he had it
    put where he could see it, since he was not going to see the other one again."""
    dx = T.xx - cx; dy = (T.yy - cy) * sq
    d = np.hypot(dx, dy); ang = np.arctan2(dy, dx)
    ring = lambda a, b: (d >= r * a) & (d < r * b)
    wedge = (np.floor(ang / (2 * math.pi) * 32 + 0.5) % 2)
    T.put(d < r, 'basalt', 3.2 + wedge * 0.9, 1.0)
    n = 16
    da = np.abs(((ang / (2 * math.pi) * n + 0.5) % 1.0) - 0.5) / n * 2 * math.pi
    t = np.clip((d - r * 0.36) / (r * 0.46), 0, 1)
    rays = ring(0.36, 0.82) & (da < 0.15 * (1 - t) + 0.012)
    T.put(rays, 'gold', np.full(d.shape, 2.9) + (d / r) * 0.8, 1.2)
    T.put(ring(0.84, 0.9), 'lapis', np.full(d.shape, 2.6) + ((np.floor(ang * 20) % 2) * 0.7), 1.1)
    T.put(ring(0.9, 0.94), 'gold', 3.0, 1.3)
    T.put(ring(0.94, 1.0), 'carpet', np.full(d.shape, 2.4) + ((np.floor(ang * 14) % 2) * 0.6), 1.1)
    T.put(ring(0.3, 0.36), 'carpet', 2.8, 1.1)
    T.put(d < r * 0.3, 'gold', np.full(d.shape, 3.4) - (d / (r * 0.3)) * 0.8, 1.3)


def tomb_3():
    """The king's chamber: the sun in the floor, the throne at the far end on its steps, his
    treasure down both sides, and nowhere to sit but the one seat."""
    TW, TH = 30, 24
    W, H = TW * 16, TH * 16
    m = MapBuilder("tomb_3", TW, TH, (12, 10, 18, 255), music="summit")
    T = floor(m, W, H, wall_h=64, seed=321)
    sun_floor(T, W // 2, 236, 88)
    runner(T, W // 2 - 12, 316, 24, H - 332)
    T.contact(W // 2 - 28, 66, W // 2 + 28, 106, reach=5, strength=1.2)
    g = m.bake()
    m.set_into_ground(town.tomb_wall(W / 16.0, h=64 / 16.0 - 0.25, d=0.25), 0, 64)
    m.solid(0, 0, W, 60); m.solid(0, 0, 24, H); m.solid(W - 24, 0, W, H)
    m.solid(0, H - 14, W // 2 - 20, H); m.solid(W // 2 + 20, H - 14, W, H)
    G.cobweb(g, 26, 68); G.cobweb(g, W - 27, 68, flip=True)
    m.model("throne", necro.throne(), W // 2, 106, box=(-27, -38, 27, 0), kind="look", data={"id": "throne"})
    for i, (x, y) in enumerate(((66, 128), (W - 66, 128), (58, 330), (W - 58, 330), (140, 100), (W - 140, 100))):
        m.model(f"treasure_{i % 4}", necro.treasure(i % 4), x, y, box=(-12, -8, 12, 0), kind="look",
                data={"id": "say", "text": "A king's treasure, heaped where the bearers set it down.^You are the night watch. You are the one man in Ashkel who can't."})
    for (x, y) in ((118, 176), (W - 118, 176), (118, 306), (W - 118, 306)):
        m.model("pillar", town.pillar(2.2), x, y, box=(-7, -11, 7, 0), kind="pillar")
    for (x, y) in ((70, 236), (W - 70, 236)):
        kit.spirit_bowl(m, x, y)
    lamps(m, ((186, 110), (W - 186, 110)))
    m.model("sarcophagus", necro.sarcophagus(1), 70, 96, box=(-16, -13, 16, 0), kind="look", data={"id": "say", "text": COFFIN})
    m.model("sarcophagus_open", necro.sarcophagus(2, True), W - 70, 90, box=(-16, -14, 16, 0), kind="look", data={"id": "say", "text": COFFIN_OPEN})
    m.marker("throne", W // 2, 88)
    m.marker("boss", W // 2, 220)
    m.marker("npc", 86, 318, who="robber_d")
    m.spawn("south", W // 2, H - 26, "up")
    m.exit(W // 2 - 20, H - 8, W // 2 + 20, H, "tomb_2", "top")
    m.save()


if __name__ == "__main__":
    which = sys.argv[1:] or ["necro_road", "necropolis", "tomb_1", "tomb_2", "tomb_3"]
    for name in which:
        globals()[name]()
