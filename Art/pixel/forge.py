"""The forge: props and buildings are put together as small 3D scenes (boxes, turned shapes,
cloth, clumps of leaves) and drawn the way the game looks at the world: straight on from the
south, one tile to sixteen pixels along the ground and up the walls alike. Moonlight comes over
the left shoulder of the town (from the north-west), so roofs and ledges catch it, fronts stand
in shade and shadows fall forward and to the right. Out of one scene come the sprite, a normal
map (so fires and the lantern light the faces turned towards them), and the shadow it throws on
the ground.

Units are tiles: x east, y north, z up. A pixel is 1/16."""
import math
import numpy as np

PPU = 16
MOON = np.array([-0.66, 0.40, 1.0]); MOON = MOON / np.linalg.norm(MOON)     # towards the moon
VIEW = np.array([0.0, -1.0, 1.0]) / math.sqrt(2)                           # towards the eye
INK = np.array([20, 12, 26], float)


def _n(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


def hash2(i, j, seed=0):
    """Repeatable pseudo-random numbers in [0, 1) for integer grids (arrays welcome)."""
    i = np.asarray(i, np.int64); j = np.asarray(j, np.int64)
    h = (i * 374761393 + j * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0x1000000)


def vnoise(x, y, seed=0):
    """Smooth value noise at real coordinates (one feature per unit)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    xi = np.floor(x).astype(np.int64); yi = np.floor(y).astype(np.int64)
    fx = x - xi; fy = y - yi
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a = hash2(xi, yi, seed); b = hash2(xi + 1, yi, seed); c = hash2(xi, yi + 1, seed); d = hash2(xi + 1, yi + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, seed=0, octaves=3):
    s = 0.0; amp = 0.5; tot = 0.0
    for o in range(octaves):
        s = s + amp * vnoise(x * (2 ** o), y * (2 ** o), seed + o * 17); tot += amp; amp *= 0.5
    return s / tot


# ---------------------------------------------------------------- materials
def hexes(*hs):
    return np.array([[int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)] for h in hs], float)


class Mat:
    """A surface: a ramp of tones (dark to light), where on the ramp it sits in full moonlight,
    and the marks that make it brick, plaster, planks or leaves."""
    def __init__(self, ramp, base, marks=None, ramp2=None, glow=False, gloss=0.0, soft=False, name=''):
        self.ramp = ramp if isinstance(ramp, np.ndarray) else hexes(*ramp)
        self.ramp2 = None if ramp2 is None else (ramp2 if isinstance(ramp2, np.ndarray) else hexes(*ramp2))
        self.base, self.marks, self.glow, self.gloss, self.soft, self.name = base, marks, glow, gloss, soft, name


# marks: f(u, v, P, seed) -> (tone change, use second ramp?)   u, v are whole texels on the face
def m_brick(bw=8, bh=4, joint=-1.0, jitter=0.9, keep=0.8):
    def f(u, v, P, seed):
        row = np.floor_divide(v, bh); uu = u + (row % 2) * (bw // 2)
        col = np.floor_divide(uu, bw)
        j = ((v % bh) == 0) | ((uu % bw) == 0)
        j &= hash2(col, row, seed + 5) < keep
        return np.where(j, joint, (hash2(col, row, seed) - 0.5) * jitter), None
    return f


def m_ashlar(bw=16, bh=8, seed2=3):
    """Dressed stone: big blocks with a lit top edge, a dark joint and the odd chipped corner."""
    def f(u, v, P, seed):
        row = np.floor_divide(v, bh); uu = u + (row % 2) * (bw // 2) + (hash2(row, 0, seed) * 5).astype(np.int64)
        col = np.floor_divide(uu, bw)
        a, b = v % bh, uu % bw
        t = (hash2(col, row, seed + seed2) - 0.5) * 0.8
        t = np.where(a == bh - 1, t + 0.7, t)             # top edge of each block (v grows upward)
        t = np.where((a == 0) | (b == 0), -1.2, t)
        chip = (hash2(col, row, seed + 9) > 0.86) & (a >= bh - 2) & (b <= 2)
        return np.where(chip, -1.0, t), None
    return f


def m_plaster(bricks=True, crack=True):
    """Mud plaster: broad patches a tone apart, a few cracks, and near the ground or at a worn
    corner the brick it covers."""
    brick = m_brick(8, 4, -0.9, 0.7)
    def f(u, v, P, seed):
        t = np.round((fbm(u / 22.0, v / 14.0, seed) - 0.5) * 3.2) * 0.42
        sel = None
        if crack:
            c = np.abs(vnoise(u / 19.0 + 3.1, v / 27.0, seed + 31) - 0.5) < 0.016
            c &= vnoise(u / 40.0, v / 40.0, seed + 33) > 0.52
            t = np.where(c, -1.4, t)
        if bricks:
            z = P[..., 2]
            worn = fbm(u / 16.0, v / 9.0, seed + 71) - z * 0.20
            w = worn > 0.56
            bt, _ = brick(u, v, P, seed)
            t = np.where(w, bt - 0.2, t)
            edge = (worn > 0.52) & ~w
            t = np.where(edge, t - 0.9, t)
            sel = w
        return t, sel
    return f


def m_planks(w=5, along='v', knots=True):
    def f(u, v, P, seed):
        a, b = (u, v) if along == 'v' else (v, u)
        k = np.floor_divide(a, w)
        t = (hash2(k, 0, seed) - 0.5) * 0.9
        t = np.where((a % w) == 0, -1.1, t)
        if knots:
            t = np.where(hash2(a, np.floor_divide(b, 3), seed + 3) > 0.93, t - 0.7, t)
        return t, None
    return f


def m_mottle(scale=14.0, amp=0.5, specks=0.0, speck_t=0.9):
    def f(u, v, P, seed):
        t = np.round((fbm(u / scale, v / scale, seed) - 0.5) * 3.0) * amp
        if specks:
            t = np.where(hash2(u, v, seed + 13) < specks, t + speck_t, t)
        return t, None
    return f


def m_stripes(w=6, along='u'):
    def f(u, v, P, seed):
        a = u if along == 'u' else v
        return np.zeros(a.shape), (np.floor_divide(a, w) % 2) == 1
    return f


def m_leaves(density=0.22):
    """Leaf marks: small light ticks with a dark one under them, scattered over the mass."""
    def f(u, v, P, seed):
        h = hash2(np.floor_divide(u, 2), np.floor_divide(v, 2), seed)
        t = np.where((h < density) & ((u + v) % 2 == 0), 0.9, 0.0)
        t = np.where((h > 1 - density * 0.7) & ((u + v) % 2 == 1), -0.9, t)
        return t, None
    return f


def m_clumps(size=5, lift=1.0, drop=1.0):
    """Foliage the way it is drawn by hand: small overlapping clumps, each with a lit shoulder
    towards the moon (up and to the left) and a dark hem where it overhangs the next one down."""
    def f(u, v, P, seed):
        s = size
        row = np.floor_divide(v, s - 1)
        uu = u + (row % 2) * (s // 2) + (hash2(row, 1, seed) * 3).astype(np.int64)
        col = np.floor_divide(uu, s)
        a = uu % s; b = v % (s - 1)                     # b counts upward inside the clump
        j = (hash2(col, row, seed) - 0.5) * 0.9
        t = j
        t = np.where((b == s - 2) & (a >= 1) & (a <= s - 3), t + lift, t)            # the lit shoulder
        t = np.where((b == s - 3) & (a == 0), t + lift * 0.7, t)
        t = np.where((b == 0) & (a >= 1), t - drop, t)                              # the hem
        t = np.where((a == s - 1) & (b <= 1), t - drop * 0.8, t)
        return t, None
    return f


def m_rubble(cell=6, jitter=1.2, gap=-1.6):
    """Field stones fitted together without mortar: each its own tone, dark where they meet."""
    def f(u, v, P, seed):
        gx, gy = np.floor_divide(u, cell), np.floor_divide(v, cell - 1)
        best = np.full(u.shape, 1e9); second = np.full(u.shape, 1e9); who = np.zeros(u.shape, np.int64)
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                cx = (gx + ox) * cell + hash2(gx + ox, gy + oy, seed) * cell
                cy = (gy + oy) * (cell - 1) + hash2(gx + ox, gy + oy, seed + 1) * (cell - 1)
                d = np.hypot(u + 0.5 - cx, (v + 0.5 - cy) * 1.25)
                nearer = d < best
                second = np.where(nearer, best, np.minimum(second, d))
                who = np.where(nearer, (gx + ox) * 7919 + (gy + oy) * 104729, who)
                best = np.where(nearer, d, best)
        t = (hash2(who, 0, seed + 3) - 0.5) * jitter
        return np.where((second - best) < 1.0, gap, t), None
    return f


def m_strata(band=6, crack=0.05):
    """Bedded rock: long level layers, each a little lighter or darker, split by the odd upright crack."""
    def f(u, v, P, seed):
        row = np.floor_divide(v + (fbm(u / 40.0, 0.0 * u, seed) * 5).astype(np.int64), band)
        t = (hash2(row, np.floor_divide(u, 23), seed) - 0.5) * 1.1
        t = np.where(((v + (fbm(u / 40.0, 0.0 * u, seed) * 5).astype(np.int64)) % band) == 0, t - 0.9, t)
        c = (hash2(np.floor_divide(u, 2), row, seed + 5) < crack) & ((u % 2) == 0)
        return np.where(c, t - 1.3, t), None
    return f


def m_reeds(w=3):
    def f(u, v, P, seed):
        k = np.floor_divide(v, w)
        t = (hash2(k, np.floor_divide(u, 7), seed) - 0.5) * 1.1
        return np.where((v % w) == 0, t - 0.6, t), None
    return f


def m_glazed(bw=8, bh=4):
    brick = m_brick(bw, bh, -0.8, 0.6, keep=1.0)
    def f(u, v, P, seed):
        t, _ = brick(u, v, P, seed)
        row = np.floor_divide(v, bh); uu = u + (row % 2) * (bw // 2); col = np.floor_divide(uu, bw)
        glint = (hash2(col, row, seed + 41) > 0.84) & ((uu % bw) == 2) & ((v % bh) == bh - 2)
        return np.where(glint, 1.6, t), None
    return f


RAMPS = {
    # warm earth and plaster: lit tones lean yellow, shade leans violet
    'mud':     hexes('#2a1c2a', '#47303a', '#6b4a46', '#946a50', '#bd9060', '#dcb47a', '#f2d49a'),
    'limewash': hexes('#33304a', '#585470', '#847e92', '#b0a8ac', '#d6cdc0', '#efe6cf', '#fff8e6'),
    'clay':    hexes('#2c1820', '#4c2a2c', '#74403a', '#9c5c46', '#c07e56', '#dca470', '#f2c890'),
    'brick':   hexes('#2a1620', '#4a242a', '#703832', '#96503c', '#b86e4a', '#d49260'),
    'sandstone': hexes('#2e2634', '#50424e', '#7a6660', '#a48a70', '#c8ac84', '#e4cc9c', '#f8e8ba'),
    'stone':   hexes('#1e1e2e', '#343648', '#525466', '#747688', '#989aa8', '#bcbec8', '#dcdee4'),
    'wood':    hexes('#1e1218', '#38222a', '#563630', '#784c3a', '#9c6846', '#bc8858', '#d8a870'),
    'cedar':   hexes('#241016', '#44201e', '#682e22', '#8c4428', '#ae6034', '#cc8448'),
    'reed':    hexes('#2e2420', '#54402c', '#806238', '#a88848', '#ccac60', '#e8d088'),
    'roof':    hexes('#2c2430', '#4a3c42', '#6e5a54', '#947a66', '#b89c7c', '#d6bc96', '#ecd8b2'),
    'lapis':   hexes('#0a0e2c', '#141e56', '#203286', '#3050b2', '#4c76d2', '#84a8ec', '#c0d8ff'),
    'gold':    hexes('#3a2610', '#6e4818', '#a87428', '#d8a238', '#f6d064', '#fff2b0'),
    'bronze':  hexes('#2a1814', '#52301a', '#825024', '#b47634', '#dca250', '#fad48a', '#fff4cc'),
    'iron':    hexes('#14141e', '#26283a', '#3e4256', '#5c6278', '#8088a0', '#aab4c8'),
    'red':     hexes('#2e0c18', '#561426', '#842234', '#b03840', '#d45c54', '#ee8a74'),
    'blue':    hexes('#12143a', '#202866', '#303e96', '#4a5ec0', '#6e8adc', '#a0b8f0'),
    'cream':   hexes('#3e3a50', '#6a6478', '#9890a0', '#c4bcbc', '#e6e0d4', '#fbf6e8'),
    'ochre':   hexes('#3a2414', '#684018', '#986222', '#c48a30', '#e4b44c', '#f8dc80'),
    'green':   hexes('#10241e', '#1a3a2a', '#265434', '#38703c', '#549048', '#7cb05c', '#a8cc7c'),
    'olive':   hexes('#14242a', '#203a38', '#305446', '#486e54', '#668c64', '#8eaa7e', '#b4c69a'),
    'cypress': hexes('#0c1c22', '#14302c', '#1e4436', '#2a5a42', '#3c724e', '#58905e'),
    'palm':    hexes('#10261c', '#1a3e26', '#2a5a30', '#40783a', '#5e9a48', '#88ba5e'),
    'trunk':   hexes('#1c1218', '#32202a', '#4c3234', '#6a4840', '#8c6650', '#aa8866'),
    'dark':    hexes('#0c0812', '#140e1c', '#1e1626', '#2a2030', '#382c3c'),
    'glow':    hexes('#b8501a', '#f08a2a', '#ffc04e', '#ffe08c', '#fff6d4'),
    'water':   hexes('#0a1430', '#12224a', '#1c3868', '#2a568a', '#4680b0', '#84b8d8'),
    'straw':   hexes('#3a2a20', '#6a4e30', '#9a7a44', '#c8a45c', '#e8cc80', '#f8e8a8'),
    'linen':   hexes('#34304a', '#5c5670', '#8a8294', '#b6aeb0', '#dcd4c8', '#f4eedc'),
    'fig':     hexes('#241030', '#42184a', '#682660', '#903c70', '#b85c84'),
}


def M(name, base, marks=None, ramp2=None, **kw):
    return Mat(RAMPS[name], base, marks, None if ramp2 is None else RAMPS[ramp2], name=name, **kw)


# ---------------------------------------------------------------- geometry
class Model:
    """Triangles with a material each, plus the points where light comes out of it."""
    def __init__(self):
        self.P = []; self.UV = []; self.N = []; self.mat = []; self.pt = []; self.two = []
        self.mats = []; self._mat_ix = {}
        self.lights = []          # (x, y, z, radius, (r, g, b), strength)
        self._part = 0
        self._xf = [np.eye(4)]

    # --- placing
    def push(self, at=(0, 0, 0), rot=0.0, scale=1.0, rx=0.0, ry=0.0):
        """Everything added until pop() is turned (rot about the upright, then tipped by rx, ry), scaled and moved."""
        def R(axis, deg):
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            m = np.eye(4)
            i, j = [(1, 2), (2, 0), (0, 1)][axis]
            m[i, i] = c; m[i, j] = -s; m[j, i] = s; m[j, j] = c
            return m
        t = np.eye(4); t[:3, 3] = at
        sc = np.diag([scale, scale, scale, 1.0])
        self._xf.append(self._xf[-1] @ t @ R(2, rot) @ R(1, ry) @ R(0, rx) @ sc); return self

    def pop(self):
        self._xf.pop(); return self

    def part(self):
        """Start a new part: edges between parts are inked even where they touch."""
        self._part += 1; return self._part

    def _mid(self, mat):
        k = id(mat)
        if k not in self._mat_ix:
            self._mat_ix[k] = len(self.mats); self.mats.append(mat)
        return self._mat_ix[k]

    def _put(self, p):
        p = np.asarray(p, float)
        return p @ self._xf[-1][:3, :3].T + self._xf[-1][:3, 3]

    def _dir(self, n):
        m = self._xf[-1][:3, :3]
        return np.asarray(n, float) @ m.T / (np.linalg.norm(m[:, 0]) + 1e-12)

    def light(self, x, y, z, radius=2.4, color=(1.0, 0.74, 0.4), strength=0.55):
        p = self._put([x, y, z]); self.lights.append((p[0], p[1], p[2], radius, color, strength))

    # --- raw faces
    def tri(self, p, mat, uv=None, n=None, two=False):
        p = self._put(p)
        fn = np.cross(p[1] - p[0], p[2] - p[0])
        ln = np.linalg.norm(fn)
        if ln < 1e-12:
            return
        fn = fn / ln
        if uv is None:
            uv = self._auto_uv(p, fn)
        self.P.append(p); self.UV.append(np.asarray(uv, float))
        self.N.append(np.tile(fn, (3, 1)) if n is None else self._dir(n))
        self.mat.append(self._mid(mat)); self.pt.append(self._part); self.two.append(two)

    @staticmethod
    def _auto_uv(p, fn):
        if abs(fn[2]) < 0.6:                                   # a wall: along it, and up
            t = _n([-fn[1], fn[0], 0.0])
            return np.stack([p @ t * PPU, p[:, 2] * PPU], 1)
        return np.stack([p[:, 0] * PPU, p[:, 1] * PPU], 1)      # a floor or roof: as the map lies

    def quad(self, a, b, c, d, mat, two=False, uv=None, n=None):
        """Corners in order round the face, seen from outside counter-clockwise."""
        if uv is None and n is None:
            self.tri([a, b, c], mat, two=two); self.tri([a, c, d], mat, two=two)
        else:
            uv = uv or [None] * 4; n = n or [None] * 4
            pick = lambda arr, ix: None if arr[0] is None else [arr[i] for i in ix]
            self.tri([a, b, c], mat, uv=pick(uv, (0, 1, 2)), n=pick(n, (0, 1, 2)), two=two)
            self.tri([a, c, d], mat, uv=pick(uv, (0, 2, 3)), n=pick(n, (0, 2, 3)), two=two)

    # --- solids
    def box(self, x0, y0, z0, x1, y1, z1, mat, top=None, bottom=False):
        """An upright box. mat covers the walls; top (default the same) the lid."""
        top = top or mat
        self.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), mat)      # south
        self.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), mat)      # east
        self.quad((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), mat)      # north
        self.quad((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), mat)      # west
        self.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), top)      # top
        if bottom:
            self.quad((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), mat)
        return self

    def prism(self, pts, z0, z1, mat, top=None):
        """A flat-topped shape standing on the outline pts (counter-clockwise, seen from above)."""
        top = top or mat
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            self.quad((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1), mat)
        c = np.mean(np.asarray(pts, float), 0)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            self.tri([(c[0], c[1], z1), (a[0], a[1], z1), (b[0], b[1], z1)], top)
        return self

    def turned(self, cx, cy, profile, mat, n=12, smooth=True, cap=None, squash=1.0):
        """A shape turned on a wheel or lathe: profile is (radius, height) pairs from the bottom up."""
        prof = np.asarray(profile, float)
        ang = np.linspace(0, 2 * math.pi, n + 1)
        ring = lambda r, z: np.stack([cx + np.cos(ang) * r, cy + np.sin(ang) * r * squash, np.full(n + 1, z)], 1)
        # outward normals of the profile
        d = np.gradient(prof, axis=0)
        nr, nz = d[:, 1], -d[:, 0]
        ln = np.hypot(nr, nz) + 1e-9; nr, nz = nr / ln, nz / ln
        for i in range(len(prof) - 1):
            a, b = ring(*prof[i]), ring(*prof[i + 1])
            rr = max(prof[i][0], prof[i + 1][0])
            for k in range(n):
                p = [a[k], a[k + 1], b[k + 1], b[k]]
                uv = [(ang[k] * rr * PPU, prof[i][1] * PPU), (ang[k + 1] * rr * PPU, prof[i][1] * PPU),
                      (ang[k + 1] * rr * PPU, prof[i + 1][1] * PPU), (ang[k] * rr * PPU, prof[i + 1][1] * PPU)]
                nn = None
                if smooth:
                    nn = [(math.cos(ang[k]) * nr[i], math.sin(ang[k]) * nr[i], nz[i]), (math.cos(ang[k + 1]) * nr[i], math.sin(ang[k + 1]) * nr[i], nz[i]),
                          (math.cos(ang[k + 1]) * nr[i + 1], math.sin(ang[k + 1]) * nr[i + 1], nz[i + 1]), (math.cos(ang[k]) * nr[i + 1], math.sin(ang[k]) * nr[i + 1], nz[i + 1])]
                self.quad(*p, mat, uv=uv, n=nn)
        if cap is not None and prof[-1][0] > 1e-6:
            top = ring(*prof[-1])
            for k in range(n):
                self.tri([(cx, cy, prof[-1][1]), top[k], top[k + 1]], cap)
        return self

    def cyl(self, cx, cy, z0, z1, r, mat, n=10, cap=None, r1=None, smooth=True):
        return self.turned(cx, cy, [(r, z0), (r if r1 is None else r1, z1)], mat, n=n, cap=cap or mat, smooth=smooth)

    def blob(self, cx, cy, cz, rx, ry, rz, mat, seed=0, bump=0.0, n=10, rings=6, facet=False):
        """A rounded lump: a canopy clump, a boulder, a sack. bump roughens it; facet keeps the
        flat chips of a rock instead of smoothing them."""
        th = np.linspace(0, 2 * math.pi, n + 1); ph = np.linspace(-math.pi / 2, math.pi / 2, rings + 1)
        T, PH = np.meshgrid(th, ph)
        d = np.stack([np.cos(PH) * np.cos(T), np.cos(PH) * np.sin(T), np.sin(PH)], -1)
        r = 1.0 + bump * (hash2((np.cos(T) * 3).round(), (PH * 3).round() + (np.sin(T) * 3).round() * 7, seed) - 0.5) * 2 if bump else np.ones(T.shape)
        r[:, -1] = r[:, 0]; r[0, :] = r[0, 0]; r[-1, :] = r[-1, 0]
        p = np.array([cx, cy, cz]) + d * r[..., None] * np.array([rx, ry, rz])
        nrm = d / np.array([rx, ry, rz]); nrm = nrm / (np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9)
        for i in range(rings):
            for k in range(n):
                q = [p[i, k], p[i, k + 1], p[i + 1, k + 1], p[i + 1, k]]
                nn = None if facet else [nrm[i, k], nrm[i, k + 1], nrm[i + 1, k + 1], nrm[i + 1, k]]
                uvn = [(np.nan, np.nan)] * 4
                self.quad(*q, mat, uv=uvn, n=nn)
        return self

    def sheet(self, grid, mat, two=True, smooth=True):
        """Cloth, a frond, a sail: a grid of points (rows, cols, 3)."""
        g = np.asarray(grid, float)
        R, C = g.shape[:2]
        gx = np.gradient(g, axis=1); gy = np.gradient(g, axis=0)
        nrm = np.cross(gx, gy); nrm = nrm / (np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9)
        # texels along the cloth itself
        du = np.concatenate([np.zeros((R, 1)), np.cumsum(np.linalg.norm(np.diff(g, axis=1), axis=-1), 1)], 1) * PPU
        dv = np.concatenate([np.zeros((1, C)), np.cumsum(np.linalg.norm(np.diff(g, axis=0), axis=-1), 0)], 0) * PPU
        for i in range(R - 1):
            for k in range(C - 1):
                ix = [(i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k)]
                self.quad(*[g[a] for a in ix], mat, two=two, uv=[(du[a], dv[a]) for a in ix], n=[nrm[a] for a in ix] if smooth else None)
        return self

    def limb(self, pts, radii, mat, n=7, smooth=True, cap=True):
        """A trunk, a branch, a rope: a round section swept along the points, radii thick."""
        pts = np.asarray(pts, float); radii = np.broadcast_to(np.asarray(radii, float), (len(pts),))
        tan = np.gradient(pts, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-12)
        ang = np.linspace(0, 2 * math.pi, n + 1)
        rings, norms = [], []
        ref = np.array([0.0, 1.0, 0.0])
        for i in range(len(pts)):
            t = tan[i]
            if abs(t @ ref) > 0.95: ref = np.array([1.0, 0.0, 0.0])
            u = _n(np.cross(t, ref)); v = np.cross(t, u)
            d = np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v
            rings.append(pts[i] + d * radii[i]); norms.append(d)
        run = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]) * PPU
        for i in range(len(pts) - 1):
            rr = max(radii[i], radii[i + 1])
            for k in range(n):
                p = [rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]]
                uv = [(ang[k] * rr * PPU, run[i]), (ang[k + 1] * rr * PPU, run[i]), (ang[k + 1] * rr * PPU, run[i + 1]), (ang[k] * rr * PPU, run[i + 1])]
                nn = [norms[i][k], norms[i][k + 1], norms[i + 1][k + 1], norms[i + 1][k]] if smooth else None
                self.quad(*p, mat, uv=uv, n=nn)
        if cap:
            for k in range(n):
                self.tri([pts[-1], rings[-1][k], rings[-1][k + 1]], mat, two=True)
        return self

    def face(self, pts, y, mat, two=False):
        """A flat shape on a south-facing wall at y: pts are (x, z) round its edge, counter-clockwise seen from the south."""
        c = np.mean(np.asarray(pts, float), 0)
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            self.tri([(c[0], y, c[1]), (a[0], y, a[1]), (b[0], y, b[1])], mat, two=two)
        return self

    def beam(self, a, b, w, mat, h=None):
        """A straight timber or pole from a to b, w wide (h tall)."""
        a = np.asarray(a, float); b = np.asarray(b, float)
        h = h or w
        d = _n(b - a)
        side = _n(np.cross(d, [0, 0, 1])) if abs(d[2]) < 0.95 else np.array([1.0, 0, 0])
        up = _n(np.cross(side, d))
        s, u = side * w / 2, up * h / 2
        c = [a - s - u, a + s - u, a + s + u, a - s + u, b - s - u, b + s - u, b + s + u, b - s + u]
        for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (1, 0, 3, 2), (4, 5, 6, 7)):
            self.quad(*[c[i] for i in f], mat, two=True)
        return self

    def arrays(self):
        return (np.array(self.P), np.array(self.UV), np.array(self.N), np.array(self.mat, int), np.array(self.pt, int), np.array(self.two, bool))


# ---------------------------------------------------------------- drawing
def _raster(S, D, W, H, cull=None):
    """Depth-buffered triangles. S (T,3,2) pixel coordinates, D (T,3) nearness (bigger is nearer)."""
    zbuf = np.full((H, W), -1e9); tid = np.full((H, W), -1, np.int32)
    b0 = np.zeros((H, W)); b1 = np.zeros((H, W))
    x0, y0 = S[:, 0, 0], S[:, 0, 1]; x1, y1 = S[:, 1, 0], S[:, 1, 1]; x2, y2 = S[:, 2, 0], S[:, 2, 1]
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    lo = np.floor(S.min(1)).astype(int); hi = np.ceil(S.max(1)).astype(int)
    for t in range(len(S)):
        if abs(area[t]) < 1e-9 or (cull is not None and cull[t]):
            continue
        xa, xb = max(lo[t, 0], 0), min(hi[t, 0], W - 1)
        ya, yb = max(lo[t, 1], 0), min(hi[t, 1], H - 1)
        if xb < xa or yb < ya:
            continue
        X = np.arange(xa, xb + 1) + 0.5; Y = (np.arange(ya, yb + 1) + 0.5)[:, None]
        w0 = ((x1[t] - X) * (y2[t] - Y) - (x2[t] - X) * (y1[t] - Y)) / area[t]
        w1 = ((x2[t] - X) * (y0[t] - Y) - (x0[t] - X) * (y2[t] - Y)) / area[t]
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        z = w0 * D[t, 0] + w1 * D[t, 1] + w2 * D[t, 2]
        sub = zbuf[ya:yb + 1, xa:xb + 1]
        up = m & (z > sub)
        sub[up] = z[up]
        tid[ya:yb + 1, xa:xb + 1][up] = t
        b0[ya:yb + 1, xa:xb + 1][up] = w0[up]; b1[ya:yb + 1, xa:xb + 1][up] = w1[up]
    return zbuf, tid, b0, b1


class _Shadow:
    """What a light from one direction can see: used for the moon and for the open sky."""
    def __init__(self, P, toward, res=24):
        self.L = _n(toward)
        a = _n(np.cross(self.L, [0.0, 1.0, 0.0])) if abs(self.L[1]) < 0.9 else _n(np.cross(self.L, [1.0, 0, 0]))
        b = np.cross(self.L, a)
        self.a, self.b, self.res = a, b, res
        flat = P.reshape(-1, 3)
        sx, sy = flat @ a, flat @ b
        self.ox, self.oy = sx.min() - 2.0 / res, sy.min() - 2.0 / res
        W = int(math.ceil((sx.max() - self.ox) * res)) + 3; H = int(math.ceil((sy.max() - self.oy) * res)) + 3
        S = np.stack([(P @ a - self.ox) * res, (P @ b - self.oy) * res], -1)
        self.z, _, _, _ = _raster(S, P @ self.L, W, H)

    def lit(self, Q, bias=0.07):
        """For points Q (..., 3): True where nothing stands between the point and the light."""
        sx = ((Q @ self.a - self.ox) * self.res).astype(int); sy = ((Q @ self.b - self.oy) * self.res).astype(int)
        H, W = self.z.shape
        inside = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
        zz = np.full(sx.shape, -1e9)
        zz[inside] = self.z[sy[inside], sx[inside]]
        return zz <= (Q @ self.L) + bias


def _sky_dirs():
    out = []
    for el, n in ((28, 8), (55, 6), (80, 3)):
        for k in range(n):
            az = 2 * math.pi * (k + 0.5 * (el > 40)) / n
            e = math.radians(el)
            out.append((math.cos(e) * math.cos(az), math.cos(e) * math.sin(az), math.sin(e)))
    return np.array(out)


SKY = _sky_dirs()


class Drawn:
    """What comes out of the forge for one prop."""
    def __init__(self):
        self.rgba = None      # (h, w, 4) uint8, the sprite
        self.normal = None    # (h, w, 4) uint8: rgb the surface normal (x east, y north, z up), a the height
        self.shade = None     # (h2, w2) bool: the shadow thrown on the ground
        self.ax = self.ay = 0           # where the model's origin lies in the sprite (pixels from the top left)
        self.sx = self.sy = 0           # the same for the shadow
        self.lights = []                # (dx, dy in map pixels from the origin, radius, colour, strength)
        self.foot = None                # (x0, y0, x1, y1) of the ground it stands on, in pixels from the origin (y down)


def draw(model, seed=0, ink=True, sky=True, shadow=True, pad=2):
    P, UV, N, MAT, PART, TWO = model.arrays()
    T = len(P)
    # the picture plane
    sx = P[..., 0] * PPU; sy = -(P[..., 1] + P[..., 2]) * PPU
    x_lo, y_lo = math.floor(sx.min()) - pad, math.floor(sy.min()) - pad
    W = int(math.ceil(sx.max())) - x_lo + pad; H = int(math.ceil(sy.max())) - y_lo + pad
    S = np.stack([sx - x_lo, sy - y_lo], -1)
    depth = P[..., 2] - P[..., 1]
    fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); fn /= (np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12)
    facing = fn @ VIEW
    zbuf, tid, b0, b1 = _raster(S, depth, W, H, cull=(facing <= 1e-6) & ~TWO)
    on = tid >= 0
    t = np.where(on, tid, 0)
    b2 = 1 - b0 - b1
    lerp = lambda A: A[t, 0] * b0[..., None] + A[t, 1] * b1[..., None] + A[t, 2] * b2[..., None]
    Q = lerp(P)                                   # where each pixel is in the world
    nrm = lerp(N); nrm /= (np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9)
    back = (nrm @ VIEW) < 0
    nrm = np.where((back & TWO[t])[..., None], -nrm, nrm)
    uv = lerp(UV)
    yy, xx = np.mgrid[0:H, 0:W]
    u = np.where(np.isnan(uv[..., 0]), xx + x_lo, np.floor(uv[..., 0] + 1e-4)).astype(np.int64)
    v = np.where(np.isnan(uv[..., 1]), -(yy + y_lo), np.floor(uv[..., 1] + 1e-4)).astype(np.int64)

    # light: the moon, and the open sky for everything it doesn't reach
    key = np.clip(nrm @ MOON, 0, 1)
    if shadow:
        key = key * _Shadow(P, MOON, 32).lit(Q + nrm * 0.03)
    if sky:
        num = np.zeros((H, W)); den = np.zeros((H, W))
        for d in SKY:
            w = np.clip(nrm @ d, 0, 1)
            num += w * _Shadow(P, d, 16).lit(Q + nrm * 0.05, bias=0.12); den += w
        ao = np.where(den > 1e-6, num / np.maximum(den, 1e-6), 1.0)
    else:
        ao = np.ones((H, W))
    light = 0.42 * ao + 0.58 * key

    out = Drawn()
    rgb = np.zeros((H, W, 3)); tone_ix = np.zeros((H, W), int)
    mid = MAT[t]
    for k, mat in enumerate(model.mats):
        m = on & (mid == k)
        if not m.any():
            continue
        if mat.glow:
            tone = np.full(m.sum(), float(mat.base))
            sel = None
            if mat.marks:
                dt, sel = mat.marks(u[m], v[m], Q[m], seed + k * 7)
                tone = tone + dt
        else:
            li = light[m]
            if mat.soft:                                       # leaves, cloth: the form turns gently
                li = 0.42 * ao[m] + 0.58 * np.clip(nrm[m] @ MOON * 0.6 + 0.4, 0, 1) * (key[m] > 0).clip(0.45, 1)
                li = 0.66 + (li - 0.62) * 1.35
            tone = mat.base + (li - 0.66) * 4.6
            sel = None
            if mat.marks:
                dt, sel = mat.marks(u[m], v[m], Q[m], seed + k * 7)
                tone = tone + dt
            if mat.gloss:
                hv = _n(MOON + VIEW)
                tone = tone + np.where((nrm[m] @ hv) > 1 - mat.gloss, 1.6, 0.0)
        ramp = mat.ramp
        ix = np.clip(np.round(tone), 0, len(ramp) - 1).astype(int)
        col = ramp[ix]
        if sel is not None and mat.ramp2 is not None:
            r2 = mat.ramp2
            col = np.where(sel[:, None], r2[np.clip(np.round(tone), 0, len(r2) - 1).astype(int)], col)
        rgb[m] = col; tone_ix[m] = ix

    if ink:
        rim_ok = np.array([not (mm.glow or mm.soft) for mm in model.mats] + [False])
        part = np.where(on, PART[t], -1)
        dz = np.where(on, zbuf, -1e9)
        dark = np.zeros((H, W), bool); edge_hi = np.zeros((H, W), bool)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nz = np.roll(dz, (dy, dx), (0, 1)); npart = np.roll(part, (dy, dx), (0, 1)); non = np.roll(on, (dy, dx), (0, 1))
            if dy == 1: nz[0, :] = -1e9; non[0, :] = False
            if dy == -1: nz[-1, :] = -1e9; non[-1, :] = False
            if dx == 1: nz[:, 0] = -1e9; non[:, 0] = False
            if dx == -1: nz[:, -1] = -1e9; non[:, -1] = False
            # a pixel is inked where something nearer passes in front of it: all round a big
            # step in depth, and only on the side away from the moon (below, to the right) for
            # small things standing a little proud of a wall, like a sill or a beam end
            gap = nz - dz
            other = npart != part
            dark |= on & non & (gap > 0.6)
            dark |= on & non & other & (gap > 0.30)
            if dy == 1 or dx == 1:
                dark |= on & non & other & (gap > 0.02)
        # the front lip of anything flat on top catches the moon, and so does the western edge
        # of anything standing (the side we never see is the one the moon is on)
        below = np.roll(on, -1, 0); below[-1, :] = False
        nb = np.roll(nrm, -1, 0); zb = np.roll(dz, -1, 0)
        edge_hi = on & below & (nrm[..., 2] > 0.8) & (nb[..., 1] < -0.6) & (np.abs(zb - dz) < 0.2) & (key > 0.3)
        lz = np.roll(dz, 1, 1); lz[:, 0] = -1e9
        rim = on & (nrm[..., 1] < -0.6) & ((dz - lz) > 0.5) & rim_ok[mid]
        edge_hi |= rim
        rgb[dark] = rgb[dark] * 0.52 + INK * 0.30
        hi = edge_hi & ~dark
        rgb[hi] = np.clip(rgb[hi] * 1.14 + np.array([12, 14, 20]), 0, 255)

    a = np.where(on, 255, 0).astype(np.uint8)
    img = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), a])
    if ink:
        # the dark line round the outside
        grow = np.zeros((H, W), bool)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            s = np.roll(on, (dy, dx), (0, 1))
            if dy == 1: s[0, :] = False
            if dy == -1: s[-1, :] = False
            if dx == 1: s[:, 0] = False
            if dx == -1: s[:, -1] = False
            grow |= s
        line = grow & ~on
        img[line] = (int(INK[0]), int(INK[1]), int(INK[2]), 255)
    out.rgba = img
    nm = np.zeros((H, W, 4), np.uint8)
    nm[..., :3] = np.clip((nrm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nm[..., 3] = np.clip(1 + Q[..., 2] * 24, 1, 255).astype(np.uint8)
    nm[~on] = (128, 128, 255, 1)
    out.normal = nm
    out.ax, out.ay = -x_lo, -y_lo
    out.lights = [(lx * PPU, -(ly + lz) * PPU, r, c, s, lz) for (lx, ly, lz, r, c, s) in model.lights]
    flat = P.reshape(-1, 3)
    low = flat[flat[:, 2] < 0.08]
    if len(low):
        out.foot = (low[:, 0].min() * PPU, -low[:, 1].max() * PPU, low[:, 0].max() * PPU, -low[:, 1].min() * PPU)

    if shadow:
        # the shadow on the ground: every ground pixel the moon cannot see past the model
        top = flat[:, 2].max()
        gx0 = math.floor(flat[:, 0].min() * PPU) - 1; gx1 = math.ceil((flat[:, 0].max() - MOON[0] / MOON[2] * top) * PPU) + 2
        gy0 = math.floor((flat[:, 1].min() - MOON[1] / MOON[2] * top) * PPU) - 2; gy1 = math.ceil(flat[:, 1].max() * PPU) + 1
        gw, gh = gx1 - gx0, gy1 - gy0
        gyy, gxx = np.mgrid[0:gh, 0:gw]
        G = np.stack([(gxx + gx0 + 0.5) / PPU, (gy1 - gyy - 0.5) / PPU, np.zeros((gh, gw))], -1)
        sh = ~_Shadow(P, MOON, 32).lit(G, bias=0.02)
        if sh.any():
            ys, xs = np.nonzero(sh)
            ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            out.shade = sh[ya:yb, xa:xb]
            out.sx, out.sy = -(gx0 + xa), gy1 - ya            # origin relative to the crop's top left (y down)
    return out
