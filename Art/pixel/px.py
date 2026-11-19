"""Wakefire pixel-art toolkit: hue-shifted colour ramps, shaded shapes with dithered band edges,
foliage clumps, masonry, and the dark 1-px outlines that make sprites pop. Everything is drawn
pixel by pixel into numpy RGBA arrays."""
import math
import numpy as np
from PIL import Image

OUTLINE = (20, 12, 26, 255)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0 + 1 / 32.0


def rgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ramp(*hexes):
    return [rgb(h) for h in hexes]


# moonlit Ashkel: bright and readable, shadows lean violet, lights lean warm
R = {
    'grass': ramp('#1c3a30', '#25523c', '#306a44', '#42844c', '#5ea05a', '#84bc6c'),
    'grass_dark': ramp('#142a26', '#1c3a30', '#25523c', '#306a44'),
    'leaf': ramp('#122620', '#1a3a2c', '#245238', '#346c40', '#4e8a4a', '#76aa5e'),
    'olive': ramp('#16282e', '#22403c', '#33584a', '#4a7256', '#688e64', '#90ac7e'),
    'cypress': ramp('#0e2026', '#16302e', '#1f4238', '#2b5642', '#3c6c4c'),
    'trunk': ramp('#1e1418', '#33222a', '#4c3434', '#684840', '#8a6650'),
    'stone': ramp('#24222e', '#3c3a48', '#5a5664', '#7a7684', '#9c98a4', '#c0bcc6'),
    'lime': ramp('#342c34', '#54484c', '#786a66', '#9e8e82', '#c2b29e', '#e2d4bc'),
    'cobble': ramp('#2a2630', '#463e46', '#655a5c', '#857a76', '#a69a92', '#c6bcb0'),
    'sand': ramp('#4a3a34', '#6e5646', '#94765a', '#b89874', '#d6b98e', '#eed8ac'),
    'dirt': ramp('#2a1e28', '#433038', '#5e4446', '#7c5c56', '#9a7866'),
    'mud': ramp('#2e1c26', '#4a2c32', '#6c403e', '#8e5a4c', '#ae7a5e', '#cc9a72'),
    'wood': ramp('#1e1218', '#38222a', '#563630', '#784c3a', '#9c6846', '#bc8858'),
    'cedar': ramp('#2a1416', '#4a2420', '#6c3626', '#8e4c30', '#b0683c'),
    'bronze': ramp('#2e1a14', '#5a3418', '#8c5424', '#bc7a34', '#e2a64e', '#ffd88a'),
    'gold': ramp('#3a2610', '#6e4818', '#a87428', '#d8a238', '#f6d064', '#fff2b0'),
    'water': ramp('#0c1630', '#14244a', '#1e3a6a', '#2c588c', '#4a80b0', '#86b8d8'),
    'fire': ramp('#6a1410', '#b8301a', '#f26a1e', '#ffac34', '#ffe08a', '#fff8d8'),
    'red': ramp('#3a0e1a', '#661828', '#962838', '#c24048', '#e06a62'),
    'blue': ramp('#14163e', '#232a6a', '#34419a', '#4c60c0', '#7088dc'),
    'white': ramp('#4a4a64', '#7a7890', '#a8a4b8', '#d0ccdc', '#f2eef6'),
    'lapis': ramp('#0c1030', '#16205a', '#22348a', '#3250b4', '#5078d2', '#86a8ea'),
    'flower_y': ramp('#7a5a10', '#d8a830', '#ffe070'),
    'flower_w': ramp('#6a6a8a', '#c8c4dc', '#f6f2ff'),
    'flower_r': ramp('#6a1a30', '#c03850', '#f07888'),
    'skin': ramp('#3a2024', '#6a3c30', '#9c6446', '#cc8e62', '#e8b486'),
    'cloth_w': ramp('#3e3a50', '#6a6478', '#9890a4', '#c4bcc8', '#e6e0ea'),
    'straw': ramp('#3a2a20', '#6a4e30', '#9a7a44', '#c8a45c', '#e8cc80'),
}


class Canvas:
    def __init__(self, w, h, fill=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.uint8)
        self.a[:, :] = fill

    @staticmethod
    def load(path):
        im = np.array(Image.open(path).convert('RGBA'))
        c = Canvas(im.shape[1], im.shape[0])
        c.a = im
        return c

    def save(self, path):
        Image.fromarray(self.a).save(path)

    def image(self):
        return Image.fromarray(self.a)

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            if len(c) == 4 and c[3] < 255:
                if c[3] == 0:
                    return
                al = c[3] / 255.0
                o = self.a[y, x].astype(np.float32)
                self.a[y, x, 0:3] = (o[0:3] * (1 - al) + np.array(c[0:3]) * al).astype(np.uint8)
                self.a[y, x, 3] = max(int(o[3]), c[3])
            else:
                self.a[y, x] = c if len(c) == 4 else (*c, 255)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(self.a[y, x])
        return (0, 0, 0, 0)

    def rect(self, x0, y0, w, h, c):
        x0, y0 = int(x0), int(y0)
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(self.w, x0 + int(w)), min(self.h, y0 + int(h))
        if xb > xa and yb > ya:
            self.a[ya:yb, xa:xb] = c

    def hline(self, x0, x1, y, c):
        for x in range(int(x0), int(x1) + 1):
            self.px(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            self.px(x, y, c)

    def blit(self, src, x, y, flip=False):
        """Alpha-composite another canvas at (x, y) (top-left)."""
        s = src.a[:, ::-1] if flip else src.a
        h, w = s.shape[0], s.shape[1]
        x, y = int(x), int(y)
        xa, ya = max(0, x), max(0, y)
        xb, yb = min(self.w, x + w), min(self.h, y + h)
        if xb <= xa or yb <= ya:
            return
        sub = s[ya - y:yb - y, xa - x:xb - x].astype(np.float32)
        dst = self.a[ya:yb, xa:xb].astype(np.float32)
        al = sub[:, :, 3:4] / 255.0
        dst[:, :, 0:3] = dst[:, :, 0:3] * (1 - al) + sub[:, :, 0:3] * al
        dst[:, :, 3:4] = np.maximum(dst[:, :, 3:4], sub[:, :, 3:4])
        self.a[ya:yb, xa:xb] = dst.astype(np.uint8)

    def mask(self):
        return self.a[:, :, 3] > 0

    def outline(self, color=OUTLINE, inside=False, sides=(1, 1, 1, 1)):
        """1-px outline around the opaque shape (outside it, or on its own edge pixels)."""
        m = self.mask()
        H, W = m.shape
        edge = np.zeros_like(m)
        shifts = []
        if sides[0]: shifts.append((0, 1))
        if sides[1]: shifts.append((0, -1))
        if sides[2]: shifts.append((1, 0))
        if sides[3]: shifts.append((-1, 0))
        for dy, dx in shifts:
            s = np.zeros_like(m)
            ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
            xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
            s[yd, xd] = m[ys, xs]
            if inside:
                edge |= m & ~s
            else:
                edge |= ~m & s
        self.a[edge] = color
        return edge

    def tint(self, c, k):
        a = self.a.astype(np.float32)
        a[:, :, 0:3] = a[:, :, 0:3] * (1 - k) + np.array(c[0:3]) * k
        self.a = a.astype(np.uint8)


def pick(ramp_, v, x, y, dither=0.12):
    """Choose a ramp colour for brightness v in [0,1], with ordered dither near band edges."""
    n = len(ramp_)
    t = v * (n - 1) + (BAYER[y & 3, x & 3] - 0.5) * dither * (n - 1) * 2
    i = int(max(0, min(n - 1, round(t))))
    return ramp_[i]


def blob(cv, cx, cy, rx, ry, rp, light=(-0.55, -0.75), bias=0.0, lumps=0, seed=0, lump_r=(2.0, 3.5),
         dither=0.10, outline=True, rim=True):
    """Shaded rounded shape (bush, canopy, boulder, pot). lumps > 0 makes a clumpy foliage surface."""
    rng = np.random.default_rng(seed)
    x0, x1 = int(math.floor(cx - rx - 1)), int(math.ceil(cx + rx + 1))
    y0, y1 = int(math.floor(cy - ry - 1)), int(math.ceil(cy + ry + 1))
    L = np.array([light[0], light[1], 0.75])
    L = L / np.linalg.norm(L)
    bumps = [(cx + rng.uniform(-rx, rx), cy + rng.uniform(-ry, ry), rng.uniform(*lump_r)) for _ in range(lumps)]
    layer = Canvas(cv.w, cv.h)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d2 = dx * dx + dy * dy
            if lumps:
                # scalloped edge: a pixel is in if it's inside the ellipse or inside a bump near the rim
                inside = d2 <= 1.0
                hgt = math.sqrt(max(0.0, 1 - d2)) if inside else 0.0
                for (bx, by, br) in bumps:
                    ddx, ddy = (x + 0.5 - bx) / br, (y + 0.5 - by) / br
                    q = ddx * ddx + ddy * ddy
                    if q < 1.0:
                        h2 = math.sqrt(1 - q) * 0.55
                        if h2 > hgt - 0.25:
                            inside = inside or (d2 < 1.25)
                            n = np.array([ddx * 0.9 + dx * 0.4, ddy * 0.9 + dy * 0.4, 0.6])
                            hgt = max(hgt, h2)
                if not inside:
                    continue
                n = np.array([dx, dy, math.sqrt(max(0.05, 1 - min(1, d2)))])
                for (bx, by, br) in bumps:
                    ddx, ddy = (x + 0.5 - bx) / br, (y + 0.5 - by) / br
                    q = ddx * ddx + ddy * ddy
                    if q < 1.0:
                        n = n + np.array([ddx, ddy, 0.2]) * (1 - q) * 0.9
            else:
                if d2 > 1.0:
                    continue
                n = np.array([dx, dy, math.sqrt(max(0.0, 1 - d2))])
            n = n / (np.linalg.norm(n) + 1e-6)
            v = 0.5 + 0.5 * float(np.dot(n, L)) + bias
            layer.px(x, y, pick(rp, max(0, min(1, v)), x, y, dither))
    if outline:
        layer.outline()
    cv.blit(layer, 0, 0)
    return layer


def noise_fill(cv, x0, y0, w, h, rp, base_i, seed=0, spots=0.06, spot_r=(1, 2), hi_i=None, lo_i=None):
    """Flat fill with sparse clumps of darker and lighter pixels (ground textures)."""
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, rp[base_i])
    n = int(w * h * spots)
    for _ in range(n):
        x = rng.integers(x0, x0 + w)
        y = rng.integers(y0, y0 + h)
        c = rp[lo_i if (lo_i is not None and rng.random() < 0.6) else (hi_i if hi_i is not None else base_i)]
        r = rng.integers(spot_r[0], spot_r[1] + 1)
        for k in range(r):
            cv.px(x + k, y, c)


def to_image(cv, scale=1):
    im = cv.image()
    if scale != 1:
        im = im.resize((cv.w * scale, cv.h * scale), Image.NEAREST)
    return im
