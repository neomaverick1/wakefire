"""Placing the things every map shares, always built the same way under the same name, so one
picture on disk serves all the maps that use it."""
import town
import necro

OLIVES = 8


def olive(m, x, y, sd):
    k = sd % OLIVES
    return m.model(f"olive_{k}", town.olive(k + 3), x, y, box=(-4, -6, 4, 0))


def cypress(m, x, y, sd):
    k = sd % 4
    return m.model(f"cypress_{k}", town.cypress(k + 1, 2.8 + 0.25 * (k % 3)), x, y, box=(-3, -5, 3, 0))


def palm(m, x, y, sd):
    k = sd % 6
    return m.model(f"palm_{k}", town.palm(k + 1, 2.6 + k % 3 * 0.25), x, y, box=(-3, -5, 3, 0))


def bush(m, x, y, k):
    k = k % 4
    return m.model(f"bush_{k}", town.bush(k, k == 0), x, y, box=(-6, -6, 6, 0), kind="bush")


def rock(m, x, y, sd):
    k = sd % 5
    s = 1.0 + 0.18 * k
    return m.model(f"rock_{k}", town.rock(k + 1, s), x, y, box=(int(-7 * s), -6, int(9 * s), 0))


def pot(m, x, y, big=False):
    return m.model("pot_big" if big else "pot", town.pot(big, seed=1), x, y, box=(-4, -4, 4, 0), kind="pot")


def torch(m, x, y, light=4.2):
    """A standing torch on a pole, burning."""
    m.model("pole_torch", town.pole_torch, x, y, box=(-2, -3, 3, 0), frames=4, kind="torch")
    m.light(x, y - 26, light, (1.0, 0.70, 0.36), 0.85, h=1.65)


def brazier(m, x, y, lit=False, uid=None, light=5.0):
    """A fire altar. Unlit ones wait for the Wakefire (the game swaps in the burning frames)."""
    if lit:
        m.model("brazier_lit", lambda fi: town.brazier(True, fi), x, y, box=(-6, -10, 6, 0), frames=4, kind="torch", lights=False)
        m.light(x, y - 18, light, (1.0, 0.70, 0.36), 0.85, h=1.1)
    else:
        m.model("brazier", town.brazier(False), x, y, box=(-6, -10, 6, 0), kind="brazier", data={"id": uid})


def brazier_frames(m):
    """The burning frames, parked off the map for the game to find when a brazier is lit."""
    m.model("brazier_lit", lambda fi: town.brazier(True, fi), -100, -100, box=None, frames=4, lights=False)


def sign(m, x, y, key, text):
    m.model(key, town.sign(), x, y, box=(-2, -4, 2, 0), kind="sign", data={"text": text})


def houses(m, T, rows, phase):
    """rows: (key, centre x, front y, width, depth, height, options). phase 0 darkens the ground
    where they stand (before the ground is baked); phase 1 puts them up."""
    for (key, cx, y, w, d, h, kw) in rows:
        if phase == 0:
            T.contact(cx - w * 8, y - d * 16, cx + w * 8, y, reach=5, strength=1.5)
        else:
            m.model(key, town.house(w, d, h, **kw), cx, y, box=(-w * 8, -(d + h) * 16, w * 8, 0))
            if kw.get('stair') == 'r': m.solid(cx + w * 8 - 37, y, cx + w * 8, y + 9)
            if kw.get('stair') == 'l': m.solid(cx - w * 8, y, cx - w * 8 + 37, y + 9)


def chest(m, x, y, uid, text, layer=0):
    """A treasure chest; the game swaps in the open picture (same pivot) once it has been opened."""
    return m.model("chest", lambda fi: town.chest(fi == 1), x, y, box=(-9, -10, 9, 0), frames=2, names=["chest", "chest_open"], still=True,
                   kind="chest", layer=layer, data={"id": uid, "text": text}, lights=False)


def lamassu(m, x, y, west=False):
    """A winged-bull guardian on its plinth, facing east (or west)."""
    return m.model("lamassu_w" if west else "lamassu_e", town.lamassu(west), x, y, box=(-34, -22, 34, 0))


# ------------------------------------------------------------------ where the map stops
# Anywhere the ground runs on but the player can't, something stands there and says why.
def say(m, key, model, x, y, box, text, **kw):
    """A thing that can be walked up to and looked at: text is what the game says about it
    (waking~~dream, if the dream has something else to say)."""
    return m.model(key, model, x, y, box=box, kind="look", data={"id": "say", "text": text}, **kw)


def wall_ns(m, x, y0, y1, seed=0, plaster=None, h=1.5, wd=0.625):
    """A yard wall along a west or east edge, from y0 (north) down to y1."""
    depth = (y1 - y0) / 16.0
    m.model(f"ywall_ns_{int(y1 - y0)}_{seed}", town.yard_wall_ns(depth, h, wd, seed, plaster), x, y1, box=None)
    m.solid(x - 1, y0, x + int(wd * 16) + 1, y1)


def wall_ew(m, x0, x1, y, seed=0, plaster=None, h=1.5, d=0.5):
    """A yard wall running east from x0 to x1, its face at y."""
    m.model(f"ywall_{int(x1 - x0)}_{seed}", town.yard_wall((x1 - x0) / 16.0, h, d, seed, plaster), x0, y, box=None)
    m.solid(x0, y - int(d * 16) - 2, x1, y)


def cypress_row(m, x, y0, y1, seed=0, step=18):
    """Cypresses planted close as a fence down a west or east edge."""
    k = seed
    y = y0
    while y <= y1:
        cypress(m, x + (3 if k % 2 else -2), y, k)
        y += step; k += 1
    m.solid(x - 7, y0 - 8, x + 8, y1 + 2)


def thicket(m, x0, x1, y, seed=0, step=15):
    """Scrub and cypress grown into a hedge, running east: a north or south edge."""
    k = seed
    x = x0
    while x <= x1:
        if k % 3 == 0: cypress(m, x, y - 2 + (k % 2) * 3, k)
        else: bush(m, x, y + (k % 2) * 3, k)
        x += step; k += 1
    m.solid(x0 - 6, y - 8, x1 + 6, y + 3)


def boulders(m, pts, seed=0):
    """Rocks dropped across a way, big ones, close together."""
    for i, (x, y) in enumerate(pts):
        rock(m, x, y, seed + i * 2 + 3)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    m.solid(min(xs) - 9, min(ys) - 7, max(xs) + 12, max(ys) + 1)


# ------------------------------------------------------------------ the hill of sleepers
SPIRIT = (0.50, 0.84, 0.94)


def spirit_lamp(m, x, y, light=3.6):
    """A lamp for the dead, burning the colour of deep water."""
    m.model("spirit_lamp", town.spirit_lamp, x, y, box=(-2, -3, 3, 0), frames=4, kind="spirit", lights=False)
    m.light(x, y - 20, light, SPIRIT, 0.5, h=1.2)


def spirit_bowl(m, x, y, light=4.6):
    """A king's lamp: a bronze bowl of the same cold fire on a tripod."""
    m.model("spirit_bowl", necro.spirit_bowl, x, y, box=(-6, -8, 6, 0), frames=4, kind="spirit", lights=False)
    m.light(x, y - 18, light, SPIRIT, 0.55, h=1.1)


def tomb(m, x, y, w=5.0, d=3.0, h=1.6, seed=0, style=None, lamp=False, text=None):
    """A house of the dead, its door facing south at (x, y). text: what a listener at the door hears."""
    style = style or ('vault', 'flat', 'step')[seed % 3]
    key = f"tomb_{style}_{int(w * 10)}_{int(d * 10)}_{int(h * 10)}_{seed}{'l' if lamp else ''}"
    kw = dict(kind="look", data={"id": "say", "text": text}) if text else {}
    m.model(key, necro.tomb_house(w, d, h, seed, style, lamp), x, y, box=(int(-w * 8), int(-d * 16), int(w * 8), 0), lights=False, **kw)
    if lamp: m.light(x + 4, y + 4, 2.4, SPIRIT, 0.45, h=0.4)


def tumulus(m, x, y, r=2.2, seed=0, lamp=False, text=None):
    """A round barrow, the mouth of its passage at (x, y)."""
    key = f"tumulus_{int(r * 10)}_{seed}{'l' if lamp else ''}"
    kw = dict(kind="look", data={"id": "say", "text": text}) if text else {}
    m.model(key, necro.tumulus(r, seed, lamp), x, y, box=(int(-r * 16) + 5, int(-r * 32) + 6, int(r * 16) - 5, -5), lights=False, **kw)
    m.solid(x - 11, y - 8, x - 6, y + 8); m.solid(x + 6, y - 8, x + 11, y + 8)
    if lamp: m.light(x + 8, y + 8, 2.4, SPIRIT, 0.45, h=0.4)


def stele(m, x, y, seed=0, text=None, uid=None):
    k = seed % 3
    if text:
        return m.model(f"stele_{k}", town.stele(1.4 + 0.15 * k, k), x, y, box=(-5, -5, 5, 0), kind="look", data={"id": uid or "say", "text": text})
    return m.model(f"stele_{k}", town.stele(1.4 + 0.15 * k, k), x, y, box=(-5, -5, 5, 0))


def dead_tree(m, x, y, sd):
    k = sd % 4
    return m.model(f"dead_tree_{k}", town.dead_tree(k + 1, 0.9 + 0.12 * k), x, y, box=(-3, -5, 3, 0))


def grave(m, x, y, sd):
    k = sd % 8
    return m.model(f"grave_{k}", necro.grave_mound(k), x, y, box=(-4, -13, 4, -2))


def graves(m, x, y, cols, rows, seed=0, dx=20, dy=30):
    """A plot of ordinary graves in rows, some rows missing a place."""
    import numpy as np
    r = np.random.default_rng(seed)
    for j in range(rows):
        for i in range(cols):
            if r.random() < 0.14: continue
            grave(m, x + i * dx + int(r.integers(-2, 3)), y + j * dy + int(r.integers(-2, 3)), int(r.integers(0, 8)))


def standard(m, x, y):
    return m.model("moon_standard", necro.moon_standard(), x, y, box=(-3, -6, 3, 0))


def urn(m, x, y, sd):
    """Grave jars: the whole ones break like any other jar; the broken ones have been."""
    k = sd % 4
    return m.model(f"urn_{k}", necro.urn(k), x, y, box=(-4, -6, 4, -1), kind="pot" if k < 2 else None)


def bones(m, x, y, sd):
    k = sd % 3
    return m.model(f"bones_{k}", necro.bones(k + 1), x, y, box=None)


def thorn(m, x, y, sd):
    k = sd % 4
    return m.model(f"thorn_{k}", necro.thorn(k + 1), x, y, box=(-3, -5, 3, -1))


def gate_post(m, x, y):
    m.model("gate_post", necro.gate_post(), x, y, box=(-8, -14, 8, 0), lights=False)
    m.light(x, y - 44, 3.6, SPIRIT, 0.5, h=2.6)
