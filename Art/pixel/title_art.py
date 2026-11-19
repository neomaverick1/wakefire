"""The title: Ashkel at night under a huge moon, the ziggurat in the middle with the sleeping
god's glow at its summit, rooftops and lit windows in front; the WAKEFIRE logo in bronze and
fire with a khopesh beneath it."""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas, R, OUTLINE, BAYER, pick

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/UI'
W, H = 480, 248
OY = H - 216


def sky(cv):
    top = np.array([10, 8, 30]); mid = np.array([30, 28, 70]); low = np.array([70, 52, 96])
    for y in range(H):
        t = y / H
        c = top + (mid - top) * min(1, t * 1.6) if t < 0.62 else mid + (low - mid) * ((t - 0.62) / 0.38)
        for x in range(W):
            d = BAYER[y & 3, x & 3] / 16 - 0.5
            cc = np.clip(c + d * 10, 0, 255).astype(int)
            cv.px(x, y, (int(cc[0]), int(cc[1]), int(cc[2]), 255))
    rng = np.random.default_rng(4)
    for _ in range(140):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, int(H * 0.55)))
        b = int(rng.integers(120, 230))
        cv.px(x, y, (b, b, min(255, b + 20), 255))
        if rng.random() < 0.08:
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.px(x + dx, y + dy, (b // 2, b // 2, b // 2 + 30, 255))


def moon(cv, cx, cy, r):
    for y in range(cy - r - 6, cy + r + 7):
        for x in range(cx - r - 6, cx + r + 7):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                u = ((x - cx) + (y - cy)) / (2 * r)
                base = 236 - int(max(0, u) * 40)
                col = (base, base - 6, base - 22, 255)
                # maria
                for (mx, my, mr) in ((-6, -4, 6), (5, 3, 5), (-2, 8, 4), (8, -8, 3)):
                    if math.hypot(x - cx - mx, y - cy - my) < mr:
                        col = (base - 34, base - 38, base - 50, 255)
                cv.px(x, y, col)
            elif d <= r + 6 and BAYER[y & 3, x & 3] / 16 > (d - r) / 6 + 0.35:
                o = cv.get(x, y)
                cv.px(x, y, (min(255, o[0] + 26), min(255, o[1] + 24), min(255, o[2] + 30), 255))


def ziggurat(cv, cx, base_y):
    lime = R['lime']
    tiers = [(150, 26), (116, 22), (84, 20), (54, 18), (30, 16)]
    y = base_y
    for i, (w, h) in enumerate(tiers):
        x0 = cx - w // 2
        for yy in range(y - h, y):
            for xx in range(x0, x0 + w):
                lx = xx - x0
                shade = 1 if lx > w * 0.62 else 2
                if yy == y - h:
                    shade = 3
                col = lime[shade]
                if (yy - (y - h)) % 5 == 4 and lx % 12 != 0:
                    col = lime[max(0, shade - 1)]
                cv.px(xx, yy, (col[0] * 6 // 10, col[1] * 6 // 10, int(col[2] * 0.8), 255))
        # the great stair up the middle
        for yy in range(y - h, y):
            for xx in range(cx - 7 + i, cx + 8 - i):
                col = lime[3] if (yy % 3) == 0 else lime[2]
                cv.px(xx, yy, (col[0] * 7 // 10, col[1] * 7 // 10, int(col[2] * 0.85), 255))
        y -= h
    # the shrine at the top, and the god's glow
    cv.rect(cx - 9, y - 12, 18, 12, (60, 46, 70, 255))
    cv.rect(cx - 3, y - 9, 6, 9, (255, 214, 140, 255))
    for yy in range(y - 40, y + 6):
        for xx in range(cx - 40, cx + 41):
            d = math.hypot(xx - cx, (yy - (y - 6)) * 1.3)
            if 4 < d < 40 and BAYER[yy & 3, xx & 3] / 16 > d / 40 + 0.15:
                o = cv.get(xx, yy)
                cv.px(xx, yy, (min(255, o[0] + 40), min(255, o[1] + 28), min(255, o[2] + 10), 255))
    return y


def rooftops(cv):
    rng = np.random.default_rng(9)
    mud = R['mud']
    x = -10
    while x < W + 10:
        w = int(rng.integers(26, 52))
        h = int(rng.integers(18, 40))
        top = H - h
        for yy in range(top, H):
            for xx in range(x, x + w):
                c = mud[1] if xx < x + w - 4 else mud[0]
                cv.px(xx, yy, (c[0] * 5 // 10, c[1] * 5 // 10, int(c[2] * 0.75), 255))
        cv.hline(x, x + w - 1, top, (mud[2][0] * 6 // 10, mud[2][1] * 6 // 10, int(mud[2][2] * 0.8), 255))
        # lit windows
        for k in range(int(rng.integers(0, 3))):
            wx = x + int(rng.integers(4, max(5, w - 8))); wy = top + int(rng.integers(6, max(7, h - 8)))
            cv.rect(wx, wy, 3, 4, (255, 190, 96, 255))
            cv.px(wx + 1, wy, (255, 230, 170, 255))
        x += w + int(rng.integers(-6, 4))


def logo():
    """WAKEFIRE in Roman capitals, cast in bronze, with a flame rising from the I and a khopesh
    lying beneath the word."""
    size = 44
    font = ImageFont.truetype('/srv/Wakefire/Art/fonts/cinzel_Cinzel[wght].ttf', size)
    try:
        font.set_variation_by_axes([800])
    except Exception:
        pass
    text = "WAKEFIRE"
    tmp = Image.new('L', (420, 90), 0)
    d = ImageDraw.Draw(tmp)
    d.fontmode = "1"
    d.text((12, 12), text, font=font, fill=255)
    m = np.array(tmp) > 127
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    m = m[y0:y1, x0:x1]
    lw, lh = m.shape[1] + 8, m.shape[0] + 30
    cv = Canvas(lw, lh)
    br = R['bronze']; gd = R['gold']; fr = R['fire']
    ox, oy = 4, 12
    for y in range(m.shape[0]):
        t = y / m.shape[0]
        for x in range(m.shape[1]):
            if not m[y, x]:
                continue
            if t < 0.18:
                col = gd[5]
            elif t < 0.45:
                col = gd[4]
            elif t < 0.7:
                col = br[4]
            else:
                col = br[3]
            # a bright bevel on top edges, dark on the bottom edges
            if y > 0 and not m[y - 1, x]:
                col = gd[5]
            if y < m.shape[0] - 1 and not m[y + 1, x]:
                col = br[2]
            cv.px(ox + x, oy + y, col)
    # the flame of the I (the sixth letter), found from the mask's column gaps
    cols = m.any(axis=0)
    starts = [i for i in range(len(cols)) if cols[i] and (i == 0 or not cols[i - 1])]
    ends = [i for i in range(len(cols)) if cols[i] and (i == len(cols) - 1 or not cols[i + 1])]
    if len(starts) >= 6:
        ix = ox + (starts[5] + ends[5]) // 2
        for k in range(10):
            half = int(round(2.6 * math.sin(min(1, (k + 1) / 9) * math.pi * 0.85)))
            for xx in range(ix - half, ix + half + 1):
                c = fr[5] if abs(xx - ix) < half * 0.5 and k > 3 else fr[4] if abs(xx - ix) < half else fr[3]
                cv.px(xx, oy - 1 - (9 - k), c)
    # khopesh beneath: a sickle sword sweeping the width of the word
    by = oy + m.shape[0] + 6
    L = m.shape[1]
    for x in range(L):
        t = x / L
        yy = by + int(round(math.sin(t * math.pi * 1.25 - 0.35) * 4))
        thick = 2 if 0.15 < t < 0.95 else 1
        for k in range(thick):
            cv.px(ox + x, yy + k, gd[4] if k == 0 else br[3])
    cv.rect(ox - 2, by - 1, 10, 3, R['wood'][2])
    cv.outline(OUTLINE)
    return cv


def main():
    bg = Canvas(W, H)
    sky(bg)
    moon(bg, 88, 44 + OY, 20)
    ziggurat(bg, W // 2, 182 + OY)
    rooftops(bg)
    bg.save(f'{OUT}/title_bg.png')
    lg = logo()
    lg.save(f'{OUT}/title_logo.png')
    print('title', bg.w, bg.h, 'logo', lg.w, lg.h)


if __name__ == '__main__':
    main()
