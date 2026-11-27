"""The ground of a map, laid as materials with a little real relief: every stone, slab and rut
has a height, so the moon picks out its north-west edges in the baked picture and, in the
game, fires and the lantern light the faces turned towards them (a normal map goes out with
the picture).

A Terrain holds, for every map pixel: which ramp it is painted from, how light it is on that
ramp (a tone, fractional until the end), and its height. Materials are stamped through masks."""
import math
import numpy as np
from scipy import ndimage
from forge import hash2, vnoise, fbm, hexes

RAMPS = {
    'earth':  hexes('#2a1e28', '#45303a', '#624640', '#80604e', '#9c7a5c', '#b8966e', '#d0b288'),
    'dust':   hexes('#322630', '#4e3a40', '#6e5448', '#8e7058', '#aa8c6a', '#c4a880', '#dcc49c'),
    'flag':   hexes('#24242e', '#3a3a48', '#565662', '#73727c', '#918f94', '#afaba8', '#cbc6b8'),
    'pale':   hexes('#3a3442', '#5e5460', '#857a7a', '#aa9e92', '#c8bea8', '#e0d8bc', '#f2ecd2'),
    'brick':  hexes('#2a1620', '#48242a', '#6c3832', '#90503c', '#b06c4a', '#cc8c5c', '#e2ac74'),
    'cobble': hexes('#181e30', '#2a3448', '#404e64', '#5a687e', '#78869a', '#9aa6b6', '#bcc6d0'),
    'grass':  hexes('#10281e', '#184026', '#225a2e', '#307436', '#468e40', '#68aa52', '#92c66e'),
    'lawn':   hexes('#0c2a20', '#124428', '#1a6030', '#268038', '#3a9c44', '#5cb858', '#8ad478'),
    'path':   hexes('#30263a', '#52404a', '#7a6056', '#a28466', '#c4a67a', '#dcc692', '#f0e0b0'),
    'straw':  hexes('#2a2630', '#484038', '#6a5c44', '#8e7c50', '#b09c62', '#ccbc7c', '#e2d69c'),
    'dry':    hexes('#2a2a20', '#46462a', '#666634', '#868642', '#a6a456', '#c4c070', '#dcd890'),
    'soil':   hexes('#1c141c', '#2e2026', '#443030', '#5c423a', '#745646', '#8c6c54'),
    'sand':   hexes('#5c4230', '#84603c', '#aa8250', '#c8a066', '#debc80', '#f0d69c', '#fcecba'),
    'lapis':  hexes('#0a0e2c', '#141e56', '#203286', '#3050b2', '#4c76d2', '#84a8ec', '#c0d8ff'),
    'gold':   hexes('#3a2610', '#6e4818', '#a87428', '#d8a238', '#f6d064', '#fff2b0'),
    'moss':   hexes('#141e1c', '#1e3226', '#2c4a30', '#40643a', '#5a8046', '#7a9c58'),
    'flower_w': hexes('#6a6a8a', '#c8c4dc', '#f6f2ff'),
    'flower_y': hexes('#7a5a10', '#d8a830', '#ffe070'),
    'flower_r': hexes('#6a1a30', '#c03850', '#f07888'),
    'rock':   hexes('#1e1e2e', '#343648', '#525466', '#747688', '#989aa8', '#bcbec8', '#dcdee4'),
    'clay':   hexes('#2c1820', '#4c2a2c', '#74403a', '#9c5c46', '#c07e56', '#dca470', '#f2c890'),
    'marble': hexes('#34365a', '#5c6088', '#8a90b0', '#b4bad0', '#d6dbe8', '#eef0f6', '#ffffff'),
    'water':  hexes('#0a1430', '#12224a', '#1c3868', '#2a568a', '#4680b0', '#84b8d8'),
    'plank':  hexes('#1e1218', '#38222a', '#563630', '#784c3a', '#9c6846', '#bc8858', '#d8a870'),
    'night':  hexes('#060818', '#0b1230', '#121c4a', '#1a2a68', '#243c88', '#3456aa', '#5078c8'),
    'tile':   hexes('#241620', '#3e2428', '#5c3832', '#7c4e3e', '#9c684c', '#b8845e', '#d0a076'),
    'carpet': hexes('#2a0a16', '#4c1020', '#74182c', '#9c2634', '#be3e40', '#da6450'),
    'wall':   hexes('#2e2634', '#50424e', '#7a6660', '#a48a70', '#c8ac84', '#e4cc9c', '#f8e8ba'),
    'ash':    hexes('#231e2c', '#3a3342', '#574d58', '#766b6e', '#968b86', '#b4aa9c', '#d0c6b2'),
    'sere':   hexes('#26232c', '#403b40', '#5d564f', '#7c745c', '#9a926e', '#b6ae86', '#d0c89e'),
    'basalt': hexes('#0d0b15', '#191722', '#282532', '#3a3644', '#4f4b58', '#69656e', '#858188'),
}
SURF = {'earth': 's', 'dust': 's', 'soil': 's', 'sand': 's', 'ash': 's', 'grass': 'g', 'lawn': 'g', 'straw': 'g', 'dry': 'g', 'sere': 'g', 'moss': 'g', 'water': 'a', 'plank': 'w'}


class Terrain:
    def __init__(self, W, H, seed=0):
        self.W, self.H, self.seed = W, H, seed
        self.tone = np.zeros((H, W)); self.hgt = np.zeros((H, W))
        self.rid = np.zeros((H, W), np.int16)
        self.names = []
        self.yy, self.xx = np.mgrid[0:H, 0:W]
        self.shade = np.zeros((H, W))          # extra darkening that should not move the relief (contact shadows)

    # ---- masks
    def none(self):
        return np.zeros((self.H, self.W), bool)

    def all(self):
        return np.ones((self.H, self.W), bool)

    def rect(self, x, y, w, h):
        m = self.none(); m[max(0, int(y)):max(0, int(y + h)), max(0, int(x)):max(0, int(x + w))] = True; return m

    def stroke(self, pts, width):
        """A band of the given width along a path of points."""
        d = np.full((self.H, self.W), 1e9)
        X, Y = self.xx + 0.5, self.yy + 0.5
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy + 1e-9
            t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
            d = np.minimum(d, np.hypot(X - ax - t * vx, Y - ay - t * vy))
        return d <= width / 2.0

    def disc(self, cx, cy, r, ry=None):
        return ((self.xx + 0.5 - cx) / r) ** 2 + ((self.yy + 0.5 - cy) / (ry or r)) ** 2 <= 1

    def ragged(self, mask, amp=3.0, scale=9.0, seed=0):
        """The same area with an edge that wanders in and out by up to amp pixels."""
        d = ndimage.distance_transform_edt(mask) - ndimage.distance_transform_edt(~mask)
        return d + (fbm(self.xx / scale, self.yy / scale, self.seed + seed, 2) - 0.5) * 2 * amp > 0

    def grow(self, mask, n=1):
        return ndimage.binary_dilation(mask, iterations=n) if n > 0 else ndimage.binary_erosion(mask, iterations=-n)

    def edge_dist(self, mask):
        """How deep inside the mask each pixel is (0 outside)."""
        return ndimage.distance_transform_edt(mask)

    # ---- painting
    def ramp(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def put(self, mask, ramp, tone, hgt=None):
        self.rid[mask] = self.ramp(ramp)
        self.tone[mask] = tone[mask] if isinstance(tone, np.ndarray) else tone
        if hgt is not None:
            self.hgt[mask] = hgt[mask] if isinstance(hgt, np.ndarray) else hgt
        self.shade[mask] = 0

    def add(self, mask, dt):
        self.tone[mask] += dt[mask] if isinstance(dt, np.ndarray) else dt

    def contact(self, x0, y0, x1, y1, reach=4, strength=1.3):
        """The dark where something heavy meets the ground: along its front foot and a little up its sides."""
        m = self.rect(x0, y0, x1 - x0, y1 - y0)
        d = ndimage.distance_transform_edt(~m)
        k = np.clip(1 - d / reach, 0, 1)
        k[self.yy < y0 - 1] = 0
        self.shade = np.maximum(self.shade, np.where(~m, k * strength, 0))

    # ---- materials
    def earth(self, mask, seed=1, grain=None, base=3.5, ramp='earth', pebbles=0.004):
        """Trodden street earth: broad patches, finer mottling, wheel ruts along the grain, pebbles."""
        X, Y = self.xx, self.yy
        big = fbm(X / 52.0, Y / 52.0, self.seed + seed, 2); mid = fbm(X / 12.0, Y / 12.0, self.seed + seed + 3, 2)
        tone = base + np.round((big - 0.5) * 3.4) * 0.5 + (mid - 0.5) * 1.1
        hgt = (mid - 0.5) * 0.5
        if grain:
            a, b = (X, Y) if grain == 'h' else (Y, X)
            rut = fbm(a / 90.0, b / 4.0, self.seed + seed + 9, 2) > 0.63
            tone = tone - 0.55 * rut; hgt = hgt - 0.3 * rut
        self.put(mask, ramp, tone, hgt)
        if pebbles:
            self.pebbles(mask, pebbles, seed + 21)

    def pebbles(self, mask, density=0.004, seed=5, ramp=None):
        p = (hash2(self.xx, self.yy, self.seed + seed) < density) & mask
        sh = np.roll(p, (1, 1), (0, 1)) & mask & ~p
        big = p & (hash2(self.xx, self.yy, self.seed + seed + 1) < 0.4)
        p2 = np.roll(big, 1, 1) & mask
        self.tone[p | p2] += 1.7; self.hgt[p | p2] = 1.2
        self.tone[sh] -= 1.2
        if ramp:
            self.rid[p | p2] = self.ramp(ramp)

    def slabs(self, mask, seed=2, rows=(11, 13, 10, 12), wmin=13, wmax=24, ramp='flag', base=3.7, jitter=1.1,
              whole=True, crack=0.07, wear=0.5, joint=-2.0, moss=0.0):
        """Paving of cut stone. With whole=True a slab is laid only if its middle is inside the mask,
        so the edge of the paving follows the stones instead of slicing through them."""
        X, Y = self.xx, self.yy
        ys, xs = np.nonzero(mask)
        if len(ys) == 0:
            return mask
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        laid = self.none()
        tone = np.zeros((self.H, self.W)); hgt = np.zeros((self.H, self.W)); isj = self.none()
        y = y0 - (seed * 5) % rows[0]; r = 0
        while y < y1:
            h = rows[(r + seed) % len(rows)]
            x = x0 - int(hash2(r, 0, self.seed + seed) * wmax); k = 0
            while x < x1:
                w = wmin + int(hash2(r, k + 1, self.seed + seed + 1) * (wmax - wmin + 1))
                xa, xb, ya, yb = max(x, 0), min(x + w, self.W), max(y, 0), min(y + h, self.H)
                if xb > xa and yb > ya:
                    cy, cx = min(max((ya + yb) // 2, 0), self.H - 1), min(max((xa + xb) // 2, 0), self.W - 1)
                    inside = mask[cy, cx] if whole else mask[ya:yb, xa:xb].any()
                    if inside:
                        j = (hash2(r, k, self.seed + seed + 7) - 0.5) * jitter
                        laid[ya:yb, xa:xb] = True
                        tone[ya:yb, xa:xb] = j; hgt[ya:yb, xa:xb] = 1.0
                        # the joint: the last row and column of each stone
                        if y + h - 1 < self.H and y + h - 1 >= 0: isj[y + h - 1, xa:xb] = True
                        if x + w - 1 < self.W and x + w - 1 >= 0: isj[ya:yb, x + w - 1] = True
                        hv = hash2(r, k, self.seed + seed + 11)
                        if hv < crack and w > 12:
                            # a crack from the top edge to the bottom, wandering
                            cx0 = x + 3 + int(hash2(r, k, self.seed + seed + 12) * (w - 7))
                            for yy_ in range(ya, yb - 1):
                                cx0 += int(round((hash2(yy_, k, self.seed + seed + 13) - 0.5) * 2.2))
                                cx0 = min(max(cx0, x + 1), x + w - 3)
                                if 0 <= cx0 < self.W: isj[yy_, cx0] = True
                        elif hv > 0.9:
                            # a chipped corner
                            if ya == y and xa == x and ya + 1 < self.H and xa + 1 < self.W: isj[ya:ya + 2, xa:xa + 2] = True; isj[ya + 1, xa + 1] = False
                x += w; k += 1
            y += h; r += 1
        if not whole:
            laid &= mask
        w_ = (fbm(X / 30.0, Y / 30.0, self.seed + seed + 17, 2) - 0.5) * 2 * wear
        self.put(laid, ramp, base + tone + np.round(w_ * 2) / 2, hgt)
        jm = laid & isj
        self.tone[jm] = base + joint; self.hgt[jm] = 0
        if moss:
            mm = jm & (fbm(X / 14.0, Y / 14.0, self.seed + seed + 19, 2) > 1 - moss)
            self.rid[mm] = self.ramp('moss'); self.tone[mm] = 2.6
        # the open edge of the paving: a thin shadow on the south and east sides
        out = ~laid
        south = laid & np.roll(out, -1, 0); east = laid & np.roll(out, -1, 1)
        self.tone[south | east] -= 0.9
        return laid

    def bricks(self, mask, seed=3, bw=8, bh=4, ramp='brick', base=3.7, jitter=1.0, herring=False):
        X, Y = self.xx, self.yy
        if herring:
            # bricks laid in a herringbone: pairs of upright and lying bricks stepping diagonally
            s = bh
            a = (X // s + Y // s) % 4
            lying = a < 2
            col = np.where(lying, (X // s - Y // s) // 2 * 7 + Y // s, (X // s - Y // s) // 2 * 13 + X // s)
            j = np.where(lying, (Y % s == s - 1) | ((X // s + Y // s) % 2 == 1) & (X % s == s - 1), (X % s == s - 1) | ((X // s + Y // s) % 2 == 1) & (Y % s == s - 1))
            jit = (hash2(col, lying.astype(int), self.seed + seed) - 0.5) * jitter
        else:
            row = Y // bh; xx = X + (row % 2) * (bw // 2); col = xx // bw
            j = (Y % bh == bh - 1) | (xx % bw == bw - 1)
            jit = (hash2(col, row, self.seed + seed) - 0.5) * jitter
        tone = base + jit; hgt = np.ones((self.H, self.W))
        self.put(mask, ramp, tone, hgt)
        jm = mask & j
        self.tone[jm] = base - 1.7; self.hgt[jm] = 0

    def cobbles(self, mask, seed=4, cell=6, ramp='cobble', base=3.5, jitter=1.3):
        """Round stones set close: each a small dome, lit on its north-west shoulder."""
        X, Y = self.xx, self.yy
        gx, gy = X // cell, Y // cell
        best = np.full((self.H, self.W), 1e9); second = np.full((self.H, self.W), 1e9); who = np.zeros((self.H, self.W), np.int64)
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                cx = (gx + ox) * cell + hash2(gx + ox, gy + oy, self.seed + seed) * cell
                cy = (gy + oy) * cell + hash2(gx + ox, gy + oy, self.seed + seed + 1) * cell
                d = np.hypot(X + 0.5 - cx, (Y + 0.5 - cy) * 1.15)
                nearer = d < best
                second = np.where(nearer, best, np.minimum(second, d))
                who = np.where(nearer, (gx + ox) * 7919 + (gy + oy) * 104729, who)
                best = np.where(nearer, d, best)
        gap = (second - best) < 1.1
        dome = np.clip(1 - best / (cell * 0.62), 0, 1)
        tone = base + (hash2(who, 0, self.seed + seed + 3) - 0.5) * jitter
        self.put(mask, ramp, tone, 0.4 + dome * 1.2)
        g = mask & gap
        self.tone[g] = base - 2.0; self.hgt[g] = 0

    def grass(self, mask, seed=5, base=2.9, ramp='grass', tufts=0.03, flowers=0.0, fringe=2):
        """Grass: soft patches a tone apart, tufts of blades (a light tip, a dark foot), a few flowers.
        fringe > 0 lets blades hang that far over whatever lies next to the grass."""
        X, Y = self.xx, self.yy
        big = fbm(X / 44.0, Y / 44.0, self.seed + seed, 2); mid = fbm(X / 13.0, Y / 13.0, self.seed + seed + 2, 2)
        tone = base + np.round((big - 0.5) * 3.0) * 0.55 + (mid - 0.5) * 0.9
        area = mask
        if fringe:
            near = self.grow(mask, fringe) & ~mask
            area = mask | (near & (hash2(X, Y // 2, self.seed + seed + 5) < 0.45))
        self.put(area, ramp, tone, (mid - 0.5) * 0.6)
        lush = fbm(X / 30.0, Y / 30.0, self.seed + seed + 7, 2)
        t = (hash2(X, Y, self.seed + seed + 9) < tufts * (0.5 + 2.2 * (lush > 0.55))) & mask
        tip = t | np.roll(t, (-1, 1), (0, 1)); foot = np.roll(t, 1, 0) | np.roll(t, (1, -1), (0, 1))
        self.tone[tip & area] += 1.3; self.hgt[tip & area] += 0.8
        self.tone[foot & area & ~tip] -= 1.1
        if flowers:
            for i, nm in enumerate(('flower_w', 'flower_y', 'flower_r')):
                patch = fbm(X / 26.0, Y / 26.0, self.seed + seed + 30 + i, 2) > 0.66
                f = (hash2(X, Y, self.seed + seed + 40 + i) < flowers) & patch & mask
                self.rid[f] = self.ramp(nm); self.tone[f] = 2
                f2 = np.roll(f, 1, 0) & mask & ~f
                self.tone[f2] -= 0.8

    def sand(self, mask, seed=6, base=3.6, ramp='sand'):
        X, Y = self.xx, self.yy
        big = fbm(X / 50.0, Y / 50.0, self.seed + seed, 2)
        rip = np.sin((Y + 5 * fbm(X / 30.0, Y / 30.0, self.seed + seed + 1, 2) * 8) * 0.9 + X * 0.08) > 0.72
        tone = base + np.round((big - 0.5) * 2.6) * 0.5 - 0.6 * rip
        self.put(mask, ramp, tone, -0.5 * rip)
        self.pebbles(mask, 0.002, seed + 3)

    def soil(self, mask, seed=7, base=2.8, rows=True):
        X, Y = self.xx, self.yy
        tone = base + (fbm(X / 9.0, Y / 9.0, self.seed + seed, 2) - 0.5) * 1.2
        if rows:
            tone = tone - 0.7 * ((Y % 5) == 0)
        self.put(mask, 'soil', tone, (fbm(X / 6.0, Y / 6.0, self.seed + seed + 1, 2) - 0.5) * 1.0)

    def water(self, mask, seed=8, deep=40.0):
        """The sea: pale in the shallows, a line of foam where it meets the land, darkening as it
        deepens. Marked so the game can make its lights move (height below zero)."""
        X, Y = self.xx, self.yy
        d = ndimage.distance_transform_edt(mask)
        wob = (fbm(X / 18.0, Y / 9.0, self.seed + seed, 2) - 0.5) * 6
        t = np.clip((d + wob) / deep, 0, 1)
        tone = 4.3 - np.round(t * 3.2 * 2) / 2
        # long low swells
        swell = np.sin(Y * 0.55 + fbm(X / 26.0, Y / 26.0, self.seed + seed + 1, 2) * 7 + X * 0.05) > 0.86
        tone = tone + 0.6 * swell
        self.put(mask, 'water', tone, np.full((self.H, self.W), -1.0))
        foam = mask & (d + wob * 0.35 < 2.2) & (hash2(X // 2, Y, self.seed + seed + 2) < 0.8)
        self.rid[foam] = self.ramp('marble'); self.tone[foam] = 4.5
        # the land beside it is wet
        wet = ~mask & (ndimage.distance_transform_edt(~mask) < 4.5 + wob * 0.5)
        self.tone[wet] -= 0.9

    def rock(self, mask, seed=10, base=3.6, ramp='rock'):
        """Bare rock seen from above: slabs a tone apart, split by cracks, with loose stones on it."""
        X, Y = self.xx, self.yy
        big = fbm(X / 24.0, Y / 16.0, self.seed + seed, 2)
        tone = base + np.round((big - 0.5) * 4.0) * 0.6
        crack = np.abs(fbm(X / 15.0, Y / 15.0, self.seed + seed + 1, 2) - 0.5) < 0.02
        self.put(mask, ramp, tone, (big - 0.5) * 2.0)
        self.tone[mask & crack] -= 1.6; self.hgt[mask & crack] -= 1.0
        self.pebbles(mask, 0.012, seed + 2)

    def planks(self, mask, seed=9, w=6, along='x', base=3.6, ramp='plank'):
        """A deck of boards (a pier, a bridge): along='x' lays them across, their length north-south."""
        X, Y = self.xx, self.yy
        a, b = (X, Y) if along == 'x' else (Y, X)
        k = a // w
        tone = base + (hash2(k, 0, self.seed + seed) - 0.5) * 1.2
        tone = tone - 0.5 * (hash2(k, b // 7, self.seed + seed + 1) > 0.8)
        hgt = np.ones((self.H, self.W))
        self.put(mask, ramp, tone, hgt)
        j = mask & ((a % w) == w - 1)
        self.tone[j] = base - 2.2; self.hgt[j] = 0
        nail = mask & ((a % w) == w // 2) & ((b % 12) == 2)
        self.tone[nail] -= 1.4

    def tiles(self, mask, seed=11, size=16, ramp='tile', base=3.6, jitter=0.9, inlay=None, every=2, checker=None):
        """A floor of square tiles, each bevelled. inlay = a ramp for a small lozenge set into every
        `every`-th tile; checker = a second ramp for alternate tiles."""
        X, Y = self.xx, self.yy
        ix, iy = X // size, Y // size
        a, b = X % size, Y % size
        tone = base + (hash2(ix, iy, self.seed + seed) - 0.5) * jitter
        hgt = np.ones((self.H, self.W))
        self.put(mask, ramp, tone, hgt)
        if checker:
            alt = mask & (((ix + iy) % 2) == 1)
            self.rid[alt] = self.ramp(checker)
        j = mask & ((a == size - 1) | (b == size - 1))
        self.tone[j] = base - 2.0; self.hgt[j] = 0
        if inlay:
            c = size // 2 - 0.5
            dia = (np.abs(a - c) + np.abs(b - c)) <= size * 0.22
            loz = mask & dia & (((ix + iy * 3) % every) == 0)
            self.rid[loz] = self.ramp(inlay); self.tone[loz] = 3.4 + (hash2(ix, iy, self.seed + seed + 5)[loz] > 0.5) * 0.8; self.hgt[loz] = 1.2
            rim = mask & ((np.abs(a - c) + np.abs(b - c)) <= size * 0.22 + 1) & ~dia & (((ix + iy * 3) % every) == 0)
            self.tone[rim] -= 1.0

    def stars(self, mask, seed=14, size=16, density=0.3, ramp='gold'):
        """Gold stars let into a floor of tiles, one to a tile here and there, big and small:
        the sky laid underfoot."""
        X, Y = self.xx, self.yy
        ix, iy = X // size, Y // size
        h1 = hash2(ix, iy, self.seed + seed); h2 = hash2(ix, iy, self.seed + seed + 1); h3 = hash2(ix, iy, self.seed + seed + 2)
        cx = ix * size + size // 2 + np.round((h2 - 0.5) * size * 0.45); cy = iy * size + size // 2 + np.round((h3 - 0.5) * size * 0.45)
        dx, dy = np.abs(X - cx), np.abs(Y - cy)
        reach = np.where(h1 < density * 0.18, 3, np.where(h1 < density * 0.5, 2, np.where(h1 < density, 1, -1)))
        star = mask & (((dx == 0) & (dy <= reach)) | ((dy == 0) & (dx <= reach)) | ((dx <= 1) & (dy <= 1) & (reach >= 3)))
        self.rid[star] = self.ramp(ramp)
        self.tone[star] = np.where((dx + dy) == 0, 4.6, np.where((dx + dy) == 1, 3.6, 2.8))[star]
        self.hgt[star] = 1.1

    def carpet(self, mask, seed=12, ramp='carpet', base=3.4):
        """A long red carpet: a gold edge, a lattice woven down the middle."""
        X, Y = self.xx, self.yy
        d = ndimage.distance_transform_edt(mask)
        lattice = (((X + Y) % 8) == 0) | (((X - Y) % 8) == 0)
        tone = base + (hash2(X // 2, Y // 2, self.seed + seed) - 0.5) * 0.5 + 0.9 * lattice
        self.put(mask, ramp, tone, np.full((self.H, self.W), 1.6))
        edge = mask & (d <= 2) & (d > 1)
        self.rid[edge] = self.ramp('gold'); self.tone[edge] = 3.4
        rim = mask & (d <= 1)
        self.tone[rim] = base - 1.6
        south = mask & ~np.roll(mask, -1, 0)
        self.shade[np.roll(south, 1, 0) & ~mask] = 0.8

    def walltop(self, mask, seed=13, ramp='wall', base=3.9, bw=24, bh=16):
        """The top of a thick wall seen from above: long capstones."""
        self.slabs(mask, seed=seed, rows=(bh,), wmin=bw, wmax=bw + 6, ramp=ramp, base=base, jitter=0.7, whole=False, crack=0.04, wear=0.3, joint=-1.8)
        self.hgt[mask] += 2.0

    def border(self, mask, ramp='lapis', tone=3.0, width=1, hgt=1.0):
        """A line of another material just inside the edge of a mask (a kerb, an inlaid band)."""
        inner = self.grow(mask, -width)
        ring = mask & ~inner
        self.put(ring, ramp, np.full((self.H, self.W), float(tone)), hgt)
        return ring

    # ---- out
    def render(self, relief=1.6):
        """(rgb uint8, normal map rgba uint8)."""
        h = np.maximum(self.hgt, 0)
        # moonlight from the north-west: a face that rises towards the south-east is lit
        se = np.roll(h, (-1, -1), (0, 1)); nw = np.roll(h, (1, 1), (0, 1))
        tone = self.tone + np.clip(se - nw, -1.5, 1.5) * relief * 0.5 - self.shade
        rgb = np.zeros((self.H, self.W, 3), np.uint8)
        for i, nm in enumerate(self.names):
            m = self.rid == i
            rp = RAMPS[nm]
            rgb[m] = rp[np.clip(np.round(tone[m]), 0, len(rp) - 1).astype(int)]
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5; dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5      # dy: towards the south
        n = np.dstack([-dx * 0.9, dy * 0.9, np.ones_like(h)])
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        nm_ = np.zeros((self.H, self.W, 4), np.uint8)
        nm_[..., :3] = np.clip((n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8); nm_[..., 3] = 1
        nm_[self.hgt < -0.5] = (128, 128, 255, 0)            # water: flat, and marked for the game by a zero in alpha
        return rgb, nm_

    def surface(self, cell=8):
        """What sandals land on, one letter per cell: g grass, s sand and earth, a water, c stone."""
        rows = []
        letters = np.array([SURF.get(n, 'c') for n in self.names])
        for y0 in range(0, self.H, cell):
            row = []
            for x0 in range(0, self.W, cell):
                ids = self.rid[y0:y0 + cell, x0:x0 + cell].ravel()
                ls = letters[ids]
                vals, counts = np.unique(ls, return_counts=True)
                row.append(str(vals[counts.argmax()]))
            rows.append(''.join(row))
        return rows
