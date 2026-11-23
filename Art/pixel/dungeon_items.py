"""The two things Azar wins in the dungeons, and the scroll that maps each one: models first, then
their 16 px icons and the small pictures of them in flight.  python3 dungeon_items.py [preview.png]"""
import math, sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from PIL import Image
import forge
from forge import Model, M, Mat, RAMPS

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Items'


def item_sling():
    """The herdsman's sling: two plaited cords, a leather cradle, a river stone in it."""
    m = Model()
    cord = M('straw', 4.2)
    hide = M('wood', 3.6)
    left = [(-0.20, 0.03, 0.74), (-0.30, 0.03, 0.56), (-0.24, 0.03, 0.36), (-0.10, 0.03, 0.22)]
    right = [(0.24, 0.03, 0.70), (0.32, 0.03, 0.52), (0.24, 0.03, 0.34), (0.10, 0.03, 0.22)]
    m.part(); m.limb(left, [0.03, 0.03, 0.032, 0.036], cord, n=5)
    m.part(); m.limb(right, [0.03, 0.03, 0.032, 0.036], cord, n=5)
    # the loop that goes over the finger, and the knot the other cord ends in
    m.part(); m.limb([(-0.20, 0.03, 0.74), (-0.10, 0.03, 0.82), (-0.02, 0.03, 0.74), (-0.12, 0.03, 0.67)], [0.026] * 4, cord, n=5)
    m.part(); m.blob(0.24, 0.03, 0.72, 0.05, 0.05, 0.05, cord, n=6, rings=4)
    m.part(); m.blob(0.0, 0.03, 0.16, 0.19, 0.08, 0.10, hide, n=8, rings=5)
    m.part(); m.blob(0.0, 0.0, 0.24, 0.115, 0.10, 0.10, M('stone', 4.6), n=8, rings=5)
    return m


def item_throwing_stick(turn=0.0, flat=False):
    """The huntsman's throwing stick: cedar, a shallow bend a third of the way along, gold at both
    ends. turn swings it round (for the frames of its flight)."""
    m = Model()
    wood = M('cedar', 3.9, gloss=0.03)
    gold = M('gold', 4.6, gloss=0.04)
    # the stick in its own plane, then swung round the middle
    shape = [(-0.40, 0.09), (-0.23, -0.04), (-0.04, -0.09), (0.17, -0.02), (0.38, 0.18)]
    c, s = math.cos(turn), math.sin(turn)
    def P(u, v):
        x, z = u * c - v * s, u * s + v * c
        return (x, 0.03, (0.5 + z) if not flat else (0.5 + z * 0.62))
    pts = [P(u, v) for u, v in shape]
    rad = [0.045, 0.055, 0.06, 0.055, 0.04]
    m.part(); m.limb(pts, rad, wood, n=6)
    for a, b in ((0, 1), (4, 3)):
        p0, p1 = np.array(pts[a]), np.array(pts[b])
        m.part(); m.limb([tuple(p0), tuple(p0 + (p1 - p0) * 0.3)], [rad[a] + 0.012, rad[a] + 0.02], gold, n=6)
    return m


def sling_stone():
    m = Model()
    m.part(); m.blob(0, 0.03, 0.14, 0.13, 0.12, 0.12, M('stone', 4.8), n=8, rings=5)
    return m


def item_scroll():
    """A map scroll: papyrus rolled on a cedar rod, tied with a red cord."""
    m = Model()
    pap = M('cream', 4.4)
    m.part(); m.limb([(-0.25, 0.03, 0.30), (0.25, 0.03, 0.52)], [0.15, 0.15], pap, n=10)
    rod = M('cedar', 3.6)
    m.part(); m.limb([(-0.36, 0.03, 0.25), (-0.25, 0.03, 0.30)], [0.05, 0.06], rod, n=6)
    m.part(); m.limb([(0.25, 0.03, 0.52), (0.36, 0.03, 0.57)], [0.06, 0.05], rod, n=6)
    m.part(); m.blob(-0.38, 0.03, 0.24, 0.06, 0.06, 0.06, M('gold', 4.6, gloss=0.04), n=6, rings=4)
    m.part(); m.blob(0.38, 0.03, 0.58, 0.06, 0.06, 0.06, M('gold', 4.6, gloss=0.04), n=6, rings=4)
    m.part(); m.limb([(-0.03, 0.03, 0.39), (0.05, 0.03, 0.43)], [0.165, 0.165], M('red', 3.8), n=10, cap=False)
    return m


def cut(model, ink=True):
    d = forge.draw(model, seed=1, shadow=False, ink=ink)
    a = d.rgba
    ys, xs = np.nonzero(a[..., 3] > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def icon(name, model, size=16, out=OUT):
    a = cut(model)
    h, w = a.shape[:2]
    if h > size or w > size:
        raise SystemExit(f'{name}: {w}x{h} does not fit {size}')
    cv = np.zeros((size, size, 4), np.uint8)
    x0 = (size - w) // 2; y0 = (size - h) // 2
    cv[y0:y0 + h, x0:x0 + w] = a
    Image.fromarray(cv).save(f'{out}/{name}.png')
    print(name, f'{w}x{h}')
    return cv


def centred(name, model, size=12):
    a = cut(model)
    h, w = a.shape[:2]
    cv = np.zeros((size, size, 4), np.uint8)
    x0 = max(0, (size - w) // 2); y0 = max(0, (size - h) // 2)
    a = a[:size - y0, :size - x0]
    cv[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    Image.fromarray(cv).save(f'{OUT}/{name}.png')
    print(name, f'{w}x{h}')
    return cv


if __name__ == '__main__':
    made = []
    made.append(icon('sling', item_sling()))
    made.append(icon('throwing_stick', item_throwing_stick(0.12)))
    made.append(icon('scroll', item_scroll()))
    for i in range(4):
        made.append(centred(f'stick_{i}', item_throwing_stick(i * math.pi / 4, flat=True)))
    made.append(centred('sling_stone', sling_stone(), size=6))
    if len(sys.argv) > 1:
        from PIL import ImageDraw
        S = 12
        sheet = Image.new('RGB', (len(made) * 17 * S + 8, 16 * S + 40), (58, 52, 70))
        d = ImageDraw.Draw(sheet)
        d.text((6, 4), 'INTERNAL TEST  -  new item icons, 12x', fill=(255, 200, 60))
        for i, cv in enumerate(made):
            im = Image.fromarray(cv).resize((cv.shape[1] * S, cv.shape[0] * S), Image.NEAREST)
            sheet.paste(im, (6 + i * 17 * S, 28), im)
        sheet.save(sys.argv[1]); print(sys.argv[1])
