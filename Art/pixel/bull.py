"""The Brazen Bull, hand-built in pixels: a bronze furnace in the shape of a bull, fire in its
flank, its chest and its nostrils, eyes like coals, horns with pale tips, a ring through its
nose and studs down its spine.

The body is modelled from solids (ellipsoids and tapered limbs) into a small depth buffer, so
masses that meet blend into one casting, and only real overlaps (a near leg over the barrel, the
head over the neck) get a dark seam. Light comes from the top left; the belly picks up the fire
from underneath. Tones are quantised to a short bronze ramp with no dithering, then the whole
import os
PREVIEWS = os.environ.get('WF_PREVIEWS', '/tmp/wakefire-previews')
os.makedirs(PREVIEWS, exist_ok=True)
silhouette gets the game's dark outline.

    python3 bull.py            export Resources/Sprites/bull.png/.json
    python3 bull.py preview    an INTERNAL TEST sheet in the scratchpad
"""
import sys, math, json
import numpy as np
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Sprites'
SCRATCH = PREVIEWS
CELL = 112
FX, FY = 56, 97

O = (22, 14, 30, 255)


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


RAMPS = {
    'bronze': [rgb(h) for h in ('#ffeeb0', '#f0bc58', '#c98432', '#985622', '#683216', '#3e1a0c')],
    'far': [rgb(h) for h in ('#d29a4a', '#ad722c', '#87501e', '#633614', '#43220c', '#2a1408')],
    'horn': [rgb(h) for h in ('#fffbea', '#f2e6c4', '#d4c296', '#a89070', '#76604a', '#4c3c30')],
    'horn_tip': [rgb(h) for h in ('#ffffff', '#fffbea', '#f2ead0', '#d8cba8', '#a8987a', '#76664e')],
    'hoof': [rgb(h) for h in ('#7a5a44', '#5a4030', '#402c22', '#2e2018', '#1e1410', '#140c0a')],
}
BOUNCE = [rgb('#c8601e'), rgb('#94401a'), rgb('#622410')]     # fire light on the underside
FIRE = [rgb(h) for h in ('#fffbe0', '#ffe27a', '#ffb43a', '#f2701c', '#b83a10', '#5a160a')]
COOL = [rgb(h) for h in ('#8c7a6a', '#6a5a4c', '#4e4238', '#3a302a', '#2a221e', '#1c1614')]
SEAM = {'bronze': rgb('#4a220e'), 'far': rgb('#2a1408'), 'horn': rgb('#5a4630'), 'horn_tip': rgb('#6a5a44'), 'hoof': rgb('#140c0a')}
L = np.array([-0.45, -0.75, 0.52]); L = L / np.linalg.norm(L)
YY, XX = np.mgrid[0:CELL, 0:CELL].astype(np.float64) + 0.5


class Scene:
    """A tiny depth buffer: each solid writes depth, normal and material where it is nearest."""

    def __init__(self):
        self.z = np.full((CELL, CELL), -1e9)
        self.n = np.zeros((CELL, CELL, 3))
        self.mat = np.full((CELL, CELL), '', dtype=object)
        self.pid = np.full((CELL, CELL), -1)
        self.count = 0

    def _put(self, m, z, nx, ny, nz, mat):
        w = m & (z > self.z)
        self.z[w] = z[w]
        nrm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        self.n[w, 0] = (nx / nrm)[w]; self.n[w, 1] = (ny / nrm)[w]; self.n[w, 2] = (nz / nrm)[w]
        self.mat[w] = mat
        self.pid[w] = self.count
        self.count += 1

    def ell(self, cx, cy, cz, rx, ry, rz, mat='bronze', tilt=0.0, power=2.0):
        ca, sa = math.cos(tilt), math.sin(tilt)
        dx0, dy0 = XX - cx, YY - cy
        u = (dx0 * ca + dy0 * sa) / rx
        v = (-dx0 * sa + dy0 * ca) / ry
        d = np.abs(u) ** power + np.abs(v) ** power
        m = d <= 1.0
        h = np.sqrt(np.clip(1 - d, 0, 1))
        gu, gv = u / rx, v / ry
        nx = gu * ca - gv * sa
        ny = gu * sa + gv * ca
        self._put(m, cz + rz * h, nx, ny, h / rz, mat)

    def limb(self, a, b, r0, r1, mat='bronze'):
        (x0, y0, z0), (x1, y1, z1) = a, b
        abx, aby = x1 - x0, y1 - y0
        L2 = abx * abx + aby * aby + 1e-9
        t = np.clip(((XX - x0) * abx + (YY - y0) * aby) / L2, 0, 1)
        qx, qy = XX - (x0 + abx * t), YY - (y0 + aby * t)
        r = r0 + (r1 - r0) * t
        d2 = qx * qx + qy * qy
        m = d2 <= r * r
        h = np.sqrt(np.clip(r * r - d2, 0, None))
        self._put(m, z0 + (z1 - z0) * t + h, qx, qy, h, mat)

    def chain(self, pts, radii, mats):
        for i in range(len(pts) - 1):
            self.limb(pts[i], pts[i + 1], radii[i], radii[i + 1], mats[min(i, len(mats) - 1)])

    def render(self, lit=1.0):
        cv = Canvas(CELL, CELL)
        on = self.pid >= 0
        nx, ny, nz = self.n[:, :, 0], self.n[:, :, 1], self.n[:, :, 2]
        v = nx * L[0] + ny * L[1] + nz * L[2]
        spec = np.clip(2 * v * nz - L[2], 0, None) ** 22
        idx = np.where(v > 0.74, 1, np.where(v > 0.46, 2, np.where(v > 0.14, 3, np.where(v > -0.22, 4, 5))))
        idx = np.where(spec > 0.55, 0, idx)
        for y in range(CELL):
            for x in range(CELL):
                if not on[y, x]:
                    continue
                mt = self.mat[y, x]
                i = idx[y, x]
                c = RAMPS[mt][i]
                if mt in ('bronze', 'far') and ny[y, x] > 0.42 and i >= 3 and lit > 0.3:
                    c = BOUNCE[min(2, i - 3)] if mt == 'bronze' else RAMPS['far'][i]
                cv.a[y, x] = c
        # seams where a nearer solid crosses a farther one
        z = self.z
        for y in range(1, CELL - 1):
            for x in range(1, CELL - 1):
                if not on[y, x]:
                    continue
                for (yy, xx) in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if on[yy, xx] and self.pid[yy, xx] != self.pid[y, x] and z[yy, xx] - z[y, x] > 3.0:
                        cv.a[y, x] = SEAM.get(self.mat[y, x], SEAM['bronze'])
                        break
        if lit < 1.0:
            # a dying furnace: the metal goes dull and cold
            a = cv.a.astype(np.float32)
            g = a[:, :, :3].mean(axis=2, keepdims=True)
            k = 1.0 - lit
            a[:, :, :3] = a[:, :, :3] * (1 - 0.55 * k) + g * 0.25 * k
            cv.a = a.clip(0, 255).astype(np.uint8)
        cv.outline(O)
        return cv


def grille(cv, x0, y0, w, h, t, lit=1.0):
    """A furnace opening: iron frame, bars, fire moving behind them."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
            bar = (x - x0) % 3 == 0
            if edge:
                c = rgb('#2a1208')
            elif bar:
                c = rgb('#5a2c12') if lit > 0.2 else COOL[4]
            elif lit <= 0.2:
                c = COOL[5]
            else:
                fy = (y - y0) / max(1, h - 1)
                flick = 0.5 + 0.5 * math.sin(t * 6.28 * 2 + x * 1.7 + y * 0.9)
                vv = ((1 - fy) * 0.3 + fy * 0.8 + flick * 0.3) * lit
                c = FIRE[0 if vv > 0.95 else 1 if vv > 0.75 else 2 if vv > 0.5 else 3 if vv > 0.3 else 4]
            cv.px(x, y, c)


def coal(cv, x, y, lit=1.0):
    if lit > 0.2:
        cv.px(x, y, FIRE[1]); cv.px(x + 1, y, FIRE[0]); cv.px(x, y + 1, FIRE[3]); cv.px(x + 1, y + 1, FIRE[2])
    else:
        cv.px(x, y, COOL[3]); cv.px(x + 1, y, COOL[2]); cv.px(x, y + 1, COOL[4]); cv.px(x + 1, y + 1, COOL[4])


def ring(cv, x, y, r=2.3):
    for a in range(0, 360, 20):
        rx_, ry_ = int(round(x + math.cos(math.radians(a)) * r)), int(round(y + math.sin(math.radians(a)) * r))
        cv.px(rx_, ry_, rgb('#fff1b0') if 150 <= a <= 250 else rgb('#d8a040') if a < 150 else rgb('#7a4818'))


def studs(cv, xs, lo=0):
    for sx in xs:
        top = None
        for y in range(lo, CELL):
            if cv.a[y, sx, 3] > 0 and tuple(cv.a[y, sx]) != O:
                top = y; break
        if top is not None:
            cv.px(sx, top, rgb('#fff6d0')); cv.px(sx + 1, top, rgb('#f0bc58')); cv.px(sx, top + 1, rgb('#985622'))


def tuft(cv, x, y, lit=1.0):
    if lit <= 0.2:
        return
    for (ox, oy, i) in ((0, 0, 2), (-1, 1, 3), (1, 1, 1), (0, 2, 0), (0, 3, 2), (-1, 2, 4), (1, 3, 3), (0, 4, 3)):
        cv.px(x + ox, y + oy, FIRE[i])


def puffs(cv, pts, lit=1.0):
    for k, (x, y) in enumerate(pts):
        for (ox, oy) in ((0, 0), (1, 0), (0, -1), (1, -1)):
            cv.px(x + ox, y + oy, (FIRE[1] if k == 0 else FIRE[2] if k == 1 else FIRE[3]) if lit > 0.2 else COOL[1])


# ----------------------------------------------------------------------------- side view (facing right)
def side(t=0.0, legs=None, bob=0, head=(0, 0), jaw=0, low=0, lit=1.0, tail=0.0, puff=0, kneel=0.0):
    """legs: four (foot dx, lift) for far-hind, far-front, near-hind, near-front."""
    cx, base = FX - 6, FY
    legs = legs or [(0, 0)] * 4
    S = Scene()
    y0 = base + bob + low                       # every body height is measured from here
    hdx, hdy = head
    # legs: hip/shoulder, joint, fetlock, hoof
    def leg(k):
        far = k < 2
        front = k in (1, 3)
        z = -7 if far else 8
        mat = 'far' if far else 'bronze'
        fb = base - (2 if far else 0)            # far feet sit a little higher: further away
        dx, lift = legs[k]
        if front:
            top = (cx + 15 + (0 if far else 2), y0 - 34, z)
            foot = (top[0] + 2 + dx, fb - 4 - lift, z)
            kx = top[0] + (foot[0] - top[0]) * 0.55 + lift * 0.9
            knee = (kx, y0 - 14 - lift * 0.6 + low * 0.4, z)
            if kneel:
                knee = (top[0] + 6 * kneel, base - 5, z + 2)
                foot = (top[0] + 10 * kneel, base - 4, z + 2)
            S.limb(top, knee, 6.4, 4.4, mat)
        else:
            top = (cx - 26 + (0 if far else 2), y0 - 33, z)
            foot = (top[0] + 2 + dx, fb - 4 - lift, z)
            hock = (top[0] - 4 + (foot[0] - top[0]) * 0.4, y0 - 15 - lift * 0.5 + low * 0.4, z)
            S.limb(top, (top[0] + 3, y0 - 24, z), 8.5, 6.0, mat)      # the thigh
            S.limb((top[0] + 3, y0 - 24, z), hock, 5.6, 3.6, mat)    # the gaskin, back to the hock
            knee = hock
        S.limb(knee, foot, 3.4, 2.9, mat)
        S.ell(foot[0] + 0.5, foot[1] + 2.2, z + 1, 3.6, 2.3, 2.5, 'hoof', power=2.6)
        return foot
    for k in range(4):
        leg(k)
    # body masses: hindquarters, barrel, shoulder, hump, chest
    S.ell(cx - 24, y0 - 41, 0, 13, 15, 12)
    S.ell(cx - 5, y0 - 38, 0, 23, 14, 14, power=2.2)
    S.ell(cx + 12, y0 - 43, 1, 15, 17, 14)
    S.ell(cx + 5, y0 - 53, -1, 13, 8, 10)
    S.ell(cx + 22, y0 - 34, 2, 8, 12, 10)
    # the tail, swinging from the rump
    S.chain([(cx - 36, y0 - 49, -1), (cx - 39 + tail * 0.3, y0 - 40, -1), (cx - 40 + tail * 0.8, y0 - 30, 0), (cx - 39 + tail * 1.2, y0 - 22, 0)],
            [1.8, 1.6, 1.4, 1.2], ['bronze'])
    # neck, head, muzzle, jaw, ear, horns
    hx, hy = cx + 35 + hdx, y0 - 44 + hdy
    S.limb((cx + 16, y0 - 48, 2), (hx - 2, hy + 2, 4), 10.5, 7.5)
    if jaw:
        S.ell(hx + 3, hy + 13 + jaw, 3, 5.5, 2.6, 4, 'far', tilt=0.5)
    S.ell(hx, hy, 5, 8, 7.2, 7)
    S.limb((hx + 1, hy + 1, 5), (hx + 5, hy + 10, 6), 6.6, 5.4)
    S.ell(hx + 6, hy + 11 - (2 if jaw else 0), 6, 5.4, 4.2, 5, power=2.4)
    S.ell(hx - 6, hy - 2, 4, 4.2, 2.0, 2, tilt=-0.5)
    S.limb((hx - 4, hy - 4, 8), (hx + 4, hy - 5, 8), 2.0, 2.0)             # the brow ridge
    hp = [(hx - 1, hy - 6, 9), (hx + 3, hy - 10, 11), (hx + 9, hy - 12, 11), (hx + 12, hy - 18, 10)]
    S.chain([(p[0] - 2, p[1] - 1, -2) for p in hp], [2.4, 1.9, 1.3, 0.6], ['far', 'far', 'horn'])
    S.chain(hp, [2.6, 2.1, 1.5, 0.7], ['horn', 'horn', 'horn_tip'])
    cv = S.render(lit)
    # the fire in it
    grille(cv, cx - 13, y0 - 43, 13, 8, t, lit)
    coal(cv, hx + 1, hy - 3, lit)
    nx_, ny_ = int(hx + 9), int(hy + 10 - (2 if jaw else 0))
    if lit > 0.2:
        cv.px(nx_, ny_, FIRE[1]); cv.px(nx_, ny_ + 1, FIRE[3])
    ring(cv, nx_ - 1, ny_ + 4)
    if jaw:
        for k in range(jaw):
            for x in range(int(hx) + 1, int(hx) + 9 - k):
                cv.px(x, int(hy) + 11 + k, FIRE[min(4, k + 1)] if lit > 0.2 else COOL[4])
    studs(cv, [cx - 22 + k * 7 for k in range(7)])
    for k in range(4):                                                   # rivets along the shoulder plate
        cv.px(cx + 4 + (k % 2), y0 - 47 + k * 5, rgb('#fff1b0')); cv.px(cx + 4 + (k % 2), y0 - 46 + k * 5, rgb('#683216'))
    tuft(cv, int(cx - 39 + tail * 1.2), y0 - 21, lit)
    if puff:
        puffs(cv, [(nx_ + 3 + k * 3, ny_ - 1 - k) for k in range(puff)], lit)
    return cv


# ----------------------------------------------------------------------------- front view
def front(t=0.0, step=0.0, bob=0, head=0, jaw=0, low=0, lit=1.0, puff=0, splay=0, kneel=0.0):
    cx, base = FX, FY
    y0 = base + bob + low
    S = Scene()
    # hind legs behind and outside
    for s_, ph in ((-1, 0.5), (1, 0.0)):
        lift = max(0, int(round(math.sin((t + ph) * 2 * math.pi) * step * 3)))
        x = cx + s_ * 17
        S.limb((x, y0 - 28, -14), (x + s_ * splay, base - 6 - lift, -14), 6.0, 3.4, 'far')
        S.ell(x + s_ * splay, base - 4 - lift, -13, 3.8, 2.3, 2, 'hoof')
    S.ell(cx, y0 - 35, -8, 23, 14, 12)                 # the barrel, at the sides
    S.ell(cx, y0 - 50, -4, 18, 10, 10)                 # the hump behind the head
    S.ell(cx, y0 - 37, 0, 21, 17, 12, power=2.2)       # chest and shoulders
    for s_, ph in ((-1, 0.0), (1, 0.5)):
        lift = max(0, int(round(math.sin((t + ph) * 2 * math.pi) * step * 3)))
        x = cx + s_ * 11
        if kneel:
            S.limb((x, y0 - 28, 6), (x + s_ * 1, base - 5, 12), 7.6, 5.2)
            S.ell(x + s_ * 1, base - 4, 13, 5.4, 3.2, 3, 'bronze')
            continue
        S.limb((x, y0 - 28, 6), (x + s_ * (1 + splay * 0.5), base - 13 - lift, 7), 7.6, 5.0)
        S.limb((x + s_ * (1 + splay * 0.5), base - 13 - lift, 7), (x + s_ * (1 + splay), base - 5 - lift, 7), 4.0, 3.4)
        S.ell(x + s_ * (1 + splay), base - 3 - lift, 8, 4.4, 2.6, 2.5, 'hoof', power=2.6)
    hy = y0 - 50 + head
    for s_ in (-1, 1):
        S.ell(cx + s_ * 12, hy - 1, 9, 4.6, 2.3, 2, 'bronze', tilt=s_ * 0.35)
    if jaw:
        S.ell(cx, hy + 18 + jaw, 12, 5, 2.4 + jaw * 0.5, 3, 'far')
    S.ell(cx, hy, 12, 9, 8, 7)
    S.limb((cx, hy + 2, 12), (cx, hy + 12, 14), 7.4, 6.2)
    S.ell(cx, hy + 14 - (2 if jaw else 0), 15, 7.0, 5.0, 5, power=2.4)
    S.limb((cx - 8, hy - 4, 18), (cx + 8, hy - 4, 18), 2.3, 2.3)          # brow ridge
    for s_ in (-1, 1):
        S.chain([(cx + s_ * 7, hy - 5, 13), (cx + s_ * 16, hy - 7, 13), (cx + s_ * 24, hy - 10, 12), (cx + s_ * 26, hy - 18, 11)],
                [2.6, 2.1, 1.5, 0.7], ['horn', 'horn', 'horn_tip'])
    cv = S.render(lit)
    grille(cv, cx - 6, y0 - 30, 13, 8, t, lit)                            # the furnace door in the chest
    for s_ in (-1, 1):
        coal(cv, cx + s_ * 5 - (1 if s_ > 0 else 0), int(hy) - 2, lit)
    if lit > 0.2:
        for s_ in (-1, 1):
            cv.px(cx + s_ * 3 - (1 if s_ > 0 else 0), int(hy) + 14 - (2 if jaw else 0), FIRE[1])
    ring(cv, cx - 0.5, hy + 18 - (2 if jaw else 0), 2.5)
    if jaw:
        for k in range(jaw):
            for x in range(cx - 3 + k, cx + 3 - k):
                cv.px(x, int(hy) + 16 + k, FIRE[min(4, k + 1)] if lit > 0.2 else COOL[4])
    if puff:
        for s_ in (-1, 1):
            puffs(cv, [(cx + s_ * (5 + k * 2) - (1 if s_ < 0 else 0), int(hy) + 15 + k * 2) for k in range(puff)], lit)
    return cv


# ----------------------------------------------------------------------------- back view
def back(t=0.0, step=0.0, bob=0, head=0, low=0, lit=1.0, tail=0.0, splay=0):
    cx, base = FX, FY
    y0 = base + bob + low
    S = Scene()
    for s_, ph in ((-1, 0.0), (1, 0.5)):
        lift = max(0, int(round(math.sin((t + ph) * 2 * math.pi) * step * 3)))
        x = cx + s_ * 16
        S.limb((x, y0 - 28, -14), (x + s_ * splay, base - 6 - lift, -14), 5.6, 3.4, 'far')
        S.ell(x + s_ * splay, base - 5 - lift, -13, 3.6, 2.2, 2, 'hoof')
    hy = y0 - 56 + head
    for s_ in (-1, 1):
        S.chain([(cx + s_ * 6, hy + 1, -10), (cx + s_ * 15, hy - 1, -10), (cx + s_ * 23, hy - 4, -10), (cx + s_ * 25, hy - 12, -10)],
                [2.6, 2.1, 1.5, 0.7], ['horn', 'horn', 'horn_tip'])
        S.ell(cx + s_ * 10, hy + 3, -11, 4.2, 2.0, 2, 'far', tilt=s_ * 0.3)
    S.ell(cx, hy + 3, -12, 7, 5, 6, 'far')
    S.ell(cx, y0 - 48, -4, 19, 10, 10)
    S.ell(cx, y0 - 35, 4, 20, 16, 12, power=2.2)
    for s_, ph in ((-1, 0.5), (1, 0.0)):
        lift = max(0, int(round(math.sin((t + ph) * 2 * math.pi) * step * 3)))
        x = cx + s_ * 11
        S.limb((x, y0 - 28, 8), (x + s_ * 1, y0 - 15 - lift, 9), 8.0, 5.0)
        S.limb((x + s_ * 1, y0 - 15 - lift, 9), (x + s_ * (1 + splay), base - 5 - lift, 9), 4.0, 3.4)
        S.ell(x + s_ * (1 + splay), base - 3 - lift, 10, 4.4, 2.6, 2.5, 'hoof', power=2.6)
    tp = [(cx, y0 - 47, 14), (cx + tail * 0.4, y0 - 37, 17), (cx + tail * 0.9, y0 - 27, 16), (cx + tail * 1.3, y0 - 19, 15)]
    S.chain(tp, [1.8, 1.6, 1.4, 1.2], ['bronze'])
    cv = S.render(lit)
    grille(cv, cx - 10, y0 - 54, 7, 5, t, lit)
    grille(cv, cx + 4, y0 - 54, 7, 5, t + 0.3, lit)
    for k in range(5):
        y = y0 - 44 + k * 6
        cv.px(cx - 4, y, rgb('#fff1b0')); cv.px(cx + 4, y, rgb('#fff1b0'))
        cv.px(cx - 4, y + 1, rgb('#683216')); cv.px(cx + 4, y + 1, rgb('#683216'))
    tuft(cv, int(cx + tail * 1.3), y0 - 18, lit)
    return cv


# ----------------------------------------------------------------------------- animation
WALK = [  # foot dx and lift for far-hind, far-front, near-hind, near-front
    [(-5, 0), (5, 0), (5, 2), (-5, 0)],
    [(-3, 0), (3, 0), (2, 4), (-3, 0)],
    [(-1, 0), (1, 2), (-1, 3), (-1, 0)],
    [(2, 0), (-2, 4), (-3, 0), (2, 0)],
    [(5, 2), (-5, 0), (-5, 0), (5, 0)],
    [(2, 4), (-3, 0), (-3, 0), (3, 0)],
    [(-1, 3), (-1, 0), (-1, 0), (1, 2)],
    [(-3, 0), (2, 0), (2, 0), (-2, 4)],
]
CHARGE = [  # a gallop: the hind pair drive together, the front pair reach together
    [(-9, 0), (8, 3), (-7, 0), (10, 4)],
    [(-11, 2), (5, 0), (-9, 3), (7, 0)],
    [(-4, 5), (-3, 0), (-2, 6), (-1, 0)],
    [(5, 3), (-8, 0), (7, 4), (-6, 0)],
    [(9, 0), (-10, 2), (7, 0), (-12, 3)],
    [(6, 0), (-9, 4), (8, 0), (-7, 5)],
    [(0, 0), (1, 6), (1, 0), (3, 7)],
    [(-6, 0), (6, 5), (-4, 0), (8, 6)],
]


def frames(anim, d, n):
    F = []
    for i in range(n):
        t = i / n
        if d == 'left':
            if anim == 'idle':
                F.append(side(t=t, bob=1 if i in (1, 2) else 0, head=(0, 1 if i in (1, 2) else 0), tail=[0, 1, 2, 1][i % 4]))
            elif anim == 'walk':
                F.append(side(t=t, legs=WALK[i % 8], bob=-1 if i % 4 in (2,) else 0, head=(0, [0, 1, 1, 0][i % 4]), tail=[0, 1, 2, 1][i % 4]))
            elif anim == 'charge':
                F.append(side(t=t, legs=CHARGE[i % 8], bob=[-1, 0, -2, 0][i % 4], head=(4, 9), low=2, tail=-4 + (i % 2), puff=1 + i % 2))
            elif anim == 'stun':
                F.append(side(t=t, head=(2, 14), low=3, legs=[(-4, 0), (6, 0), (-2, 0), (8, 0)], lit=0.7, tail=2 + i, puff=0))
            elif anim == 'shoot':
                F.append(side(t=t, head=[(0, 0), (-2, -6), (2, -3), (0, 0)][i], jaw=[0, 2, 4, 1][i], tail=1))
            elif anim == 'hurt':
                F.append(side(t=t, head=(-3, -4), bob=-1, jaw=1, tail=-2))
            else:
                F.append(side(t=t))
        elif d == 'down':
            if anim == 'idle':
                F.append(front(t=t, bob=1 if i in (1, 2) else 0, head=1 if i in (1, 2) else 0))
            elif anim == 'walk':
                F.append(front(t=t, step=1.0, bob=-1 if i % 4 == 2 else 0))
            elif anim == 'charge':
                F.append(front(t=t, step=1.6, bob=[-1, 0, -2, 0][i % 4], head=8, low=2, puff=1 + i % 2))
            elif anim == 'stun':
                F.append(front(t=t, head=12, low=3, lit=0.7, splay=2))
            elif anim == 'shoot':
                F.append(front(t=t, head=[0, -5, -2, 0][i], jaw=[0, 2, 4, 1][i]))
            elif anim == 'hurt':
                F.append(front(t=t, head=-4, bob=-1, jaw=1))
            elif anim == 'death':
                F.append(death(i))
            else:
                F.append(front(t=t))
        else:
            if anim == 'idle':
                F.append(back(t=t, bob=1 if i in (1, 2) else 0, tail=[0, 1, 2, 1][i % 4]))
            elif anim == 'walk':
                F.append(back(t=t, step=1.0, bob=-1 if i % 4 == 2 else 0, tail=[0, 1, 2, 1][i % 4]))
            elif anim == 'charge':
                F.append(back(t=t, step=1.6, bob=[-1, 0, -2, 0][i % 4], head=6, low=2, tail=2))
            elif anim == 'stun':
                F.append(back(t=t, head=8, low=3, lit=0.7, splay=2, tail=1))
            elif anim == 'shoot':
                F.append(back(t=t, head=[0, -4, -2, 0][i]))
            elif anim == 'hurt':
                F.append(back(t=t, head=-3, bob=-1))
            else:
                F.append(back(t=t))
    return F


def death(i):
    """It staggers, its front knees go, it sinks onto them, and the fire in it goes out."""
    if i == 0:
        return front(head=-5, jaw=3, bob=-1)
    if i == 1:
        return front(head=6, low=4, splay=3, jaw=1, lit=0.8)
    if i == 2:
        return front(head=12, low=9, kneel=1.0, lit=0.55)
    if i == 3:
        return front(head=15, low=12, kneel=1.0, lit=0.3)
    return front(head=16, low=13, kneel=1.0, lit=0.0)


def export():
    from PIL import Image
    old = json.load(open(f'{OUT}/bull.json'))
    rows = []
    for a in old['anims']:
        fr = frames(a['name'], a['dir'], a['frames'])
        if a['dir'] == 'left':
            fl = []
            for f in fr:
                g = Canvas(CELL, CELL); g.a[:, :] = f.a[:, ::-1]; fl.append(g)
            fr = fl
        rows.append((a, fr))
    W = max(len(r[1]) for r in rows) * CELL
    img = Image.new('RGBA', (W, len(rows) * CELL), (0, 0, 0, 0))
    meta = {"size": CELL, "pivot": [FX, FY], "anims": []}
    for ri, (a, fr) in enumerate(rows):
        for ci, f in enumerate(fr):
            img.paste(f.image(), (ci * CELL, ri * CELL))
        meta["anims"].append({"name": a['name'], "dir": a['dir'], "row": ri, "frames": len(fr)})
    img.save(f'{OUT}/bull.png')
    json.dump(meta, open(f'{OUT}/bull.json', 'w'))
    print('bull', img.size)


def preview(path, picks=None):
    from PIL import Image, ImageDraw, ImageFont
    picks = picks or [('idle', 'left', 4), ('walk', 'left', 8), ('charge', 'left', 8), ('shoot', 'left', 4), ('stun', 'left', 2),
                      ('idle', 'down', 4), ('shoot', 'down', 4), ('death', 'down', 5), ('walk', 'up', 4)]
    Z = 2
    cols = 8
    out = Image.new('RGB', (130 + cols * (CELL * Z + 2), 36 + len(picks) * (CELL * Z + 2)), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - the bull (x2)', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22))
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    for r, (an, dr, n) in enumerate(picks):
        fr = frames(an, dr, n)
        y = 34 + r * (CELL * Z + 2)
        d.text((4, y + 60), f'{an} {dr}', fill=(220, 220, 220), font=fs)
        for c, f in enumerate(fr[:cols]):
            bg = Image.new('RGBA', (CELL, CELL), (92, 74, 60, 255))
            bg.alpha_composite(f.image())
            out.paste(bg.convert('RGB').resize((CELL * Z, CELL * Z), Image.NEAREST), (130 + c * (CELL * Z + 2), y))
    out.save(path)
    print(out.size)


if __name__ == '__main__':
    if 'preview' in sys.argv:
        picks = None
        if len(sys.argv) > 2:
            picks = [tuple(p.split(':')[:2]) + (int(p.split(':')[2]),) for p in sys.argv[2:]]
        preview(f'{SCRATCH}/internal-test-bull.png', picks)
    else:
        export()
