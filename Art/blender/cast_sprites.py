"""Render the townsfolk and the goat into sprite sheets (same format as Azar's).
Usage: python3 cast_sprites.py [name ...] [test]"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from PIL import Image
import people
import goat
import enemies
import sprites

RES = "/srv/Wakefire/Assets/Wakefire/Resources/Sprites"
TMP = "/tmp/wfsprites/cast"

FRAMES = {
    'idle': [0, 15, 30, 45],
    'walk': [0, 4, 7, 10, 14, 18, 21, 24],
    'sleep': [0, 15, 30, 45],
    'sleepwalk': [0, 5, 10, 15, 20, 25, 30, 35],
    'knead': [0, 6, 12, 18],
    'talk': [0, 5, 10, 15, 20, 25],
    'lie': [0, 30],
    'lean': [0, 15, 30, 45],
    'cower': [0, 10, 20, 30],
    'shrug': [8], 'point': [6], 'sigh': [12, 26], 'itemget': [8], 'hurt': [2, 6],
    # goat
    'stare': [0, 30],
    'eat': [0, 10, 20, 30],
    'bleat': [0, 6, 14, 22],
    'butt': [0, 6, 9, 11, 14],
}
GOAT_FRAMES = {'idle': [0, 8, 16, 24, 32, 46], 'walk': [0, 3, 6, 9, 12, 15, 18, 21]}
ASLEEP = {'sleep', 'lie', 'lean', 'knead', 'sleepwalk'}
D, DL, DLU = ('down',), ('down', 'left'), ('down', 'left', 'up')
DIRS = {'down': 0, 'left': -90, 'up': 180}

PLAN = {
    'captain': (1.0, {'lean': DL, 'sleep': D, 'idle': DL, 'talk': DL}),
    'captain_child': (0.72, {'cower': D, 'idle': DLU, 'talk': DL, 'point': DL, 'itemget': D, 'walk': DLU}),
    'baker': (1.0, {'knead': D, 'sleep': D, 'idle': DL, 'talk': DL}),
    'potter': (1.0, {'sleep': D, 'idle': DL, 'talk': DL, 'shrug': D}),
    'oracle': (1.0, {'sleep': D, 'idle': DL, 'talk': DL, 'point': D}),
    'fisher': (1.0, {'sleep': D, 'lie': D, 'idle': DL, 'talk': DL}),
    'priest': (1.0, {'sleep': D, 'lie': D, 'idle': DL, 'talk': DL, 'walk': DLU, 'sigh': D}),
    'sleeper_a': (1.0, {'lie': D, 'sleep': D, 'sleepwalk': DLU, 'idle': D, 'talk': D}),
    'sleeper_b': (1.0, {'lie': D, 'sleep': D, 'sleepwalk': DLU, 'idle': D, 'talk': D}),
    'sleeper_c': (1.0, {'lie': D, 'sleep': D, 'sleepwalk': DLU, 'idle': D, 'talk': D}),
    'goat': (1.0, {'idle': DLU, 'stare': ('left',), 'walk': DLU, 'eat': DL, 'bleat': DL, 'butt': ('left',)}),
    'crab': (1.0, {'idle': D, 'walk': D, 'attack': D, 'hurt': D}),
    'jackal': (1.0, {'idle': DLU, 'walk': DLU, 'run': DLU, 'crouch': DLU, 'lunge': DLU, 'hurt': DLU}),
    'moth': (1.0, {'fly': D}),
    'sentinel': (1.0, {'idle': DLU, 'walk': DLU, 'hurt': DLU}),
    'bull': (1.0, {'idle': DLU, 'walk': DLU, 'charge': DLU, 'stun': DLU, 'shoot': DLU, 'hurt': DLU, 'death': D}),
    'god': (2.4, {'lie': D, 'sleep': D}),
}
SIZE = {'bull': 112, 'god': 128}
OVERRIDE = {
    'goat': {'idle': [0, 8, 16, 24, 32, 46], 'walk': [0, 3, 6, 9, 12, 15, 18, 21]},
    'crab': {'idle': [0, 10, 20, 30], 'walk': [0, 3, 6, 9], 'attack': [0, 3, 5, 8, 11], 'hurt': [2, 5]},
    'jackal': {'idle': [0, 10, 20, 30], 'walk': [0, 5, 10, 15], 'run': [0, 3, 6, 9], 'crouch': [8], 'lunge': [0, 6], 'hurt': [2]},
    'moth': {'fly': [0, 2, 4, 6]},
    'bull': {'idle': [0, 10, 20, 30], 'walk': [0, 3, 6, 9, 12, 15, 18, 21], 'charge': [0, 2, 3, 5, 6, 8, 9, 11], 'stun': [0, 20],
             'shoot': [0, 6, 10, 14], 'hurt': [2], 'death': [0, 8, 16, 28, 40]},
    'god': {'lie': [0, 30], 'sleep': [0, 30]},
}
BUILD = {
    'goat': (goat.build, 10.0),
    'crab': (enemies.build_crab, 6.0),
    'jackal': (enemies.build_jackal, 10.0),
    'moth': (enemies.build_moth, 12.0),
    'bull': (enemies.build_bull, 20.0),
}


def render(name, test=False):
    scale, plan = PLAN[name]
    if name in BUILD:
        fn, tz = BUILD[name]
        ao, obs = fn()
        target = (0, 0, tz)
    elif name == 'sentinel':
        ao, obs = people.build(enemies.SENTINEL, scale=scale)
        target = (0, 0, 15.0)
    elif name == 'god':
        ao, obs = people.build(enemies.GOD, scale=scale)
        target = (0, 0, 20.0)
    else:
        ao, obs = people.build(people.CAST[name], scale=scale)
        target = (0, 0, 15.0)
    meshes = list(obs.values())
    size = SIZE.get(name, 48)
    ppm = {'bull': 2.1, 'jackal': 1.3, 'crab': 1.25}.get(name, 1.0)
    rig = sprites.SpriteRig(ao, meshes, size=size, target=target, px_per_m=ppm, elev=14.0 if name != 'god' else 30.0, scales={}, dist=60.0 if size <= 48 else 120.0)
    os.makedirs(TMP, exist_ok=True)
    out = {}
    for anim, dirs in plan.items():
        fl = OVERRIDE.get(name, {}).get(anim) or FRAMES[anim]
        if test:
            fl = fl[:2]
        # eyes: shut when asleep, open (or wide) when awake
        if 'closed' in obs:
            obs['closed'].hide_render = anim not in ASLEEP
            obs['open'].hide_render = anim in ASLEEP
        for dname in dirs:
            imgs = []
            for i, f in enumerate(fl):
                pc = f"{TMP}/{name}_{anim}_{dname}_{i}_c.png"
                pi = f"{TMP}/{name}_{anim}_{dname}_{i}_i.png"
                rig.render(anim, f, DIRS[dname], pc, pi)
                imgs.append(sprites.outline(pc, pi))
            out[(anim, dname)] = imgs
    return out, rig.pivot()


def sheet(out, pivot, S=48):
    rows = list(out.keys())
    ncol = max(len(v) for v in out.values())
    img = Image.new('RGBA', (ncol * S, len(rows) * S), (0, 0, 0, 0))
    meta = {"size": S, "pivot": [pivot[0], pivot[1]], "anims": []}
    for r, key in enumerate(rows):
        for c, im in enumerate(out[key]):
            img.paste(Image.fromarray(im), (c * S, r * S))
        meta["anims"].append({"name": key[0], "dir": key[1], "row": r, "frames": len(out[key])})
    return img, meta


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != 'test']
    test = 'test' in sys.argv
    names = args or list(PLAN.keys())
    for n in names:
        out, pivot = render(n, test)
        img, meta = sheet(out, pivot, SIZE.get(n, 48))
        if test:
            img.save(f"/tmp/wfsprites/{n}_test.png")
        else:
            img.save(f"{RES}/{n}.png")
            json.dump(meta, open(f"{RES}/{n}.json", "w"), indent=1)
        print(n, img.size, pivot, flush=True)
