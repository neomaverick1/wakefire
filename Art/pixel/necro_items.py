"""The things Azar is handed on the Hill of Sleepers, as 16 px icons: each is its model, drawn
the way the props are.  python3 necro_items.py"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from PIL import Image
import forge
import necro

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Items'


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
    Image.fromarray(cv).save(f'{OUT}/{name}.png')
    print(name, f'{w}x{h}')


def centred(name, model, size=12):
    d = forge.draw(model, seed=1, shadow=False, ink=True)
    a = d.rgba
    ys, xs = np.nonzero(a[..., 3] > 0)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape[:2]
    cv = np.zeros((size, size, 4), np.uint8)
    x0 = (size - w) // 2; y0 = (size - h) // 2
    cv[y0:y0 + h, x0:x0 + w] = a[:size - y0, :size - x0]
    Image.fromarray(cv).save(f'{OUT}/{name}.png')
    print(name, f'{w}x{h}')


if __name__ == '__main__':
    for i in range(3):
        centred(f'bolt_{i}', necro.item_bolt(i))
    icon('hill_key', necro.item_hill_key())
    icon('dawn_horn', necro.item_dawn_horn())
    icon('figs', necro.item_figs())
    icon('crown', necro.item_crown())
