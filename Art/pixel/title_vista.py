"""The picture behind the title: Ashkel asleep. A great moon rising behind the rooftop where the
watchman stands, the ziggurat over the city with the sleeping god's cold light at its summit and
torches up its stair, three depths of flat roofs with a few lamps still burning, and a winged
bull on the gate tower looking back at him. Everything in it is one of the game's own models,
drawn smaller and bluer the further off it stands; only the sky is painted.
  python3 title_vista.py            writes Resources/UI/title_bg.png and title_hero.json"""
import json, math, sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from PIL import Image
from scipy import ndimage
import forge, town
from forge import Model, M, Mat, RAMPS, fbm, hash2, m_brick, m_mottle, m_stripes, m_ashlar

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/UI'
W, H = 560, 248                       # a 16:9 screen shows the middle 384 columns and the bottom 216 rows
HERO = (150, 196)                     # where the watchman's feet rest
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
HAZE = np.array([34.0, 32.0, 78.0])
NIGHT = np.array([0.60, 0.64, 0.92])


LOW = 0.30          # the city is seen from a rooftop, not from the sky: depth is drawn this much flatter


def scaled(model, s, depth=LOW):
    """The same model, s times the size, and seen from lower down (its depth pressed flat)."""
    k = np.array([s, s * depth, s])
    for i in range(len(model.P)):
        model.P[i] = model.P[i] * k
    model.lights = [(x * s, y * s, z * s, r * s, c, st) for (x, y, z, r, c, st) in model.lights]
    return model


class Picture:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3))
        self.glow = np.zeros((H, W, 3))          # light that spills: added back, blurred, at the end

    def paste(self, model, x, y, far=0.0, dim=1.0, ink=True, seed=0, glow=1.0):
        """Draw a model with its origin at (x, y). far = how much of the night air lies in front of it."""
        d = forge.draw(model, seed=seed, ink=ink, shadow=False)
        h, w = d.rgba.shape[:2]
        x0, y0 = int(round(x - d.ax)), int(round(y - d.ay))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xa >= xb or ya >= yb:
            return d
        sub = d.rgba[ya - y0:yb - y0, xa - x0:xb - x0].astype(float)
        a = sub[..., 3:4] / 255.0
        c = sub[..., :3]
        # what burns keeps its colour: lamps in windows, flames, the god's light
        hot = d.burning[ya - y0:yb - y0, xa - x0:xb - x0]
        g = c * NIGHT * dim
        g = g * (1 - far) + HAZE * far
        g = np.where(hot[..., None], c * (1 - far * 0.45) + HAZE * far * 0.45, g)
        self.rgb[ya:yb, xa:xb] = self.rgb[ya:yb, xa:xb] * (1 - a) + g * a
        self.glow[ya:yb, xa:xb] *= (1 - a)
        self.glow[ya:yb, xa:xb] += np.where((hot & (a[..., 0] > 0))[..., None], c / 255.0, 0) * glow * (1 - far * 0.5)
        return d

    def veil(self, y0, y1, colour, strength, seed=0, stretch=5.0):
        """Mist lying in a band: thickest in the middle of it, drifting in long streaks."""
        yy, xx = np.mgrid[0:H, 0:W]
        t = np.clip((yy - y0) / max(1, y1 - y0), 0, 1)
        prof = np.sin(t * math.pi) ** 1.3
        n = fbm(xx / (16.0 * stretch), yy / 9.0, seed, 4)
        a = np.clip(prof * (0.35 + 0.9 * n) * strength, 0, 0.9)
        a = np.where(BAYER[yy & 3, xx & 3] < (a * 16 % 1), np.ceil(a * 16) / 16, np.floor(a * 16) / 16)
        self.rgb = self.rgb * (1 - a[..., None]) + np.array(colour, float) * a[..., None]
        self.glow *= (1 - a[..., None] * 0.6)


# ------------------------------------------------------------------ the sky
def sky(p):
    yy, xx = np.mgrid[0:H, 0:W]
    stops = [(0.0, (8, 6, 26)), (0.34, (16, 14, 48)), (0.62, (30, 24, 76)), (0.80, (58, 36, 92)), (0.92, (96, 52, 96)), (1.0, (128, 66, 86))]
    t = yy / 204.0
    col = np.zeros((H, W, 3))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        k = np.clip((t - t0) / (t1 - t0), 0, 1)
        m = (t >= t0) & (t <= t1 + 1e-6)
        col[m] = (np.array(c0) + (np.array(c1) - np.array(c0)) * k[..., None])[m]
    col[t > 1] = stops[-1][1]
    # step the gradient in bands and break each edge with an ordered dither, the pixel way
    q = 6.0
    col = np.floor(col / q + BAYER[yy & 3, xx & 3][..., None]) * q
    p.rgb[:] = col
    # stars: many faint, a few bright with rays, thinning toward the glow of the city
    rng = np.random.default_rng(11)
    for _ in range(520):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, 190))
        if rng.random() < (y / 190.0) ** 1.6:
            continue
        b = rng.uniform(70, 235) * (1 - 0.5 * y / 190.0)
        tint = np.array([1.0, 1.0, 1.08]) if rng.random() < 0.7 else np.array([1.08, 0.96, 0.86])
        p.rgb[y, x] = np.clip(np.maximum(p.rgb[y, x], b * tint), 0, 255)
        if b > 190 and rng.random() < 0.5:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    p.rgb[y + dy, x + dx] = np.maximum(p.rgb[y + dy, x + dx], b * 0.42 * tint)
    # the river of stars, a faint slant of dust across the top
    band = np.exp(-(((yy - 30) + (xx - 280) * 0.16) / 20.0) ** 2) * fbm(xx / 26.0, yy / 26.0, 5, 4)
    dust = (hash2(xx, yy, 77) > 1 - band * 0.16)
    p.rgb[dust] = np.maximum(p.rgb[dust], np.array([92, 90, 138]))


def moon(p, cx, cy, r):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    # its light in the air round it
    halo = np.clip(1 - (d - r) / (r * 1.5), 0, 1) ** 2 * 0.55
    halo = np.floor(halo * 9 + BAYER[yy & 3, xx & 3]) / 9
    p.rgb += halo[..., None] * np.array([96, 100, 150]) * (d > r)[..., None]
    disc = d <= r
    u = ((xx - cx) * 0.5 + (yy - cy) * 0.85) / r                       # darker toward the lower right limb
    base = 232 - np.clip(u, -1, 1) * 22 - np.clip((d / r) ** 6, 0, 1) * 26
    seas = fbm((xx - cx) / 13.0 + 3, (yy - cy) / 11.0 + 7, 21, 4)
    seas2 = fbm((xx - cx) / 5.0, (yy - cy) / 5.0, 22, 3)
    mare = (seas > 0.56) & (np.hypot(xx - cx + r * 0.2, yy - cy + r * 0.1) < r * 0.86)
    tone = base - np.where(mare, 44, 0) - np.where(seas2 > 0.68, 10, 0)
    tone = np.floor(tone / 9 + BAYER[yy & 3, xx & 3] * 0.8) * 9
    col = np.dstack([tone, tone - 4, tone - 22])
    # craters: a bright rim on the side toward the light
    rng = np.random.default_rng(3)
    for _ in range(9):
        a, rr = rng.uniform(0, 6.28), rng.uniform(0, r * 0.8)
        kx, ky, kr = cx + math.cos(a) * rr, cy + math.sin(a) * rr, rng.uniform(1.6, 3.6)
        dd = np.hypot(xx + 0.5 - kx, yy + 0.5 - ky)
        col[(dd < kr)] -= 16
        col[(np.abs(dd - kr) < 0.7) & (xx < kx) & (yy < ky + 1)] += 22
    p.rgb[disc] = np.clip(col, 0, 255)[disc]
    edge = (d > r - 1.2) & disc
    p.rgb[edge] = p.rgb[edge] * 0.86 + np.array([20, 20, 46]) * 0.14
    p.glow[disc] += 0.05


def clouds(p, cx, cy):
    """Long thin bars of cloud low in the sky, silvered where they cross near the moon."""
    yy, xx = np.mgrid[0:H, 0:W]
    n = fbm(xx / 70.0, yy / 7.0, 31, 4) * np.exp(-((yy - 150) / 34.0) ** 2)
    a = np.clip((n - 0.40) * 4.0, 0, 0.72)
    a = np.floor(a * 6 + BAYER[yy & 3, xx & 3]) / 6
    near = np.clip(1 - np.hypot(xx - cx, (yy - cy) * 1.4) / 150.0, 0, 1)
    col = np.array([30, 26, 66]) + near[..., None] * np.array([84, 86, 122]) * (n - 0.36)[..., None] * 3.0
    p.rgb = p.rgb * (1 - a[..., None]) + np.clip(col, 0, 255) * a[..., None]


# ------------------------------------------------------------------ the ziggurat, whole
def ziggurat():
    m = Model()
    brick = M('brick', 3.7, m_brick(8, 4, jitter=0.7))
    rib = M('brick', 4.3, m_brick(8, 4, jitter=0.5))
    terrace = M('sandstone', 4.6, m_mottle(8, 0.3))
    band = M('lapis', 3.6)
    gold = M('gold', 4.3)
    stone = M('sandstone', 4.4, m_stripes(2, 'v'))
    wall = M('sandstone', 3.6)
    widths = [15.4, 12.6, 10.0, 7.6, 5.4]
    heights = [1.30, 1.20, 1.10, 1.0, 0.92]
    z, y, back = 0.0, 0.0, 0.17
    flights = []
    for i, (w, h) in enumerate(zip(widths, heights)):
        m.part(); m.box(-w / 2, y, z, w / 2, y + 2.0, z + h, brick, top=terrace)
        m.part()
        for bx in np.arange(-w / 2 + 0.35, w / 2 - 0.5, 0.92):
            if abs(bx + 0.2) > 1.15:
                m.box(bx, y - 0.03, z, bx + 0.4, y, z + h - 0.2, rib)
        m.box(-w / 2, y - 0.02, z + h - 0.2, w / 2, y, z + h - 0.09, band)
        m.box(-w / 2, y - 0.03, z + h - 0.09, w / 2, y, z + h, gold if i == len(widths) - 1 else terrace)
        flights.append((y, z, h))
        z += h; y += back
    # the stair: one straight flight up the middle, tier to tier, between low walls
    m.part()
    for (fy, fz, fh) in flights:
        run = 1.0
        m.quad((-0.62, fy - run, fz), (0.62, fy - run, fz), (0.62, fy, fz + fh), (-0.62, fy, fz + fh), stone, two=True)
        for sx in (-0.86, 0.62):
            m.quad((sx, fy - run, fz + 0.16), (sx + 0.24, fy - run, fz + 0.16), (sx + 0.24, fy, fz + fh + 0.16), (sx, fy, fz + fh + 0.16), wall, two=True)
    # torches up the stair, one pair to a terrace
    fire = Mat(RAMPS['glow'], 3.2, glow=True)
    for (fy, fz, fh) in flights:
        for sx in (-1.12, 1.0):
            m.part(); m.box(sx + 0.03, fy - 0.05, fz + fh, sx + 0.09, fy - 0.02, fz + fh + 0.32, M('wood', 2.6))
            m.part(); m.box(sx, fy - 0.07, fz + fh + 0.3, sx + 0.13, fy - 0.02, fz + fh + 0.46, fire)
    # the house of the god on top: glazed blue, a gold cornice, stepped merlons, and the door his light comes out of
    w = 2.5
    m.part(); m.box(-w / 2, y, z, w / 2, y + 1.0, z + 1.05, M('lapis', 3.4, m_brick(6, 3, jitter=0.6)), top=terrace)
    m.part(); m.box(-w / 2 - 0.04, y - 0.03, z + 0.86, w / 2 + 0.04, y, z + 0.96, gold)
    m.part()
    for k in range(7):
        bx = -w / 2 + 0.07 + k * 0.345
        m.box(bx, y - 0.02, z + 1.05, bx + 0.2, y + 0.12, z + 1.22, terrace)
    god = Mat(np.array([(90, 130, 220), (150, 190, 250), (206, 228, 255), (240, 248, 255), (255, 255, 255)], float), 3.4, glow=True)
    m.part(); m.box(-0.3, y - 0.03, z, 0.3, y, z + 0.66, god)
    m.part(); m.box(-0.38, y - 0.04, z, -0.3, y, z + 0.72, gold); m.box(0.3, y - 0.04, z, 0.38, y, z + 0.72, gold); m.box(-0.38, y - 0.04, z + 0.66, 0.38, y, z + 0.74, gold)
    return m, z + 0.4, y


def tower():
    """The gate tower the winged bull stands on: dressed stone, a band of glazed blue, merlons."""
    m = Model()
    st = M('sandstone', 4.0, m_ashlar(14, 7))
    m.part(); m.box(-2.6, 0, 0, 2.6, 2.2, 3.6, st, top=M('sandstone', 4.5, m_mottle(8, 0.3)))
    m.part(); m.box(-2.62, -0.03, 2.75, 2.62, 0, 3.05, M('lapis', 3.6, m_brick(8, 4, jitter=0.6)))
    m.part(); m.box(-2.62, -0.04, 3.05, 2.62, 0, 3.13, M('gold', 4.2)); m.box(-2.62, -0.04, 2.67, 2.62, 0, 2.75, M('gold', 4.0))
    m.part()
    for k in range(6):
        bx = -2.6 + k * 0.9
        m.box(bx, -0.02, 3.6, bx + 0.52, 0.3, 3.95, st, top=M('sandstone', 4.6))
    return m


def build():
    p = Picture()
    mcx, mcy, mr = HERO[0] - 8, 150, 47
    sky(p)
    clouds(p, mcx, mcy)
    moon(p, mcx, mcy, mr)
    # far off: the line of the precinct wall and the land beyond it
    yy, xx = np.mgrid[0:H, 0:W]
    ridge = 196 - (fbm(xx / 90.0, 0 * yy, 41, 3) * 12 - 4)
    land = yy >= ridge
    p.rgb[land] = np.array([26, 22, 58]); p.glow[land] = 0
    # the ziggurat
    zm, zz, zy = ziggurat()
    zx, zbase, zs = 296, 234, 0.92
    scaled(zm, zs)
    p.paste(zm, zx, zbase, far=0.40, dim=0.74, ink=False, seed=3, glow=1.6)
    gx, gy = zx, int(round(zbase - (zz + zy * LOW) * zs * 16))
    # the god's light: a breath of cold fire at the door, and a thin shaft going up from the roof into the sky
    d = np.hypot(xx - gx, (yy - gy) * 1.15)
    p.rgb += (np.clip(1 - d / 30.0, 0, 1) ** 2.2)[..., None] * np.array([60, 92, 176])
    shaft = np.exp(-((xx - gx) / 2.6) ** 2) * np.clip((gy - 10 - yy) / 70.0, 0, 1) * np.clip(yy / 50.0, 0, 1) * (0.6 + 0.4 * fbm(xx / 3.0, yy / 14.0, 9, 2))
    shaft = np.floor(shaft * 7 + BAYER[yy & 3, xx & 3]) / 7 * (yy < gy - 8)
    p.rgb += shaft[..., None] * np.array([46, 66, 128])
    p.veil(176, 226, (44, 38, 92), 0.70, seed=5)
    # the far roofs: small, close together, most of them dark
    rng = np.random.default_rng(8)
    x = -30
    while x < W + 40:
        w = float(rng.uniform(4.2, 7.5)); h = float(rng.uniform(1.5, 2.6))
        hm = town.house(w, 2.6, h, seed=int(rng.integers(0, 999)), plain=True, lit=rng.random() < 0.5, roof_stuff=False)
        s = 0.42
        p.paste(scaled(hm, s), x + w * 8 * s, 216 + int(rng.integers(-2, 3)), far=0.56, dim=0.74, ink=False, seed=int(x))
        x += w * 16 * s + rng.uniform(-2, 4)
    p.veil(200, 232, (40, 34, 84), 0.5, seed=6)
    # the middle of the city: taller houses, palms between, a lamp here and there
    x = -40
    k = 0
    while x < W + 60:
        w = float(rng.uniform(5.0, 8.0)); h = float(rng.uniform(1.7, 2.6))
        up = (float(-w / 2 + 0.5), float(-w / 2 + 3.2), 1.6, 1.3) if rng.random() < 0.4 else None
        hm = town.house(w, 2.6, h, seed=int(rng.integers(0, 999)), plain=True, lit=rng.random() < 0.6, upper=up)
        s = 0.68
        p.paste(scaled(hm, s), x + w * 8 * s, 238 + int(rng.integers(-3, 4)), far=0.32, dim=0.80, seed=int(x) + 5)
        if k % 2 == 1:
            p.paste(scaled(town.palm(seed=k, h=3.6), s, 1.0), x + w * 16 * s + 3, 238, far=0.36, dim=0.6, seed=k)
        x += w * 16 * s + rng.uniform(2, 10); k += 1
    p.veil(226, 254, (36, 30, 76), 0.30, seed=7)
    # near: the watchman's roof on the left, the street's other roofs below, the gate tower and its guardian on the right
    hw, hd, hh = 9.0, 3.6, 4.2
    hy = HERO[1] + int(round((hh + hd * LOW * 0.5) * 16))
    p.paste(scaled(town.house(hw, hd, hh, seed=3, plaster=3, plain=True, lit=True, ladder_x=2.6), 1.0), HERO[0] + 10, hy, far=0.04, dim=0.84, seed=1)
    for (cx, w, h, sd, pl) in ((282, 7.4, 3.0, 12, 0), (20, 6.0, 3.4, 21, 2), (520, 6.0, 3.2, 23, 4)):
        p.paste(scaled(town.house(w, 3.4, h, seed=sd, plaster=pl, plain=True, lit=True), 1.0), cx, 292, far=0.10, dim=0.80, seed=sd)
    p.paste(town.palm(seed=4, h=3.8), 236, 282, far=0.06, dim=0.5, seed=2)
    p.paste(town.palm(seed=9, h=3.2), 338, 292, far=0.08, dim=0.55, seed=3)
    ty = 288
    p.paste(scaled(tower(), 1.0), 408, ty, far=0.05, dim=0.74, seed=4)
    p.paste(scaled(town.lamassu(True, scale=1.3), 1.0, 0.5), 400, ty - int(3.6 * 16) - int(2.2 * LOW * 16 * 0.45), far=0.04, dim=0.72, seed=5)
    # a palm leaning in across the moon's edge
    p.paste(town.palm(seed=2, h=4.6), 208, 238, far=0.0, dim=0.36, seed=6)
    # light that spills: lamps, torches, the door on the summit
    g1 = ndimage.gaussian_filter(p.glow, (2.2, 2.2, 0)); g2 = ndimage.gaussian_filter(p.glow, (7.0, 7.0, 0))
    p.rgb += g1 * 70 + g2 * 150
    # darker toward the corners, so the middle holds the eye
    v = 1 - 0.30 * np.clip(np.hypot((xx - W / 2) / (W / 2), (yy - H * 0.55) / (H * 0.75)) - 0.55, 0, 1) ** 1.5
    p.rgb *= v[..., None]
    img = np.clip(p.rgb, 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([img, np.full((H, W), 255, np.uint8)])).save(f'{OUT}/title_bg.png')
    json.dump({"frames": 4, "w": 16, "h": 37, "x": HERO[0] - 8, "y": HERO[1] - 37}, open(f'{OUT}/title_hero.json', 'w'))
    print('title backdrop', W, H, 'hero at', HERO)
    return img


if __name__ == '__main__':
    img = build()
    if len(sys.argv) > 1:
        from PIL import ImageDraw
        im = Image.fromarray(img).resize((W * 3, H * 3), Image.NEAREST)
        dr = ImageDraw.Draw(im)
        dr.text((6, 5), "INTERNAL TEST  -  title backdrop, not the final look", fill=(255, 200, 60))
        dr.rectangle([88 * 3, 32 * 3, (88 + 384) * 3 - 1, H * 3 - 1], outline=(255, 80, 80))
        im.save(sys.argv[1])
