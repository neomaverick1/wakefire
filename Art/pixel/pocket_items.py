"""Nod's Pocket, and what has been in it so far: the pouch itself, and a 16 px picture of each
thing a dream has let go of.   python3 pocket_items.py [preview.png]
(WF_RES points it at a staging folder instead of the game's own Resources.)"""
import math, os, sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from PIL import Image
import forge
from forge import Model, M, Mat
import town
import bprops
from dungeon_items import cut

RES = os.environ.get("WF_RES", "/srv/Wakefire/Assets/Wakefire/Resources")


def moon(base=4.0, marks=None):
    return Mat(bprops.MOON, base, marks, glow=True)


def item_pocket():
    """A soldier's belt pouch, worn soft: a flap, a bronze toggle, and two loops for the belt."""
    m = Model()
    hide = M('wood', 4.1)
    flap = M('cedar', 3.0)
    m.part()
    for sx in (-0.2, 0.12):
        m.box(sx, 0.06, 0.66, sx + 0.08, 0.1, 0.86, M('trunk', 3.2))
    m.part(); m.blob(0, 0.05, 0.36, 0.36, 0.13, 0.3, hide, seed=2, bump=0.06, n=10, rings=6)
    m.part(); m.blob(0, 0.0, 0.56, 0.37, 0.12, 0.17, flap, seed=3, bump=0.04, n=10, rings=5)
    m.part(); m.face([(-0.3, 0.52), (0.3, 0.52), (0.0, 0.3)], -0.1, flap)
    m.part(); m.blob(0, -0.12, 0.31, 0.05, 0.04, 0.05, M('bronze', 4.4, gloss=0.04), n=6, rings=4)
    return m


def item_key():
    m = Model()
    mo = moon(4.4)
    ring = [(math.cos(a) * 0.2, 0.7 + math.sin(a) * 0.2) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
    m.part(); m.face(ring, 0.0, mo)
    m.part(); m.face([(math.cos(a) * 0.085, 0.7 + math.sin(a) * 0.085) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)], -0.01, M('dark', 1.6))
    m.part(); m.box(-0.045, -0.02, 0.06, 0.045, 0.02, 0.52, mo)
    m.part(); m.box(0.045, -0.02, 0.06, 0.24, 0.02, 0.15, mo)
    m.part(); m.box(0.045, -0.02, 0.24, 0.19, 0.02, 0.32, mo)
    return m


def item_plank():
    """One plank of moonlight, on the slant."""
    m = Model()
    a, b = (-0.34, 0.14), (0.34, 0.8)
    dx, dz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dz); nx, nz = -dz / ln * 0.11, dx / ln * 0.11
    m.part(); m.face([(a[0] - nx, a[1] - nz), (b[0] - nx, b[1] - nz), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)], 0.0, moon(4.0))
    m.part(); m.face([(a[0] + nx * 0.55, a[1] + nz * 0.55), (b[0] + nx * 0.55, b[1] + nz * 0.55), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)], -0.01, moon(5.2))
    return m


def item_flame():
    m = Model()
    bprops.cold_flame(m, 0, 0, 0.12, 1.25, 1)
    return m


def item_snore():
    """A snore: a curl of breath, still turning."""
    m = Model()
    pts = []
    for i in range(9):
        k = i / 8
        a = 0.6 + k * 5.2
        r = 0.28 * (1 - k * 0.62)
        pts.append((math.cos(a) * r, 0.0, 0.46 + math.sin(a) * r + k * 0.1))
    m.part(); m.limb(pts, [0.03, 0.06, 0.075, 0.075, 0.07, 0.06, 0.05, 0.035, 0.012], moon(4.0), n=5)
    return m


def item_word():
    """The last word: a scrap of tablet with one sign on it."""
    m = Model()
    m.part(); m.face([(-0.3, 0.2), (0.26, 0.16), (0.32, 0.6), (0.1, 0.74), (-0.26, 0.66)], 0.0, moon(3.6))
    m.part()
    # one sign, the way a scribe in a hurry cuts it: a long stroke, an upright through it, a tick
    for (x0, z0, x1, z1) in ((-0.2, 0.54, 0.16, 0.6), (0.06, 0.28, 0.12, 0.66), (-0.16, 0.34, -0.04, 0.4)):
        m.box(x0, -0.02, z0, x1, -0.01, z1, M('dark', 2.0))
    return m


def bullet(turn=0):
    """A slinger's bullet: baked clay, the shape of an olive, a thumbprint in one side."""
    m = Model()
    m.part(); m.blob(0, 0, 0.3, 0.2, 0.14, 0.14, M('clay', 4.0), n=8, rings=5)
    m.part(); m.blob(-0.07 + 0.14 * turn, -0.1, 0.33, 0.06, 0.04, 0.05, M('clay', 5.4), n=5, rings=3)
    return m


def small(name, model, size=8):
    a = cut(model)
    h, w = a.shape[:2]
    cv = np.zeros((size, size, 4), np.uint8)
    x0 = max(0, (size - w) // 2); y0 = max(0, (size - h) // 2)
    a = a[:size - y0, :size - x0]
    cv[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    os.makedirs(f'{RES}/Items', exist_ok=True)
    Image.fromarray(cv).save(f'{RES}/Items/{name}.png')
    print(name, f'{w}x{h}')


THINGS = [('pocket', item_pocket), ('pocket_key', item_key), ('pocket_plank', item_plank), ('pocket_flame', item_flame),
          ('pocket_snore', item_snore), ('pocket_word', item_word)]


def icon(name, model, size=16):
    a = cut(model)
    h, w = a.shape[:2]
    if h > size or w > size:
        raise SystemExit(f'{name}: {w}x{h} does not fit {size}')
    cv = np.zeros((size, size, 4), np.uint8)
    x0 = (size - w) // 2; y0 = (size - h) // 2
    cv[y0:y0 + h, x0:x0 + w] = a
    for sub in ('Items', 'Menu'):
        os.makedirs(f'{RES}/{sub}', exist_ok=True)
        Image.fromarray(cv).save(f'{RES}/{sub}/{name}.png')
    print(name, f'{w}x{h}')
    return cv


if __name__ == '__main__':
    made = [icon(n, f()) for n, f in THINGS]
    small('bullet_0', bullet(0)); small('bullet_1', bullet(1))
    if len(sys.argv) > 1:
        from PIL import ImageDraw
        S = 12
        sheet = Image.new('RGB', (len(made) * 17 * S + 8, 16 * S + 40), (58, 52, 70))
        d = ImageDraw.Draw(sheet)
        d.text((6, 4), 'INTERNAL TEST  -  Nod\'s Pocket and what has been in it, 12x', fill=(255, 200, 60))
        for i, cv in enumerate(made):
            im = Image.fromarray(cv).resize((cv.shape[1] * S, cv.shape[0] * S), Image.NEAREST)
            sheet.paste(im, (6 + i * 17 * S, 28), im)
        sheet.save(sys.argv[1]); print(sys.argv[1])
