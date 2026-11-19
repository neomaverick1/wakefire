"""Map building: a baked ground layer plus separate prop sprites (sorted by their base, so the
hero walks behind trees and in front of houses), collision boxes, lights and game markers,
exported for Unity as PNGs and one JSON file per map."""
import os
import json
import numpy as np
from PIL import Image
from px import Canvas, R

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

    def solid(self, x0, y0, x1, y1, layer=0, kind=None):
        self.boxes.append([int(x0), int(y0), int(x1), int(y1), layer, kind])

    def light(self, x, y, radius, color=(1.0, 0.62, 0.3), intensity=1.0, flicker=True, tag=None):
        self.lights.append({"x": int(x), "y": int(y), "r": radius, "c": list(color), "i": intensity, "f": flicker, "tag": tag})

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
        surface = surface_grid(self.ground)
        meta = {"name": self.name, "music": self.music, "w": self.W, "h": self.H, "ground": f"Maps/{self.name}_ground",
                "surface": surface, "cell": SURF_CELL,
                "objects": objs, "boxes": boxes, "lights": self.lights, "markers": self.markers}
        json.dump(meta, open(f"{RES}/Maps/{self.name}.json", "w"))
        print(f"map {self.name}: {self.W}x{self.H}px, {len(self.objects)} props, {len(self.sprite_cache)} sprites")
