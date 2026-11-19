"""Ground and props for the rest of Ashkel: sand and sea, cliffs, docks and boats, the olive
terraces' dry-stone walls, the bakery oven, the potter's yard, the oracle's awning, a dream
bridge of moonlight, and the ziggurat's interior (blue glazed brick in the manner of the great
gates of the old cities)."""
import math
import numpy as np
from px import Canvas, R, OUTLINE, blob, pick, BAYER, ramp
import ashkel_art as A

R['sea'] = ramp('#0e1a3a', '#16285a', '#1e3c78', '#2a5a96', '#4a84b8', '#8ec0de')
R['rock'] = ramp('#241e2a', '#3a3040', '#564a58', '#766a74', '#9a8e92', '#c0b4b2')
R['glaze'] = ramp('#0c1438', '#16246a', '#20389a', '#2e54c0', '#4a7ad8', '#86aaee')
R['brick'] = ramp('#2a1a1e', '#46282a', '#6a3c34', '#8e5642', '#b07658', '#cc9a76')
R['moon'] = ramp('#3a3a6a', '#5a62a0', '#8a96d0', '#b8c6ee', '#e4ecff')


# ------------------------------------------------------------------ outdoors
def sand(cv, x0, y0, w, h, seed=51):
    s = R['sand']
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, s[4])
    for _ in range(int(w * h / 60)):
        x, y = int(rng.integers(x0, x0 + w)), int(rng.integers(y0, y0 + h))
        cv.px(x, y, s[3] if rng.random() < 0.7 else s[5])
    for _ in range(int(w * h / 900)):     # ripples left by the wind
        x, y = int(rng.integers(x0, x0 + w - 8)), int(rng.integers(y0, y0 + h))
        L = int(rng.integers(4, 9))
        for k in range(L):
            cv.px(x + k, y + (1 if k in (0, L - 1) else 0), s[3])


def water(cv, x0, y0, w, h, seed=52, deep_from=None):
    """Open water: depth bands that wander with the swell and blend through an ordered dither,
    then loose rows of wave marks (a lit crest over a little shadow)."""
    sea = R['sea']
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.283, 3)
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

    def depth(x, y):
        if deep_from is None:
            return 0.0
        wob = (math.sin(x * 0.045 + ph[0]) * 0.05 + math.sin(y * 0.06 + ph[1]) * 0.05
               + math.sin((x + y) * 0.11 + ph[2]) * 0.025)
        return max(0.0, min(1.0, deep_from(x, y) + wob))

    def level(x, y):
        d = depth(x, y)
        base = 3 if d < 0.35 else 2 if d < 0.7 else 1
        for edge in (0.35, 0.7):
            z = 0.03
            if edge - z < d < edge + z:
                frac = (d - (edge - z)) / (2 * z)
                shallow = 3 if edge == 0.35 else 2
                base = shallow - 1 if bayer[y % 4, x % 4] < frac else shallow
        return base

    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            cv.px(x, y, sea[level(x, y)])
    for _ in range(int(w * h / 230)):
        x, y = int(rng.integers(x0 + 2, x0 + w - 7)), int(rng.integers(y0 + 1, y0 + h - 2))
        L = int(rng.integers(3, 6))
        lv = level(x, y)
        hi = sea[min(5, lv + 2)]
        for k in range(L):
            cv.px(x + k, y, hi if 0 < k < L - 1 else sea[min(5, lv + 1)])
        cv.px(x, y + 1, sea[max(0, lv - 1)])
        cv.px(x + L - 1, y + 1, sea[max(0, lv - 1)])


def shore(cv, is_water, x0, y0, w, h):
    """Foam where the sea meets the sand, and a wet dark band on the sand."""
    sea = R['sea']; s = R['sand']
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if is_water(x, y):
                if not is_water(x, y - 1) or not is_water(x - 1, y) or not is_water(x + 1, y) or not is_water(x, y + 1):
                    cv.px(x, y, sea[5])
                elif not is_water(x, y - 2) or not is_water(x - 2, y) or not is_water(x + 2, y):
                    cv.px(x, y, sea[4] if (x + y) % 2 else sea[3])
            else:
                near = any(is_water(x + dx, y + dy) for dx, dy in ((0, 1), (0, 2), (1, 0), (-1, 0), (0, -1)))
                if near:
                    cv.px(x, y, s[2])


def cliff(cv, x0, y0, w, h, seed=53, grass_top=True):
    """A rock face seen from the front: lit top lip (with grass), strata, cracks, dark foot."""
    rk = R['rock']
    rng = np.random.default_rng(seed)
    for y in range(y0, y0 + h):
        t = (y - y0) / max(1, h)
        for x in range(x0, x0 + w):
            band = int((y - y0 + int(math.sin(x * 0.21 + seed) * 2)) / 5) % 3
            base = 3 if band == 0 else 2
            if t > 0.8:
                base = 1
            col = rk[base]
            cv.px(x, y, col)
    for _ in range(int(w * h / 90)):
        x, y = int(rng.integers(x0, x0 + w)), int(rng.integers(y0 + 2, y0 + h - 2))
        for k in range(int(rng.integers(2, 6))):
            cv.px(x, y + k, rk[1])
            x += int(rng.integers(-1, 2))
    for x in range(x0, x0 + w):
        cv.px(x, y0, rk[5]); cv.px(x, y0 + 1, rk[4])
        cv.px(x, y0 + h - 1, OUTLINE)
    if grass_top:
        g = R['grass']
        for x in range(x0, x0 + w):
            k = int(rng.integers(1, 4))
            for j in range(k):
                cv.px(x, y0 + j, g[3] if j == 0 else g[2])


def dock(cv, x0, y0, w, h):
    wd = R['wood']
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            plank = ((x - x0) // 6)
            col = wd[3] if plank % 2 else wd[2]
            if (x - x0) % 6 == 5:
                col = wd[1]
            if (y - y0 + plank * 7) % 23 == 0:
                col = wd[1]
            cv.px(x, y, col)
    cv.hline(x0, x0 + w - 1, y0, wd[4])
    for x in (x0 + 1, x0 + w - 3):
        for y in range(y0, y0 + h, 18):
            cv.rect(x, y, 2, 4, wd[0])
    cv.rect(x0, y0 + h, w, 3, R['sea'][1])


def boat(cv, cx, cy, seed=54):
    wd = R['wood']; cl = R['cloth_w']
    layer = Canvas(cv.w, cv.h)
    for y in range(cy - 6, cy + 7):
        for x in range(cx - 18, cx + 19):
            dx, dy = (x - cx) / 18, (y - cy) / 6
            if dx * dx * (1 + 0.6 * abs(dy)) + dy * dy <= 1:
                inner = dx * dx + (dy * 1.4) ** 2 < 0.62
                layer.px(x, y, wd[1] if inner else (wd[3] if y < cy else wd[2]))
    for x in range(cx - 12, cx + 13, 6):
        layer.vline(x, cy - 3, cy + 3, wd[3])
    blob(layer, cx + 6, cy, 4, 2.5, cl, seed=seed, dither=0.05)  # a folded net
    layer.outline()
    cv.blit(layer, 0, 0)


def drystone_wall(cv, x0, y0, w, h, seed=55):
    """The terrace walls: rough fieldstones stacked without mortar, a turf lip on top."""
    rk = R['rock']; g = R['grass']
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, rk[1])
    y = y0
    while y < y0 + h:
        bh = int(rng.integers(3, 6))
        x = x0 - int(rng.integers(0, 6))
        while x < x0 + w:
            bw = int(rng.integers(5, 11))
            base = int(rng.choice([2, 3, 3, 4]))
            for yy in range(y, min(y + bh - 1, y0 + h)):
                for xx in range(max(x, x0), min(x + bw - 1, x0 + w)):
                    c = rk[base]
                    if yy == y:
                        c = rk[min(5, base + 1)]
                    elif yy == y + bh - 2 or xx == x + bw - 2:
                        c = rk[base - 1]
                    cv.px(xx, yy, c)
            x += bw
        y += bh
    for x in range(x0, x0 + w):
        k = int(rng.integers(1, 3))
        for j in range(k):
            cv.px(x, y0 - 1 + j, g[3] if j == 0 else g[2])
    cv.hline(x0, x0 + w - 1, y0 + h - 1, OUTLINE)


def stone_steps(cv, x0, y0, w, h, n=3):
    lime = R['lime']
    sh = max(2, h // n)
    for k in range(n):
        ty = y0 + k * sh
        for yy in range(ty, min(y0 + h, ty + sh)):
            for xx in range(x0, x0 + w):
                cv.px(xx, yy, lime[4] if yy == ty else lime[3] if yy < ty + sh - 1 else lime[2])
    cv.vline(x0 - 1, y0, y0 + h - 1, OUTLINE); cv.vline(x0 + w, y0, y0 + h - 1, OUTLINE)


def dirt(cv, x0, y0, w, h, seed=56):
    d = R['dirt']
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, d[3])
    for _ in range(int(w * h / 40)):
        x, y = int(rng.integers(x0, x0 + w)), int(rng.integers(y0, y0 + h))
        cv.px(x, y, d[2] if rng.random() < 0.7 else d[4])
    for _ in range(int(w * h / 300)):
        x, y = int(rng.integers(x0, x0 + w - 2)), int(rng.integers(y0, y0 + h - 1))
        cv.px(x, y, R['rock'][3]); cv.px(x + 1, y, R['rock'][4]); cv.px(x, y + 1, R['rock'][1])


def oven(cv, cx, by, frame=0):
    """The bakery's clay dome oven, fire still glowing at its mouth after forty nights."""
    m = R['mud']; fr = R['fire']
    layer = Canvas(cv.w, cv.h)
    blob(layer, cx, by - 9, 12, 10, m, bias=0.05, dither=0.06)
    for y in range(by - 10, by - 2):
        for x in range(cx - 4, cx + 5):
            if (x - cx) ** 2 / 16 + (y - (by - 2)) ** 2 / 64 <= 1:
                layer.px(x, y, fr[2] if y > by - 6 else fr[1])
    rng = np.random.default_rng(frame)
    for k in range(8):
        x = cx + int(rng.integers(-3, 4)); y = by - 3 - int(rng.integers(0, 4))
        layer.px(x, y, fr[4] if k % 2 else fr[3])
    layer.rect(cx - 4, by - 21, 3, 3, m[1])
    layer.outline()
    cv.blit(layer, 0, 0)


def awning(cv, x, y, w, col_a, col_b):
    for yy in range(y, y + 8):
        for xx in range(x, x + w):
            stripe = ((xx - x) // 4) % 2
            c = col_a if stripe else col_b
            cv.px(xx, yy, c)
    for xx in range(x, x + w, 4):
        cv.px(xx + 1, y + 8, col_a); cv.px(xx + 2, y + 8, col_a)
    cv.hline(x, x + w - 1, y, R['wood'][3])


def potters_wheel(cv, cx, by):
    wd = R['wood']; m = R['mud']
    layer = Canvas(cv.w, cv.h)
    blob(layer, cx, by - 3, 6, 2.5, wd, dither=0.04)
    blob(layer, cx, by - 7, 3, 3, m, dither=0.04)
    layer.outline()
    cv.blit(layer, 0, 0)


def kiln(cv, cx, by, frame=0):
    br = R['brick']; fr = R['fire']
    layer = Canvas(cv.w, cv.h)
    for y in range(by - 24, by):
        t = (y - (by - 24)) / 24
        half = 8 + t * 4
        for x in range(int(cx - half), int(cx + half) + 1):
            c = br[3] if (x + (y // 3) * 2) % 6 else br[2]
            if (y - by) % 3 == 0:
                c = br[1]
            layer.px(x, y, c)
    layer.rect(cx - 3, by - 8, 7, 7, fr[2])
    layer.rect(cx - 2, by - 6, 5, 5, fr[3 + frame % 2])
    layer.outline()
    cv.blit(layer, 0, 0)


def moon_bridge(cv, pts, width=10, frame=0):
    """A path of moonlight laid across nothing: planks of pale light with dark seams.
    pts is a polyline of (x, y); drawn on a prop canvas."""
    mn = R['moon']
    layer = Canvas(cv.w, cv.h)
    for (a, b) in zip(pts, pts[1:]):
        ax, ay = a; bx, by = b
        L = max(1, int(math.hypot(bx - ax, by - ay)))
        for i in range(L + 1):
            t = i / L
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            nx, ny = -(by - ay) / L, (bx - ax) / L
            for k in range(-width // 2, width // 2 + 1):
                px_, py_ = int(round(x + nx * k)), int(round(y + ny * k))
                edge = abs(k) >= width // 2
                seam = (i + frame) % 7 == 0
                c = mn[1] if edge else (mn[2] if seam else (mn[4] if abs(k) < width // 4 else mn[3]))
                layer.px(px_, py_, c)
    cv.blit(layer, 0, 0)


def chasm(cv, x0, y0, w, h, seed=57):
    """A drop into the dark. The far lip is lit by the moon; the near side is a cliff that
    falls away in strata until there's nothing but violet night, with a few motes of dust."""
    rk = R['rock']
    rng = np.random.default_rng(seed)
    face = min(30, h // 3)
    for y in range(y0, y0 + h):
        t = (y - y0) / max(1, h)
        for x in range(x0, x0 + w):
            if y - y0 < 3:
                c = rk[4] if y - y0 == 0 else rk[3] if y - y0 == 1 else rk[1]
            elif y - y0 < 10:
                # the far wall, dropping into shadow
                k = (y - y0 - 3) / 7
                c = rk[1] if BAYER[y & 3, x & 3] / 16 > k else (20, 14, 32, 255)
            elif y >= y0 + h - face:
                # the near cliff, seen from above as it falls away
                k = (y - (y0 + h - face)) / face
                band = int((y + int(math.sin(x * 0.19) * 2)) / 4) % 2
                base = rk[2] if band else rk[1]
                c = base if BAYER[y & 3, x & 3] / 16 < k * 1.3 else (22, 16, 34, 255)
            else:
                d = abs(t - 0.45) * 2
                c = (14 + int(8 * (1 - d)), 10 + int(6 * (1 - d)), 28 + int(14 * (1 - d)), 255)
                if BAYER[y & 3, x & 3] / 16 > 0.9 - (1 - d) * 0.2 and (x + y) % 3 == 0:
                    c = (30, 22, 50, 255)
            cv.px(x, y, c)
    for x in range(x0, x0 + w):
        cv.px(x, y0 + h - 1, rk[4])
        cv.px(x, y0 + h - 2, rk[3])
    for _ in range(int(w * h / 500)):
        x, y = int(rng.integers(x0, x0 + w)), int(rng.integers(y0 + 12, y0 + h - face))
        cv.px(x, y, (70, 62, 110, 255))


# ------------------------------------------------------------------ inside the ziggurat
def glazed_wall(cv, x0, y0, w, h, seed=60, frieze=True):
    """Blue glazed brick with a band of striding bulls in gold, like the old processional gates."""
    gl = R['glaze']; gd = R['gold']
    rng = np.random.default_rng(seed)
    bw, bh = 8, 4
    for y in range(y0, y0 + h):
        row = (y - y0) // bh
        for x in range(x0, x0 + w):
            off = (row % 2) * (bw // 2)
            lx, ly = (x - x0 + off) % bw, (y - y0) % bh
            c = gl[3]
            if ly == 0:
                c = gl[4]
            elif ly == bh - 1 or lx == bw - 1:
                c = gl[1]
            cv.px(x, y, c)
    if frieze and h > 16:
        fy = y0 + h // 2 - 5
        cv.rect(x0, fy, w, 11, gl[2])
        cv.hline(x0, x0 + w - 1, fy, gd[4]); cv.hline(x0, x0 + w - 1, fy + 10, gd[3])
        for bx in range(x0 + 4, x0 + w - 14, 26):
            # a striding bull in profile, gold on blue
            for (dx, dy) in [(1, 3), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 3), (9, 2), (10, 1), (11, 1),
                             (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 4), (9, 3), (10, 3), (11, 2), (12, 2),
                             (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (9, 4), (10, 4),
                             (2, 5), (3, 6), (4, 7), (6, 5), (7, 6), (8, 7), (9, 5), (10, 6), (11, 7), (0, 2), (0, 3), (10, 0), (12, 0)]:
                cv.px(bx + dx, fy + 1 + dy, gd[4] if dy < 3 else gd[3])
    cv.hline(x0, x0 + w - 1, y0 + h - 1, OUTLINE)


def tile_floor(cv, x0, y0, w, h, seed=61):
    """Big fired-clay floor tiles, one to a grid square: each a slightly different burn, a lit
    top-left edge, a dark joint, here and there a chip or a crack, worn paler where feet go."""
    br = R['brick']
    rng = np.random.default_rng(seed)
    T = 16
    tones = {}
    for ty in range((h + T - 1) // T + 1):
        for tx in range((w + T - 1) // T + 1):
            r = rng.random()
            tones[(tx, ty)] = (3 if r < 0.55 else 2 if r < 0.9 else 4, rng.random() < 0.12, int(rng.integers(3, 12)), int(rng.integers(3, 12)))
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            tx, ty = (x - x0) // T, (y - y0) // T
            lx, ly = (x - x0) % T, (y - y0) % T
            base, cracked, cx, cy = tones[(tx, ty)]
            c = br[base]
            if lx == T - 1 or ly == T - 1:
                c = br[1]
            elif lx == 0 or ly == 0:
                c = br[min(5, base + 1)]
            elif cracked and (lx - cx) == (ly - cy) // 2 and 0 <= ly - cy < 6:
                c = br[base - 1]
            elif (x * 7 + y * 13) % 29 == 0:
                c = br[base - 1]          # grit
            cv.px(x, y, c)


def pillar(cv, cx, by, h=34):
    lime = R['lime']; gd = R['gold']
    layer = Canvas(cv.w, cv.h)
    for y in range(by - h, by):
        for x in range(cx - 5, cx + 6):
            u = (x - cx) / 5
            c = lime[4] if u < -0.4 else lime[3] if u < 0.4 else lime[2]
            if (x - cx) % 3 == 0:
                c = lime[max(0, [4, 3, 2][0 if u < -0.4 else 1 if u < 0.4 else 2] - 1)]
            layer.px(x, y, c)
    layer.rect(cx - 7, by - h - 4, 15, 4, lime[4]); layer.hline(cx - 7, cx + 7, by - h - 4, lime[5])
    layer.rect(cx - 7, by - 3, 15, 3, lime[3])
    layer.hline(cx - 6, cx + 6, by - h - 1, gd[3])
    layer.outline()
    cv.blit(layer, 0, 0)


def bronze_door(cv, cx, by, w=28, h=30, kind='lock'):
    br = R['bronze']; gd = R['gold']
    layer = Canvas(cv.w, cv.h)
    x = cx - w // 2
    for y in range(by - h, by):
        for xx in range(x, x + w):
            c = br[3] if (xx - x) < w // 2 else br[2]
            if (xx - x) % 7 == 0:
                c = br[1]
            layer.px(xx, y, c)
    layer.vline(cx, by - h, by - 1, OUTLINE)
    for yy in (by - h + 5, by - 8):
        layer.hline(x, x + w - 1, yy, gd[4])
    if kind == 'lock':
        layer.rect(cx - 2, by - h // 2 - 3, 5, 6, gd[4]); layer.px(cx, by - h // 2 - 1, OUTLINE); layer.px(cx, by - h // 2, OUTLINE)
    else:   # the bull lock
        for (dx, dy) in ((-5, -4), (-4, -5), (4, -5), (5, -4), (-3, -3), (3, -3)):
            layer.px(cx + dx, by - h // 2 + dy, gd[5])
        layer.rect(cx - 3, by - h // 2 - 3, 7, 6, gd[4]); layer.px(cx - 1, by - h // 2 - 1, OUTLINE); layer.px(cx + 1, by - h // 2 - 1, OUTLINE)
    layer.outline()
    cv.blit(layer, 0, 0)


def block(cv, cx, by):
    lime = R['lime']
    layer = Canvas(cv.w, cv.h)
    layer.rect(cx - 8, by - 15, 16, 15, lime[3])
    layer.rect(cx - 8, by - 15, 16, 4, lime[4]); layer.hline(cx - 8, cx + 7, by - 15, lime[5])
    layer.rect(cx - 8, by - 4, 16, 4, lime[2])
    for (dx, dy) in ((-4, -8), (3, -9), (0, -6)):
        layer.px(cx + dx, by + dy, lime[2])
    layer.outline()
    cv.blit(layer, 0, 0)


def plate(cv, cx, cy, pressed=False):
    br = R['bronze']
    for y in range(cy - 6, cy + 6):
        for x in range(cx - 7, cx + 7):
            edge = y in (cy - 6, cy + 5) or x in (cx - 7, cx + 6)
            cv.px(x, y, OUTLINE if edge else (br[2] if pressed else br[3]) if (x + y) % 5 else br[4])


def stairs_up(cv, cx, by, w=32, h=24):
    lime = R['lime']
    for k in range(6):
        y = by - (k + 1) * (h // 6)
        inset = k * 2
        cv.rect(cx - w // 2 + inset, y, w - 2 * inset, h // 6, lime[4] if k % 2 == 0 else lime[3])
        cv.hline(cx - w // 2 + inset, cx + w // 2 - inset - 1, y, lime[5])
    cv.rect(cx - w // 2 + 12, by - h - 6, w - 24, 6, (8, 6, 16, 255))


def bull_statue(cv, cx, by):
    """A bronze bull's head on a plinth: it breathes fire on a beat (fire-reflect puzzles)."""
    br = R['bronze']; lime = R['lime']
    layer = Canvas(cv.w, cv.h)
    layer.rect(cx - 9, by - 8, 18, 8, lime[2]); layer.hline(cx - 9, cx + 8, by - 8, lime[4])
    blob(layer, cx, by - 15, 7, 6, br, dither=0.04)
    for s in (-1, 1):
        for k in range(5):
            layer.px(cx + s * (6 + k), by - 19 - (k if k < 3 else 4 - k + 2), br[5] if k > 2 else br[4])
    layer.px(cx - 3, by - 16, (255, 200, 80, 255)); layer.px(cx + 3, by - 16, (255, 200, 80, 255))
    layer.rect(cx - 2, by - 12, 5, 2, (40, 10, 10, 255))
    layer.outline()
    cv.blit(layer, 0, 0)


def path(cv, pts, width=16, seed=58):
    """A trodden dirt path along a polyline: ragged edges, pebbles, a darker worn middle."""
    d = R['dirt']
    rng = np.random.default_rng(seed)
    layer = np.zeros((cv.h, cv.w), np.uint8)
    for (a, b) in zip(pts, pts[1:]):
        ax, ay = a; bx, by = b
        L = max(1, int(math.hypot(bx - ax, by - ay)))
        for i in range(L + 1):
            t = i / L
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            r = width / 2 + math.sin(i * 0.31 + seed) * 1.5 + rng.uniform(-0.8, 0.8)
            for yy in range(int(y - r - 1), int(y + r + 2)):
                for xx in range(int(x - r - 1), int(x + r + 2)):
                    if 0 <= xx < cv.w and 0 <= yy < cv.h:
                        dd = math.hypot(xx - x, yy - y)
                        if dd <= r:
                            layer[yy, xx] = max(layer[yy, xx], 2 if dd < r * 0.45 else 1)
    ys, xs = np.nonzero(layer)
    for (y, x) in zip(ys, xs):
        mid = layer[y, x] == 2
        c = d[2] if mid and (x * 7 + y * 3) % 5 == 0 else d[3]
        if not mid and (x + y) % 7 == 0:
            c = d[4]
        cv.px(x, y, c)
    for _ in range(len(xs) // 90):
        k = int(rng.integers(0, len(xs)))
        x, y = xs[k], ys[k]
        cv.px(x, y, R['rock'][3]); cv.px(x + 1, y, R['rock'][4])
    # a dark lip where grass gives way
    for (y, x) in zip(ys, xs):
        for (dx, dy) in ((0, 1), (1, 0), (-1, 0), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= xx < cv.w and 0 <= yy < cv.h and layer[yy, xx] == 0:
                cv.px(xx, yy, R['grass'][1])


def palm(cv, cx, by, h=40, seed=59):
    """A date palm: a ringed trunk leaning a little, a burst of fronds, a cluster of dates."""
    tr = R['trunk']; lf = R['leaf']
    rng = np.random.default_rng(seed)
    layer = Canvas(cv.w, cv.h)
    lean = rng.uniform(-0.18, 0.18)
    for k in range(h):
        x = cx + int(lean * k)
        y = by - k
        for dx in (-1, 0, 1):
            c = tr[3] if dx < 0 else tr[2] if dx == 0 else tr[1]
            if k % 3 == 0:
                c = tr[1]
            layer.px(x + dx, y, c)
    top = (cx + int(lean * h), by - h)
    for a in range(0, 360, 36):
        ang = math.radians(a + rng.uniform(-10, 10))
        L = rng.uniform(11, 16)
        for i in range(int(L)):
            t = i / L
            x = top[0] + math.cos(ang) * i
            y = top[1] + math.sin(ang) * i * 0.6 + (t * t) * 7
            c = lf[4] if t < 0.4 else lf[3] if t < 0.75 else lf[2]
            layer.px(int(x), int(y), c)
            if 0.2 < t < 0.9:
                layer.px(int(x), int(y) + 1, lf[2])
    for (dx, dy) in ((-1, 2), (1, 2), (0, 3), (-2, 3), (2, 3)):
        layer.px(top[0] + dx, top[1] + dy, R['bronze'][2])
    layer.outline()
    cv.blit(layer, 0, 0)


def cart(cv, cx, by, seed=60):
    wd = R['wood']
    layer = Canvas(cv.w, cv.h)
    layer.rect(cx - 13, by - 14, 26, 8, wd[3]); layer.hline(cx - 13, cx + 12, by - 14, wd[4])
    for x in range(cx - 12, cx + 12, 5):
        layer.vline(x, by - 13, by - 8, wd[1])
    blob(layer, cx - 3, by - 16, 7, 4, R['straw'], seed=seed, dither=0.05)
    for wx in (cx - 9, cx + 9):
        for y in range(by - 7, by):
            for x in range(wx - 3, wx + 4):
                if math.hypot(x - wx, y - (by - 4)) < 3.5:
                    layer.px(x, y, wd[2] if math.hypot(x - wx, y - (by - 4)) > 1.5 else wd[4])
    layer.rect(cx + 13, by - 11, 9, 2, wd[2])
    layer.outline()
    cv.blit(layer, 0, 0)


def crates(cv, cx, by):
    wd = R['wood']
    layer = Canvas(cv.w, cv.h)
    for (ox, oy) in ((-6, 0), (5, 0), (0, -9)):
        x, y = cx + ox - 5, by + oy - 9
        layer.rect(x, y, 11, 9, wd[3]); layer.hline(x, x + 10, y, wd[4]); layer.hline(x, x + 10, y + 4, wd[1])
        layer.vline(x, y, y + 8, wd[2]); layer.vline(x + 10, y, y + 8, wd[1])
    layer.outline()
    cv.blit(layer, 0, 0)


def laundry(cv, x0, x1, y, seed=61):
    """A line strung between rooftops with washing that hasn't dried in forty nights."""
    rng = np.random.default_rng(seed)
    cols = [R['cloth_w'][3], R['red'][3], R['lapis'][3], R['straw'][3], R['cloth_w'][4]]
    for x in range(x0, x1):
        sag = int(4 * math.sin(math.pi * (x - x0) / max(1, x1 - x0)))
        cv.px(x, y + sag, R['wood'][1])
    x = x0 + 6
    while x < x1 - 10:
        w = int(rng.integers(5, 9)); h = int(rng.integers(6, 11))
        sag = int(4 * math.sin(math.pi * (x - x0) / max(1, x1 - x0)))
        c = cols[int(rng.integers(0, len(cols)))]
        cv.rect(x, y + sag + 1, w, h, c)
        cv.hline(x, x + w - 1, y + sag + h, OUTLINE)
        cv.vline(x + w - 1, y + sag + 1, y + sag + h, OUTLINE)
        x += w + int(rng.integers(3, 7))


def carpet(cv, x0, y0, w, h):
    """A processional runner: oxblood wool, gold borders, a repeating rosette."""
    rd = R['red']; gd = R['gold']
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            lx, ly = x - x0, y - y0
            c = rd[2] if (lx + ly) % 2 else rd[1]
            if lx in (1, w - 2):
                c = gd[3]
            elif lx in (0, w - 1):
                c = OUTLINE
            elif lx in (3, w - 4):
                c = gd[2] if ly % 4 < 2 else rd[3]
            else:
                cx, cy = w // 2, (ly % 24) - 12
                d = abs(lx - cx) + abs(cy)
                if d in (5, 6):
                    c = gd[3]
                elif d < 3:
                    c = R['lapis'][3]
            cv.px(x, y, c)


def floor_inlays(cv, x0, y0, w, h, inset=12, band=7):
    """A lapis border set into the floor all the way round the room, edged in gold and studded
    with gold squares, like the edge of a great rug in stone; small lapis lozenges at its corners."""
    lp = R['lapis']; gd = R['gold']
    bx0, by0, bx1, by1 = x0 + inset, y0 + inset, x0 + w - inset - 1, y0 + h - inset - 1
    for y in range(by0, by1 + 1):
        for x in range(bx0, bx1 + 1):
            dx = min(x - bx0, bx1 - x); dy = min(y - by0, by1 - y)
            d = min(dx, dy)
            if d >= band:
                continue
            if d == 0 or d == band - 1:
                c = gd[3] if (x + y) % 2 else gd[4]
            else:
                c = lp[3] if d in (1, band - 2) else lp[2]
                along = x if dy < dx else y
                if d == band // 2 and along % 10 in (0, 1):
                    c = gd[4]
            cv.px(x, y, c)
    for (cx, cy) in ((bx0 + band // 2, by0 + band // 2), (bx1 - band // 2, by0 + band // 2),
                     (bx0 + band // 2, by1 - band // 2), (bx1 - band // 2, by1 - band // 2)):
        for yy in range(cy - 5, cy + 6):
            for xx in range(cx - 5, cx + 6):
                dd = abs(xx - cx) + abs(yy - cy)
                if dd <= 5:
                    cv.px(xx, yy, gd[3] if dd == 5 else lp[3] if dd > 2 else lp[4])


def cobweb(cv, x, y, flip=False):
    c = (150, 146, 170, 255)
    for k in range(10):
        xx = x - k if flip else x + k
        if (k % 2) == 0:
            cv.px(xx, y + k // 2, c)
        cv.px(xx if not flip else xx, y, c) if k < 8 else None
    for k in range(8):
        cv.px(x - k // 2 if flip else x + k // 2, y + k, c)


# ------------------------------------------------------------------ thick walls, doorways, the summit
def floor_shadow(cv, x0, y0, w, h, fade='x+', strength=110):
    """A soft shadow cast onto the floor by a wall: solid near the wall, dithered as it fades."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if fade == 'x+':
                k = (x - x0) / max(1, w)
            elif fade == 'x-':
                k = (x0 + w - 1 - x) / max(1, w)
            else:
                k = (y - y0) / max(1, h)
            if k < 0.45 or (k < 0.85 and (x + y) % 2 == 0):
                cv.px(x, y, (8, 6, 26, int(strength * (1 - k * 0.6))))


def wall_top(cv, x0, y0, w, h, inner='right', seed=70, merlons=False):
    """The top of a thick glazed-brick wall seen from above: capstones with a lit bevel, a gold
    coping line along the edge that faces the room, a dark outer lip. merlons=True cuts
    crenellations into the outer edge (for a parapet open to the sky)."""
    gl = R['glaze']; gd = R['gold']
    rng = np.random.default_rng(seed)
    vertical = inner in ('right', 'left')
    L = h if vertical else w            # length along the wall
    T = w if vertical else h            # thickness across it
    stone = 12
    for a in range(L):
        blk = a // stone
        la = a % stone
        shade = 3 if (blk * 7 + seed) % 5 else 2
        for b in range(T):
            # b = 0 at the outer edge, T-1 at the edge facing the room
            if vertical:
                x = x0 + (b if inner == 'right' else T - 1 - b); y = y0 + a
            else:
                x = x0 + a; y = y0 + (b if inner == 'down' else T - 1 - b)
            c = gl[shade]
            if la == 0:
                c = gl[min(5, shade + 1)]
            elif la == stone - 1:
                c = gl[1]
            if b <= 1:
                c = gl[0] if b == 0 else gl[1]
            elif b == T - 3:
                c = gd[3]
            elif b == T - 2:
                c = gd[4] if la % 4 else gd[3]
            elif b == T - 1:
                c = OUTLINE
            if merlons and b <= 3 and (a // 8) % 2 == 1:
                c = None                    # gap between merlons: the void shows through
            if c is not None:
                cv.px(x, y, c)


def doorway(cv, cx, by, w=40, h=16, down=True):
    """An opening in the front wall with steps going down into the dark, framed in gold."""
    gd = R['gold']; lime = R['lime']
    x0 = cx - w // 2
    for k in range(h):
        y = by - h + k
        t = k / max(1, h - 1)
        c = lime[3] if k % 4 == 0 else lime[2] if t < 0.4 else lime[1] if t < 0.75 else (14, 10, 24, 255)
        cv.hline(x0 + 2, x0 + w - 3, y, c)
    for s in (x0, x0 + w - 2):
        cv.vline(s, by - h, by - 1, gd[3]); cv.vline(s + 1, by - h, by - 1, gd[4] if s == x0 else gd[2])


def night_drop(cv, x0, y0, w, h, seed=110):
    """What you see over the parapet at the top of the ziggurat: a long fall into the night,
    the sleeping city a scatter of embers far below, wisps of mist drifting between."""
    rng = np.random.default_rng(seed)
    top = np.array([12, 16, 40]); bot = np.array([5, 6, 16])
    for y in range(y0, y0 + h):
        t = (y - y0) / max(1, h - 1)
        base = (top * (1 - t) + bot * t).astype(int)
        for x in range(x0, x0 + w):
            cv.px(x, y, (*base, 255))
    # mist bands, dithered
    for _ in range(int(w * h / 900)):
        mx, my = int(rng.integers(x0, x0 + w)), int(rng.integers(y0, y0 + h))
        L = int(rng.integers(10, 30))
        for k in range(L):
            if (mx + k + my) % 2 == 0:
                cv.px(mx + k, my, (34, 40, 74, 255))
    # the city's lamps and banked fires, far below
    for _ in range(int(w * h / 260)):
        lx, ly = int(rng.integers(x0, x0 + w)), int(rng.integers(y0, y0 + h))
        warm = rng.random()
        c = (255, 176, 84, 255) if warm > 0.35 else (190, 120, 70, 255)
        cv.px(lx, ly, c)
        if warm > 0.9:
            cv.px(lx + 1, ly, (150, 90, 52, 255))
