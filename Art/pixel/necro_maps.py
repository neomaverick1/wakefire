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
import hkit
import tombs
import bprops
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


# ------------------------------------------------------------------ the houses of the dead
IN_ROAD, IN_HILL = "necro_road_in", "necropolis_in"
THORN = 'bone'                  # what the hedges up here are made of: thorn, dead, white as a bone, and clipped all the same

# the stone by each door, that says who is behind it: (how far from the door it stands, the words)
STONES = {
    'nr_sweeper': (24, "The stone by the door reads:^{g}'AMAT. SHE KEPT A CLEAN HOUSE.'{/}| Somebody has swept round the foot of the stone, in a circle, as far as a broom will reach."),
    'nr_shepherd': (-22, "The stone by the door reads:^{g}'A SHEPHERD. HE NEVER LOST ONE.'{/}| Lower down, in the same hand, later: {g}'HE HAS LOST COUNT.'{/}"),
    'nr_proud': (-22, "The stone by the door reads:^{g}'KI-AG. HE LOOKED UP TO NOBODY.'{/}| It is a hand taller than any other stone on the road. It has been measured."),
    'nr_couple': (26, "The stone by the door reads:^{g}'THEY WERE NEVER PARTED.'{/}| Under it, scratched from the inside, by the look of it: {g}'NOT FOR WANT OF ASKING.'{/}"),
    'np_rich': (48, "The stone by the door reads:^{g}'PUZUR, MERCHANT. HE TOOK IT WITH HIM.'{/}| There is a second stone behind the first, with the list."),
    'np_knocker': (-24, "The stone by the door reads:^{g}'IBBI. HE DID NOT LIKE TO BE A BOTHER.'{/}"),
    'np_five': (-24, "The stone by the door reads:^{g}'SHE SAID SHE WOULD ONLY BE A MINUTE.'{/}"),
    'np_reader': (22, "The stone by the door reads:^{g}'ADAPA, SCRIBE. SIXTY TABLETS.'{/}| The mason has added, on his own account: {g}'I CUT NINE. NOBODY SHOULD HAVE TO CUT SIXTY.'{/}"),
    'np_pillow': (-26, "The stone by the door reads:^{g}'A NIGHT WATCHMAN. HE NEVER ONCE SLEPT ON DUTY.'{/}| {g}'HE IS MAKING UP FOR IT.'{/}"),
}
# what a shut door on the hill says for itself, and what is said when it opens
SHUT = {
    'nr_proud': {0: "Bricked up from the inside, and never pointed.^He went in and had it closed behind him, so that nobody could come and stand level.| "
                    "The steps up the front are for the neighbours to look at. The hatch in the roof is for the man who sweeps it."},
    'nr_couple': {0: "Bolted, on the inside. Through it, in whispers: an argument about whose turn it is to lie on the left.^Nobody is coming to the door until that is settled.| "
                     "The dead do not dream. Asleep, there would be nobody behind this door to keep it shut.",
                  ('open', 0): "The bolt is drawn, and the door of the two vaults stands open.^The argument has moved on to who left it open."},
    'np_knocker': {0: "Shut. From inside: knocking. Three knocks, a wait, three knocks.^He does not want to be let out. He is making sure that somebody is there.| There is a gong beside the door, for callers.",
                   ('open', 0): "The gong sings. The knocking stops.^Then, very quickly, a great many bolts."},
    'np_five': {0: "On the door, in chalk: {g}BACK IN FIVE MINUTES.{/}^The dust on the chalk is forty nights deep, and the door is barred on the inside."},
    'np_pillow': {0: "Shut. A rattle is cut over the door: a night watchman's.^The fire bowl beside it is cold. Whoever is inside has had enough of the dark, and is not opening the door to any more of it.",
                  ('open', 0): "Fire at the door: the first warm light on this hill in three hundred years.^Inside, a bar is lifted.| {g}'That's more like it,'{/} says somebody."},
}


def houses_of(m, B, inside):
    """Stand the houses of the dead, each with its stone by the door."""
    for (b, x, y) in B:
        hkit.place(m, b, x, y, inside=inside, say=SHUT.get(b.key))
        off, words = STONES[b.key]
        m.model("name_stone", tombs.name_stone(), x + int(round(b.doors[0][0] * 16)) + off, y + 6, box=(-6, -4, 6, 0), kind="look", data={"id": "say", "text": words + BLANK})


def thorn_tree(m, x, y):
    """The one tree of the hill, its foot at (x, y)."""
    return m.model("thorn_tree", tombs.thorn_tree(1), x, y, box=(-3, -5, 3, 0))


def straw(T, seed=5):
    """The hill is under straw: grass that died standing, and has been kept short ever since."""
    hkit.green(T, T.all(), seed=seed, base=3.5, ramp='straw')


def ways(T, road, paths, seed=7):
    """The ways of the dead: the road itself in pale stone, worn, as the king's avenue is; the paths to the doors
    in grey; a dark kerb, and one kerb round the lot."""
    T.slabs(road, seed=seed, rows=(12,), wmin=14, wmax=20, ramp='pale', base=4.2, jitter=0.9, crack=0.1, whole=False, wear=0.6)
    T.slabs(paths & ~road, seed=seed + 2, rows=(8,), wmin=8, wmax=12, ramp='flag', base=4.3, whole=False, jitter=0.7, crack=0.03, wear=0.3)
    hkit.edge_stones(T, road | paths, 'flag', 2.2)


def yard(T, x0, y0, x1, y1, seed=0):
    """The ground a house of the dead stands on: gravel, raked, pale, a line of stones round it."""
    area = T.rect(x0, y0, x1 - x0, y1 - y0)
    hkit.calm(T, area, 'ash', base=4.7, seed=seed, amp=0.15, pebbles=0.0)
    X, Y = T.xx, T.yy
    T.add(area & ((Y % 4) == 1), -0.35)                       # the rake
    T.border(area, ramp='pale', tone=4.6, width=1, hgt=0.8)
    return area


def grave_plot(T, x, y, w, h, seed=0):
    """Where the plain graves are: turned earth, square, with a line of pale stones round it."""
    area = T.rect(x, y, w, h)
    T.earth(area, seed=seed + 1, base=2.9, ramp='ash', pebbles=0.02)
    T.border(area, ramp='pale', tone=4.0, width=1, hgt=0.8)
    return area


def asphodel(T, pts):
    """The only thing that flowers up here, and it flowers white."""
    for (x, y) in pts:
        hkit.flowers(T, x, y, 'w', leaf='straw')


# ------------------------------------------------------------------ the road of the dead
ROAD = [(320, 704), (316, 600), (250, 520), (200, 450), (230, 372), (420, 330), (452, 250), (400, 170), (320, 110), (320, 0)]


def necro_road():
    TW, TH = 40, 44
    W, H = TW * 16, TH * 16
    m = MapBuilder("necro_road", TW, TH, (10, 12, 28, 255), music="hill")
    T = m.lay(seed=201)
    town.STYLE = tombs.LOOK
    B = [(tombs.sweeper(), 128, 652), (tombs.shepherd(), 508, 656), (tombs.proud(), 500, 500), (tombs.couple(), 180, 168)]
    town.STYLE = None
    land = T.ragged(T.rect(52, 70, W - 104, H), 15, 52, seed=31) | T.ragged(T.rect(-30, -30, W + 60, 126), 9, 34, seed=30) | T.rect(40, H - 26, W - 80, 26)
    land &= ~T.ragged(T.disc(0, 400, 86, 70) | T.disc(W, 560, 78, 80), 6, 18, seed=32)
    straw(T)
    T.rock(T.ragged(T.disc(112, 246, 54, 40), 5, 12, seed=2), seed=3, base=3.3)
    coast(T, land, seed=33)
    # every house on its own raked ground
    for k, (xa, ya, xb, yb) in enumerate(((78, 552, 180, 662), (454, 570, 564, 666), (454, 392, 548, 512), (118, 72, 244, 178), (466, 64, 534, 122))):
        yard(T, xa, ya, xb, yb, seed=k)
    # the road, and a path from every door to it
    road = T.stroke(ROAD, 30)
    paths = (T.rect(106, 652, 16, 28) | T.rect(106, 664, 206, 16) |                      # the sweeper's
             T.rect(476, 656, 16, 24) | T.rect(326, 664, 166, 16) |                      # the shepherd's
             T.rect(540, 504, 34, 14) | T.rect(558, 336, 16, 182) | T.rect(430, 328, 144, 16) |      # round to the foot of the proud man's stair
             T.rect(172, 168, 16, 24) | T.rect(172, 176, 232, 16) |                      # the two vaults
             T.stroke([(230, 372), (160, 320), (118, 268)], 14))                         # up to the stone of the first king
    ways(T, road, paths)
    for (x, y, w, h, sd) in ((200, 548, 92, 56, 41), (392, 488, 60, 64, 42), (286, 396, 70, 44, 43), (250, 210, 92, 52, 44), (60, 120, 58, 70, 45)):
        grave_plot(T, x, y, w, h, sd)
    asphodel(T, ((92, 668), (164, 668), (452, 672), (548, 672), (120, 190), (232, 190), (474, 516), (300, 640), (340, 560), (270, 340), (470, 250), (350, 130), (90, 560), (560, 590)))
    BARROWS = [(104, 476, 2.0, 3, True), (540, 268, 2.2, 4, False)]
    for (b, x, y) in B:
        hkit.contact(T, b, x, y)
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
    # ---- the houses, each on its own ground, a hedge of dead thorn either side
    houses_of(m, B, IN_ROAD)
    for (xa, xb, ya, yb, sd) in ((70, 178, 560, 656, 1), (446, 562, 574, 660, 3), (110, 242, 78, 172, 5)):
        hkit.hedge_sn(m, xa, ya, yb, sd, leaf=THORN); hkit.hedge_sn(m, xb, ya, yb, sd + 1, leaf=THORN)
    hkit.hedge_sn(m, 446, 400, 504, 7, leaf=THORN)
    # the assessor's vault, against the rock at the top of the road: a square of dead thorn with a bronze grille in
    # it, and before the grille a plate in the ground that knows what a debt weighs and does not notice a man
    hkit.hedge_sn(m, 462, 66, 122, 9, leaf=THORN); hkit.hedge_sn(m, 529, 66, 122, 10, leaf=THORN)
    hkit.hedge_ew(m, 462, 489, 122, 11, leaf=THORN); hkit.hedge_ew(m, 511, 538, 122, 12, leaf=THORN)
    m.model("bars_22", town.bars(22 / 16.0, 1.3), 500, 122, box=(-11, -6, 11, 0), kind="bars",
            data={"id": "nr_vault", "text": "plate:nr_weigh",
                  "say": "The grille of the assessor's vault goes up.^It has been waiting three hundred years to hear the end of this."})
    kit.chest(m, 500, 92, "nr_assessor", "shekels:120")
    m.model("plate", town.plate(), 500, 148, box=None, kind="plate", data={"id": "nr_weigh"}, shadow=False)
    kit.stele(m, 532, 146, 2, text="{g}THE ASSESSOR OF THE DEAD.{/}^{t}DEBTS ARE WEIGHED HERE. THE VAULT OPENS TO WHAT IS OWED, WHEN IT COMES TO BE WEIGHED, "
                                   "OR TO THE NEWS THAT IT IS PAID.{/}| Scratched under it: {t}I STOOD ON THE PLATE. I AM OWED PLENTY. NOTHING.{/}")
    # what he had cut so as never to be without them, in a pen of their own beside his door
    for k, (x, y) in enumerate(((532, 676), (552, 688), (516, 692))):
        kit.say(m, "tb_sheep", tombs.stone_sheep(1), x, y, (-6, -5, 8, 0),
                "A sheep, cut in stone, the size of a sheep.^He had six made, so that he would never be without them. People leave them a little grass, to be kind."
                "~~In the dream it is a stone, and has never looked like anything.")
    for i, (x, y, r, sd, lamp) in enumerate(BARROWS):
        kit.tumulus(m, x, y, r, sd, lamp, text=barrow(i))
    # the wall the queue stands in the gap of: field stone right across the hill
    m.model("nr_wall_w", town.drystone((394 - 44) / 16.0, h=1.1, seed=11), 44, 300, box=None)
    m.model("nr_wall_e", town.drystone((W - 44 - 446) / 16.0, h=1.1, seed=12), 446, 300, box=None)
    m.solid(0, 290, 394, 300); m.solid(446, 290, W, 300)
    m.solid(394, 286, 446, 300, 1)            # the dead in the gap: there in the waking world, not in the dream
    kit.standard(m, 386, 308); kit.standard(m, 454, 308)
    # the plain graves, in rows
    kit.graves(m, 210, 570, 4, 2, seed=1); kit.graves(m, 402, 512, 3, 2, seed=2); kit.graves(m, 296, 418, 3, 1, seed=3)
    kit.graves(m, 260, 232, 4, 1, seed=4); kit.graves(m, 70, 144, 2, 2, seed=5)
    # stones with things to say
    kit.stele(m, 112, 244, 0, uid="stele_kur", text="stele")
    kit.standard(m, 88, 250)
    for i, (x, y) in enumerate(((270, 620), (368, 530), (160, 420), (476, 290), (364, 150), (270, 104))):
        kit.stele(m, x, y, i + 1, text=epitaph(i))
    for (x, y) in ((286, 650), (350, 566), (226, 476), (252, 336), (474, 232), (372, 126)):
        kit.spirit_lamp(m, x, y)
    # the trees of the hill, in rows: up the east side of the road at the foot, along the wall, under the rock
    for (x, y) in ((364, 690), (364, 630), (84, 540), (84, 420), (96, 384), (572, 430), (150, 306), (236, 286), (332, 286), (500, 286),
                   (420, 80), (556, 84), (206, 82), (572, 160), (60, 206)):
        thorn_tree(m, x, y)
    for sd, (x, y) in enumerate(((204, 690), (436, 610), (510, 556), (414, 226), (96, 110))):
        kit.rock(m, x, y, sd)
    k = 0
    for (x0, y0) in ((228, 648), (396, 440), (296, 250)):                    # thorn, in blocks
        for dx in (0, 14, 28):
            for dy in (0, 12):
                kit.thorn(m, x0 + dx, y0 + dy, 0); k += 1
    for i, (x, y) in enumerate(((184, 664), (444, 664), (90, 500), (300, 470), (510, 200), (246, 160), (450, 140))):
        kit.urn(m, x, y, i)
    for i, (x, y) in enumerate(((400, 640), (150, 350), (340, 216), (584, 400))):
        kit.bones(m, x, y, i)
    m.model("offer_a", town.offering_table(1), 156, 500, box=(-12, -10, 12, 0))
    m.model("offer_b", town.offering_table(2, food=False), 420, 462, box=(-12, -10, 12, 0))
    # the gate from the terraces: two posts and a wall of field stone along the foot of the hill
    kit.gate_post(m, 284, H - 4); kit.gate_post(m, 356, H - 4)
    m.model("nr_foot_w", town.drystone((272 - 44) / 16.0, h=0.9, seed=13), 44, H - 2, box=None)
    m.model("nr_foot_e", town.drystone((W - 44 - 368) / 16.0, h=0.9, seed=14), 368, H - 2, box=None)
    m.solid(0, H - 12, 296, H); m.solid(344, H - 12, W, H)
    m.marker("npc", 350, 640, who="namtar")
    m.marker("npc", 148, 512, who="gran_dur")
    m.marker("npc", 438, 474, who="belu")
    m.marker("npc", 520, 300, who="goat_tomb")
    for i, x in enumerate((402, 414, 426, 438)):
        m.marker("npc", x, 296, who=f"queue_{i}")
    for i, (x, y) in enumerate(((150, 270), (96, 330), (300, 224), (520, 180))):
        m.enemy("unremembered", x, y, f"nr_u{i}")
    for i, (x, y) in enumerate(((330, 470), (220, 520), (330, 262))):
        m.enemy("scarab", x, y, f"nr_s{i}")
    # somebody up here died owing money. It is standing in the road.
    m.enemy("debt", 392, 170, "nr_debt", once=True)
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
    town.STYLE = tombs.LOOK
    B = [(tombs.rich(), 200, 380), (tombs.knocker(), 112, 520), (tombs.five(), 246, 540), (tombs.pillow(), 484, 372), (tombs.reader(), 540, 612)]
    town.STYLE = None
    land = T.ragged(T.rect(46, 60, W - 92, H), 14, 56, seed=35) | T.ragged(T.rect(-30, -30, W + 60, 174), 9, 34, seed=34) | T.rect(40, H - 26, W - 80, 26)
    cleft = T.ragged(T.disc(664, 256, 112, 96) | T.rect(690, 176, 90, 160), 7, 22, seed=36)
    isle = T.ragged(T.disc(664, 262, 34, 50), 3, 10, seed=37)
    land = (land & ~cleft) | isle
    straw(T)
    coast(T, land, seed=38)
    T.rock(isle, seed=39, base=3.5)
    # the avenue from the gate up to the king's door, the court in front of it, and a path from every door to the avenue
    avenue = T.rect(364, 188, 40, H - 188)
    court = T.rect(272, 118, 224, 74)
    paths = (T.rect(192, 380, 16, 36) | T.rect(192, 400, 172, 16) |                       # the rich man's
             T.rect(115, 520, 16, 48) | T.rect(115, 552, 249, 16) | T.rect(238, 540, 16, 16) |      # the man who knocks, and next door
             T.rect(476, 372, 16, 24) | T.rect(404, 384, 88, 12) |                        # the watchman's
             T.rect(558, 612, 16, 16) | T.rect(404, 614, 170, 14))                        # the scribe's
    for k, (xa, ya, xb, yb) in enumerate(((124, 284, 280, 392), (64, 424, 168, 530), (204, 456, 298, 550), (436, 250, 532, 384), (482, 528, 606, 620))):
        yard(T, xa, ya, xb, yb, seed=k + 5)
    ways(T, avenue | court, paths, seed=4)
    T.border(court, 'lapis', 3.0, 2, 1.2)
    # the court of the game, east of the avenue
    game = T.rect(474, 400, 144, 92)
    T.slabs(game, seed=5, rows=(10, 11), wmin=12, wmax=18, ramp='flag', base=3.3, moss=0.0, whole=False)
    T.border(game, 'pale', 4.2, 1, 1.1)
    for (x, y, w, h, sd) in ((296, 440, 56, 64, 46), (612, 500, 98, 62, 47), (60, 300, 60, 64, 48)):
        grave_plot(T, x, y, w, h, sd)
    asphodel(T, ((150, 400), (250, 400), (84, 536), (150, 536), (300, 556), (440, 392), (530, 392), (500, 626), (596, 626), (80, 190), (190, 190),
                 (340, 210), (424, 210), (340, 500), (424, 300), (640, 590), (60, 590)))
    GB = (676, 474, 3.0)                                 # the Generals' Barrow: the mouth of its passage, and how big it is
    for (b, x, y) in B:
        hkit.contact(T, b, x, y)
    T.contact(GB[0] - GB[2] * 14, GB[1] - GB[2] * 30, GB[0] + GB[2] * 14, GB[1] - 4, reach=7, strength=1.4)
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
    # (their own names: the city's pair is bigger, and one name must always be one picture)
    m.model("lamassu_hill_a", town.lamassu(False, 1.25), 252, 156, box=(-30, -20, 30, 0))
    m.model("lamassu_hill_b", town.lamassu(True, 1.25), 516, 156, box=(-30, -20, 30, 0))
    kit.spirit_bowl(m, 316, 148); kit.spirit_bowl(m, 452, 148)
    kit.standard(m, 348, 200); kit.standard(m, 420, 200)
    # the gate from the road: two posts and a wall of field stone
    kit.gate_post(m, 348, H - 4); kit.gate_post(m, 420, H - 4)
    m.model("np_wall_w", town.drystone((336 - 44) / 16.0, h=0.9, seed=21), 44, H - 2, box=None)
    m.model("np_wall_e", town.drystone((W - 44 - 432) / 16.0, h=0.9, seed=22), 432, H - 2, box=None)
    m.solid(0, H - 12, 360, H); m.solid(408, H - 12, W, H)
    # ---- the houses of the great dead, each on its own ground
    houses_of(m, B, IN_HILL)
    hkit.gong(m, 152, 530, "np_knocker_gong")
    kit.brazier(m, 516, 386, False, "np_pillow_sign")
    for (x, ya, yb, sd) in ((116, 290, 384, 1), (272, 290, 384, 2), (56, 430, 524, 3), (160, 430, 524, 4), (196, 462, 544, 5), (290, 462, 544, 6),
                            (474, 534, 616, 7), (598, 534, 616, 8)):
        hkit.hedge_sn(m, x, ya, yb, sd, leaf=THORN)
    # the Generals' Barrow: the biggest mound on the hill, one door, and a standard either side that neither army will take down first
    gx, gy, gr = GB
    m.model("great_barrow", bprops.great_barrow(gr, 5), gx, gy, box=None, lights=False)
    hw, up = int(gr * 16) - 6, int(gr * 32) - 8
    m.solid(gx - hw, gy - up, gx - 12, gy - 5); m.solid(gx + 12, gy - up, gx + hw, gy - 5); m.solid(gx - 12, gy - up, gx + 12, gy - 24)
    m.model("standard_red_hill", bprops.standard('red'), gx - 34, gy + 4, box=(-4, -6, 4, 0), lights=False)
    m.model("standard_blue_hill", bprops.standard('blue'), gx + 34, gy + 4, box=(-4, -6, 4, 0), lights=False)
    kit.stele(m, gx - 52, gy + 18, 3, text="{g}'USHUR AND BALTU, GENERALS. THEY KILLED EACH OTHER IN THE SAME BATTLE AT THE SAME MOMENT.'{/}^"
                                              "{g}'ONE BARROW. ONE DOOR. THE CITY WAS NOT MADE OF MONEY.'{/}~~"
                                              "In the dream the door of the barrow stands open, as it does awake.^Nobody on this hill locks anything. Nobody is expected to leave.")
    m.light(gx, gy - 14, 2.6, (1.0, 0.70, 0.36), 0.4, h=0.8)
    # the garden of the dead: its trees in two rows, two fire altars that have gone out, and the stone they used to light
    for (x, y) in ((70, 168), (134, 152), (200, 152), (70, 232), (134, 250), (200, 232)):
        thorn_tree(m, x, y)
    kit.stele(m, 134, 182, 1, uid="stele_tar", text="stele")
    kit.brazier(m, 104, 194, False, "garden_0")
    kit.brazier(m, 164, 194, False, "garden_1")
    kit.brazier_frames(m)
    # the stone on the island, and what somebody left with it
    kit.stele(m, 664, 240, 2, uid="stele_ash", text="stele")
    kit.chest(m, 664, 290, "isle_vessel", "vessel")
    # graves in rows; stones and lamps along the avenue, a pair to every pair
    kit.graves(m, 304, 462, 2, 2, seed=6); kit.graves(m, 622, 520, 4, 2, seed=7); kit.graves(m, 70, 322, 2, 2, seed=8)
    for i, (x, y) in enumerate(((330, 590), (438, 590), (330, 500), (438, 500), (330, 320), (438, 320), (330, 240), (438, 240))):
        if i % 2 == 0: kit.spirit_lamp(m, x, y)
        else: kit.stele(m, x, y, i, text=epitaph((6, 10, 11, 9)[i // 2]))
    # the court of the game: four columns that held a roof once, the board, two seats
    for i, (x, y) in enumerate(((484, 416), (606, 416), (484, 488), (606, 488))):
        m.model(f"col_{i % 2}", necro.broken_column(1.4 - 0.5 * (i % 2), i, fallen=(i == 1)), x, y, box=(-5, -9, 5, -1))
    m.model("game_board", town.game_board(), 546, 452, box=(-8, -10, 8, 0), kind="look", data={"id": "game_board"})
    m.model("stone_seat", necro.stone_seat(), 520, 452, box=(-5, -8, 5, 0))
    m.model("stone_seat", necro.stone_seat(), 572, 452, box=(-5, -8, 5, 0))
    m.model("offer_c", town.offering_table(3), 300, 404, box=(-12, -10, 12, 0))
    m.model("offer_d", town.offering_table(4, food=False), 640, 624, box=(-12, -10, 12, 0))
    for sd, (x, y) in enumerate(((66, 400), (700, 356), (440, 560), (604, 146))):
        kit.rock(m, x, y, sd + 3)
    # the hill's trees, in rows: along the west edge, either side of the gate, behind the court of the game
    for (x, y) in ((60, 480), (60, 556), (60, 620), (320, 622), (448, 600), (704, 560), (704, 620), (640, 380), (560, 172), (620, 172), (300, 300), (444, 300)):
        thorn_tree(m, x, y)
    for (x0, y0) in ((296, 590), (420, 430), (620, 596)):                    # thorn, in blocks
        for dx in (0, 14, 28):
            for dy in (0, 12):
                kit.thorn(m, x0 + dx, y0 + dy, 0)
    for i, (x, y) in enumerate(((286, 398), (84, 590), (452, 344), (620, 624), (340, 624), (712, 500), (512, 512))):
        kit.urn(m, x, y, i)
    for i, (x, y) in enumerate(((300, 270), (580, 340), (90, 600))):
        kit.bones(m, x, y, i)
    m.marker("npc", 527, 453, who="general_a")
    m.marker("npc", 565, 453, who="general_b")
    m.marker("npc", 320, 584, who="poet")
    m.marker("npc", 300, 172, who="doorman")
    m.marker("npc", 428, 596, who="goat_hill")
    for i, (x, y) in enumerate(((90, 280), (300, 420), (640, 580), (540, 230), (150, 270), (230, 270))):
        m.enemy("unremembered", x, y, f"np_u{i}")
    for i, (x, y) in enumerate(((450, 520), (340, 470), (60, 420))):
        m.enemy("scarab", x, y, f"np_s{i}")
    m.spawn("south", 384, H - 30, "up")
    m.spawn("door", 384, 138, "down")
    m.spawn("barrow", GB[0], GB[1] + 16, "down")
    m.exit(GB[0] - 10, GB[1] - 22, GB[0] + 10, GB[1] - 9, "barrow", "south")
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
    m.exit(W // 2 - 20, H - 8, W // 2 + 20, H, "tomb_hi", "top")
    m.save()


if __name__ == "__main__":
    # (the tomb's two floors of halls are in tomb_maps.py)
    which = sys.argv[1:] or ["necro_road", "necropolis", "tomb_3"]
    for name in which:
        globals()[name]()
