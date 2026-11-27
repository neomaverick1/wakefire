"""Everything the pause screen paints with (Resources/Menu, the one texture folder the game reads
back): the item pictures, the flames and counters, and the map of the world, which is the places
themselves, each drawn whole and small and set where it lies, in one land.  python3 menu_art.py [preview.png]"""
import json, os, sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RES = '/srv/Wakefire/Assets/Wakefire/Resources'
OUT = f'{RES}/Menu'
os.makedirs(OUT, exist_ok=True)


def compose(name):
    """A whole place as the waking world shows it: its ground with everything standing on it."""
    m = json.load(open(f'{RES}/Maps/{name}.json'))
    im = Image.open(f"{RES}/{m['ground']}.png").convert('RGBA')
    shade = np.zeros((im.height, im.width), bool)
    for o in m['objects']:
        if o['x'] < 0 or o.get('layer', 0) == 2 or not o.get('sh'): continue
        s = np.array(Image.open(f"{RES}/Objects/{o['sh']}.png").convert('RGBA'))[..., 3] > 0
        x0, y0 = o['x'] - o['shx'], o['y'] - o['shy']
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(im.width, x0 + s.shape[1]), min(im.height, y0 + s.shape[0])
        if xb > xa and yb > ya: shade[ya:yb, xa:xb] |= s[ya - y0:yb - y0, xa - x0:xb - x0]
    a = np.array(im).astype(float)
    a[shade, :3] = a[shade, :3] * 0.6 + np.array([3, 4, 13]) * 0.4
    im = Image.fromarray(a.astype('uint8'), 'RGBA')
    for o in sorted(m['objects'], key=lambda o: o['y']):
        if o['x'] < 0 or o.get('layer', 0) == 2: continue
        p = f"{RES}/Objects/{o['s']}.png"
        if not os.path.exists(p): continue
        s = Image.open(p).convert('RGBA')
        im.alpha_composite(s, (max(0, o['x'] - o['px']), max(0, o['y'] - o['py'])), (max(0, o['px'] - o['x']), max(0, o['py'] - o['y'])))
    return im.convert('RGB')


# ------------------------------------------------------------------ the world, one tenth the size
SCALE = 10
# where each place sits on the sheet (its top left, in sheet pixels). North is up. The places are drawn to
# one scale and set as they join: the town, the gate square and the temple yard one above the other, the
# terraces and the cliffs either side of the town. Only the Hill is moved, west of where its gate would put
# it, so that it does not lie on top of the city; a path through the rock makes up the difference.
LAYOUT = {
    'necropolis': (16, 2),
    'necro_road': (22, 72),
    'terraces': (8, 150),
    'temple_yard': (107, 34),
    'ashkel': (91, 92),
    'lowtown': (91, 140),
    'cliffs': (187, 150),
}
# the ways between places that do not touch: (place, edge point in its own map pixels) pairs
ROADS = [(('terraces', (700, 0)), ('necro_road', (320, 704))), (('necro_road', (320, 0)), ('necropolis', (384, 640)))]
# places that are inside another: where their door is, in the outer place's own map pixels
INSIDE = {'zig_1': ('temple_yard', 320, 70), 'zig_2': ('temple_yard', 320, 70), 'zig_3': ('temple_yard', 320, 70), 'zig_hi': ('temple_yard', 320, 70),
          'crypt': ('terraces', 420, 30), 'barrow': ('necropolis', 676, 470),
          'tomb_1': ('necropolis', 384, 100), 'tomb_2': ('necropolis', 384, 100), 'tomb_3': ('necropolis', 384, 100)}
W, H = 292, 228
HILL = ('necropolis', 'necro_road')            # the places that stand on the Hill of Sleepers, with nothing round them but the fall

GREEN = np.array([44, 132, 62], float); GREEN_D = np.array([30, 104, 52], float)
SEA = np.array([22, 42, 88], float); SEA_L = np.array([48, 84, 136], float); FOAM = np.array([190, 214, 236], float)
SAND = np.array([214, 190, 134], float); PATH = np.array([196, 166, 122], float); KERB = np.array([122, 96, 86], float)
ROCK = np.array([96, 92, 110], float); ROCK_D = np.array([54, 52, 72], float); ROCK_L = np.array([138, 134, 148], float)
WALL = np.array([214, 196, 150], float); WALL_D = np.array([120, 100, 88], float)
WHITE = np.array([222, 214, 198], float)
ROOFS = [np.array(c, float) for c in ((176, 60, 64), (54, 88, 182), (176, 60, 64), (54, 88, 182), (70, 150, 132), (188, 128, 60))]
LAPIS = np.array([44, 70, 170], float); GOLD = np.array([236, 190, 80], float)


def noise(rng, h, w, r):
    n = rng.normal(0, 1, (h, w))
    n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(float)
    return (n - n.min()) / max(1e-6, n.max() - n.min())


def land(seed=7):
    """The country the places lie in, drawn at the scale they are shown at, so that the whole sheet is one land: the
    sea along the south, the rock of the Hill to the west with the road of the dead climbing it, the rest of the
    sleeping city inside its wall to the east, and over the temple yard the ziggurat."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W]
    big, fine = noise(rng, H, W, 7), noise(rng, H, W, 1.2)
    a = np.zeros((H, W, 3), float)
    # ---- grass, kept: one green, tufts in a weave, a darker breath here and there
    a[:] = GREEN
    a[big > 0.62] = GREEN * 0.92 + GREEN_D * 0.08
    tuft = ((yy % 4) == 1) & (((xx + (yy // 4) * 3) % 6) == 1)
    a[tuft] = GREEN * 0.6 + GREEN_D * 0.4
    # orchards outside the wall: trees in rows, the same tree every time
    for (ox, oy, ow, oh) in ((192, 6, 86, 20), (2, 152, 5, 44)):
        for ty in range(oy, oy + oh - 3, 6):
            for tx in range(ox + (ty // 6 % 2) * 3, ox + ow - 3, 7):
                a[ty:ty + 3, tx:tx + 3] = GREEN_D * 0.8; a[ty:ty + 1, tx:tx + 2] = GREEN_D * 1.25; a[ty + 3:ty + 4, tx + 1:tx + 4] = GREEN * 0.7
    # ---- the sea: the coast runs along the foot of the terraces, the quay, the foot of the cliffs
    coast = np.full(W, 206.0)
    coast[:8] = 204; coast[8:92] = 213; coast[92:188] = 211; coast[188:278] = 207; coast[278:] = 196
    coast = coast + (noise(rng, 1, W, 3)[0] - 0.5) * 3
    sea = yy >= coast[None, :]
    wave = (((yy * 3 + xx + (fine * 5).astype(int)) % 9) == 0) | (((yy * 3 + xx + (fine * 5).astype(int)) % 9) == 1)
    a[sea] = SEA; a[sea & wave] = SEA_L
    deep = np.clip((yy - coast[None, :]) / 14.0, 0, 1)[..., None]
    a = np.where(sea[..., None], a * (1 - 0.25 * deep), a)
    shore = sea & ~np.roll(sea, 1, 0)
    a[shore] = FOAM
    a[np.roll(shore, -1, 0) & ~sea] = SAND
    # the east: past the cliffs, open water
    east = (xx >= 280 + (fine[:, :] * 3)) & (yy > 142)
    a[east & ~sea] = SEA; a[east & wave] = SEA_L
    # ---- the Hill: rock from the west edge of the sheet to the wall of the city, down to the top of the terraces
    edge = 88 + (noise(rng, H, 1, 4)[:, 0] - 0.5) * 6
    hill = (xx < edge[:, None]) & (yy < 149 + (noise(rng, 1, W, 3)[0][None, :] - 0.5) * 3)
    strata = ((yy + (big * 9).astype(int)) % 5) == 0
    rock = ROCK[None, None, :] * (0.86 + 0.3 * (fine[..., None] - 0.5)) + (big[..., None] - 0.5) * 26
    rock[strata] = rock[strata] * 0.72
    rock[np.roll(strata, 1, 0)] = rock[np.roll(strata, 1, 0)] * 1.12
    a[hill] = rock[hill]
    face = hill & ~np.roll(hill, 1, 0) | (hill & ~np.roll(hill, -2, 0))            # its upper lip lit, its foot in shade
    foot = ~hill & np.roll(hill, 2, 0) & ~sea
    a[foot] = a[foot] * 0.55
    side = ~hill & np.roll(hill, 2, 1) & (yy < 149)
    a[side] = ROCK_D
    # ---- the city: a wall round it, streets, and the roofs of the quarters nobody has walked
    cx0, cy0, cx1, cy1 = 89, 30, 284, 213
    city = (xx >= cx0) & (xx < cx1) & (yy >= cy0) & (yy < cy1) & ~((xx >= 187) & (yy >= 146))       # the cliffs lie outside it
    a[city & ~sea] = PATH
    # (small, close, and a little under the night: nobody has walked there, and it should not shout over the places he has)
    street = PATH * 0.86
    a[(xx >= 189) & (xx < cx1 - 2) & (yy >= cy0 + 2) & (yy < 144)] = street
    by = cy0 + 4
    row = 0
    while by < 141:
        h = 5 if row % 3 else 6
        bx = 190 + (row % 2) * 2
        while bx < cx1 - 8:
            k = int(rng.integers(0, 100))
            w = 5 + k % 3
            if k < 10:
                a[by:by + h, bx:bx + w] = GREEN * 0.8; a[by + 1:by + 3, bx + 2:bx + 4] = GREEN_D * 0.8        # a court, with a tree in it
            else:
                roof = ROOFS[0] if by < 92 else ROOFS[1]                    # red tile up by the temple, blue down by the water
                if k > 93: roof = ROOFS[4]
                roof = (roof * 0.7 + street * 0.3) * (0.9 + 0.2 * rng.random())
                a[by:by + h - 1, bx:bx + w] = roof
                a[by:by + 1, bx:bx + w] = roof * 1.15
                a[by + h - 1:by + h, bx:bx + w] = WHITE * 0.86
            bx += w + (2 if k % 4 else 3)
        by += h + (2 if row % 4 != 3 else 4)
        row += 1
    # the wall, and a tower every so often
    for (x0, y0, x1, y1) in ((cx0, cy0, cx1, cy0 + 2), (cx1 - 2, cy0, cx1, 146), (187, 144, cx1, 146), (cx0, cy0, cx0 + 2, 140)):
        a[y0:y1, x0:x1] = WALL
        a[y1:y1 + 1, x0:x1] = WALL_D
    for tx in range(cx0, cx1, 24):
        a[cy0 - 1:cy0 + 3, tx:tx + 4] = WALL * 1.08; a[cy0 + 3:cy0 + 4, tx:tx + 4] = WALL_D
    for ty in range(cy0 + 20, 146, 24):
        a[ty:ty + 4, cx1 - 3:cx1 + 1] = WALL * 1.08; a[ty + 4:ty + 5, cx1 - 3:cx1 + 1] = WALL_D
    # ---- the ziggurat, over the temple yard: three tiers, the stair up the front of it, the god's house on top
    zx, zy = 139, 4
    for k, (hw, y0, y1) in enumerate(((27, zy + 6, 36), (20, zy + 3, 30), (13, zy, 24))):
        tone = WALL * (0.78 + 0.1 * k)
        a[y0:y1, zx - hw:zx + hw] = tone
        a[y0:y0 + 1, zx - hw:zx + hw] = tone * 1.15
        a[y1 - 1:y1, zx - hw:zx + hw] = LAPIS if k < 2 else GOLD
        a[y0:y1, zx + hw:zx + hw + 1] = WALL_D
    a[zy + 8:36, zx - 2:zx + 2] = WALL * 1.1
    a[zy + 2:zy + 6, zx - 4:zx + 4] = LAPIS; a[zy + 1:zy + 2, zx - 4:zx + 4] = GOLD
    return np.clip(a, 0, 255), hill


def void_of(name, w, h):
    """How much of each sheet pixel of a place on the Hill is the fall, not ground (0..1)."""
    m = json.load(open(f'{RES}/Maps/{name}.json'))
    full = np.zeros((m['h'], m['w']), float)
    for b in m['boxes']:
        if (b.get('kind') or '') == 'pit' and b.get('layer', 0) == 0:
            full[max(0, b['y0']):b['y1'], max(0, b['x0']):b['x1']] = 1.0
    return np.array(Image.fromarray((full * 255).astype(np.uint8)).resize((w, h), Image.BOX)).astype(float) / 255


def world():
    sheet, hill = land()
    places = []
    small = {}
    for name, (x, y) in LAYOUT.items():
        im = compose(name)
        w, h = round(im.width / SCALE), round(im.height / SCALE)
        s = im.resize((w * 2, h * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 80, 2)).resize((w, h), Image.LANCZOS)
        a = np.array(s).astype(float)
        # the game is played at night; the map keeps the places' own colours, a little richer so
        # that a tenth of the size still tells town from olive grove from sea
        g = a.mean(axis=2, keepdims=True)
        a = np.clip(g + (a - g) * 1.25, 0, 255)
        a = np.clip(a * 1.04 + 4, 0, 255)
        small[name] = a
        places.append({'map': name, 'x': x, 'y': y, 'w': w, 'h': h})
    pos = {p['map']: p for p in places}
    # the ways through the rock between the places on the Hill, first, so that the places sit on their ends
    road = Image.new('L', (W * 4, H * 4), 0)
    d = ImageDraw.Draw(road)
    def at(name, pt):
        p = pos[name]
        return ((p['x'] + pt[0] / SCALE) * 4, (p['y'] + pt[1] / SCALE) * 4)
    for (pa_, pb_) in ROADS:
        pa, pb = at(*pa_), at(*pb_)
        mid = (pa[1] + pb[1]) / 2
        d.line([pa, (pa[0], mid), (pb[0], mid), pb], fill=255, width=9, joint='curve')
    road = np.array(road.resize((W, H), Image.LANCZOS)).astype(float) / 255
    sheet = sheet * (1 - road[..., None]) + PATH[None, None, :] * road[..., None]
    for p in places:
        a = small[p['map']]
        x, y, w, h = p['x'], p['y'], p['w'], p['h']
        if p['map'] in HILL:
            # a place on the Hill is its ground and nothing else: where it falls away, the rock of the Hill shows
            v = void_of(p['map'], w, h)[..., None]
            under = sheet[y:y + h, x:x + w]
            rim = (v[..., 0] > 0.5) & (np.roll(v[..., 0], 1, 0) <= 0.5)                 # under a lip that faces us: its shadow
            under[rim] = under[rim] * 0.5
            sheet[y:y + h, x:x + w] = a * (1 - v) + under * v
        else:
            sheet[y:y + h, x:x + w] = a
    sheet = np.clip(sheet, 0, 255)
    # a place not yet walked lies under the night: the same land, darker and bluer
    g = sheet.mean(axis=2, keepdims=True)
    dark = np.clip((g * 0.4 + sheet * 0.6) * 0.6 + np.array([6, 8, 26]), 0, 255)
    Image.fromarray(sheet.astype(np.uint8)).convert('RGBA').save(f'{OUT}/world.png')
    Image.fromarray(dark.astype(np.uint8)).convert('RGBA').save(f'{OUT}/world_dark.png')
    inside = [{'map': k, 'at': v[0], 'x': v[1], 'y': v[2]} for k, v in INSIDE.items()]
    json.dump({'w': W, 'h': H, 'scale': SCALE, 'places': places, 'inside': inside}, open(f'{OUT}/world.json', 'w'))
    print('world', W, H, [(p['map'], p['x'], p['y'], p['w'], p['h']) for p in places])
    return Image.fromarray(sheet.astype(np.uint8)), Image.fromarray(dark.astype(np.uint8))


def pictures():
    """The item pictures and the HUD's small things, copied to where the menus can read them."""
    def put(src, name, size=None):
        im = Image.open(src).convert('RGBA')
        if size and im.size != size:
            cv = Image.new('RGBA', size, (0, 0, 0, 0))
            cv.alpha_composite(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
            im = cv
        im.save(f'{OUT}/{name}.png')
    put(f'{RES}/UI/icon_lantern.png', 'wakefire', (16, 16))
    for n in ('mirror_shield', 'night_oil', 'bronze_lamp', 'flame_vessel', 'big_key', 'ghost_key', 'hill_key', 'figs', 'dawn_horn', 'small_key', 'khopesh', 'sun_wheel', 'scroll', 'fork_zig', 'fork_tomb'):
        put(f'{RES}/Items/{n}.png', n)
    for n in ('life_full', 'life_half', 'life_empty', 'coin', 'key'):
        put(f'{RES}/UI/{n}.png', n)


if __name__ == '__main__':
    pictures()
    lit, dark = world()
    if len(sys.argv) > 1:
        S = 4
        sheet = Image.new('RGB', (W * S * 2 + 24, H * S + 34), (16, 16, 22))
        d = ImageDraw.Draw(sheet)
        d.text((6, 6), 'INTERNAL TEST  -  the world map as the pause screen will paint it (4x): walked / not yet walked', fill=(255, 200, 60))
        sheet.paste(lit.resize((W * S, H * S), Image.NEAREST), (8, 28))
        sheet.paste(dark.resize((W * S, H * S), Image.NEAREST), (16 + W * S, 28))
        sheet.save(sys.argv[1]); print(sys.argv[1], sheet.size)
