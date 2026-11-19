"""Render Azar's sprite sheet. 'test' renders a few animations into an upscaled, labelled sheet."""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
import azar
import azar_px
import sprites

OUT_DIR = "/srv/Wakefire/Art/sprites/azar"
SHEET = "/srv/Wakefire/Assets/Wakefire/Resources/Sprites/azar.png"
META = "/srv/Wakefire/Assets/Wakefire/Resources/Sprites/azar.json"

# frames to keep from each 30 fps animation, chosen for the strongest poses
FRAMES = {
    'idle': [0, 15, 30, 45],
    'run': [0, 2, 4, 7, 9, 11, 13, 16],
    'attack1': [2, 3, 5, 7, 9, 12],
    'attack2': [1, 2, 4, 5, 7, 10],
    'attack3': [2, 4, 6, 7, 9, 12, 16],
    'roll': [1, 2, 4, 5, 7, 8, 10, 11, 13, 15],
    'hurt': [2, 6],
    'death': [4, 8, 14, 24, 30, 34, 40, 45],
    'nod': [3, 5, 9],
    'wake': [0, 3, 4, 8],
    'use': [3, 5, 12],
    'itemget': [8],
    'push': [0, 4, 8, 12, 16, 20],
    'block': [4],
    'doze': [6, 12, 18, 24, 30, 33, 36, 38, 44],
    'yawn': [6, 14, 28, 40, 48, 52, 58, 66],
    'shrug': [8],
    'point': [6],
    'sigh': [12, 26],
    'idle_nod': [0, 8, 16, 20, 26],
}
DIRS = {'down': 0, 'left': -90, 'up': 180}
SCALES = {'head': 1.55, 'hand.L': 1.2, 'hand.R': 1.2, 'weapon': 1.25, 'lantern': 1.2}


def main(test=False):
    ao = azar_px.build()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    shield = bpy.data.objects.get("AzarShield")
    if shield:
        shield.hide_render = True
        meshes = [m for m in meshes if m != shield]
    rig = sprites.SpriteRig(ao, meshes, size=48, target=(0, 0, 15.0), px_per_m=1.0, elev=14.0, scales={}, dist=60.0)
    frames = FRAMES
    dirs = DIRS
    if test:
        frames = {'idle': [0], 'run': [0, 4, 9, 13], 'attack1': [3, 5, 7]}
    tmp = "/tmp/wfsprites"
    os.makedirs(tmp, exist_ok=True)
    out = {}
    for anim, fl in frames.items():
        for dname, yaw in dirs.items():
            imgs = []
            for i, f in enumerate(fl):
                pc = f"{tmp}/{anim}_{dname}_{i}_c.png"
                pi = f"{tmp}/{anim}_{dname}_{i}_i.png"
                rig.render(anim, f, yaw, pc, pi)
                imgs.append(sprites.outline(pc, pi))
            out[(anim, dname)] = imgs
    pivot = rig.pivot()
    return out, pivot


def write_sheet(out, pivot, label=None, scale=1):
    from PIL import Image, ImageDraw
    rows = list(out.keys())
    ncol = max(len(v) for v in out.values())
    S = 48
    sheet = Image.new('RGBA', (ncol * S, len(rows) * S), (0, 0, 0, 0))
    meta = {"size": S, "pivot": [pivot[0], pivot[1]], "anims": []}
    for r, key in enumerate(rows):
        for c, img in enumerate(out[key]):
            sheet.paste(Image.fromarray(img), (c * S, r * S))
        meta["anims"].append({"name": key[0], "dir": key[1], "row": r, "frames": len(out[key])})
    if label:
        bg = Image.new('RGBA', sheet.size, (52, 74, 60, 255))
        bg.alpha_composite(sheet)
        big = bg.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
        canvas = Image.new('RGBA', (big.width, big.height + 40), (20, 16, 24, 255))
        canvas.paste(big, (0, 40))
        d = ImageDraw.Draw(canvas)
        d.text((10, 12), label, fill=(255, 220, 120, 255))
        return canvas, meta
    return sheet, meta


if __name__ == "__main__":
    test = "test" in sys.argv
    out, pivot = main(test)
    if test:
        img, meta = write_sheet(out, pivot, "INTERNAL TEST - sprite pipeline, not final art", scale=4)
        img.save("/tmp/wfsprites/test_sheet.png")
        print("test sheet saved", img.size, pivot)
    else:
        os.makedirs(os.path.dirname(SHEET), exist_ok=True)
        img, meta = write_sheet(out, pivot)
        img.save(SHEET)
        json.dump(meta, open(META, "w"), indent=1)
        print("sheet saved", img.size)
