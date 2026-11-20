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
