"""The king's tomb's own things, as 16 px pictures for the pack: the Ghost Key.  python3 tomb_items.py [preview.png]"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from PIL import Image
import forge
import tprops

RES = '/srv/Wakefire/Assets/Wakefire/Resources'


def icon(name, model, size=16):
    d = forge.draw(model, seed=1, shadow=False)
    a = d.rgba
    ys, xs = np.nonzero(a[..., 3] > 0)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape[:2]
    if h > size or w > size:
        raise SystemExit(f'{name}: {w}x{h} does not fit {size}')
    cv = np.zeros((size, size, 4), np.uint8)
    x0 = (size - w) // 2; y0 = size - h
    cv[y0:y0 + h, x0:x0 + w] = a
    for folder in ('Items', 'Menu'):
        Image.fromarray(cv).save(f'{RES}/{folder}/{name}.png')
    print(name, f'{w}x{h}')
    return cv


if __name__ == '__main__':
    made = [icon('ghost_key', tprops.item_ghost_key())]
    if len(sys.argv) > 1:
        S = 10
        sheet = Image.new('RGBA', (len(made) * 17 * S + S, 17 * S + S), (34, 30, 44, 255))
        for i, cv in enumerate(made):
            sheet.alpha_composite(Image.fromarray(cv).resize((16 * S, 16 * S), Image.NEAREST), (S + i * 17 * S, S))
        sheet.save(sys.argv[1]); print(sys.argv[1])
