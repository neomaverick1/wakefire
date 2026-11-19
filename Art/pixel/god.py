"""Ninhal, god of the sky, asleep on his own summit: a giant lying on his back, head to the
left, a horned crown, a white beard spread over his chest, a night-blue robe sewn with gold
stars, hands folded on his belly. Two frames: the belly rises and falls.

Built with the bull's little depth-buffer renderer, so he reads as one heavy, lit figure.

    python3 god.py             export Resources/Sprites/god.png/.json
    python3 god.py preview
"""
import sys, math, json
import numpy as np
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import bull
from bull import Scene, rgb, O
from px import Canvas

OUT = bull.OUT
CELL = 144
FX, FY = 72, 92

bull.RAMPS.update({
    'robe': [rgb(h) for h in ('#5a6ad8', '#3a48b0', '#283488', '#1c2464', '#141a48', '#0c1030')],
    'skin': [rgb(h) for h in ('#ffe2c2', '#f0c094', '#d89a6c', '#b0744c', '#7c4c32', '#4c2c1e')],
    'beard': [rgb(h) for h in ('#ffffff', '#f4f2fa', '#dcd8ea', '#b8b2cc', '#8a84a2', '#5c5874')],
    'gold': [rgb(h) for h in ('#fff6c8', '#ffd760', '#e8a838', '#b87424', '#7a4618', '#46240c')],
    'leather': [rgb(h) for h in ('#a87850', '#86583a', '#64402a', '#46281c', '#2e1a12', '#1c0f0a')],
})
bull.SEAM.update({'robe': rgb('#080a20'), 'skin': rgb('#5a3020'), 'beard': rgb('#6a6484'), 'gold': rgb('#4a2a0c'), 'leather': rgb('#1c0f0a')})


def figure(breath=0):
    old = (bull.CELL, bull.YY, bull.XX)
    bull.CELL = CELL
    bull.YY, bull.XX = np.mgrid[0:CELL, 0:CELL].astype(np.float64) + 0.5
    try:
        cx, by = FX - 2, FY - 22
        S = Scene()
        # robe-covered legs and the sandalled feet, toes up
        for s_ in (-1, 1):
            S.limb((cx + 14, by + s_ * 6, 2), (cx + 44, by + s_ * 5, 1), 7.4, 5.4, 'robe')
            S.ell(cx + 47, by + s_ * 5.5, 3, 4.6, 5.2, 4, 'gold', power=2.4)              # the gold hem
            S.ell(cx + 52, by + s_ * 5.5, 8, 3.0, 3.6, 7, 'skin')
            S.limb((cx + 51, by + s_ * 5.5 - 3, 12), (cx + 51, by + s_ * 5.5 + 3, 12), 0.9, 0.9, 'leather')
        # body and belly (the belly rises when he breathes in)
        S.ell(cx - 6, by, 0, 25, 15, 10 + breath, power=2.2, mat='robe')
        S.ell(cx + 4, by, 2 + breath, 15, 12.5, 9 + breath, mat='robe')
        # the gold sash
        S.limb((cx + 10, by - 13, 9 + breath), (cx + 10, by + 13, 9 + breath), 2.0, 2.0, 'gold')
        # shoulders, sleeves and the folded hands
        for s_ in (-1, 1):
            S.ell(cx - 22, by + s_ * 13, 3, 7, 6, 7, 'robe')
            S.limb((cx - 20, by + s_ * 14, 8), (cx - 6, by + s_ * 11, 12 + breath), 4.6, 4.2, 'robe')
            S.limb((cx - 6, by + s_ * 11, 12 + breath), (cx + 2, by + s_ * 4, 14 + breath), 4.2, 3.8, 'robe')
            S.ell(cx + 4, by + s_ * 2.5, 16 + breath, 3.8, 3.2, 3, 'skin')
        # head (top of it to the left), white hair spread on the stone
        hx, hy = cx - 38, by
        S.ell(hx - 8, hy, -2, 8, 13, 6, 'beard')
        S.ell(hx, hy, 6, 10, 9.5, 8, 'skin')
        # the long beard over the chest
        S.ell(hx + 19 - breath * 0.5, hy, 12 + breath, 11, 6.8, 5, 'beard', power=2.2)
        S.limb((hx + 26, hy, 13 + breath), (hx + 34, hy + 1, 13 + breath), 5.2, 1.6, 'beard')
        # moustache and brows
        for s_ in (-1, 1):
            S.limb((hx + 7, hy, 15), (hx + 10, hy + s_ * 7, 14), 1.8, 1.4, 'beard')
            S.limb((hx - 3, hy + s_ * 2, 15), (hx - 3, hy + s_ * 7, 15), 1.6, 1.3, 'beard')
        S.ell(hx + 3, hy, 16, 2.8, 2.0, 3, 'skin')                                        # the nose
        # the horned crown, pointing away from his head
        S.limb((hx - 11, hy, 3), (hx - 24, hy, 3), 7.6, 5.6, 'gold')
        S.ell(hx - 25, hy, 3, 3.2, 4.4, 4, 'gold')
        cv = S.render(1.0)
        # closed eyes: two short dark lines under the brows
        for s_ in (-1, 1):
            for k in range(3):
                cv.px(hx, int(hy + s_ * (2.5 + k)), rgb('#5a3020'))
        # the horns wrapped round the crown: ivory bands
        for k in range(3):
            x = int(hx - 13 - k * 4)
            for y in range(int(hy - 6 + k), int(hy + 7 - k)):
                if cv.a[y, x, 3] > 0 and tuple(cv.a[y, x]) != O:
                    cv.px(x, y, rgb('#fff4dc') if y < hy else rgb('#d8c8a4'))
                    cv.px(x - 1, y, rgb('#a89070'))
        # gold stars sewn into the robe
        for (sx, sy) in ((-16, -9), (-4, 8), (6, -8), (-10, 3), (20, -4), (28, 6), (34, -3), (14, 10), (-24, 7)):
            x, y = cx + sx, int(by + sy)
            if cv.a[y, x, 3] > 0 and cv.a[y, x, 2] > cv.a[y, x, 0]:
                cv.px(x, y, rgb('#ffe27a'))
                for (ox, oy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if cv.a[y + oy, x + ox, 2] > cv.a[y + oy, x + ox, 0]:
                        cv.px(x + ox, y + oy, rgb('#b87424'))
        return cv
    finally:
        bull.CELL, bull.YY, bull.XX = old


def export():
    from PIL import Image
    fr = [figure(0), figure(1)]
    img = Image.new('RGBA', (CELL * 2, CELL), (0, 0, 0, 0))
    for i, f in enumerate(fr):
        img.paste(f.image(), (i * CELL, 0))
    img.save(f'{OUT}/god.png')
    json.dump({"size": CELL, "pivot": [FX, FY], "anims": [{"name": "lie", "dir": "down", "row": 0, "frames": 2}]}, open(f'{OUT}/god.json', 'w'))
    print('god', img.size)


def preview(path):
    from PIL import Image, ImageDraw, ImageFont
    Z = 3
    out = Image.new('RGB', (CELL * Z * 2 + 6, CELL * Z + 40), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - Ninhal asleep (x3)', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22))
    for i in range(2):
        bg = Image.new('RGBA', (CELL, CELL), (112, 100, 88, 255))
        bg.alpha_composite(figure(i).image())
        out.paste(bg.convert('RGB').resize((CELL * Z, CELL * Z), Image.NEAREST), (i * (CELL * Z + 6), 38))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    if 'preview' in sys.argv:
        preview(bull.PREVIEWS + '/internal-test-god.png')
    else:
        export()
