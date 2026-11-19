"""The things that hunt Azar, in pixel units like everyone else: a brine crab, a jackal, a
moth-shade from the dream, and a bronze sentinel (a person-rig statue that walks)."""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from wf import Builder, Anim, hexc, METAL, GLOW
from mathutils import Vector
import people
import azar_px

# ------------------------------------------------------------------ brine crab
SHELL = hexc('#c2503a')
SHELL_D = hexc('#86302a')
SHELL_L = hexc('#e88a5a')
CLAW = hexc('#d8664a')
BELLY = hexc('#e8c8a0')
CEYE = hexc('#120c10')

CRAB_BONES = [
    ("root", (0, 0, 0), (0, 0, 2), None),
    ("body", (0, 0, 5), (0, -1, 5), "root"),
    ("claw.L", (5.5, -3, 6), (8.5, -7, 7), "body"),
    ("pincer.L", (8.5, -7, 7), (8.5, -10, 7.5), "claw.L"),
    ("claw.R", (-5.5, -3, 6), (-8.5, -7, 7), "body"),
    ("pincer.R", (-8.5, -7, 7), (-8.5, -10, 7.5), "claw.R"),
] + [(f"leg{i}.{s}", (sx * 5.0, -1.5 + i * 2.2, 4.5), (sx * 10.0, -1.5 + i * 2.6, 0.5), "body")
     for i in range(3) for (s, sx) in (("L", 1), ("R", -1))]


def crab(b: Builder):
    b.ellipsoid((0, 0.5, 5.2), (7.0, 5.4, 3.4), 14, 8, SHELL, True, 'body')
    b.ellipsoid((0, 0.5, 7.4), (5.0, 3.8, 1.5), 12, 6, SHELL_L, True, 'body')
    b.ellipsoid((0, -1.5, 3.4), (5.5, 3.0, 1.4), 12, 6, BELLY, True, 'body')
    for s in (-1, 1):
        b.limb((s * 2.0, -3.6, 7.0), (s * 2.4, -4.6, 10.0), [0.5, 0.45], 5, SHELL_D, False, 'body')
        b.ellipsoid((s * 2.4, -4.7, 10.4), (0.9, 0.9, 0.9), 6, 4, CEYE, True, 'body')
        side = 'L' if s > 0 else 'R'
        b.limb((s * 5.5, -3, 6), (s * 8.5, -7, 7), [1.2, 1.1], 6, CLAW, True, 'claw.' + side)
        b.ellipsoid((s * 8.6, -8.4, 7.3), (2.2, 2.6, 1.8), 8, 5, CLAW, True, 'pincer.' + side)
        b.box((s * 9.5, -10.6, 7.6), (1.0, 2.4, 1.0), SHELL_L, 'pincer.' + side)
        b.box((s * 7.8, -10.4, 7.2), (0.9, 2.0, 0.9), SHELL_D, 'pincer.' + side)
        for i in range(3):
            p0 = Vector((s * 5.0, -1.5 + i * 2.2, 4.5))
            mid = Vector((s * 8.6, -1.5 + i * 2.5, 5.4))
            p1 = Vector((s * 10.0, -1.5 + i * 2.6, 0.5))
            b.limb(p0, mid, [0.6, 0.55], 5, SHELL_D, False, f'leg{i}.{side}')
            b.limb(mid, p1, [0.55, 0.3], 5, SHELL, False, f'leg{i}.{side}')


def crab_anims():
    A = []
    a = Anim('idle', 40, True)
    a.key(0, claw_L=(0, 0, 0), claw_R=(0, 0, 0), loc={'body': (0, 0, 0)})
    a.key(20, claw_L=(-8, 0, 6), claw_R=(-8, 0, -6), loc={'body': (0, 0, 0.3 / 15)})
    A.append(a)
    a = Anim('walk', 12, True)
    legs = {}
    for i in range(3):
        sgn = 1 if i % 2 == 0 else -1
        legs[f'leg{i}_L'] = (0, 18 * sgn, 0)
        legs[f'leg{i}_R'] = (0, 18 * sgn, 0)
    a.key(0, **legs, loc={'body': (0, 0, 0)})
    a.key(6, **{k: (0, -v[1], 0) for k, v in legs.items()}, loc={'body': (0, 0, 0.4 / 15)})
    A.append(a)
    a = Anim('attack', 14)
    a.key(0)
    a.key(4, claw_L=(-40, 0, 20), claw_R=(-40, 0, -20), pincer_L=(0, 0, 20), pincer_R=(0, 0, -20))
    a.key(8, claw_L=(10, 0, -10), claw_R=(10, 0, 10), pincer_L=(0, 0, -10), pincer_R=(0, 0, 10))
    a.key(14)
    A.append(a)
    a = Anim('hurt', 8)
    a.key(0, body=(10, 0, 0), claw_L=(-30, 0, 30), claw_R=(-30, 0, -30))
    a.key(8)
    A.append(a)
    return A


def build_crab():
    wf.reset()
    ao = wf.armature("Crab", CRAB_BONES)
    b = Builder()
    crab(b)
    mo = b.mesh_object("CrabBody")
    wf.bind(mo, ao)
    wf.apply_anims(ao, [_scale(a, 15) for a in crab_anims()])
    return ao, {'body': mo}


def _scale(a, k):
    a.keys = [(f, r, {bn: (v[0] * k, v[1] * k, v[2] * k) for bn, v in l.items()}) for (f, r, l) in a.keys]
    return a


# ------------------------------------------------------------------ jackal (the goat's rig, leaner)
FUR = hexc('#b4946a')
FUR_D = hexc('#7e6446')
FUR_L = hexc('#d8bc8c')
MUZ = hexc('#2a1c18')
JEYE = hexc('#f0c040', GLOW)

JACKAL_BONES = [
    ("root", (0, 0, 0), (0, 0, 2), None),
    ("body", (0, 6.5, 10.5), (0, -4.5, 11.0), "root"),
    ("neck", (0, -4.5, 11.5), (0, -7.4, 14.6), "body"),
    ("head", (0, -7.4, 14.6), (0, -12.4, 13.4), "neck"),
    ("tail", (0, 7.0, 11.0), (0, 11.0, 8.0), "body"),
    ("fleg.L", (2.2, -4.0, 9.0), (2.2, -4.2, 4.6), "body"),
    ("fshin.L", (2.2, -4.2, 4.6), (2.2, -4.4, 0.4), "fleg.L"),
    ("fleg.R", (-2.2, -4.0, 9.0), (-2.2, -4.2, 4.6), "body"),
    ("fshin.R", (-2.2, -4.2, 4.6), (-2.2, -4.4, 0.4), "fleg.R"),
    ("bleg.L", (2.2, 5.0, 9.0), (2.2, 6.4, 4.8), "body"),
    ("bshin.L", (2.2, 6.4, 4.8), (2.2, 5.6, 0.4), "bleg.L"),
    ("bleg.R", (-2.2, 5.0, 9.0), (-2.2, 6.4, 4.8), "body"),
    ("bshin.R", (-2.2, 6.4, 4.8), (-2.2, 5.6, 0.4), "bleg.R"),
]


def jackal(b: Builder):
    b.ellipsoid((0, 1.0, 10.6), (3.2, 7.4, 3.3), 12, 8, FUR, True, 'body')
    b.ellipsoid((0, -3.6, 11.2), (3.2, 3.2, 3.4), 12, 7, FUR, True, 'body')
    b.ellipsoid((0, 1.0, 12.8), (2.4, 6.2, 1.2), 10, 5, FUR_D, True, 'body')      # dark saddle
    b.ellipsoid((0, 1.0, 8.4), (2.4, 5.4, 1.2), 10, 5, FUR_L, True, 'body')       # pale belly
    b.limb((0, -4.6, 11.8), (0, -7.4, 14.6), [2.3, 2.0, 1.8], 10, FUR, True, 'neck')
    b.ellipsoid((0, -8.2, 14.8), (2.4, 2.4, 2.2), 10, 7, FUR, True, 'head')
    b.box((0, -11.2, 13.9), (2.0, 4.0, 1.7), FUR_L, 'head', rot=(-8, 0, 0), taper=0.7)      # long snout
    b.box((0, -13.0, 14.0), (1.2, 0.8, 0.9), MUZ, 'head')
    for s in (-1, 1):
        b.box((s * 1.5, -9.4, 15.6), (0.8, 0.8, 0.7), JEYE, 'head')
        b.box((s * 1.5, -7.6, 17.6), (1.4, 1.0, 3.8), FUR_D, 'head', rot=(-10, s * 14, 0), taper=0.3)   # tall ears
    for s, side in ((1, 'L'), (-1, 'R')):
        b.limb((s * 2.2, -4.0, 9.8), (s * 2.2, -4.2, 4.6), [1.2, 0.9], 8, FUR, True, 'fleg.' + side)
        b.limb((s * 2.2, -4.2, 4.6), (s * 2.2, -4.4, 0.6), [0.8, 0.7], 8, FUR_D, True, 'fshin.' + side)
        b.limb((s * 2.2, 5.0, 10.0), (s * 2.2, 6.4, 4.8), [1.6, 1.0], 8, FUR, True, 'bleg.' + side)
        b.limb((s * 2.2, 6.4, 4.8), (s * 2.2, 5.6, 0.6), [0.8, 0.7], 8, FUR_D, True, 'bshin.' + side)
    b.limb((0, 7.0, 11.0), (0, 11.0, 8.0), [1.2, 1.6, 1.0], 8, FUR_D, True, 'tail')


def jackal_anims():
    A = []
    a = Anim('idle', 40, True)
    a.key(0, head=(0, 0, 0), tail=(0, 0, 8))
    a.key(20, head=(-4, 0, 6), tail=(0, 0, -8), loc={'body': (0, 0, 0.2 / 15)})
    A.append(a)
    for name, n, amp, lift in (('walk', 20, 22, 0.4), ('run', 12, 40, 1.0)):
        a = Anim(name, n, True)
        h = n // 2
        a.key(0, fleg_L=(-amp, 0, 0), fshin_L=(10, 0, 0), bleg_R=(-amp * 0.7, 0, 0), bshin_R=(-10, 0, 0),
              fleg_R=(amp * 0.8, 0, 0), fshin_R=(30, 0, 0), bleg_L=(amp, 0, 0), bshin_L=(-20, 0, 0), body=(2, 0, 0), tail=(-10, 0, 0))
        a.key(h // 2, fleg_L=(0, 0, 0), bleg_R=(0, 0, 0), fleg_R=(-6, 0, 0), fshin_R=(40, 0, 0), bleg_L=(4, 0, 0), bshin_L=(-30, 0, 0),
              loc={'body': (0, 0, lift / 15)}, tail=(-14, 0, 0))
        a.mirrored(h, {0, h // 2})
        A.append(a)
    a = Anim('crouch', 10)
    a.key(0)
    a.key(6, body=(-6, 0, 0), neck=(30, 0, 0), head=(-14, 0, 0), fleg_L=(-30, 0, 0), fleg_R=(-30, 0, 0), fshin_L=(50, 0, 0), fshin_R=(50, 0, 0),
          bleg_L=(-20, 0, 0), bleg_R=(-20, 0, 0), bshin_L=(30, 0, 0), bshin_R=(30, 0, 0), loc={'body': (0, 0.8 / 15, -2.0 / 15)}, tail=(20, 0, 0))
    a.key(10, body=(-6, 0, 0), neck=(30, 0, 0), head=(-14, 0, 0), fleg_L=(-30, 0, 0), fleg_R=(-30, 0, 0), fshin_L=(50, 0, 0), fshin_R=(50, 0, 0),
          bleg_L=(-20, 0, 0), bleg_R=(-20, 0, 0), bshin_L=(30, 0, 0), bshin_R=(30, 0, 0), loc={'body': (0, 0.8 / 15, -2.2 / 15)}, tail=(20, 0, 0))
    A.append(a)
    a = Anim('lunge', 10)
    a.key(0, body=(8, 0, 0), neck=(-10, 0, 0), head=(-20, 0, 0), fleg_L=(-70, 0, 0), fleg_R=(-64, 0, 0), bleg_L=(50, 0, 0), bleg_R=(46, 0, 0),
          loc={'body': (0, 0, 2.0 / 15)}, tail=(-30, 0, 0))
    a.key(10, body=(4, 0, 0), neck=(-6, 0, 0), head=(-12, 0, 0), fleg_L=(-40, 0, 0), fleg_R=(-36, 0, 0), bleg_L=(30, 0, 0), bleg_R=(28, 0, 0),
          loc={'body': (0, 0, 1.0 / 15)}, tail=(-20, 0, 0))
    A.append(a)
    a = Anim('hurt', 8)
    a.key(0, body=(-10, 0, 0), neck=(-20, 0, 0), head=(-20, 0, 0))
    a.key(8)
    A.append(a)
    return A


def build_jackal():
    wf.reset()
    ao = wf.armature("Jackal", JACKAL_BONES)
    b = Builder()
    jackal(b)
    mo = b.mesh_object("JackalBody")
    wf.bind(mo, ao)
    wf.apply_anims(ao, [_scale(a, 15) for a in jackal_anims()])
    return ao, {'body': mo}


# ------------------------------------------------------------------ moth-shade
MOTH = hexc('#3a2a5a')
MOTH_L = hexc('#7a62b0')
MOTH_EYE = hexc('#ffe28a', GLOW)

MOTH_BONES = [
    ("root", (0, 0, 0), (0, 0, 2), None),
    ("body", (0, 0, 8), (0, 0, 12), "root"),
    ("wing.L", (1.0, 0, 11), (8, 1, 14), "body"),
    ("wing.R", (-1.0, 0, 11), (-8, 1, 14), "body"),
    ("hind.L", (1.0, 0.5, 9.5), (6, 1.5, 7), "body"),
    ("hind.R", (-1.0, 0.5, 9.5), (-6, 1.5, 7), "body"),
]


def moth(b: Builder):
    b.ellipsoid((0, 0, 10), (1.6, 1.8, 3.4), 8, 6, MOTH, True, 'body')
    b.ellipsoid((0, -0.6, 13.6), (1.6, 1.6, 1.4), 8, 5, MOTH, True, 'body')
    for s in (-1, 1):
        side = 'L' if s > 0 else 'R'
        b.box((s * 0.8, -1.9, 13.9), (0.8, 0.6, 0.8), MOTH_EYE, 'body')
        b.limb((s * 0.6, -0.8, 14.6), (s * 2.8, -1.4, 17.4), [0.25, 0.2], 4, MOTH_L, False, 'body')
        pts = [(0.0, 0.0), (4.0, 2.8), (7.6, 2.4), (8.2, -0.6), (5.0, -2.6), (1.2, -1.2)]
        from mathutils import Matrix
        M = Matrix.Translation((s * 1.0, 0.2, 11.0)) @ Matrix.Rotation(math.radians(90), 4, 'X')
        if s < 0:
            M = M @ Matrix.Scale(-1, 4, Vector((1, 0, 0)))
        b.prism(pts, 0.5, M, MOTH, 'wing.' + side, color_edge=MOTH_L)
        hp = [(0.0, 0.0), (3.6, -0.6), (5.0, -3.0), (2.4, -3.6)]
        M2 = Matrix.Translation((s * 1.0, 0.6, 9.6)) @ Matrix.Rotation(math.radians(90), 4, 'X')
        if s < 0:
            M2 = M2 @ Matrix.Scale(-1, 4, Vector((1, 0, 0)))
        b.prism(hp, 0.5, M2, MOTH_L, 'hind.' + side, color_edge=MOTH)


def moth_anims():
    a = Anim('fly', 8, True)
    a.key(0, wing_L=(0, 30, 0), wing_R=(0, -30, 0), hind_L=(0, 20, 0), hind_R=(0, -20, 0), loc={'body': (0, 0, 0.6 / 15)})
    a.key(4, wing_L=(0, -40, 0), wing_R=(0, 40, 0), hind_L=(0, -30, 0), hind_R=(0, 30, 0), loc={'body': (0, 0, -0.6 / 15)})
    return [a]


def build_moth():
    wf.reset()
    ao = wf.armature("Moth", MOTH_BONES)
    b = Builder()
    moth(b)
    mo = b.mesh_object("MothBody")
    wf.bind(mo, ao)
    wf.apply_anims(ao, [_scale(a, 15) for a in moth_anims()])
    return ao, {'body': mo}


# ------------------------------------------------------------------ bronze sentinel
SENTINEL = dict(width=1.15, tunic='#b8783a', tunic_d='#7a4a22', skin='#c8884a', skin_d='#8a5828', hair='#6a4020', beard='full',
                beard_col='#8a5a2a', headwear='helmet', head_col='#d89a46', carry='spear_held', eyes='glow', belt='#5a3418',
                boots='#6a4020', cloak=None, metal=True)


# ------------------------------------------------------------------ the Brazen Bull (boss)
BRONZE_B = hexc('#dc9440', METAL)
BRONZE_BD = hexc('#8a5224', METAL)
BRONZE_BL = hexc('#ffd27a', METAL)
FIRE_B = hexc('#ff9a30', GLOW)
FIRE_BC = hexc('#fff0b0', GLOW)

BULL_BONES = [
    ("root", (0, 0, 0), (0, 0, 2), None),
    ("body", (0, 12, 20), (0, -9, 21), "root"),
    ("neck", (0, -9, 22), (0, -14, 26), "body"),
    ("head", (0, -14, 26), (0, -22, 22), "neck"),
    ("jaw", (0, -17, 21), (0, -23, 19), "head"),
    ("tail", (0, 13, 22), (0, 16, 14), "body"),
    ("fleg.L", (5, -7, 16), (5, -7.5, 8), "body"),
    ("fshin.L", (5, -7.5, 8), (5, -8, 0.6), "fleg.L"),
    ("fleg.R", (-5, -7, 16), (-5, -7.5, 8), "body"),
    ("fshin.R", (-5, -7.5, 8), (-5, -8, 0.6), "fleg.R"),
    ("bleg.L", (5, 9, 16), (5, 11, 8), "body"),
    ("bshin.L", (5, 11, 8), (5, 10, 0.6), "bleg.L"),
    ("bleg.R", (-5, 9, 16), (-5, 11, 8), "body"),
    ("bshin.R", (-5, 11, 8), (-5, 10, 0.6), "bleg.R"),
]


def bull(b: Builder):
    b.ellipsoid((0, 2, 20.5), (8.4, 14.5, 8.6), 16, 10, BRONZE_B, True, 'body')
    b.ellipsoid((0, -6.5, 22.5), (9.2, 7.0, 9.6), 16, 10, BRONZE_B, True, 'body')       # the hump and chest
    b.ellipsoid((0, 2, 27.6), (5.0, 11.0, 2.2), 12, 6, BRONZE_BL, True, 'body')
    for k in range(6):
        b.box((0, -6 + k * 3.4, 29.2), (1.2, 1.2, 1.0), hexc('#fff0c0', METAL), 'body')
    b.box((0, -11.6, 15.4), (6.0, 1.0, 4.0), FIRE_B, 'body')                              # furnace door in the chest
    # the furnace grille in its flank, fire showing through
    for s in (-1, 1):
        b.box((s * 8.6, 1.0, 19.0), (0.6, 9.0, 7.0), BRONZE_BD, 'body')
        for k in range(4):
            b.box((s * 8.8, -2.2 + k * 2.2, 19.0), (0.4, 1.0, 5.6), FIRE_B, 'body')
    b.limb((0, -9, 23), (0, -14, 25.5), [5.4, 4.6, 4.0], 12, BRONZE_B, True, 'neck')
    b.ellipsoid((0, -16.5, 25.0), (5.6, 5.4, 5.2), 12, 8, BRONZE_B, True, 'head')
    b.box((0, -20.8, 22.6), (6.6, 5.6, 5.2), BRONZE_B, 'head', rot=(-16, 0, 0), taper=0.85)
    b.box((0, -18.0, 29.4), (7.0, 3.0, 1.2), BRONZE_BL, 'head')                          # brow plate
    b.box((0, -21.8, 20.4), (4.6, 3.6, 2.0), BRONZE_BD, 'jaw', rot=(-12, 0, 0))
    b.box((0, -22.8, 22.0), (3.4, 1.0, 1.6), FIRE_BC, 'head')                            # fire in the nostrils
    b.ellipsoid((0, -23.0, 23.2), (1.8, 0.8, 0.8), 6, 4, BRONZE_BL, True, 'head')           # nose ring
    for s in (-1, 1):
        b.box((s * 3.6, -19.6, 26.8), (1.8, 1.0, 1.2), FIRE_BC, 'head')                      # eyes like coals
        pts = [Vector((s * 4.4, -15.8, 28.8)), Vector((s * 9.4, -15.0, 30.4)), Vector((s * 12.0, -15.6, 34.6)), Vector((s * 10.6, -17.6, 39.0))]
        rad = [1.9, 1.5, 1.0, 0.4]
        for i in range(3):
            b.limb(pts[i], pts[i + 1], [rad[i], rad[i + 1]], 6, BRONZE_BL if i < 2 else hexc('#fff0c0', METAL), True, 'head')
        b.box((s * 5.6, -14.6, 26.0), (3.0, 1.2, 1.6), BRONZE_BD, 'head', rot=(0, s * -20, s * -16))
    for s, side in ((1, 'L'), (-1, 'R')):
        b.limb((s * 5, -7, 17), (s * 5, -7.5, 8), [3.2, 2.8, 2.4], 10, BRONZE_B, True, 'fleg.' + side)
        b.limb((s * 5, -7.5, 8), (s * 5, -8, 1.4), [2.2, 2.0, 2.0], 10, BRONZE_BD, True, 'fshin.' + side)
        b.box((s * 5, -8.6, 0.9), (3.6, 4.0, 1.8), hexc('#2a1a14'), 'fshin.' + side)
        b.limb((s * 5, 9, 18), (s * 5, 11, 8), [3.8, 3.2, 2.4], 10, BRONZE_B, True, 'bleg.' + side)
        b.limb((s * 5, 11, 8), (s * 5, 10, 1.4), [2.2, 2.0, 2.0], 10, BRONZE_BD, True, 'bshin.' + side)
        b.box((s * 5, 9.4, 0.9), (3.6, 4.0, 1.8), hexc('#2a1a14'), 'bshin.' + side)
    b.limb((0, 15, 23), (0, 17, 14), [1.0, 0.8, 0.6], 6, BRONZE_BD, True, 'tail')
    b.ellipsoid((0, 17.2, 12.6), (1.4, 1.4, 2.2), 6, 4, FIRE_B, True, 'tail')


def bull_anims():
    A = []
    a = Anim('idle', 40, True)
    a.key(0, head=(0, 0, 0), jaw=(0, 0, 0), tail=(0, 0, 10))
    a.key(20, head=(4, 0, 4), jaw=(6, 0, 0), tail=(0, 0, -10), loc={'body': (0, 0, 0.6 / 15)})
    A.append(a)
    for name, n, amp, lift in (('walk', 24, 18, 0.6), ('charge', 12, 42, 1.6)):
        a = Anim(name, n, True)
        h = n // 2
        hd = (24, 0, 0) if name == 'charge' else (0, 0, 0)
        a.key(0, fleg_L=(-amp, 0, 0), fshin_L=(10, 0, 0), bleg_R=(-amp * 0.7, 0, 0), bshin_R=(-10, 0, 0), fleg_R=(amp * 0.8, 0, 0),
              fshin_R=(30, 0, 0), bleg_L=(amp, 0, 0), bshin_L=(-20, 0, 0), head=hd, neck=(hd[0] * 0.6, 0, 0))
        a.key(h // 2, fleg_L=(0, 0, 0), bleg_R=(0, 0, 0), fleg_R=(-6, 0, 0), fshin_R=(40, 0, 0), bleg_L=(4, 0, 0), bshin_L=(-30, 0, 0),
              head=hd, neck=(hd[0] * 0.6, 0, 0), loc={'body': (0, 0, lift / 15)})
        a.mirrored(h, {0, h // 2})
        A.append(a)
    a = Anim('stun', 40, True)       # dazed against a pillar: head down, legs splayed
    a.key(0, body=(6, 0, 0), neck=(30, 0, 0), head=(20, 0, -10), fleg_L=(-10, 10, 0), fleg_R=(-10, -10, 0), loc={'body': (0, 0, -1.4 / 15)})
    a.key(20, body=(6, 0, 0), neck=(32, 0, 0), head=(22, 0, 10), fleg_L=(-10, 10, 0), fleg_R=(-10, -10, 0), loc={'body': (0, 0, -1.6 / 15)})
    A.append(a)
    a = Anim('shoot', 18)            # rears its head, opens its jaw
    a.key(0)
    a.key(6, neck=(-24, 0, 0), head=(-20, 0, 0), jaw=(10, 0, 0), body=(-4, 0, 0))
    a.key(10, neck=(10, 0, 0), head=(12, 0, 0), jaw=(34, 0, 0), body=(2, 0, 0))
    a.key(18)
    A.append(a)
    a = Anim('hurt', 8)
    a.key(0, body=(-8, 0, 0), neck=(-16, 0, 0), head=(-16, 0, 0))
    a.key(8)
    A.append(a)
    a = Anim('death', 40)
    a.key(0)
    a.key(16, body=(10, 0, 8), neck=(30, 0, 0), head=(30, 0, 0), fleg_L=(-40, 0, 0), fleg_R=(-40, 0, 0), loc={'body': (0, 0, -4 / 15)})
    a.key(40, body=(14, 0, 14), neck=(40, 0, 0), head=(40, 0, 10), fleg_L=(-70, 0, 0), fleg_R=(-70, 0, 0), bleg_L=(40, 0, 0), bleg_R=(40, 0, 0),
          loc={'body': (0, 0, -9 / 15)})
    A.append(a)
    return A


def build_bull():
    wf.reset()
    ao = wf.armature("Bull", BULL_BONES)
    b = Builder()
    bull(b)
    mo = b.mesh_object("BullBody")
    wf.bind(mo, ao)
    wf.apply_anims(ao, [_scale(a, 15) for a in bull_anims()])
    return ao, {'body': mo}


# ------------------------------------------------------------------ Ninhal, asleep (a giant)
GOD = dict(width=1.25, belly=1.0, tunic='#1c2464', tunic_d='#121848', robe=True, trim='#e8b848', skin='#e0ae84', hair='#f0ecf6',
           beard='long', beard_col='#f4f0fa', headwear='horned', head_col='#f2d27a', eyes='closed', sash='#e8b848', stars=True,
           hair_style='long')
