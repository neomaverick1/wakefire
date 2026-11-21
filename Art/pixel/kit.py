"""Placing the things every map shares, always built the same way under the same name, so one
picture on disk serves all the maps that use it."""
import town

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
