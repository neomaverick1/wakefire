"""Map building: a baked ground layer plus separate prop sprites (sorted by their base, so the
hero walks behind trees and in front of houses), collision boxes, lights and game markers,
exported for Unity as PNGs and one JSON file per map."""
import os
import json
import numpy as np
from PIL import Image
from px import Canvas, R
import forge
from ground import Terrain

RES = "/srv/Wakefire/Assets/Wakefire/Resources"


SURF_CELL = 8
_SURF = {'g': ('grass', 'grass_dark', 'leaf', 'olive', 'cypress', 'flower_y', 'flower_w', 'flower_r'),
         's': ('sand', 'dirt', 'mud', 'straw'),
         'w': ('wood', 'cedar', 'trunk'),
         'a': ('sea', 'water')}


def surface_grid(cv):
    """What Azar's sandals land on, one letter per 8x8 cell: g grass, s sand and earth, w wood,
    a water, c stone (everything else). Found from the ground picture's own palette ramps."""
    import numpy as np
    names, cols = [], []
    for k, ramp in R.items():
        for c in ramp:
            names.append(k); cols.append(c[:3])
    cols = np.array(cols, float)
    letter = {}
    for ch, ks in _SURF.items():
        for k in ks:
            letter[k] = ch
    a = cv.a[:, :, :3].astype(float)
    H, W = a.shape[:2]
    rows = []
    for y0 in range(0, H, SURF_CELL):
        row = []
        for x0 in range(0, W, SURF_CELL):
            px = a[y0:y0 + SURF_CELL:2, x0:x0 + SURF_CELL:2].reshape(-1, 3)
            d = ((px[:, None, :] - cols[None, :, :]) ** 2).sum(2)
            votes = {}
            for i in d.argmin(1):
                ch = letter.get(names[i], 'c')
                votes[ch] = votes.get(ch, 0) + 1
            row.append(max(votes, key=votes.get))
        rows.append(''.join(row))
    return rows


def normal_from_luma(rgba, k=2.6):
    """A normal map for a painted ground that has no heights of its own: brighter is taken as higher,
    so mortar lines and cracks sit low and the faces of stones sit high."""
    a = rgba.astype(float)
    lum = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114) / 255.0
    dx = np.roll(lum, 1, 1) - np.roll(lum, -1, 1); dy = np.roll(lum, -1, 0) - np.roll(lum, 1, 0)
    n = np.dstack([dx * k, dy * k, np.ones_like(lum)]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    out = np.zeros((*lum.shape, 4), np.uint8)
    out[..., :3] = np.clip((n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8); out[..., 3] = 1
    return out


class MapBuilder:
    def __init__(self, name, w_tiles, h_tiles, ground_fill, music="town"):
        self.name = name
        self.music = music
        self.W, self.H = w_tiles * 16, h_tiles * 16
        self.ground = Canvas(self.W, self.H, ground_fill)
        self.objects = []
        self.boxes = []       # extra solid boxes (px, map space): [x0, y0, x1, y1, layer]
        self.lights = []
        self.markers = []
        self.sprite_cache = {}
        self.terrain = None       # the new ground (ground.Terrain), if this map is laid with it
        self.ground_n = None      # the ground's normal map (h, w, 4)

    # ---- the ground
    def lay(self, seed=0):
        """Start the ground as a Terrain of materials with relief (see ground.py)."""
        self.terrain = Terrain(self.W, self.H, seed)
        return self.terrain

    def bake(self):
        """Turn the Terrain into the ground picture; after this the old painters can still draw on m.ground."""
        rgb, nm = self.terrain.render()
        self.ground.a[..., :3] = rgb; self.ground.a[..., 3] = 255
        self.ground_n = nm
        return self.ground

    def set_into_ground(self, model, x, y, seed=0):
        """Something low and walked on (a terrace, steps, a kerb) drawn straight into the ground."""
        d = forge.draw(model, seed=seed, shadow=False)
        h, w = d.rgba.shape[:2]
        x0, y0 = int(x) - d.ax, int(y) - d.ay
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(self.W, x0 + w), min(self.H, y0 + h)
        sub = d.rgba[ya - y0:yb - y0, xa - x0:xb - x0]
        on = sub[..., 3] > 0
        self.ground.a[ya:yb, xa:xb][on] = sub[on]
        if self.ground_n is None:
            self.ground_n = np.zeros((self.H, self.W, 4), np.uint8); self.ground_n[:] = (128, 128, 255, 1)
        self.ground_n[ya:yb, xa:xb][on] = d.normal[ya - y0:yb - y0, xa - x0:xb - x0][on]
        return d

    # ---- props from the forge
    def model(self, key, build, x, y, box='foot', layer=0, kind=None, data=None, frames=None, seed=0, shadow=True,
              lights=True, grow_box=0, names=None, still=False):
        """Place a forge model with its origin at map (x, y). build is a Model or f(frame) -> Model.
        box: 'foot' = solid where it stands, None = not solid, or (x0, y0, x1, y1) pixels from the origin."""
        if key not in self.sprite_cache:
            n = frames or 1
            ds = [forge.draw(build(fi) if callable(build) else build, seed=seed, shadow=shadow and fi == 0) for fi in range(n)]
            left = max(d.ax for d in ds); top = max(d.ay for d in ds)
            right = max(d.rgba.shape[1] - d.ax for d in ds); bot = max(d.rgba.shape[0] - d.ay for d in ds)
            out_names = []
            for fi, d in enumerate(ds):
                cv = np.zeros((top + bot, left + right, 4), np.uint8)
                cv[top - d.ay:top - d.ay + d.rgba.shape[0], left - d.ax:left - d.ax + d.rgba.shape[1]] = d.rgba
                fname = names[fi] if names else key if not frames else f"{key}_{fi}"
                Image.fromarray(cv).save(f"{RES}/Objects/{fname}.png")
                out_names.append(fname)
                if fi == 0 or still:
                    nm = np.zeros((top + bot, left + right, 4), np.uint8); nm[:] = (128, 128, 255, 1)
                    nm[top - d.ay:top - d.ay + d.rgba.shape[0], left - d.ax:left - d.ax + d.rgba.shape[1]] = d.normal
                    Image.fromarray(nm).save(f"{RES}/Objects/{fname}_lin.png")
            d0 = ds[0]
            c = {"names": out_names, "w": left + right, "h": top + bot, "px": left, "py": top, "foot": d0.foot, "lights": d0.lights, "still": still}
            if d0.shade is not None:
                sh = np.zeros((*d0.shade.shape, 4), np.uint8); sh[d0.shade] = (8, 8, 24, 255)
                Image.fromarray(sh).save(f"{RES}/Objects/{out_names[0]}_sh.png")
                c.update({"sh": out_names[0] + "_sh", "shx": int(d0.sx), "shy": int(d0.sy)})
            self.sprite_cache[key] = c
        c = self.sprite_cache[key]
        o = {"s": c["names"][0], "x": int(x), "y": int(y), "px": c["px"], "py": c["py"], "w": c["w"], "h": c["h"], "layer": layer, "n": 1}
        if len(c["names"]) > 1 and not c.get("still"):
            o["frames"] = c["names"]
        if "sh" in c:
            o.update({"sh": c["sh"], "shx": c["shx"], "shy": c["shy"]})
        if box == 'foot' and c["foot"] is not None:
            f = c["foot"]
            o["box"] = [int(round(f[0])) - grow_box, int(round(f[1])) - grow_box, int(round(f[2])) + grow_box, min(0, int(round(f[3]))) + grow_box]
        elif box is not None and box != 'foot':
            o["box"] = [int(b) for b in box]
        if kind:
            o["kind"] = kind
        if data:
            o.update(data)
        self.objects.append(o)
        if lights:
            for (dx, dy, r, col, st, lz) in c["lights"]:
                self.lights.append({"x": int(x + dx), "y": int(y + dy), "r": r, "c": list(col), "i": st, "f": True, "tag": "model", "h": round(float(lz), 2)})
        return o

    def prop(self, key, draw_fn, x, y, box=None, layer=0, pad=24, size=(96, 96), anchor=None, kind=None, data=None, frames=None):
        """Draw a prop once (cached by key) on its own canvas, crop it, and place it with its
        base at map (x, y). box = (x0, y0, x1, y1) solid area relative to the base point."""
        if key not in self.sprite_cache:
            imgs = []
            for fi in range(frames or 1):
                cv = Canvas(size[0], size[1])
                ax, ay = anchor or (size[0] // 2, size[1] - pad)
                draw_fn(cv, ax, ay, fi)
                imgs.append((cv, ax, ay))
            # one crop for all frames so they line up
            union = np.zeros((size[1], size[0]), dtype=bool)
            for (cv, _, _) in imgs:
                union |= cv.a[:, :, 3] > 0
            ys, xs = np.nonzero(union)
            x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            names = []
            for fi, (cv, ax, ay) in enumerate(imgs):
                crop = cv.a[y0:y1, x0:x1]
                fname = f"{key}" if not frames else f"{key}_{fi}"
                path = f"{RES}/Objects/{fname}.png"
                os.makedirs(os.path.dirname(path), exist_ok=True)
                Image.fromarray(crop).save(path)
                names.append(fname)
            ax, ay = imgs[0][1], imgs[0][2]
            self.sprite_cache[key] = {"names": names, "w": int(x1 - x0), "h": int(y1 - y0),
                                      "px": int(ax - x0), "py": int(ay - y0)}
        s = self.sprite_cache[key]
        o = {"s": s["names"][0], "x": int(x), "y": int(y), "px": s["px"], "py": s["py"], "w": s["w"], "h": s["h"], "layer": layer}
        if len(s["names"]) > 1:
            o["frames"] = s["names"]
        if box:
            o["box"] = [int(b) for b in box]
        if kind:
            o["kind"] = kind
        if data:
            o.update({k: v for k, v in data.items()})
        self.objects.append(o)
        return o

    def stall(self, key, seed, x, y, town_module, layer=0):
        """A market stall as two props, so a seller standing behind the counter is drawn between them."""
        deep = int(round(town_module.STALL_DEEP * 16))
        self.model(f"{key}_back", town_module.stall_back(seed), x, y - deep, box=None, layer=layer)
        self.model(f"{key}_front", town_module.stall_front(seed), x, y, box=(-22, -deep - 2, 22, 0), layer=layer)

    def solid(self, x0, y0, x1, y1, layer=0, kind=None):
        self.boxes.append([int(x0), int(y0), int(x1), int(y1), layer, kind])

    def light(self, x, y, radius, color=(1.0, 0.62, 0.3), intensity=1.0, flicker=True, tag=None, h=1.0):
        """(x, y) is where the flame shows on the map; h is how high above the ground it burns."""
        self.lights.append({"x": int(x), "y": int(y), "r": radius, "c": list(color), "i": intensity, "f": flicker, "tag": tag, "h": h})

    def exit(self, x0, y0, x1, y1, to, spawn, need=None):
        """Walking into this rectangle takes Azar to map `to`, arriving at its spawn `spawn`."""
        m = {"kind": "exit", "x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0), "id": to, "text": spawn}
        if need:
            m["who"] = need
        self.markers.append(m)

    def spawn(self, name, x, y, face="down"):
        self.markers.append({"kind": "spawn", "x": int(x), "y": int(y), "who": name, "text": face})

    def enemy(self, kind, x, y, uid=None, once=False):
        m = {"kind": "enemy", "x": int(x), "y": int(y), "who": kind}
        if uid:
            m["id"] = uid
            if once:
                m["text"] = "once"
        self.markers.append(m)

    def marker(self, kind, x, y, **data):
        m = {"kind": kind, "x": int(x), "y": int(y)}
        m.update(data)
        self.markers.append(m)

    def save(self):
        os.makedirs(f"{RES}/Maps", exist_ok=True)
        self.ground.save(f"{RES}/Maps/{self.name}_ground.png")
        boxes = [{"x0": b[0], "y0": b[1], "x1": b[2], "y1": b[3], "layer": b[4], "kind": b[5] if len(b) > 5 else None} for b in self.boxes]
        objs = []
        for o in self.objects:
            o = dict(o)
            if "box" in o:
                b = o.pop("box")
                o["bx0"], o["by0"], o["bx1"], o["by1"] = b
                o["solid"] = True
            objs.append(o)
        surface = self.terrain.surface(SURF_CELL) if self.terrain is not None else surface_grid(self.ground)
        if self.ground_n is None:
            self.ground_n = normal_from_luma(self.ground.a)
        Image.fromarray(self.ground_n).save(f"{RES}/Maps/{self.name}_ground_lin.png")
        meta = {"name": self.name, "music": self.music, "w": self.W, "h": self.H, "ground": f"Maps/{self.name}_ground",
                "normal": f"Maps/{self.name}_ground_lin",
                "surface": surface, "cell": SURF_CELL,
                "objects": objs, "boxes": boxes, "lights": self.lights, "markers": self.markers}
        json.dump(meta, open(f"{RES}/Maps/{self.name}.json", "w"))
        print(f"map {self.name}: {self.W}x{self.H}px, {len(self.objects)} props, {len(self.sprite_cache)} sprites")
