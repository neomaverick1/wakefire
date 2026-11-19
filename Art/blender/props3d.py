"""Statues and big set pieces modelled in pixel units and rendered through the sprite pipeline,
so they share Azar's light, bands and outlines.  Usage: python3 props3d.py [name ...] [test]"""
import os
import sys
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from PIL import Image
from mathutils import Vector, Matrix, Euler
import wf
from wf import Builder, hexc, METAL, GLOW, D2R
import sprites

OBJ = "/srv/Wakefire/Art/sprites/props"
TMP = "/tmp/wfsprites/props"

LIME = hexc('#cdbda4')
LIME_D = hexc('#9e8e78')
LIME_L = hexc('#e6d8c0')
GOLD = hexc('#e2a64e', METAL)
GOLD_L = hexc('#ffd88a', METAL)
LAPIS = hexc('#3250b4')
EYE = hexc('#1a1016')


def lamassu(b: Builder, side=1):
    """Winged bull with a crowned, bearded man's head: the gate guardian of Ashkel."""
    # plinth
    b.box((0, 5, 2.0), (15, 26, 4.0), LIME_D, 'root')
    b.box((0, 5, 4.6), (13.5, 24.5, 1.2), LIME, 'root')
    # body, chest and haunches
    b.ellipsoid((0, 7, 15.5), (6.4, 10.0, 6.0), 14, 9, LIME, True, 'root')
    b.ellipsoid((0, -2.5, 17.0), (6.6, 4.6, 6.2), 14, 9, LIME, True, 'root')
    for s in (-1, 1):
        # front legs, squared like carved pillars, with hooves
        b.box((s * 3.6, -3.4, 9.6), (3.6, 3.6, 8.6), LIME, 'root', taper=0.9)
        b.box((s * 3.6, -3.9, 6.0), (4.2, 4.4, 1.6), LIME_D, 'root')
        # rear legs further back
        b.box((s * 3.8, 14.0, 9.6), (3.4, 3.4, 8.6), LIME_D, 'root', taper=0.9)
        # great wings sweeping up and back from the shoulders, carved in feather rows
        for k in range(5):
            t = k / 4.0
            p0 = Vector((s * (5.6 + t * 2.2), 0.5 + t * 4.5, 21.5 + t * 1.5))
            p1 = Vector((s * (9.0 + t * 4.4), 3.0 + t * 7.0, 33.5 - t * 4.0))
            col = LIME_L if k % 2 == 0 else LIME
            b.limb(p0, p1, [1.5, 1.7, 1.1], 6, col, False, 'root', squash=0.55)
        b.limb(Vector((s * 6.0, 0.0, 22.5)), Vector((s * 8.6, 1.4, 35.5)), [1.4, 1.6, 0.9], 6, GOLD, False, 'root', squash=0.5)
    # the man's head: heavy brows, almond eyes, a tall horned crown
    head0 = len(b.v)
    b.ellipsoid((0, -5.6, 26.8), (4.6, 3.8, 5.0), 12, 8, LIME, True, 'root')
    for s in (-1, 1):
        b.box((s * 1.8, -9.2, 27.6), (1.6, 0.8, 1.0), EYE, 'root')
        b.box((s * 1.9, -9.3, 28.8), (2.2, 0.6, 0.6), LIME_D, 'root')
        b.ellipsoid((s * 4.6, -5.0, 27.0), (0.8, 1.2, 1.6), 6, 4, LIME_D, True, 'root')
    b.box((0, -9.6, 26.6), (1.2, 1.2, 2.0), LIME_D, 'root', taper=0.6)
    # beard in braided rows
    for i, z in enumerate((23.6, 22.0, 20.4, 18.8)):
        b.box((0, -8.6 + i * 0.25, z), (7.4 - i * 0.8, 2.8, 1.6), LIME_L if i % 2 == 0 else LIME_D, 'root')
    # crown: a cylinder with three bands of horns and a feathered rim
    b.loft([((0, -5.2, 29.6), 4.1, 3.9), ((0, -5.2, 36.0), 4.3, 4.1)], 14, LIME, False, 'root', True, True)
    for z in (30.6, 32.6, 34.6):
        b.loft([((0, -5.2, z), 4.45, 4.25), ((0, -5.2, z + 0.7), 4.45, 4.25)], 14, GOLD, False, 'root', False, False)
    b.loft([((0, -5.2, 36.0), 4.6, 4.4), ((0, -5.2, 36.8), 4.6, 4.4)], 14, GOLD_L, False, 'root', True, True)
    if side:
        # turn the head (everything built since head0) to look out of the picture
        R = Matrix.Rotation(side * 90 * D2R, 4, 'Z')
        c = Vector((0, -5.6, 0))
        for i in range(head0, len(b.v)):
            b.v[i] = (R @ (b.v[i] - c)) + c + Vector((0, -2.0, 0))


def build(name):
    wf.reset()
    ao = wf.armature("Rig", [("root", (0, 0, 0), (0, 0, 2), None)])
    b = Builder()
    if name == 'lamassu':
        lamassu(b, side=1)
    mo = b.mesh_object("Body")
    wf.bind(mo, ao)
    return ao, [mo]


SPEC = {
    # name: (canvas size, target z, elevation)
    'lamassu': (64, 20.0, 24.0),
}
YAW = {'lamassu': -90}


def render(name):
    size, tz, elev = SPEC[name]
    ao, meshes = build(name)
    ao.animation_data_create()
    rig = sprites.SpriteRig(ao, meshes, size=size, target=(0, 0, tz), px_per_m=1.0, elev=elev, scales={}, dist=90.0)
    os.makedirs(TMP, exist_ok=True)
    pc, pi = f"{TMP}/{name}_c.png", f"{TMP}/{name}_i.png"
    rig.render(None, 0, YAW.get(name, 0), pc, pi)
    img = sprites.outline(pc, pi)
    return img, rig.pivot()


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if a != 'test'] or list(SPEC.keys())
    for n in names:
        img, piv = render(n)
        # crop to content, remember where the base sits
        a = img[:, :, 3] > 0
        ys, xs = np.where(a)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        out = Image.fromarray(img[y0:y1, x0:x1])
        out.save(f"{OBJ}/{n}.png" if 'test' not in sys.argv else f"{TMP}/{n}_crop.png")
        if 'test' not in sys.argv:
            import json
            json.dump({"base": [int(round(piv[0] - x0)), int(round(piv[1] - y0))]}, open(f"{OBJ}/{n}.json", "w"))
        print(n, out.size, "base at", round(piv[0] - x0, 1), round(piv[1] - y0, 1))
