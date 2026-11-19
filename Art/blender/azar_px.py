"""AZAR built for the sprite: modelled directly in pixel units (1 unit = 1 screen pixel),
with game-sprite proportions (head about a third of his height, broad shoulders, chunky
hands and boots) so every feature lands on readable pixels. Same rig names as azar.py, so
the same animations drive it. Faces -Y, Z up."""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from wf import Builder, hexc, METAL, GLOW, D2R
from mathutils import Vector, Matrix
import azar

SKIN = hexc('#e0a77a')
SKIN_D = hexc('#b67650')
STUBBLE = hexc('#c28660')
HAIR = hexc('#2a1d28')
HAIR_L = hexc('#4a3346')
EYE = hexc('#1a1016')
BROW = hexc('#2a1d28')
BAND = hexc('#e03a3a')
TUNIC = hexc('#b83a40')
TUNIC_D = hexc('#86232f')
BRONZE = hexc('#d89a46', METAL)
BRONZE_D = hexc('#a2672a', METAL)
BRONZE_L = hexc('#ffd47a', METAL)
LEATHER = hexc('#7a4a2a')
BOOT = hexc('#5a3420')
CLOAK = hexc('#3e4ca6')
CLOAK_D = hexc('#2a3378')
CLOAK_IN = hexc('#26275a')
FLAME = hexc('#ffb347', GLOW)
FLAME_CORE = hexc('#fff3c0', GLOW)
WRAP = hexc('#3a2418')

# rig in pixels: feet at z=0, head top ~31
BONES = [
    ("root", (0, 0, 0), (0, 0, 2), None),
    ("hips", (0, 0, 12), (0, 0, 14), "root"),
    ("spine", (0, 0, 14), (0, 0, 17), "hips"),
    ("chest", (0, 0, 17), (0, 0, 20), "spine"),
    ("neck", (0, 0, 20), (0, 0, 21), "chest"),
    ("head", (0, 0, 21), (0, 0, 31), "neck"),
    ("band1", (0, 5.0, 27.5), (0, 7.5, 25.5), "head"),
    ("band2", (0, 7.5, 25.5), (0, 9.0, 22.5), "band1"),
    ("cape1", (0, 3.6, 20), (0, 5.0, 13), "chest"),
    ("cape2", (0, 5.0, 13), (0, 6.2, 5), "cape1"),
    ("upperarm.R", (-7.2, 0, 19), (-7.8, 0, 15), "chest"),
    ("forearm.R", (-7.8, 0, 15), (-8.0, -0.5, 11), "upperarm.R"),
    ("hand.R", (-8.0, -0.5, 11), (-8.0, -0.8, 9), "forearm.R"),
    ("weapon", (-8.0, -0.9, 9.6), (-8.0, -6.0, 6.5), "hand.R"),
    ("upperarm.L", (7.2, 0, 19), (7.8, 0, 15), "chest"),
    ("forearm.L", (7.8, 0, 15), (8.0, -0.5, 11), "upperarm.L"),
    ("hand.L", (8.0, -0.5, 11), (8.0, -0.8, 9), "forearm.L"),
    ("lantern", (8.0, -0.9, 9.4), (8.0, -0.9, 5.5), "hand.L"),
    ("shield", (9.3, -0.2, 13), (9.3, -2.2, 13), "forearm.L"),
    ("thigh.R", (-2.8, 0, 12), (-2.9, 0, 7), "hips"),
    ("shin.R", (-2.9, 0, 7), (-2.9, 0.3, 2.2), "thigh.R"),
    ("foot.R", (-2.9, 0.3, 2.2), (-2.9, -2.5, 0.8), "shin.R"),
    ("thigh.L", (2.8, 0, 12), (2.9, 0, 7), "hips"),
    ("shin.L", (2.9, 0, 7), (2.9, 0.3, 2.2), "thigh.L"),
    ("foot.L", (2.9, 0.3, 2.2), (2.9, -2.5, 0.8), "shin.L"),
]


def body(b: Builder):
    # head: a big readable block with a stern, tired face
    b.ellipsoid((0, -0.2, 25.6), (5.4, 5.0, 5.4), 14, 9, SKIN, True, 'head')
    b.ellipsoid((0, -1.7, 21.7), (3.7, 3.3, 1.6), 12, 6, STUBBLE, True, 'head')
    for s in (-1, 1):
        b.box((s * 2.0, -4.95, 24.9), (0.9, 0.8, 1.4), EYE, 'head')              # eyes: narrow, tired
        b.box((s * 2.2, -5.0, 26.1), (1.8, 0.7, 0.35), BROW, 'head', rot=(0, s * 12, 0))  # brows
        b.ellipsoid((s * 5.3, 0.0, 25.4), (0.9, 1.3, 1.6), 6, 4, SKIN_D, True, 'head')
    b.box((0, -5.5, 24.8), (1.1, 1.2, 1.8), SKIN_D, 'head', taper=0.6)          # nose
    b.box((0, -4.7, 22.5), (2.0, 0.6, 0.4), hexc('#6a2e2a'), 'head')            # mouth, set
    # hair: a dark mass with swept-back spikes; open at the face
    h0 = len(b.f)
    b.ellipsoid((0, 0.9, 28.0), (5.85, 6.0, 3.7), 14, 9, HAIR, True, 'head')
    keep = []
    for i, f in enumerate(b.f):
        if i < h0:
            keep.append(f)
            continue
        c = sum((b.v[k] for k in f[0]), Vector()) / len(f[0])
        if c.y < -1.4 and c.z < 28.9:
            continue
        keep.append(f)
    b.f = keep
    for (p, r, sz, col) in [((1.8, 3.8, 30.0), (-66, 12, 0), 4.0, HAIR), ((-1.8, 3.8, 30.0), (-66, -12, 0), 4.0, HAIR),
                            ((0, 5.2, 29.0), (-92, 0, 0), 4.6, HAIR), ((3.6, 3.4, 28.4), (-80, 34, 0), 3.4, HAIR),
                            ((-3.6, 3.4, 28.4), (-80, -34, 0), 3.4, HAIR), ((0, 5.0, 26.6), (-112, 0, 0), 3.4, HAIR),
                            ((1.2, -1.6, 30.6), (58, 10, 0), 2.4, HAIR_L), ((-1.6, -1.0, 30.8), (52, -16, 0), 2.2, HAIR_L)]:
        b.box(p, (2.6, 2.2, sz), col, 'head', rot=r, taper=0.12)
    # red headband, knotted at the back with two tails
    b.loft([((0, 0.4, 27.3), 5.7, 5.55), ((0, 0.4, 28.2), 5.7, 5.55)], 16, BAND, True, 'head', False, False)
    b.box((0, 5.6, 27.8), (1.8, 1.4, 1.6), BAND, 'head')
    b.limb((0, 5.6, 27.6), (0, 7.5, 25.5), [0.85, 0.75], 4, BAND, False, 'band1', squash=0.4)
    b.limb((0, 7.5, 25.5), (0, 9.0, 22.5), [0.75, 0.4], 4, BAND, False, 'band2', squash=0.4)

    # torso: crimson tunic under a bronze scale vest, leather belt, kilt
    b.loft([((0, 0, 13.4), 5.4, 3.8), ((0, 0, 15.5), 5.6, 3.9), ((0, 0, 17.0), 5.9, 4.0)], 14, TUNIC, True, 'spine')
    b.loft([((0, 0, 17.0), 5.9, 4.0), ((0, 0, 19.0), 6.6, 4.1), ((0, 0, 20.4), 5.0, 3.6), ((0, 0, 21.0), 2.8, 2.4)], 14, TUNIC, True, 'chest')
    for (z0, z1, col) in ((15.2, 16.4, BRONZE_D), (16.4, 17.6, BRONZE), (17.6, 18.8, BRONZE_D), (18.8, 19.8, BRONZE)):
        grp = 'chest' if z0 >= 17 else 'spine'
        w0 = 5.75 + (z0 - 15.2) * 0.22
        w1 = 5.75 + (z1 - 15.2) * 0.22
        b.loft([((0, 0.05, z0), w0, 4.05), ((0, 0.05, z1), w1, 4.1)], 14, col, False, grp, False, False)
    b.loft([((0, 0, 13.0), 5.6, 3.95), ((0, 0, 14.4), 5.6, 3.95)], 14, LEATHER, False, 'hips', False, False)
    b.box((0, -4.0, 13.7), (1.9, 0.7, 1.6), BRONZE_L, 'hips')
    b.loft([((0, 0, 13.4), 5.4, 3.8), ((0, 0, 12.0), 5.8, 4.1), ((0, 0.1, 10.0), 6.4, 4.6), ((0, 0.2, 8.4), 6.8, 5.0)], 14, TUNIC, True, 'hips', False, False)
    b.loft([((0, 0.2, 8.9), 6.75, 4.95), ((0, 0.2, 8.4), 6.8, 5.0)], 14, TUNIC_D, False, 'hips', False, False)
    b.box((0, -4.6, 10.6), (3.4, 0.8, 4.6), LEATHER, 'hips', rot=(-8, 0, 0))
    for z in (12.0, 10.8, 9.6):
        b.box((0, -5.05, z), (1.0, 0.5, 0.8), BRONZE_L, 'hips')

    for s, side in ((-1, 'R'), (1, 'L')):
        sh, el, wr = Vector((s * 7.2, 0, 19)), Vector((s * 7.8, 0, 15)), Vector((s * 8.0, -0.5, 11))
        b.box((s * 7.0, 0.0, 19.6), (3.6, 4.4, 2.2), BRONZE, 'upperarm.' + side, rot=(0, s * 18, 0))   # shoulder plate
        b.limb(sh, el, [1.9, 1.8, 1.6], 8, SKIN, True, 'upperarm.' + side)
        b.limb(el, wr, [1.7, 1.6, 1.4], 8, SKIN, True, 'forearm.' + side)
        b.limb(el.lerp(wr, 0.15), el.lerp(wr, 0.85), [1.95, 1.9, 1.7], 8, BRONZE, False, 'forearm.' + side)
        b.ellipsoid((s * 8.0, -0.6, 9.9), (1.9, 2.0, 2.1), 8, 5, SKIN, True, 'hand.' + side)
        hip, knee, ank = Vector((s * 2.8, 0, 12)), Vector((s * 2.9, 0, 7)), Vector((s * 2.9, 0.3, 2.2))
        b.limb(hip, knee, [2.3, 2.2, 2.0], 8, SKIN, True, 'thigh.' + side)
        b.limb(knee, ank, [2.0, 1.9, 1.6], 8, SKIN, True, 'shin.' + side)
        b.limb(knee.lerp(ank, 0.05), knee.lerp(ank, 0.85), [2.25, 2.15, 1.9], 8, BRONZE, False, 'shin.' + side)
        b.box((s * 2.95, -1.0, 1.2), (3.8, 6.4, 2.6), BOOT, 'foot.' + side, taper=0.85)
        b.box((s * 2.9, 0.4, 2.6), (3.4, 3.4, 2.4), BOOT, 'foot.' + side)

    # cloak: deep blue mantle over the shoulders, long cape behind
    b.loft([((0, 0.6, 21.6), 3.6, 3.2), ((0, 0.6, 20.8), 7.2, 4.8), ((0, 0.8, 19.0), 9.0, 5.6), ((0, 1.0, 17.6), 9.3, 5.9)],
           16, CLOAK, True, 'chest', arc=(-148, 148), double=True, color_in=CLOAK_IN)
    b.ellipsoid((0, -4.3, 20.6), (1.0, 0.7, 1.0), 6, 4, BRONZE_L, False, 'chest')
    b.loft([((0, 1.4, 19.6), 6.6, 4.2), ((0, 1.8, 16.4), 7.6, 5.2), ((0, 2.0, 13.0), 8.0, 5.6)], 14, CLOAK, True, 'cape1',
           arc=(108, 252), double=True, color_in=CLOAK_IN)
    b.loft([((0, 2.0, 13.0), 8.0, 5.6), ((0, 2.3, 9.0), 8.6, 6.1), ((0, 2.6, 5.4), 9.0, 6.6)], 14, CLOAK_D, True, 'cape2',
           arc=(108, 252), double=True, color_in=CLOAK_IN)


def khopesh(b: Builder):
    head = Vector((-8.0, -0.9, 9.6))
    tail = Vector((-8.0, -6.0, 6.5))
    u = (tail - head).normalized()
    w = Vector((1, 0, 0))
    v = w.cross(u).normalized()
    if v.z < 0:
        v = -v
    M = Matrix((u, v, w)).transposed().to_4x4()
    M.translation = head
    b.limb(head - u * 0.8, head + u * 2.2, [0.8, 0.8], 6, WRAP, False, 'weapon')
    b.ellipsoid(head - u * 1.1, (1.0, 1.0, 1.0), 6, 4, BRONZE_L, False, 'weapon')
    b.box(head + u * 2.3, (1.6, 1.6, 1.6), BRONZE_D, 'weapon')
    k = 21.0  # blade length scale
    pts = [(0.11, 0.022), (0.27, 0.022), (0.32, 0.055), (0.38, 0.095), (0.45, 0.115), (0.52, 0.105), (0.57, 0.072),
           (0.59, 0.022), (0.578, -0.03), (0.545, -0.075), (0.53, -0.03), (0.522, 0.005), (0.50, 0.038), (0.46, 0.054),
           (0.40, 0.05), (0.35, 0.025), (0.315, -0.018), (0.27, -0.022), (0.11, -0.022)]
    pts = [(p[0] * k, p[1] * k) for p in pts]
    b.prism(pts, 0.8, M, BRONZE, 'weapon', False, color_edge=BRONZE_L)


def lantern(b: Builder):
    x, y = 8.0, -0.9
    b.limb((x, y, 9.4), (x, y, 8.4), [0.35, 0.35], 4, BRONZE_D, False, 'lantern')
    b.loft([((x, y, 8.4), 0.7, 0.7), ((x, y, 7.6), 2.3, 2.3)], 8, BRONZE, False, 'lantern', True, True)
    b.loft([((x, y, 7.6), 1.9, 1.9), ((x, y, 4.8), 1.9, 1.9)], 8, FLAME, True, 'lantern', True, True)
    b.ellipsoid((x, y, 6.1), (1.0, 1.0, 1.2), 6, 4, FLAME_CORE, True, 'lantern')
    for kk in range(4):
        a = (45 + 90 * kk) * D2R
        b.box((x + math.sin(a) * 1.95, y - math.cos(a) * 1.95, 6.2), (0.5, 0.5, 2.8), BRONZE_D, 'lantern')
    b.loft([((x, y, 4.8), 2.3, 2.3), ((x, y, 4.1), 1.7, 1.7)], 8, BRONZE, False, 'lantern', True, True)


def shield(b: Builder):
    c = Vector((9.6, -0.6, 13))
    M = Matrix.Translation(c) @ __import__('mathutils').Euler((0, 90 * D2R, 0)).to_matrix().to_4x4()
    b.loft([((0, 0, -0.5), 5.4, 5.4), ((0, 0, 0.0), 5.6, 5.6), ((0, 0, 0.8), 4.0, 4.0), ((0, 0, 1.1), 2.0, 2.0)], 16,
           BRONZE_L, False, 'shield', True, True, xf=M)


LOC_SCALE = 15.0  # animation hip offsets were authored in metres for a 1.8 m body


def build():
    wf.reset()
    ao = wf.armature("Azar", BONES)
    b = Builder()
    body(b)
    khopesh(b)
    lantern(b)
    mo = b.mesh_object("AzarBody")
    wf.bind(mo, ao)
    sb = Builder()
    shield(sb)
    so = sb.mesh_object("AzarShield")
    wf.bind(so, ao)
    anims = azar.anims()
    for a in anims:
        a.keys = [(f, r, {bn: (v[0] * LOC_SCALE, v[1] * LOC_SCALE, v[2] * LOC_SCALE) for bn, v in l.items()}) for (f, r, l) in a.keys]
    wf.apply_anims(ao, anims)
    return ao
