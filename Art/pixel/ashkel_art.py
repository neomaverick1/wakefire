"""Ashkel's tiles and props, drawn pixel by pixel: grass with tufts, limestone pavers, the city
wall and gate, mudbrick houses with cedar beam ends, olive and cypress trees, bushes, pots,
braziers, a well and a market stall. Light comes from the upper left; outlines are near-black."""
import math
import numpy as np
from px import Canvas, R, OUTLINE, blob, pick, BAYER, rgb

SHADOW = (14, 24, 38, 120)


# ------------------------------------------------------------------ ground
def grass(cv, x0, y0, w, h, seed=1, dense=1.0, flowers=0.0):
    g = R['grass']
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, g[3])
    # soft darker patches so the field isn't flat
    for _ in range(int(w * h / 2400)):
        cx, cy = rng.uniform(x0, x0 + w), rng.uniform(y0, y0 + h)
        rx, ry = rng.uniform(6, 14), rng.uniform(4, 8)
        for y in range(int(cy - ry), int(cy + ry)):
            for x in range(int(cx - rx), int(cx + rx)):
                if x0 <= x < x0 + w and y0 <= y < y0 + h:
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                    if d < 1 and (d < 0.6 or BAYER[y & 3, x & 3] > d):
                        cv.px(x, y, g[2])
    # tufts: little dark "v"s with a lit tip, on a jittered grid
    step = int(14 / max(0.3, dense))
    for gy in range(y0, y0 + h, step):
        for gx in range(x0, x0 + w, step):
            if rng.random() < 0.55:
                x = gx + rng.integers(0, step - 3)
                y = gy + rng.integers(0, step - 3)
                if x + 4 >= x0 + w or y + 3 >= y0 + h:
                    continue
                cv.px(x, y + 1, g[1]); cv.px(x + 1, y + 2, g[1]); cv.px(x + 2, y + 1, g[1])
                cv.px(x + 3, y + 2, g[1]); cv.px(x + 4, y + 1, g[1])
                cv.px(x, y, g[4]); cv.px(x + 4, y, g[4]); cv.px(x + 2, y, g[5])
    for _ in range(int(w * h * flowers / 256)):
        x = int(rng.integers(x0 + 1, x0 + w - 2)); y = int(rng.integers(y0 + 1, y0 + h - 2))
        fr = R['flower_w'] if rng.random() < 0.6 else R['flower_y']
        cv.px(x, y, fr[2]); cv.px(x + 1, y, fr[1]); cv.px(x, y + 1, fr[1]); cv.px(x + 1, y + 1, g[1])


def pavers(cv, x0, y0, w, h, seed=2):
    c = R['cobble']
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, c[1])
    bw, bh = 14, 8
    row = 0
    for y in range(y0, y0 + h, bh):
        off = (row % 2) * (bw // 2)
        for x in range(x0 - off, x0 + w, bw):
            base = 3 if rng.random() > 0.12 else 2
            for yy in range(y, min(y + bh - 1, y0 + h)):
                for xx in range(max(x, x0), min(x + bw - 1, x0 + w)):
                    lx, ly = xx - x, yy - y
                    col = c[base]
                    if ly == 0 or lx == 0:
                        col = c[min(5, base + 1)]
                    if ly == bh - 2 or lx == bw - 2:
                        col = c[base - 1]
                    if (lx == 0 and ly == 0) or (lx == bw - 2 and ly == bh - 2) or (lx == 0 and ly == bh - 2) or (lx == bw - 2 and ly == 0):
                        col = c[1]
                    cv.px(xx, yy, col)
        row += 1


def edge_line(cv, mask_fn, x0, y0, w, h, col):
    """Dark border on the outside of a region (e.g. grass around a paved square)."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if not mask_fn(x, y) and (mask_fn(x + 1, y) or mask_fn(x - 1, y) or mask_fn(x, y + 1) or mask_fn(x, y - 1)):
                cv.px(x, y, col)


def soft_shadow(cv, cx, cy, rx, ry):
    """Moon shadow: a dithered dark ellipse on the ground, to the lower right of things."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d < 1 and (d < 0.55 or BAYER[y & 3, x & 3] > (d - 0.55) * 2.2):
                o = cv.get(x, y)
                if o[3]:
                    cv.px(x, y, (int(o[0] * 0.55), int(o[1] * 0.6), int(o[2] * 0.75), 255))


# ------------------------------------------------------------------ city wall and gate
def ashlar(cv, x0, y0, w, h, rp, seed=3, bw=14, bh=7, moss=True):
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, rp[1])
    row = 0
    for y in range(y0, y0 + h, bh):
        off = (row % 2) * (bw // 2)
        for x in range(x0 - off, x0 + w, bw):
            base = 3 if rng.random() > 0.25 else (2 if rng.random() < 0.7 else 4)
            for yy in range(y, min(y + bh - 1, y0 + h)):
                for xx in range(max(x, x0), min(x + bw - 1, x0 + w)):
                    lx, ly = xx - x, yy - y
                    col = rp[base]
                    if ly == 0:
                        col = rp[min(len(rp) - 1, base + 1)]
                    elif ly >= bh - 2:
                        col = rp[base - 1]
                    elif lx == 0:
                        col = rp[min(len(rp) - 1, base + 1)] if base < 4 else rp[base]
                    cv.px(xx, yy, col)
            if rng.random() < 0.15:
                sx = x + rng.integers(2, bw - 4)
                cv.px(sx, y + 2, rp[1]); cv.px(sx + 1, y + 3, rp[1])
        row += 1
    if moss:
        g = R['grass']
        for x in range(x0, x0 + w):
            if rng.random() < 0.5:
                hh = rng.integers(1, 4)
                for k in range(hh):
                    cv.px(x, y0 + h - 1 - k, g[1] if k else g[2])


def city_wall(cv, x0, y0, w, face_h=34, top_h=10, seed=4, crenel=True):
    lime = R['lime']
    # walkway on top
    cv.rect(x0, y0, w, top_h, lime[3])
    for x in range(x0, x0 + w):
        if (x // 7) % 2 == 0:
            cv.px(x, y0 + top_h - 2, lime[2])
    cv.hline(x0, x0 + w - 1, y0, lime[4])
    # merlons along the outer lip
    if crenel:
        for x in range(x0 + 2, x0 + w - 6, 12):
            cv.rect(x, y0 - 5, 7, 6, lime[4])
            cv.rect(x, y0 - 5, 7, 1, lime[5])
            cv.rect(x + 6, y0 - 5, 1, 6, lime[2])
    # the face, with its overhanging lip
    ashlar(cv, x0, y0 + top_h, w, face_h, lime, seed)
    cv.hline(x0, x0 + w - 1, y0 + top_h, lime[5])
    cv.hline(x0, x0 + w - 1, y0 + top_h + 1, lime[2])


def tower(cv, x, y, w=36, h=58, seed=5):
    lime = R['lime']
    cv.rect(x, y, w, 12, lime[4])
    cv.hline(x, x + w - 1, y, lime[5])
    for k in range(x + 2, x + w - 5, 9):
        cv.rect(k, y - 6, 6, 7, lime[4]); cv.rect(k, y - 6, 6, 1, lime[5]); cv.rect(k + 5, y - 6, 1, 7, lime[2])
    ashlar(cv, x, y + 12, w, h - 12, lime, seed, bw=12, bh=7)
    cv.vline(x, y, y + h - 1, OUTLINE); cv.vline(x + w - 1, y, y + h - 1, OUTLINE)
    # arrow slit
    cv.rect(x + w // 2 - 1, y + 22, 3, 9, OUTLINE)
    cv.px(x + w // 2, y + 23, R['fire'][2])


def gate(cv, cx, y, w=44, h=40, open_=False):
    """Cedar double doors with bronze bands and studs, under a stone arch (or swung open)."""
    lime = R['lime']; cd = R['cedar']; br = R['bronze']
    x = cx - w // 2
    if open_:
        gate_open(cv, cx, y, w, h)
        return
    # arch frame
    for yy in range(y - 6, y + h):
        for xx in range(x - 6, x + w + 6):
            dx = (xx + 0.5 - cx) / (w / 2 + 6)
            top = y + 10 - math.sqrt(max(0, 1 - dx * dx)) * 16
            if yy >= top:
                cv.px(xx, yy, lime[4] if (xx + yy) % 9 else lime[3])
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dx = (xx + 0.5 - cx) / (w / 2)
            top = y + 12 - math.sqrt(max(0, 1 - dx * dx)) * 14
            if yy >= top:
                lx = xx - x
                plank = (lx // 5) % 2
                col = cd[3] if plank else cd[2]
                if lx % 5 == 0:
                    col = cd[1]
                if abs(xx + 0.5 - cx) < 1:
                    col = OUTLINE
                cv.px(xx, yy, col)
    for by in (y + 12, y + h - 10):
        cv.rect(x, by, w, 3, br[3]); cv.hline(x, x + w - 1, by, br[4]); cv.hline(x, x + w - 1, by + 2, br[1])
        for sx in range(x + 3, x + w - 2, 6):
            cv.px(sx, by + 1, br[5])
    for ry in (y + 20, y + 26):
        cv.px(cx - 4, ry, br[4]); cv.px(cx + 3, ry, br[4])
        cv.px(cx - 4, ry + 1, br[2]); cv.px(cx + 3, ry + 1, br[2])
    # shadowed threshold
    cv.rect(x, y + h - 2, w, 2, cd[0])


def gate_open(cv, cx, y, w, h):
    """The same arch with its doors pushed inward: a dark passage and the first steps up."""
    lime = R['lime']; cd = R['cedar']; st = R['cobble']
    x = cx - w // 2
    for yy in range(y - 6, y + h):
        for xx in range(x - 6, x + w + 6):
            dx = (xx + 0.5 - cx) / (w / 2 + 6)
            top = y + 10 - math.sqrt(max(0, 1 - dx * dx)) * 16
            if yy >= top:
                cv.px(xx, yy, lime[4] if (xx + yy) % 9 else lime[3])
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dx = (xx + 0.5 - cx) / (w / 2)
            top = y + 12 - math.sqrt(max(0, 1 - dx * dx)) * 14
            if yy < top:
                continue
            lx = xx - x
            depth = (yy - y) / h
            col = (12, 8, 20, 255)
            # steps rising into the dark
            if yy > y + h - 14:
                k = (y + h - 1 - yy)
                col = st[2] if k % 4 == 0 else st[1] if k % 4 in (1, 2) else st[0]
                if k > 10:
                    col = (24, 18, 30, 255)
            # the doors, swung back against the passage walls
            if lx < 5 or lx >= w - 5:
                edge = lx == 4 or lx == w - 5
                col = cd[1] if edge else (cd[2] if (lx // 2) % 2 else cd[3])
                if (yy - y) in (12, 13, h - 10, h - 9):
                    col = R['bronze'][2]
            cv.px(xx, yy, col)
    cv.rect(x, y + h - 2, w, 2, st[1])


def torch_bracket(cv, x, y, frame=0):
    br = R['bronze']; fr = R['fire']
    cv.rect(x - 1, y + 4, 3, 5, br[2]); cv.px(x - 1, y + 4, br[4])
    cv.rect(x - 2, y + 3, 5, 2, br[3])
    flick = [(0, 0), (1, -1), (-1, 0), (0, -1)][frame % 4]
    shape = [(0, 0, 4), (-1, 1, 4), (1, 1, 4), (0, 1, 5), (-1, 2, 3), (0, 2, 5), (1, 2, 3), (0, -1, 3), (flick[0], -2 + flick[1], 2)]
    for (dx, dy, i) in shape:
        cv.px(x + dx, y + dy, fr[i])


# ------------------------------------------------------------------ houses
def mud_house(cv, x, y, w, roof_d, wall_h, door=True, window=True, seed=6, beams=True, ladder=False):
    """Flat-roofed mudbrick house in 3/4 view: roof top, parapet lip, plastered front wall."""
    mud = R['mud']; cd = R['cedar']; st = R['straw']; fr = R['fire']
    rng = np.random.default_rng(seed)
    # roof surface: packed earth with straw mats
    cv.rect(x, y, w, roof_d, mud[3])
    for k in range(int(w * roof_d / 40)):
        px_, py_ = x + rng.integers(1, w - 1), y + rng.integers(2, roof_d - 1)
        cv.px(px_, py_, mud[2]); cv.px(px_ + 1, py_, mud[4] if rng.random() < 0.3 else mud[2])
    mx, my, mw, mh = x + 4, y + 4, min(18, w - 10), max(6, roof_d - 9)
    cv.rect(mx, my, mw, mh, st[3])
    for yy in range(my, my + mh, 2):
        cv.hline(mx, mx + mw - 1, yy, st[2])
    cv.hline(mx, mx + mw - 1, my, st[4])
    # parapet: raised lip on all four sides of the roof
    cv.rect(x, y, w, 2, mud[5]); cv.rect(x, y, 2, roof_d, mud[4]); cv.rect(x + w - 2, y, 2, roof_d, mud[2])
    cv.rect(x, y + roof_d - 2, w, 2, mud[4])
    # front wall
    wy = y + roof_d
    cv.rect(x, wy, w, wall_h, mud[3])
    for k in range(int(w * wall_h / 26)):
        px_, py_ = x + rng.integers(1, w - 2), wy + rng.integers(2, wall_h - 2)
        cv.px(px_, py_, mud[2])
    # plaster patches and bricks showing through
    for k in range(3):
        bx, by = x + rng.integers(2, w - 12), wy + rng.integers(4, max(5, wall_h - 8))
        for r in range(2):
            for c in range(3):
                xx, yy = bx + c * 4 + (r % 2) * 2, by + r * 3
                cv.rect(xx, yy, 3, 2, mud[2]); cv.px(xx, yy, mud[4])
    cv.hline(x, x + w - 1, wy, mud[1])
    cv.rect(x, wy + wall_h - 3, w, 3, mud[2])
    cv.hline(x, x + w - 1, wy + wall_h - 1, mud[1])
    if beams:
        for bx in range(x + 4, x + w - 3, 9):
            cv.rect(bx, wy + 2, 3, 3, cd[3]); cv.px(bx, wy + 2, cd[4]); cv.px(bx + 2, wy + 4, cd[1])
    if door:
        dx = x + w // 2 - 5
        cv.rect(dx - 1, wy + wall_h - 22, 12, 22, mud[1])
        cv.rect(dx, wy + wall_h - 21, 10, 21, R['red'][2])
        for yy in range(wy + wall_h - 21, wy + wall_h):
            cv.px(dx + 3, yy, R['red'][1]); cv.px(dx + 7, yy, R['red'][1]); cv.px(dx + 1, yy, R['red'][3])
        cv.hline(dx, dx + 9, wy + wall_h - 21, R['red'][3])
        cv.rect(dx - 1, wy + wall_h - 23, 12, 2, cd[3])
    if window:
        wx = x + 6
        cv.rect(wx - 1, wy + 9, 9, 8, mud[1])
        cv.rect(wx, wy + 10, 7, 6, fr[3])
        cv.rect(wx, wy + 13, 7, 3, fr[2])
        cv.vline(wx + 3, wy + 10, wy + 15, cd[1]); cv.hline(wx, wx + 6, wy + 12, cd[1])
        cv.px(wx, wy + 10, fr[4]); cv.px(wx + 1, wy + 10, fr[4])
    if ladder:
        lx = x + w - 10
        for yy in range(y + roof_d - 6, wy + wall_h):
            cv.px(lx, yy, R['wood'][3]); cv.px(lx + 5, yy, R['wood'][2])
            if (yy - y) % 4 == 0:
                cv.hline(lx, lx + 5, yy, R['wood'][4])
    # outline the whole block
    layer = Canvas(cv.w, cv.h)
    layer.rect(x, y, w, roof_d + wall_h, (1, 1, 1, 255))
    for (xx, yy) in zip(*np.nonzero(layer.outline().T)):
        cv.px(xx, yy, OUTLINE)


# ------------------------------------------------------------------ trees and plants
def olive_tree(cv, cx, base_y, seed=7, size=1.0):
    """Gnarled trunk, silvery clumped canopy."""
    tr = R['trunk']
    soft_shadow(cv, cx + 6, base_y + 1, 15 * size, 5 * size)
    layer = Canvas(cv.w, cv.h)
    # trunk: two twisting strands
    for k in range(int(16 * size)):
        t = k / (16 * size)
        xo = math.sin(t * 3.2 + seed) * 2.2
        y = base_y - k
        for dx in range(-3, 3):
            col = tr[3] if dx < -1 else (tr[2] if dx < 1 else tr[1])
            if abs(dx - xo * 0.5) < 2.6 - t:
                layer.px(cx + dx + int(xo * 0.6), y, col)
    for dx in (-4, -3, 3, 4):  # roots
        layer.px(cx + dx, base_y, tr[2]); layer.px(cx + dx - (1 if dx < 0 else -1), base_y - 1, tr[2])
    layer.outline()
    cv.blit(layer, 0, 0)
    canopy_cy = base_y - int(24 * size)
    blob(cv, cx, canopy_cy, 19 * size, 13 * size, R['olive'], lumps=int(18 * size), seed=seed, lump_r=(2.6, 4.6), bias=-0.12, dither=0.06)


def cypress(cv, cx, base_y, h=46, seed=8):
    soft_shadow(cv, cx + 5, base_y, 8, 3)
    layer = Canvas(cv.w, cv.h)
    rng = np.random.default_rng(seed)
    cp = R['cypress']
    for y in range(base_y - h, base_y):
        t = (y - (base_y - h)) / h
        half = 1.5 + 6.2 * math.sin(min(1.0, t * 1.25) * math.pi * 0.62) * (0.55 + 0.45 * t)
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x + 0.5 - cx) / max(1, half)
            v = 0.58 - u * 0.45 + (0.18 if ((y + x * 2) % 7 < 2) else 0) - t * 0.18 + rng.uniform(-0.05, 0.05)
            layer.px(x, y, pick(cp, max(0, min(1, v)), x, y, 0.12))
    layer.rect(cx - 1, base_y - 2, 3, 3, R['trunk'][2])
    layer.outline()
    cv.blit(layer, 0, 0)


def bush(cv, cx, cy, seed=9, r=7, flowers=False):
    soft_shadow(cv, cx + 3, cy + r * 0.6, r * 1.1, r * 0.45)
    blob(cv, cx, cy, r, r * 0.8, R['leaf'], lumps=7, seed=seed, lump_r=(2.0, 3.2), bias=-0.06, dither=0.06)
    if flowers:
        rng = np.random.default_rng(seed)
        for _ in range(4):
            x, y = cx + rng.integers(-r + 2, r - 2), cy + rng.integers(-r // 2, r // 3)
            cv.px(x, y, R['flower_r'][2]); cv.px(x, y + 1, R['flower_r'][1])


def flower_bed(cv, x, y, w, h, seed=10):
    st = R['stone']; d = R['dirt']
    cv.rect(x, y, w, h, d[1])
    rng = np.random.default_rng(seed)
    for yy in range(y + 2, y + h - 1, 4):
        for xx in range(x + 2, x + w - 2, 4):
            fr = [R['flower_w'], R['flower_y'], R['flower_r']][int(rng.integers(0, 3))]
            ox = xx + (yy // 4) % 2 * 2
            cv.px(ox, yy, fr[2]); cv.px(ox + 1, yy, fr[1]); cv.px(ox, yy + 1, fr[1]); cv.px(ox - 1, yy, fr[1]); cv.px(ox, yy - 1, fr[2])
            cv.px(ox + 1, yy + 1, R['leaf'][2]); cv.px(ox - 1, yy + 1, R['leaf'][3])
    for xx in range(x, x + w):
        cv.px(xx, y, st[4] if xx % 4 else st[2]); cv.px(xx, y + h - 1, st[2])
    for yy in range(y, y + h):
        cv.px(x, yy, st[3]); cv.px(x + w - 1, yy, st[2])


# ------------------------------------------------------------------ props
def pot(cv, cx, by, seed=11, big=False):
    m = R['mud']
    h = 13 if big else 10
    w = 6 if big else 5
    soft_shadow(cv, cx + 3, by, w + 2, 2.5)
    layer = Canvas(cv.w, cv.h)
    for y in range(by - h, by):
        t = (y - (by - h)) / h
        half = (w * 0.45) + w * 0.62 * math.sin(min(1, t * 1.15) * math.pi * 0.9)
        if t < 0.16:
            half = w * 0.42
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x + 0.5 - cx) / max(1, half)
            v = 0.62 - u * 0.5 - (t - 0.5) * 0.15
            layer.px(x, y, pick(m, max(0, min(1, v)), x, y, 0.1))
    layer.hline(cx - int(w * 0.42), cx + int(w * 0.42), by - h, m[1])
    layer.hline(cx - int(w * 0.2), cx + int(w * 0.2), by - h, OUTLINE)
    layer.outline()
    cv.blit(layer, 0, 0)


def brazier(cv, cx, by, lit=False, frame=0):
    br = R['bronze']; fr = R['fire']
    soft_shadow(cv, cx + 4, by, 8, 2.5)
    layer = Canvas(cv.w, cv.h)
    for (dx0, dx1) in ((-5, -3), (5, 3)):  # tripod legs
        for k in range(8):
            layer.px(cx + dx0 + (dx1 - dx0) * k // 8, by - 1 - k, br[2])
    layer.rect(cx - 1, by - 9, 3, 8, br[2])
    for y in range(by - 15, by - 8):
        t = (y - (by - 15)) / 7
        half = 7 - t * 3
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x + 0.5 - cx) / half
            v = 0.52 - u * 0.4 - t * 0.25
            layer.px(x, y, pick(br, max(0, min(1, v)), x, y, 0.06))
    layer.hline(cx - 7, cx + 7, by - 15, br[4])
    layer.hline(cx - 6, cx + 6, by - 16, br[1] if not lit else fr[2])
    if not lit:
        for x in range(cx - 5, cx + 6, 2):
            layer.px(x, by - 16, R['stone'][1])
    layer.outline()
    cv.blit(layer, 0, 0)
    if lit:
        rng = np.random.default_rng(frame)
        for k in range(26):
            dx = rng.integers(-5, 6)
            hh = int(rng.integers(2, 10 - abs(dx)))
            for j in range(hh):
                cv.px(cx + dx, by - 17 - j, fr[min(5, 2 + (hh - j) // 3)])


def well(cv, cx, cy):
    st = R['stone']; wd = R['wood']; wt = R['water']
    soft_shadow(cv, cx + 5, cy + 9, 15, 4)
    layer = Canvas(cv.w, cv.h)
    # ring wall (front face) and the dark water inside
    for y in range(cy - 7, cy + 9):
        for x in range(cx - 13, cx + 14):
            d = ((x + 0.5 - cx) / 13) ** 2 + ((y + 0.5 - cy) / 7) ** 2
            if d <= 1:
                inner = ((x + 0.5 - cx) / 9) ** 2 + ((y + 0.5 - cy + 1) / 4.5) ** 2
                if inner <= 1:
                    layer.px(x, y, wt[1] if inner > 0.5 else wt[0])
                else:
                    layer.px(x, y, st[4] if y < cy else st[3])
            elif y > cy and abs(x + 0.5 - cx) <= 13 * math.sqrt(max(0, 1 - ((y - 8 - cy) / 7) ** 2)) and y < cy + 9:
                layer.px(x, y, st[2] if (x + y) % 5 else st[1])
    layer.px(cx - 3, cy - 1, wt[4]); layer.px(cx - 2, cy - 1, wt[3])
    # posts and crossbar with rope
    for px_ in (cx - 12, cx + 11):
        for y in range(cy - 20, cy + 2):
            layer.px(px_, y, wd[3]); layer.px(px_ + 1, y, wd[2])
    layer.rect(cx - 12, cy - 21, 25, 3, wd[4]); layer.hline(cx - 12, cx + 12, cy - 19, wd[2])
    for y in range(cy - 18, cy - 4):
        layer.px(cx, y, R['straw'][3])
    layer.rect(cx - 2, cy - 5, 5, 4, wd[3]); layer.hline(cx - 2, cx + 2, cy - 5, wd[4])
    layer.outline()
    cv.blit(layer, 0, 0)


def stall(cv, x, y, w=40, seed=12):
    """Market stall: striped awning, posts, a counter with jars and fruit."""
    wd = R['wood']; rd = R['red']; cw = R['cloth_w']
    soft_shadow(cv, x + w // 2 + 6, y + 34, w * 0.6, 5)
    layer = Canvas(cv.w, cv.h)
    for px_ in (x + 2, x + w - 4):
        layer.rect(px_, y + 8, 2, 24, wd[3]); layer.vline(px_ + 1, y + 8, y + 31, wd[2])
    layer.rect(x + 1, y + 20, w - 2, 9, wd[3]); layer.hline(x + 1, x + w - 2, y + 20, wd[5]); layer.hline(x + 1, x + w - 2, y + 28, wd[1])
    for k in range(5):
        pot_x = x + 6 + k * 7
        layer.rect(pot_x, y + 15, 4, 5, R['mud'][3]); layer.px(pot_x, y + 15, R['mud'][4]); layer.hline(pot_x, pot_x + 3, y + 14, R['mud'][1])
    for k in range(4):
        fx = x + 9 + k * 7
        layer.px(fx, y + 19, R['fire'][3]); layer.px(fx + 1, y + 19, R['fire'][2]); layer.px(fx, y + 18, R['fire'][4])
    # awning: stripes, scalloped front edge
    for yy in range(y, y + 10):
        for xx in range(x - 2, x + w + 2):
            stripe = ((xx - x) // 5) % 2
            col = (rd[3] if yy < y + 3 else rd[2]) if stripe else (cw[4] if yy < y + 3 else cw[3])
            if yy == y + 9 and (xx - x) % 5 in (0, 4):
                continue
            layer.px(xx, yy, col)
    layer.hline(x - 2, x + w + 1, y, (255, 240, 230, 255))
    layer.outline()
    cv.blit(layer, 0, 0)


def sign(cv, cx, by):
    wd = R['wood']
    layer = Canvas(cv.w, cv.h)
    layer.rect(cx - 1, by - 8, 2, 8, wd[2])
    layer.rect(cx - 7, by - 15, 15, 8, wd[3]); layer.hline(cx - 7, cx + 7, by - 15, wd[5]); layer.hline(cx - 7, cx + 7, by - 8, wd[1])
    for k in range(3):
        layer.hline(cx - 5 + k, cx + 3 - k, by - 13 + k * 2, wd[1])
    layer.outline()
    cv.blit(layer, 0, 0)


# ------------------------------------------------------------------ the Temple Gate square, dressed
def slabs(cv, x0, y0, w, h, rp, sw=16, sh=12, seed=21, joint=1, lo=2, hi=3):
    """Big dressed slabs with a lit top-left bevel and a shaded bottom-right one."""
    rng = np.random.default_rng(seed)
    cv.rect(x0, y0, w, h, rp[joint])
    for y in range(y0, y0 + h, sh):
        off = ((y - y0) // sh % 2) * (sw // 2)
        for x in range(x0 - off, x0 + w, sw):
            base = hi if rng.random() > 0.22 else lo
            for yy in range(y, min(y + sh - 1, y0 + h)):
                for xx in range(max(x, x0), min(x + sw - 1, x0 + w)):
                    lx, ly = xx - x, yy - y
                    col = rp[base]
                    if ly == 0 or lx == 0:
                        col = rp[min(len(rp) - 1, base + 1)]
                    elif ly == sh - 2 or lx == sw - 2:
                        col = rp[base - 1]
                    cv.px(xx, yy, col)
            if rng.random() < 0.18:   # a hairline crack
                sx, sy = x + int(rng.integers(3, sw - 5)), y + int(rng.integers(2, sh - 4))
                cv.px(sx, sy, rp[base - 1]); cv.px(sx + 1, sy + 1, rp[base - 1]); cv.px(sx + 1, sy + 2, rp[base - 1])


def kerb(cv, x0, y0, w, h, band=5):
    """A border of long dark kerbstones around a paved area."""
    c = R['cobble']
    for (bx, by, bw, bh, horiz) in ((x0, y0, w, band, True), (x0, y0 + h - band, w, band, True),
                                   (x0, y0, band, h, False), (x0 + w - band, y0, band, h, False)):
        L = bw if horiz else bh
        for k in range(0, L, 12):
            for yy in range(by, by + bh):
                for xx in range(bx, bx + bw):
                    t = (xx - bx) if horiz else (yy - by)
                    if not (k <= t < k + 12):
                        continue
                    lt = t - k
                    col = c[2]
                    if lt == 11:
                        col = c[0]
                    elif (yy == by if horiz else xx == bx):
                        col = c[3]
                    elif (yy == by + bh - 1 if horiz else xx == bx + bw - 1):
                        col = c[1]
                    cv.px(xx, yy, col)


def sigil(cv, cx, cy, r=22):
    """Ninhal's sun-and-moon worked into the paving in lapis and gold tesserae."""
    lp = R['lapis']; gd = R['gold']; c = R['cobble']
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) * 1.0
            d = math.hypot(dx, dy)
            if d > r:
                continue
            tile = ((x // 2) + (y // 2)) % 2
            grout = (x % 2 == 0 and y % 2 == 0)
            if d > r - 1.2:
                col = OUTLINE
            elif d > r - 4:
                col = lp[3] if tile else lp[2]
                if grout:
                    col = lp[1]
            elif d > r - 5.5:
                col = gd[3] if (x + y) % 3 else gd[4]
            elif d > 7.5:
                a = (math.degrees(math.atan2(dy, dx)) + 360) % 45
                ray = a < 7 or a > 38
                col = (gd[4] if d < r - 9 else gd[3]) if ray else (c[2] if tile else c[3])
                if grout and not ray:
                    col = c[1]
            elif d > 6.2:
                col = OUTLINE
            else:
                col = gd[5] if (dx < -1 and dy < -1) else gd[4]
                # the crescent moon inside the sun
                if math.hypot(dx - 1.6, dy + 0.8) < 3.6 and math.hypot(dx - 0.2, dy + 0.2) < 4.6 and math.hypot(dx - 2.8, dy + 1.6) > 3.0:
                    col = lp[3]
            cv.px(x, y, col)


def terrace(cv, x0, y0, w, top_h, face_h, step_x0, step_w, steps=3, seed=23):
    """A raised walk before the gate: slab top, an ashlar face with a lit lip, steps down the middle."""
    lime = R['lime']; c = R['cobble']
    slabs(cv, x0, y0, w, top_h, lime, 16, 10, seed, joint=1, lo=2, hi=3)
    fy = y0 + top_h
    ashlar(cv, x0, fy, w, face_h, c, seed, bw=12, bh=4, moss=False)
    cv.hline(x0, x0 + w - 1, fy, lime[5])
    cv.hline(x0, x0 + w - 1, fy + 1, lime[2])
    cv.hline(x0, x0 + w - 1, fy + face_h - 1, OUTLINE)
    # steps: treads lit, risers in shade
    sh = face_h / steps
    for k in range(steps):
        ty = int(fy + k * sh)
        inset = k * 2
        for yy in range(ty, int(fy + (k + 1) * sh)):
            for xx in range(step_x0 - inset, step_x0 + step_w + inset):
                cv.px(xx, yy, lime[4] if yy == ty else (lime[2] if yy == ty + 1 else lime[3]))
        cv.vline(step_x0 - inset - 1, ty, int(fy + (k + 1) * sh) - 1, OUTLINE)
        cv.vline(step_x0 + step_w + inset, ty, int(fy + (k + 1) * sh) - 1, OUTLINE)
    # side faces of the terrace
    for side, xx in ((0, x0), (1, x0 + w - 1)):
        cv.vline(xx, y0, fy + face_h - 1, OUTLINE)


def planter(cv, cx, by, w=28, box_h=9, hedge_h=12, seed=24):
    """A stone planter with a clipped myrtle hedge, drawn the way the classics drew hedges:
    a lit top band, leaf flecks, a dark foot."""
    layer = Canvas(cv.w, cv.h)
    x = cx - w // 2
    top = by - box_h - hedge_h
    g = R['leaf']; lime = R['lime']
    for yy in range(top, by - box_h + 2):
        for xx in range(x + 1, x + w - 1):
            # rounded top corners
            if yy - top < 2 and (xx - x < 3 - (yy - top) or x + w - 1 - xx < 3 - (yy - top)):
                continue
            t = (yy - top) / hedge_h
            col = g[4] if t < 0.22 else g[3] if t < 0.62 else g[2]
            if (xx * 3 + yy * 5) % 7 == 0:
                col = g[5] if t < 0.4 else g[4] if t < 0.8 else g[3]
            if (xx * 5 + yy * 3) % 11 == 0 and t > 0.3:
                col = g[1]
            layer.px(xx, yy, col)
    layer.hline(x + 1, x + w - 2, by - box_h + 1, g[1])
    ashlar(layer, x, by - box_h, w, box_h, lime, seed, bw=10, bh=5, moss=False)
    layer.hline(x, x + w - 1, by - box_h, lime[5])
    layer.outline()
    cv.blit(layer, 0, 0)


def banner(cv, x, y, w=10, h=28, frame=0):
    """A crimson banner of Ninhal: gold borders, the sun-disc, a swallow-tail hem."""
    rd = R['red']; gd = R['gold']; br = R['bronze']
    layer = Canvas(cv.w, cv.h)
    layer.hline(x - 2, x + w + 1, y, br[3])
    layer.px(x - 3, y, br[4]); layer.px(x + w + 2, y, br[4])
    for yy in range(y + 1, y + h):
        sway = int(round(math.sin((yy - y) / h * 2.4 + frame * 1.57) * 0.6 * (yy - y) / h))
        for k in range(w):
            xx = x + k + sway
            if yy > y + h - 5 and abs(k - (w - 1) / 2) < (yy - (y + h - 5)) * 0.9:
                continue   # swallow-tail
            col = rd[3] if k < w - 3 else rd[2]
            if k == 0 or k == w - 1:
                col = gd[3]
            elif k == 1:
                col = rd[4]
            if yy in (y + 2, y + h - 6):
                col = gd[3] if 0 < k < w - 1 else col
            layer.px(xx, yy, col)
    # the sun disc
    ex, ey = x + w // 2, y + 11
    for yy in range(ey - 3, ey + 4):
        for xx in range(ex - 3, ex + 4):
            d = math.hypot(xx - ex, yy - ey)
            if d < 2.2:
                layer.px(xx, yy, gd[5] if (xx < ex and yy < ey) else gd[4])
            elif d < 3.3 and (xx == ex or yy == ey or abs(xx - ex) == abs(yy - ey)):
                layer.px(xx, yy, gd[3])
    layer.outline()
    cv.blit(layer, 0, 0)


def pole_torch(cv, cx, by, frame=0):
    """A standing torch: bronze pole, a fire cup, flames that never quite settle."""
    br = R['bronze']; fr = R['fire']
    layer = Canvas(cv.w, cv.h)
    for yy in range(by - 22, by):
        layer.px(cx, yy, br[3]); layer.px(cx + 1, yy, br[1])
    layer.rect(cx - 2, by - 2, 6, 2, br[2])
    layer.rect(cx - 3, by - 25, 8, 3, br[3]); layer.hline(cx - 3, cx + 4, by - 25, br[4]); layer.hline(cx - 2, cx + 3, by - 23, br[1])
    layer.outline()
    cv.blit(layer, 0, 0)
    rng = np.random.default_rng(frame + 5)
    for k in range(18):
        dx = int(rng.integers(-3, 5))
        hh = int(rng.integers(2, max(3, int(9 - abs(dx - 0.5) * 1.2))))
        for j in range(hh):
            cv.px(cx + dx, by - 26 - j, fr[min(5, 2 + (hh - j) // 2)])


def amphorae(cv, cx, by, seed=31):
    """Two or three tall storage jars leaning together, pointed feet in the dust."""
    m = R['mud']
    rng = np.random.default_rng(seed)
    layer = Canvas(cv.w, cv.h)
    for k, (ox, h) in enumerate(((-5, 16), (4, 18), (0, 14))[:2 + int(rng.integers(0, 2))]):
        x = cx + ox
        for yy in range(by - h, by):
            t = (yy - (by - h)) / h
            half = 1.5 if t < 0.12 else (3.6 * math.sin(min(1, (t - 0.1) / 0.75) * math.pi * 0.95) + 0.8)
            for xx in range(int(x - half), int(x + half) + 1):
                u = (xx + 0.5 - x) / max(1, half)
                layer.px(xx, yy, pick(m, max(0, min(1, 0.62 - u * 0.4 - t * 0.2)), xx, yy, 0.05))
        layer.px(x - 3, by - h + 3, m[1]); layer.px(x + 3, by - h + 3, m[1])
        layer.hline(x - 1, x + 1, by - h, m[4])
    layer.outline()
    cv.blit(layer, 0, 0)


def sacks(cv, cx, by, seed=32):
    st = R['straw']; cl = R['cloth_w']
    layer = Canvas(cv.w, cv.h)
    for (ox, oy, r) in ((-4, 0, 5), (4, 0, 5), (0, -5, 4.5)):
        blob(layer, cx + ox, by - 4 + oy, r, r * 0.8, cl, lumps=2, seed=seed + ox, bias=-0.05, dither=0.05)
        layer.px(cx + ox, by - 4 + oy - int(r * 0.8), st[3])
    layer.outline()
    cv.blit(layer, 0, 0)
