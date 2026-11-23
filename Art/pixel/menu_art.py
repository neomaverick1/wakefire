"""Everything the pause screen paints with (Resources/Menu, the one texture folder the game reads
back): the item pictures, the flames and counters, and the map of the world, which is the places
themselves, each drawn whole and small and set where it lies.  python3 menu_art.py [preview.png]"""
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
# where each place sits on the sheet (its top left, in sheet pixels). North is up. The places are
# drawn to one scale and set as they join, except that the Hill is moved west of where its gate
# would put it, so it does not lie on top of the city.
LAYOUT = {
    'necropolis': (20, 2),
    'necro_road': (26, 72),
    'terraces': (2, 150),
    'temple_yard': (113, 28),
    'ashkel': (97, 94),
    'lowtown': (97, 150),
    'cliffs': (200, 150),
}
# the roads between them: (place, edge point in its own map pixels) pairs
ROADS = [(('lowtown', (480, 0)), ('ashkel', (480, 480))), (('ashkel', (480, 30)), ('temple_yard', (320, 576))),
         (('lowtown', (0, 320)), ('terraces', (832, 320))), (('lowtown', (960, 320)), ('cliffs', (0, 320))),
         (('terraces', (700, 14)), ('necro_road', (320, 704))), (('necro_road', (320, 44)), ('necropolis', (384, 640)))]
# places that are inside another: where their door is, in the outer place's own map pixels
INSIDE = {'zig_1': ('temple_yard', 320, 70), 'zig_2': ('temple_yard', 320, 70), 'zig_3': ('temple_yard', 320, 70), 'zig_hi': ('temple_yard', 320, 70),
          'crypt': ('terraces', 420, 30), 'barrow': ('necropolis', 676, 470),
          'tomb_1': ('necropolis', 384, 100), 'tomb_2': ('necropolis', 384, 100), 'tomb_3': ('necropolis', 384, 100)}
W, H = 292, 218


def clay(w, h, seed=7):
    """The tablet the world is drawn on: dark fired clay, a little uneven."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w))
    n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2))).astype(float) / 255
    base = np.array([34, 26, 40], float)
    a = base[None, None, :] * (0.82 + 0.5 * (n[..., None] - 0.5))
    fine = rng.normal(0, 2.0, (h, w, 1))
    return np.clip(a + fine, 0, 255)


def world():
    sheet = clay(W, H)
    dark = sheet.copy()
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
    # roads first, so the places sit on top of their ends
    road = Image.new('L', (W * 4, H * 4), 0)
    d = ImageDraw.Draw(road)
    pos = {p['map']: p for p in places}
    def at(name, pt):
        p = pos[name]
        return ((p['x'] + pt[0] / SCALE) * 4, (p['y'] + pt[1] / SCALE) * 4)
    for (a, b) in ROADS:
        pa, pb = at(*a), at(*b)
        mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        d.line([pa, (pa[0], mid[1]), (pb[0], mid[1]), pb] if abs(pa[1] - pb[1]) > abs(pa[0] - pb[0]) else [pa, (mid[0], pa[1]), (mid[0], pb[1]), pb], fill=255, width=7, joint='curve')
    road = np.array(road.resize((W, H), Image.LANCZOS)).astype(float) / 255
    for layer, k in ((sheet, 1.0), (dark, 0.35)):
        col = np.array([150, 124, 86], float) * k + layer * (1 - k)
        layer[:] = layer * (1 - road[..., None] * 0.85) + col * road[..., None] * 0.85
    for p in places:
        a = small[p['map']]
        x, y, w, h = p['x'], p['y'], p['w'], p['h']
        # a dark edge and a bronze line round each place, like an inlay
        for layer in (sheet, dark):
            layer[y - 2:y + h + 2, x - 2:x + w + 2] = (12, 8, 18)
        sheet[y - 1:y + h + 1, x - 1:x + w + 1] = (150, 100, 46)
        dark[y - 1:y + h + 1, x - 1:x + w + 1] = (58, 44, 44)
        sheet[y:y + h, x:x + w] = a
        # a place not yet walked: only its shape, as if under a cloth
        g = a.mean(axis=2, keepdims=True)
        dark[y:y + h, x:x + w] = np.clip(g * 0.16 + np.array([18, 14, 26]), 0, 255)
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
    for n in ('mirror_shield', 'night_oil', 'bronze_lamp', 'flame_vessel', 'big_key', 'hill_key', 'figs', 'dawn_horn', 'small_key', 'khopesh', 'sun_wheel', 'scroll', 'fork_zig', 'fork_tomb'):
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
