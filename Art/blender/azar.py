"""AZAR, the night watchman of Ashkel. Forty nights awake: wild black hair, a red headband,
dark eyes ringed with tiredness, bronze scale vest over an indigo tunic, a night-blue cloak,
a bronze khopesh in the right hand and the Wakefire lantern in the left.
Run:  python3 azar.py [check]   -> Models/Azar.fbx (+ check renders with 'check')."""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from wf import Builder, Anim, hexc, METAL, GLOW, D2R
from mathutils import Vector

OUT = "/srv/Wakefire/Assets/Wakefire/Resources/Models/Azar.fbx"

SKIN = hexc('#d29a6a')
SKIN_D = hexc('#b07a52')
STUBBLE = hexc('#7a5440')
HAIR = hexc('#231a22')
EYE = hexc('#0b080a')
BAGS = hexc('#6b4536')
BAND = hexc('#d8323a')
TUNIC = hexc('#a8303a')
TUNIC_D = hexc('#7a1f2a')
BRONZE = hexc('#d0913f', METAL)
BRONZE_D = hexc('#9c6428', METAL)
BRONZE_L = hexc('#f2c66a', METAL)
LEATHER = hexc('#6a4026')
BOOT = hexc('#4a2c1a')
CLOAK = hexc('#3a4492')
CLOAK_IN = hexc('#24285e')
FLAME = hexc('#ffb347', GLOW)
FLAME_CORE = hexc('#fff0b0', GLOW)
WRAP = hexc('#2b1c13')

BONES = [
    ("root", (0, 0, 0), (0, 0, 0.2), None),
    ("hips", (0, 0, 0.98), (0, 0, 1.10), "root"),
    ("spine", (0, 0, 1.10), (0, 0, 1.28), "hips"),
    ("chest", (0, 0, 1.28), (0, 0, 1.48), "spine"),
    ("neck", (0, 0, 1.48), (0, 0, 1.57), "chest"),
    ("head", (0, 0, 1.57), (0, 0, 1.80), "neck"),
    ("band1", (0, 0.13, 1.73), (0, 0.21, 1.66), "head"),
    ("band2", (0, 0.21, 1.66), (0, 0.27, 1.57), "band1"),
    ("cape1", (0, 0.12, 1.46), (0, 0.17, 1.05), "chest"),
    ("cape2", (0, 0.17, 1.05), (0, 0.21, 0.62), "cape1"),
    ("upperarm.R", (-0.25, 0, 1.44), (-0.28, 0, 1.16), "chest"),
    ("forearm.R", (-0.28, 0, 1.16), (-0.29, -0.01, 0.90), "upperarm.R"),
    ("hand.R", (-0.29, -0.01, 0.90), (-0.29, -0.02, 0.80), "forearm.R"),
    ("weapon", (-0.29, -0.03, 0.855), (-0.29, -0.36, 0.72), "hand.R"),
    ("upperarm.L", (0.25, 0, 1.44), (0.28, 0, 1.16), "chest"),
    ("forearm.L", (0.28, 0, 1.16), (0.29, -0.01, 0.90), "upperarm.L"),
    ("hand.L", (0.29, -0.01, 0.90), (0.29, -0.02, 0.80), "forearm.L"),
    ("lantern", (0.29, -0.03, 0.83), (0.29, -0.03, 0.60), "hand.L"),
    ("shield", (0.34, -0.01, 1.04), (0.34, -0.12, 1.04), "forearm.L"),
    ("thigh.R", (-0.10, 0, 0.97), (-0.11, 0, 0.53), "hips"),
    ("shin.R", (-0.11, 0, 0.53), (-0.11, 0.02, 0.10), "thigh.R"),
    ("foot.R", (-0.11, 0.02, 0.10), (-0.11, -0.15, 0.03), "shin.R"),
    ("thigh.L", (0.10, 0, 0.97), (0.11, 0, 0.53), "hips"),
    ("shin.L", (0.11, 0, 0.53), (0.11, 0.02, 0.10), "thigh.L"),
    ("foot.L", (0.11, 0.02, 0.10), (0.11, -0.15, 0.03), "shin.L"),
]


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


R_LIMB = 1.55
R_BODY = 1.28


def body(b: Builder):
    # head
    b.ellipsoid((0, -0.005, 1.665), (0.105, 0.115, 0.13), 12, 8, SKIN, True, 'head')
    b.ellipsoid((0, -0.035, 1.588), (0.088, 0.083, 0.052), 10, 6, STUBBLE, True, 'head')
    for s in (-1, 1):
        b.box((s * 0.042, -0.111, 1.682), (0.028, 0.012, 0.014), EYE, 'head')
        b.box((s * 0.044, -0.108, 1.664), (0.03, 0.01, 0.012), BAGS, 'head')
        b.box((s * 0.046, -0.112, 1.703), (0.04, 0.012, 0.01), HAIR, 'head', rot=(0, s * 12, 0))
        b.ellipsoid((s * 0.104, 0.0, 1.662), (0.02, 0.03, 0.036), 6, 4, SKIN_D, True, 'head')
    b.box((0, -0.123, 1.652), (0.022, 0.03, 0.042), SKIN_D, 'head', taper=0.7)
    b.box((0, -0.104, 1.606), (0.036, 0.01, 0.007), hexc('#3a2420'), 'head')
    # hair: a cap that leaves the face open, plus wild tufts that stick out the back
    h0 = len(b.f)
    b.ellipsoid((0, 0.014, 1.712), (0.118, 0.13, 0.112), 12, 8, HAIR, True, 'head')
    keep = []
    for i, (idx, col, sm, g) in enumerate(b.f):
        if i < h0:
            keep.append(b.f[i])
            continue
        c = sum((b.v[k] for k in idx), Vector()) / len(idx)
        if c.y < -0.04 and c.z < 1.752:
            continue
        keep.append(b.f[i])
    b.f = keep
    for (p, r, sz) in [((0.04, 0.09, 1.78), (-70, 10, 0), 0.10), ((-0.04, 0.09, 1.78), (-70, -10, 0), 0.10),
                       ((0.0, 0.12, 1.74), (-95, 0, 0), 0.11), ((0.075, 0.08, 1.72), (-80, 35, 0), 0.08),
                       ((-0.075, 0.08, 1.72), (-80, -35, 0), 0.08), ((0.0, 0.11, 1.68), (-110, 0, 0), 0.09),
                       ((0.03, -0.05, 1.80), (55, 10, 0), 0.06), ((-0.04, -0.03, 1.81), (50, -15, 0), 0.05)]:
        b.box(p, (0.06, 0.05, sz), HAIR, 'head', rot=r, taper=0.12)
    # headband and its knot
    b.loft([((0, 0.01, 1.712), 0.121, 0.131), ((0, 0.01, 1.742), 0.121, 0.131)], 14, BAND, True, 'head', False, False)
    b.box((0, 0.135, 1.727), (0.04, 0.03, 0.035), BAND, 'head')
    b.limb((0.0, 0.135, 1.725), (0.0, 0.21, 1.66), [0.017, 0.015], 4, BAND, False, 'band1', squash=0.35)
    b.limb((0.0, 0.21, 1.66), (0.0, 0.27, 1.57), [0.015, 0.008], 4, BAND, False, 'band2', squash=0.35)

    # neck, torso, vest
    b.limb((0, 0, 1.46), (0, 0, 1.58), [0.055, 0.05], 8, SKIN, True, 'neck')
    b.loft([((0, 0, 1.08), 0.150 * R_BODY, 0.105 * R_BODY), ((0, 0, 1.18), 0.152 * R_BODY, 0.106 * R_BODY), ((0, 0, 1.28), 0.166 * R_BODY, 0.112 * R_BODY)], 12, TUNIC, True, 'spine')
    b.loft([((0, 0, 1.28), 0.166 * R_BODY, 0.112 * R_BODY), ((0, 0, 1.38), 0.19 * R_BODY, 0.118 * R_BODY), ((0, 0, 1.46), 0.20 * R_BODY, 0.115 * R_BODY), ((0, 0, 1.52), 0.11 * R_BODY, 0.085 * R_BODY)], 12, TUNIC, True, 'chest')
    rows = [(1.255, 1.31, BRONZE_D), (1.31, 1.365, BRONZE), (1.365, 1.42, BRONZE_D), (1.42, 1.47, BRONZE)]
    for (z0, z1, col) in rows:
        def w(z):
            return 0.172 + (z - 1.26) * (0.205 - 0.172) / (1.47 - 1.26)
        grp = 'chest' if z0 >= 1.28 else 'spine'
        b.loft([((0, 0.002, z0), (w(z0) + 0.006) * R_BODY, 0.122 * R_BODY), ((0, 0.002, z1), (w(z1) + 0.006) * R_BODY, 0.124 * R_BODY)], 12, col, False, grp, False, False)
    # belt + buckle, kilt and its leather front flap
    b.loft([((0, 0, 1.07), 0.162 * R_BODY, 0.114 * R_BODY), ((0, 0, 1.12), 0.162 * R_BODY, 0.114 * R_BODY)], 12, LEATHER, False, 'hips', False, False)
    b.box((0, -0.118, 1.095), (0.052, 0.02, 0.046), BRONZE_L, 'hips')
    b.loft([((0, 0, 1.08), 0.158 * R_BODY, 0.110 * R_BODY), ((0, 0, 0.99), 0.170 * R_BODY, 0.120 * R_BODY), ((0, 0.005, 0.86), 0.196 * R_BODY, 0.142 * R_BODY), ((0, 0.01, 0.73), 0.214 * R_BODY, 0.156 * R_BODY)],
           12, TUNIC, True, 'hips', False, False)
    b.loft([((0, 0.01, 0.745), 0.215 * R_BODY, 0.157 * R_BODY), ((0, 0.01, 0.73), 0.216 * R_BODY, 0.158 * R_BODY)], 12, TUNIC_D, False, 'hips', False, False)
    b.box((0, -0.152, 0.86), (0.12, 0.022, 0.25), LEATHER, 'hips', rot=(-8, 0, 0))
    for z in (0.95, 0.88, 0.81):
        b.box((0, -0.165, z), (0.03, 0.012, 0.025), BRONZE_L, 'hips')

    for s, side in ((-1, 'R'), (1, 'L')):
        # shoulders, arms, bracers, hands
        b.box((s * 0.26, 0.0, 1.405), (0.09, 0.14, 0.07), BRONZE, 'upperarm.' + side, rot=(0, s * 20, 0))
        sh, el, wr = Vector((s * 0.25, 0, 1.44)), Vector((s * 0.28, 0, 1.16)), Vector((s * 0.29, -0.01, 0.90))
        b.limb(sh, el, [0.056 * R_LIMB, 0.052 * R_LIMB, 0.045 * R_LIMB], 8, SKIN, True, 'upperarm.' + side)
        b.limb(el, wr, [0.046 * R_LIMB, 0.042 * R_LIMB, 0.034 * R_LIMB], 8, SKIN, True, 'forearm.' + side)
        b.limb(lerp(el, wr, 0.18), lerp(el, wr, 0.88), [0.052 * R_LIMB, 0.05 * R_LIMB, 0.043 * R_LIMB], 8, BRONZE, False, 'forearm.' + side)
        b.ellipsoid((s * 0.29, -0.016, 0.855), (0.05, 0.055, 0.06), 8, 5, SKIN, True, 'hand.' + side)
        # legs: thighs (mostly under the kilt), shins with greaves, knee caps, boots
        hip, knee, ank = Vector((s * 0.10, 0, 0.97)), Vector((s * 0.11, 0, 0.53)), Vector((s * 0.11, 0.02, 0.10))
        b.limb(hip, knee, [0.078 * R_LIMB, 0.07 * R_LIMB, 0.056 * R_LIMB], 8, SKIN, True, 'thigh.' + side)
        b.limb(knee, ank, [0.056 * R_LIMB, 0.05 * R_LIMB, 0.036 * R_LIMB], 8, SKIN, True, 'shin.' + side)
        b.limb(lerp(knee, ank, 0.08), lerp(knee, ank, 0.82), [0.062 * R_LIMB, 0.056 * R_LIMB, 0.045 * R_LIMB], 8, BRONZE, False, 'shin.' + side)
        b.ellipsoid((s * 0.11, -0.045, 0.535), (0.046, 0.03, 0.046), 6, 4, BRONZE_L, False, 'shin.' + side)
        b.box((s * 0.12, -0.05, 0.06), (0.13, 0.27, 0.12), BOOT, 'foot.' + side, taper=0.85)
        b.box((s * 0.11, 0.035, 0.12), (0.09, 0.09, 0.08), BOOT, 'foot.' + side)

    # cloak: open at the front, crimson lining, bunched collar
    b.loft([((0, 0.03, 1.47), 0.19 * R_BODY, 0.13 * R_BODY), ((0, 0.04, 1.26), 0.235 * R_BODY, 0.17 * R_BODY), ((0, 0.05, 1.05), 0.25 * R_BODY, 0.19 * R_BODY)], 12, CLOAK, True, 'cape1',
           arc=(112, 248), double=True, color_in=CLOAK_IN)
    b.loft([((0, 0.05, 1.05), 0.25 * R_BODY, 0.19 * R_BODY), ((0, 0.06, 0.82), 0.27 * R_BODY, 0.21 * R_BODY), ((0, 0.07, 0.62), 0.29 * R_BODY, 0.23 * R_BODY)], 12, CLOAK, True, 'cape2',
           arc=(112, 248), double=True, color_in=CLOAK_IN)
    MANTLE = hexc('#434fa6')
    b.loft([((0, 0.02, 1.53), 0.10 * R_BODY, 0.09 * R_BODY), ((0, 0.02, 1.50), 0.19 * R_BODY, 0.14 * R_BODY), ((0, 0.025, 1.44), 0.265 * R_BODY, 0.175 * R_BODY), ((0, 0.03, 1.37), 0.285 * R_BODY, 0.19 * R_BODY)],
           14, MANTLE, True, 'chest', arc=(-150, 150), double=True, color_in=CLOAK_IN)
    b.ellipsoid((0, -0.11, 1.49), (0.03, 0.02, 0.03), 6, 4, BRONZE_L, False, 'chest')


def khopesh(b: Builder):
    head = Vector((-0.29, -0.03, 0.855))
    tail = Vector((-0.29, -0.36, 0.72))
    u = (tail - head).normalized()
    w = Vector((1, 0, 0))
    v = w.cross(u).normalized()
    if v.z < 0:
        v = -v
    from mathutils import Matrix
    M = Matrix((u, v, w)).transposed().to_4x4()
    M.translation = head
    b.limb(head - u * 0.03, head + u * 0.11, [0.019, 0.019], 6, WRAP, False, 'weapon')
    b.ellipsoid(head - u * 0.04, (0.024, 0.024, 0.024), 6, 4, BRONZE_L, False, 'weapon')
    b.box(head + u * 0.115, (0.05, 0.05, 0.05), BRONZE_D, 'weapon')
    pts = [(0.11, 0.018), (0.27, 0.018), (0.32, 0.05), (0.38, 0.09), (0.45, 0.11), (0.52, 0.10), (0.57, 0.068),
           (0.59, 0.02), (0.578, -0.03), (0.545, -0.07), (0.53, -0.03), (0.522, 0.005), (0.50, 0.035), (0.46, 0.05),
           (0.40, 0.045), (0.35, 0.02), (0.315, -0.015), (0.27, -0.018), (0.11, -0.018)]
    b.prism(pts, 0.016, M, BRONZE, 'weapon', False, color_edge=BRONZE_L)


def lantern(b: Builder):
    x, y = 0.29, -0.03
    from mathutils import Matrix
    start = len(b.v)
    b.limb((x, y, 0.84), (x, y, 0.78), [0.006, 0.006], 4, BRONZE_D, False, 'lantern')
    b.loft([((x, y, 0.78), 0.012, 0.012), ((x, y, 0.75), 0.06, 0.06)], 8, BRONZE, False, 'lantern', True, True)
    b.loft([((x, y, 0.75), 0.05, 0.05), ((x, y, 0.645), 0.05, 0.05)], 8, FLAME, True, 'lantern', True, True)
    b.ellipsoid((x, y, 0.69), (0.026, 0.026, 0.034), 6, 4, FLAME_CORE, True, 'lantern')
    for k in range(4):
        a = (45 + 90 * k) * D2R
        b.box((x + math.sin(a) * 0.052, y - math.cos(a) * 0.052, 0.697), (0.014, 0.014, 0.11), BRONZE_D, 'lantern')
    b.loft([((x, y, 0.645), 0.06, 0.06), ((x, y, 0.62), 0.045, 0.045)], 8, BRONZE, False, 'lantern', True, True)
    pivot = Vector((x, y, 0.83))
    for i in range(start, len(b.v)):
        b.v[i] = pivot + (b.v[i] - pivot) * 1.3


def shield(b: Builder):
    """Bronze Mirror Shield, strapped to the left forearm (separate mesh, shown once found)."""
    c = Vector((0.355, -0.02, 1.04))
    b.loft([((0, 0, -0.012), 0.16, 0.16), ((0, 0, 0.0), 0.165, 0.165), ((0, 0, 0.022), 0.12, 0.12), ((0, 0, 0.03), 0.06, 0.06)], 16,
           BRONZE_L, False, 'shield', True, True,
           xf=__import__('mathutils').Matrix.Translation(c) @ __import__('mathutils').Euler((0, 90 * D2R, 0)).to_matrix().to_4x4())


def anims():
    A = []
    # ---- idle: forty nights awake: slumped, breathing, head heavy
    a = Anim('idle', 60, True)
    a.key(0, loc={'hips': (0.012, 0, -0.006)}, hips=(0, 0, 3), thigh_R=(-6, 0, 2), shin_R=(10, 0, 0), thigh_L=(2, 0, 0),
          spine=(4, 0, 0), chest=(3, 0, 0), neck=(6, 0, 0), head=(9, 0, 0),
          upperarm_R=(4, 5, 0), forearm_R=(-16, 0, 0), upperarm_L=(-12, -5, 0), forearm_L=(-50, 0, 0), cape1=(2, 0, 0))
    a.key(30, loc={'hips': (0.012, 0, -0.013)}, hips=(0, 0, 3), thigh_R=(-6, 0, 2), shin_R=(12, 0, 0), thigh_L=(2, 0, 0),
          spine=(5, 0, 0), chest=(7, 0, 0), neck=(8, 0, 0), head=(13, 0, 2),
          upperarm_R=(5, 4, 0), forearm_R=(-14, 0, 0), upperarm_L=(-10, -5, 0), forearm_L=(-46, 0, 0), cape1=(1, 0, 0))
    A.append(a)
    # ---- micro-sleep: head drops, snaps back up
    a = Anim('idle_nod', 34)
    base = dict(spine=(4, 0, 0), chest=(4, 0, 0), upperarm_R=(4, 5, 0), forearm_R=(-16, 0, 0), upperarm_L=(-12, -5, 0), forearm_L=(-50, 0, 0))
    a.key(0, neck=(6, 0, 0), head=(9, 0, 0), **base)
    a.key(16, neck=(16, 0, 0), head=(34, 0, 4), loc={'hips': (0, 0, -0.03)}, thigh_R=(-6, 0, 0), shin_R=(12, 0, 0), **base)
    a.key(20, neck=(-4, 0, 0), head=(-10, 0, 0), **base)
    a.key(34, neck=(6, 0, 0), head=(9, 0, 0), **base)
    A.append(a)
    # ---- run (18 frames): contact, down, pass, flight; then mirrored
    a = Anim('run', 18, True)
    a.key(0, loc={'hips': (0, 0, -0.02)}, hips=(8, 0, 8), spine=(6, 0, -6), chest=(4, 0, -8), neck=(-4, 0, 6), head=(-4, 0, 4),
          thigh_R=(-38, 0, 0), shin_R=(12, 0, 0), foot_R=(-15, 0, 0), thigh_L=(22, 0, 0), shin_L=(75, 0, 0), foot_L=(25, 0, 0),
          upperarm_R=(30, 6, 0), forearm_R=(-65, 0, 0), upperarm_L=(-30, -6, 0), forearm_L=(-55, 0, 0), cape1=(18, 0, 0), cape2=(10, 0, 0))
    a.key(3, loc={'hips': (0, 0, -0.06)}, hips=(10, 0, 4), spine=(6, 0, -3), chest=(4, 0, -4), neck=(-4, 0, 3), head=(-4, 0, 2),
          thigh_R=(-22, 0, 0), shin_R=(38, 0, 0), foot_R=(5, 0, 0), thigh_L=(5, 0, 0), shin_L=(95, 0, 0), foot_L=(20, 0, 0),
          upperarm_R=(15, 6, 0), forearm_R=(-70, 0, 0), upperarm_L=(-15, -6, 0), forearm_L=(-50, 0, 0), cape1=(22, 0, 0), cape2=(14, 0, 0))
    a.key(5, loc={'hips': (0, 0, -0.01)}, hips=(9, 0, 0), spine=(6, 0, 0), chest=(4, 0, 0), neck=(-4, 0, 0), head=(-4, 0, 0),
          thigh_R=(0, 0, 0), shin_R=(18, 0, 0), foot_R=(10, 0, 0), thigh_L=(-25, 0, 0), shin_L=(85, 0, 0), foot_L=(10, 0, 0),
          upperarm_R=(-5, 6, 0), forearm_R=(-75, 0, 0), upperarm_L=(5, -6, 0), forearm_L=(-50, 0, 0), cape1=(20, 0, 0), cape2=(16, 0, 0))
    a.key(7, loc={'hips': (0, 0, 0.05)}, hips=(8, 0, -6), spine=(6, 0, 4), chest=(4, 0, 6), neck=(-4, 0, -4), head=(-4, 0, -3),
          thigh_R=(22, 0, 0), shin_R=(20, 0, 0), foot_R=(35, 0, 0), thigh_L=(-42, 0, 0), shin_L=(50, 0, 0), foot_L=(-5, 0, 0),
          upperarm_R=(-25, 6, 0), forearm_R=(-75, 0, 0), upperarm_L=(22, -6, 0), forearm_L=(-45, 0, 0), cape1=(16, 0, 0), cape2=(12, 0, 0))
    a.mirrored(9, {0, 3, 5, 7})
    A.append(a)
    # ---- walk (28 frames)
    a = Anim('walk', 28, True)
    a.key(0, loc={'hips': (0, 0, -0.01)}, hips=(2, 0, 5), chest=(2, 0, -6), neck=(4, 0, 3), head=(6, 0, 2),
          thigh_R=(-25, 0, 0), shin_R=(5, 0, 0), foot_R=(-12, 0, 0), thigh_L=(15, 0, 0), shin_L=(12, 0, 0), foot_L=(15, 0, 0),
          upperarm_R=(14, 4, 0), forearm_R=(-12, 0, 0), upperarm_L=(-14, -4, 0), forearm_L=(-40, 0, 0), cape1=(4, 0, 0))
    a.key(4, loc={'hips': (0, 0, -0.03)}, hips=(2, 0, 3), chest=(2, 0, -4), neck=(4, 0, 2), head=(6, 0, 1),
          thigh_R=(-18, 0, 0), shin_R=(18, 0, 0), foot_R=(2, 0, 0), thigh_L=(12, 0, 0), shin_L=(35, 0, 0), foot_L=(18, 0, 0),
          upperarm_R=(10, 4, 0), forearm_R=(-12, 0, 0), upperarm_L=(-10, -4, 0), forearm_L=(-40, 0, 0), cape1=(5, 0, 0))
    a.key(7, loc={'hips': (0, 0, 0.01)}, hips=(2, 0, 0), chest=(2, 0, 0), neck=(4, 0, 0), head=(6, 0, 0),
          thigh_R=(-2, 0, 0), shin_R=(8, 0, 0), foot_R=(2, 0, 0), thigh_L=(-15, 0, 0), shin_L=(45, 0, 0), foot_L=(5, 0, 0),
          upperarm_R=(0, 4, 0), forearm_R=(-15, 0, 0), upperarm_L=(0, -4, 0), forearm_L=(-42, 0, 0), cape1=(6, 0, 0))
    a.key(10, loc={'hips': (0, 0, 0.02)}, hips=(2, 0, -4), chest=(2, 0, 4), neck=(4, 0, -2), head=(6, 0, -2),
          thigh_R=(10, 0, 0), shin_R=(5, 0, 0), foot_R=(15, 0, 0), thigh_L=(-28, 0, 0), shin_L=(20, 0, 0), foot_L=(-8, 0, 0),
          upperarm_R=(-10, 4, 0), forearm_R=(-18, 0, 0), upperarm_L=(10, -4, 0), forearm_L=(-40, 0, 0), cape1=(5, 0, 0))
    a.mirrored(14, {0, 4, 7, 10})
    A.append(a)
    # ---- three-hit combo
    ready = dict(upperarm_R=(-20, 15, 0), forearm_R=(-30, 0, 0), upperarm_L=(-14, -8, 0), forearm_L=(-45, 0, 0))
    a = Anim('attack1', 15)
    a.key(0, **ready)
    a.key(3, hips=(0, 0, -10), spine=(0, 0, -15), chest=(-5, 0, -35), upperarm_R=(10, 75, 25), forearm_R=(-40, 0, 0),
          thigh_R=(5, 0, 0), thigh_L=(-15, 0, 0), shin_L=(10, 0, 0), upperarm_L=(-25, -20, 0), forearm_L=(-45, 0, 0), loc={'hips': (0, 0.02, -0.02)})
    a.key(5, hips=(0, 0, 8), spine=(5, 0, 5), chest=(5, 0, 10), upperarm_R=(-60, 40, -30), forearm_R=(-10, 0, 0),
          thigh_R=(-30, 0, 0), shin_R=(20, 0, 0), thigh_L=(15, 0, 0), shin_L=(15, 0, 0), upperarm_L=(-5, -30, 0), forearm_L=(-40, 0, 0),
          loc={'hips': (0, -0.06, -0.06)}, cape1=(14, 0, 0))
    a.key(7, hips=(0, 0, 15), spine=(6, 0, 20), chest=(8, 0, 45), upperarm_R=(-55, -10, -60), forearm_R=(-25, 0, 0),
          thigh_R=(-32, 0, 0), shin_R=(22, 0, 0), thigh_L=(16, 0, 0), shin_L=(16, 0, 0), upperarm_L=(10, -35, 0), forearm_L=(-40, 0, 0),
          loc={'hips': (0, -0.08, -0.07)}, cape1=(18, 0, 6))
    a.key(11, hips=(0, 0, 6), spine=(4, 0, 8), chest=(4, 0, 20), upperarm_R=(-30, 10, -20), forearm_R=(-30, 0, 0),
          thigh_R=(-18, 0, 0), shin_R=(12, 0, 0), thigh_L=(8, 0, 0), loc={'hips': (0, -0.04, -0.03)})
    a.key(15, **ready)
    A.append(a)
    a = Anim('attack2', 15)
    a.key(0, chest=(8, 0, 40), upperarm_R=(-55, -10, -55), forearm_R=(-25, 0, 0), loc={'hips': (0, -0.05, -0.05)})
    a.key(2, chest=(6, 0, 55), spine=(4, 0, 15), upperarm_R=(-40, -25, -70), forearm_R=(-60, 0, 0), loc={'hips': (0, -0.04, -0.05)})
    a.key(5, hips=(0, 0, -8), chest=(4, 0, -15), upperarm_R=(-65, 50, 10), forearm_R=(-5, 0, 0), thigh_L=(-25, 0, 0), shin_L=(20, 0, 0),
          thigh_R=(15, 0, 0), shin_R=(12, 0, 0), loc={'hips': (0, -0.09, -0.06)}, cape1=(14, 0, -6))
    a.key(7, hips=(0, 0, -14), chest=(2, 0, -40), spine=(4, 0, -12), upperarm_R=(-30, 80, 20), forearm_R=(-10, 0, 0),
          thigh_L=(-26, 0, 0), shin_L=(22, 0, 0), thigh_R=(16, 0, 0), loc={'hips': (0, -0.1, -0.07)})
    a.key(11, chest=(0, 0, -20), upperarm_R=(-20, 40, 0), forearm_R=(-30, 0, 0), loc={'hips': (0, -0.05, -0.03)})
    a.key(15, **ready)
    A.append(a)
    a = Anim('attack3', 22)
    a.key(0, **ready)
    a.key(4, upperarm_R=(-170, 10, 0), forearm_R=(-40, 0, 0), chest=(-12, 0, 0), head=(-10, 0, 0), upperarm_L=(-60, -20, 0), forearm_L=(-30, 0, 0),
          thigh_R=(-10, 0, 0), thigh_L=(10, 0, 0), loc={'hips': (0, 0.02, 0.02)})
    a.key(7, upperarm_R=(-175, 10, 0), forearm_R=(-25, 0, 0), chest=(-8, 0, 0), upperarm_L=(-70, -25, 0), forearm_L=(-30, 0, 0),
          thigh_R=(-40, 0, 0), shin_R=(60, 0, 0), thigh_L=(-10, 0, 0), shin_L=(70, 0, 0), loc={'hips': (0, -0.10, 0.10)}, cape1=(30, 0, 0), cape2=(20, 0, 0))
    a.key(9, upperarm_R=(-40, 5, 0), forearm_R=(-5, 0, 0), chest=(30, 0, 0), spine=(15, 0, 0), head=(10, 0, 0), upperarm_L=(10, -30, 0),
          thigh_R=(-55, 0, 0), shin_R=(75, 0, 0), foot_R=(-15, 0, 0), thigh_L=(20, 0, 0), shin_L=(60, 0, 0), foot_L=(30, 0, 0),
          loc={'hips': (0, -0.22, -0.18)}, cape1=(-10, 0, 0), cape2=(-6, 0, 0))
    a.key(14, upperarm_R=(-38, 5, 0), forearm_R=(-8, 0, 0), chest=(26, 0, 0), spine=(14, 0, 0), head=(8, 0, 0), upperarm_L=(5, -28, 0),
          thigh_R=(-52, 0, 0), shin_R=(72, 0, 0), foot_R=(-12, 0, 0), thigh_L=(18, 0, 0), shin_L=(58, 0, 0), foot_L=(28, 0, 0),
          loc={'hips': (0, -0.21, -0.16)}, cape1=(4, 0, 0))
    a.key(22, **ready)
    A.append(a)
    # ---- roll
    tuck = dict(spine=(30, 0, 0), chest=(30, 0, 0), head=(35, 0, 0), thigh_R=(-110, 0, 0), shin_R=(130, 0, 0), thigh_L=(-110, 0, 0),
                shin_L=(130, 0, 0), upperarm_R=(-60, 10, 0), forearm_R=(-90, 0, 0), upperarm_L=(-60, -10, 0), forearm_L=(-90, 0, 0), cape1=(30, 0, 0))
    a = Anim('roll', 16)
    a.key(0)
    a.key(2, loc={'hips': (0, -0.1, -0.35)}, hips=(40, 0, 0), spine=(30, 0, 0), chest=(20, 0, 0), head=(20, 0, 0), thigh_R=(-80, 0, 0),
          shin_R=(110, 0, 0), thigh_L=(-80, 0, 0), shin_L=(110, 0, 0), upperarm_R=(-60, 10, 0), forearm_R=(-90, 0, 0),
          upperarm_L=(-60, -10, 0), forearm_L=(-90, 0, 0))
    a.key(5, loc={'hips': (0, -0.2, -0.55)}, hips=(130, 0, 0), **tuck)
    a.key(8, loc={'hips': (0, -0.25, -0.55)}, hips=(250, 0, 0), **tuck)
    t2 = dict(tuck)
    t2.update(thigh_R=(-70, 0, 0), shin_R=(100, 0, 0), thigh_L=(-70, 0, 0), shin_L=(100, 0, 0))
    a.key(11, loc={'hips': (0, -0.15, -0.35)}, hips=(360, 0, 0), **t2)
    a.key(13, loc={'hips': (0, -0.05, -0.15)}, hips=(20, 0, 0), spine=(10, 0, 0), thigh_R=(-30, 0, 0), shin_R=(50, 0, 0), thigh_L=(-30, 0, 0),
          shin_L=(50, 0, 0), upperarm_R=(-30, 10, 0), forearm_R=(-50, 0, 0), upperarm_L=(-30, -10, 0), forearm_L=(-50, 0, 0))
    a.key(16)
    A.append(a)
    # ---- hurt, death
    a = Anim('hurt', 12)
    a.key(0)
    a.key(2, chest=(-18, 0, 8), spine=(-8, 0, 0), head=(-15, 0, 0), upperarm_R=(15, 25, 0), upperarm_L=(15, -25, 0), loc={'hips': (0, 0.05, 0)}, cape1=(-10, 0, 0))
    a.key(6, chest=(-8, 0, 3), head=(-5, 0, 0), upperarm_R=(5, 10, 0), upperarm_L=(5, -10, 0), loc={'hips': (0, 0.02, 0)})
    a.key(12)
    A.append(a)
    a = Anim('death', 45)
    a.key(0)
    a.key(6, chest=(-20, 0, 0), head=(-20, 0, 0), upperarm_R=(15, 25, 0), upperarm_L=(15, -25, 0), loc={'hips': (0, 0.05, 0)})
    kneel = dict(thigh_R=(-85, 0, 0), shin_R=(95, 0, 0), foot_R=(30, 0, 0), thigh_L=(-85, 0, 0), shin_L=(95, 0, 0), foot_L=(30, 0, 0),
                 chest=(20, 0, 0), head=(25, 0, 0), upperarm_R=(5, 10, 0), upperarm_L=(5, -10, 0))
    a.key(14, loc={'hips': (0, 0, -0.45)}, **kneel)
    a.key(24, loc={'hips': (0, 0, -0.46)}, **kneel)
    a.key(34, loc={'hips': (0, -0.45, -0.78)}, hips=(80, 0, 0), spine=(10, 0, 0), chest=(5, 0, 0), head=(10, 0, 0), thigh_R=(-10, 0, 0),
          shin_R=(20, 0, 0), thigh_L=(-12, 0, 0), shin_L=(25, 0, 0), upperarm_R=(-150, 30, 0), upperarm_L=(-150, -30, 0))
    a.key(45, loc={'hips': (0, -0.46, -0.80)}, hips=(84, 0, 0), spine=(10, 0, 0), chest=(5, 0, 0), head=(14, 0, 0), thigh_R=(-10, 0, 0),
          shin_R=(20, 0, 0), thigh_L=(-12, 0, 0), shin_L=(25, 0, 0), upperarm_R=(-155, 32, 0), upperarm_L=(-155, -32, 0))
    A.append(a)
    # ---- nodding off into the dream, and waking up
    a = Anim('nod', 14)
    a.key(0)
    a.key(5, head=(35, 0, 0), neck=(15, 0, 0), chest=(8, 0, 0), thigh_R=(-8, 0, 0), shin_R=(14, 0, 0), thigh_L=(-8, 0, 0), shin_L=(14, 0, 0),
          loc={'hips': (0, 0, -0.03)})
    a.key(9, head=(40, 0, 0), neck=(16, 0, 0), chest=(8, 0, 0), thigh_R=(-8, 0, 0), shin_R=(14, 0, 0), thigh_L=(-8, 0, 0), shin_L=(14, 0, 0),
          loc={'hips': (0, 0, -0.03)})
    a.key(14)
    A.append(a)
    a = Anim('wake', 12)
    a.key(0, head=(35, 0, 0), neck=(15, 0, 0), chest=(8, 0, 0))
    a.key(4, head=(-12, 0, 0), neck=(-4, 0, 0), chest=(-6, 0, 0), upperarm_R=(10, 20, 0), upperarm_L=(10, -20, 0))
    a.key(12)
    A.append(a)
    # ---- yawn (idle flavour): stretch, yawn, rub an eye
    a = Anim('yawn', 75)
    a.key(0)
    a.key(14, upperarm_R=(-155, 20, 0), forearm_R=(-25, 0, 0), upperarm_L=(-155, -20, 0), forearm_L=(-25, 0, 0), chest=(-10, 0, 0),
          head=(-25, 0, 0), loc={'hips': (0, 0, 0.02)})
    a.key(40, upperarm_R=(-160, 24, 0), forearm_R=(-20, 0, 0), upperarm_L=(-160, -24, 0), forearm_L=(-20, 0, 0), chest=(-12, 0, 0),
          head=(-28, 0, 0), loc={'hips': (0, 0, 0.025)})
    a.key(52, upperarm_R=(-70, -12, 0), forearm_R=(-125, 0, 0), upperarm_L=(-12, -6, 0), forearm_L=(-48, 0, 0), head=(12, 0, -6), chest=(6, 0, 0))
    a.key(62, upperarm_R=(-72, -14, 0), forearm_R=(-122, 0, 0), upperarm_L=(-12, -6, 0), forearm_L=(-48, 0, 0), head=(14, 0, 6), chest=(6, 0, 0))
    a.key(75)
    A.append(a)
    # ---- the Wakefire: hold the lantern out to light something
    a = Anim('use', 18)
    a.key(0)
    a.key(5, upperarm_L=(-85, -5, 0), forearm_L=(-10, 0, 0), chest=(5, 0, -20), spine=(3, 0, -8), thigh_L=(-20, 0, 0), shin_L=(10, 0, 0))
    a.key(12, upperarm_L=(-88, -5, 0), forearm_L=(-8, 0, 0), chest=(5, 0, -22), spine=(3, 0, -8), thigh_L=(-20, 0, 0), shin_L=(10, 0, 0))
    a.key(18)
    A.append(a)
    # ---- holding up a found treasure
    a = Anim('itemget', 40)
    a.key(0)
    a.key(8, upperarm_R=(-170, 8, 0), forearm_R=(-10, 0, 0), head=(-15, 0, 0), chest=(-6, 0, 0), upperarm_L=(-20, -15, 0), forearm_L=(-40, 0, 0))
    a.key(40, upperarm_R=(-172, 8, 0), forearm_R=(-8, 0, 0), head=(-16, 0, 0), chest=(-7, 0, 0), upperarm_L=(-20, -15, 0), forearm_L=(-40, 0, 0))
    A.append(a)
    # ---- pushing a block
    a = Anim('push', 24, True)
    lean = dict(hips=(15, 0, 0), spine=(15, 0, 0), chest=(8, 0, 0), upperarm_R=(-80, 5, 0), forearm_R=(-30, 0, 0), upperarm_L=(-80, -5, 0), forearm_L=(-30, 0, 0))
    a.key(0, thigh_R=(-20, 0, 0), shin_R=(20, 0, 0), thigh_L=(25, 0, 0), shin_L=(10, 0, 0), foot_L=(20, 0, 0), loc={'hips': (0, 0.06, -0.06)}, **lean)
    a.mirrored(12, {0})
    A.append(a)
    # ---- shield up
    a = Anim('block', 8)
    a.key(0)
    a.key(4, upperarm_L=(-62, -30, 0), forearm_L=(-85, 0, 35), chest=(4, 0, -12), thigh_L=(-15, 0, 0), shin_L=(15, 0, 0), thigh_R=(10, 0, 0),
          shin_R=(15, 0, 0), loc={'hips': (0, 0, -0.04)})
    a.key(8, upperarm_L=(-62, -30, 0), forearm_L=(-85, 0, 35), chest=(4, 0, -12), thigh_L=(-15, 0, 0), shin_L=(15, 0, 0), thigh_R=(10, 0, 0),
          shin_R=(15, 0, 0), loc={'hips': (0, 0, -0.04)})
    A.append(a)
    # ---- conversation gestures
    a = Anim('shrug', 26)
    a.key(0)
    a.key(8, upperarm_R=(-10, 30, 0), forearm_R=(-85, 0, -35), upperarm_L=(-10, -30, 0), forearm_L=(-85, 0, 35), chest=(-4, 0, 0), head=(0, 0, 9))
    a.key(17, upperarm_R=(-10, 32, 0), forearm_R=(-88, 0, -38), upperarm_L=(-10, -32, 0), forearm_L=(-88, 0, 38), chest=(-4, 0, 0), head=(0, 0, 10))
    a.key(26)
    A.append(a)
    a = Anim('point', 24)
    a.key(0)
    a.key(6, upperarm_R=(-85, 12, 0), forearm_R=(-4, 0, 0), chest=(0, 0, 10))
    a.key(18, upperarm_R=(-86, 12, 0), forearm_R=(-4, 0, 0), chest=(0, 0, 10))
    a.key(24)
    A.append(a)
    a = Anim('sigh', 40)
    a.key(0)
    a.key(12, chest=(-7, 0, 0), head=(-6, 0, 0), loc={'hips': (0, 0, 0.012)})
    a.key(26, chest=(12, 0, 0), spine=(4, 0, 0), head=(16, 0, 0), upperarm_R=(6, 3, 0), upperarm_L=(6, -3, 0), loc={'hips': (0, 0, -0.01)})
    a.key(40)
    A.append(a)
    # ---- drowsiness runs out: he falls asleep on his feet and jolts awake
    a = Anim('doze', 54)
    a.key(0)
    a.key(12, head=(40, 0, 0), neck=(12, 0, 0), chest=(12, 0, 0), upperarm_R=(6, 2, 0), upperarm_L=(6, -2, 0))
    a.key(24, head=(44, 0, 10), neck=(12, 0, 0), chest=(14, 0, 0), spine=(0, 6, 0), thigh_R=(-10, 0, 0), shin_R=(20, 0, 0), thigh_L=(-10, 0, 0),
          shin_L=(20, 0, 0), loc={'hips': (0, 0, -0.06)})
    a.key(33, head=(46, 0, -8), neck=(12, 0, 0), chest=(15, 0, 0), spine=(0, -6, 0), thigh_R=(-10, 0, 0), shin_R=(20, 0, 0), thigh_L=(-10, 0, 0),
          shin_L=(20, 0, 0), loc={'hips': (0, 0, -0.07)})
    a.key(38, head=(-16, 0, 0), neck=(-6, 0, 0), chest=(-8, 0, 0), upperarm_R=(20, 30, 0), upperarm_L=(20, -30, 0), loc={'hips': (0, 0, 0.03)})
    a.key(54)
    A.append(a)
    return A


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
    wf.apply_anims(ao, anims())
    return ao


if __name__ == "__main__":
    ao = build()
    if "check" in sys.argv:
        out = "/tmp/wfblend"
        os.makedirs(out, exist_ok=True)
        wf.check_render(f"{out}/azar_front.png", 360, (12, 0, 0), dist=4.6)
        wf.check_render(f"{out}/azar_34.png", 360, (48, 0, 35), dist=4.6)
        wf.check_render(f"{out}/azar_back.png", 360, (20, 0, 160), dist=4.6)
    else:
        wf.export_fbx(OUT)
        print("exported", OUT)
