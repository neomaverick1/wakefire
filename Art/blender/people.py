"""The people of Ashkel, built like Azar (pixel units, sprite proportions, same rig) from a
recipe: build, clothes, hair, beard, headwear and what they carry. Sleepers have closed eyes.
Also the animations only townsfolk need: asleep on their feet, sleepwalking, kneading dough,
a dream-self's lively talking, and lying down."""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from wf import Builder, Anim, hexc, METAL, GLOW, D2R
from mathutils import Vector, Matrix, Euler
import azar
import azar_px

BONES = azar_px.BONES

DEFAULT = dict(skin='#d79e72', skin_d='#a8704c', hair='#2a1d28', hair_style='short', beard=None, beard_col=None,
               eyes='closed', tunic='#5a6a3a', tunic_d='#3e4a28', robe=False, trim='#c8a24a', belt='#6a4026',
               boots='#5a3420', headwear=None, head_col='#d0913f', cloak=None, cloak_d=None, width=1.0, belly=0.0,
               apron=None, carry=None, sash=None, height=1.0)


def person(b: Builder, **kw):
    P = dict(DEFAULT)
    P.update(kw)
    hexc = (lambda h, a=None: wf.hexc(h, METAL)) if P.get('metal') else wf.hexc
    SK, SKD = hexc(P['skin']), hexc(P['skin_d'])
    HAIR = hexc(P['hair'])
    TU, TUD = hexc(P['tunic']), hexc(P['tunic_d'])
    TRIM = hexc(P['trim'])
    W = P['width']
    BEL = P['belly']
    EYE = hexc('#1a1016')
    # head and face
    b.ellipsoid((0, -0.2, 25.6), (5.4, 5.0, 5.4), 14, 9, SK, True, 'head')
    for s in (-1, 1):
        b.box((s * 2.2, -5.0, 26.1), (1.8, 0.7, 0.35), hexc(P['beard_col'] or P['hair']), 'head', rot=(0, s * 10, 0))
        b.ellipsoid((s * 5.3, 0.0, 25.4), (0.9, 1.3, 1.6), 6, 4, SKD, True, 'head')
    b.box((0, -5.5, 24.6), (1.2, 1.3, 1.9), SKD, 'head', taper=0.6)
    b.box((0, -4.7, 22.6), (2.0, 0.6, 0.4), hexc('#6a2e2a'), 'head')
    # hair
    style = P['hair_style']
    if style in ('short', 'long', 'bun', 'curly'):
        h0 = len(b.f)
        b.ellipsoid((0, 0.9, 28.0), (5.85, 6.0, 3.7 if style != 'curly' else 4.2), 14, 9, HAIR, True, 'head')
        keep = []
        for i, f in enumerate(b.f):
            if i < h0:
                keep.append(f)
                continue
            c = sum((b.v[k] for k in f[0]), Vector()) / len(f[0])
            if c.y < -1.4 and c.z < 28.6:
                continue
            keep.append(f)
        b.f = keep
        if style == 'long':
            b.loft([((0, 2.5, 27.5), 5.6, 3.6), ((0, 3.4, 22.0), 5.8, 3.4), ((0, 3.6, 18.5), 5.0, 2.6)], 12, HAIR, True, 'head',
                   arc=(100, 260), double=True)
        if style == 'bun':
            b.ellipsoid((0, 4.2, 29.5), (2.4, 2.2, 2.2), 8, 5, HAIR, True, 'head')
    if P['beard']:
        bc = hexc(P['beard_col'] or P['hair'])
        if P['beard'] == 'full':
            b.ellipsoid((0, -2.4, 21.6), (5.0, 3.2, 3.2), 12, 6, bc, True, 'head')
            b.box((0, -4.6, 19.6), (4.4, 1.6, 3.4), bc, 'head', taper=0.5)
            b.box((0, -5.2, 23.0), (3.2, 0.8, 0.8), bc, 'head')                       # moustache
        elif P['beard'] == 'long':
            b.ellipsoid((0, -2.4, 21.4), (4.6, 3.0, 3.0), 12, 6, bc, True, 'head')
            b.box((0, -4.0, 17.4), (3.6, 1.6, 6.0), bc, 'head', taper=0.35)
        elif P['beard'] == 'stubble':
            b.ellipsoid((0, -1.7, 21.7), (3.7, 3.3, 1.6), 12, 6, hexc('#b98060'), True, 'head')
    hw = P['headwear']
    HC = hexc(P['head_col'], METAL if hw in ('helmet',) else 1.0)
    if hw == 'helmet':      # bronze conical helmet with cheek guards
        b.loft([((0, 0.6, 27.0), 6.1, 6.2), ((0, 0.6, 29.0), 5.6, 5.8), ((0, 0.8, 31.5), 3.6, 3.8), ((0, 1.0, 34.0), 0.8, 0.8)], 14, HC,
               False, 'head', True, True)
        b.loft([((0, 0.6, 27.0), 6.3, 6.4), ((0, 0.6, 27.8), 6.3, 6.4)], 14, hexc('#ffd47a', METAL), False, 'head', False, False)
        for s in (-1, 1):
            b.box((s * 5.0, -2.6, 23.8), (1.2, 2.6, 4.6), HC, 'head')
    elif hw == 'turban':
        b.loft([((0, 0.6, 26.8), 6.0, 6.0), ((0, 0.6, 29.0), 6.4, 6.4), ((0, 0.8, 31.2), 5.0, 5.0), ((0, 0.8, 32.0), 2.0, 2.0)], 14, HC,
               True, 'head', True, True)
        b.loft([((0, 0.6, 28.4), 6.5, 6.5), ((0, 0.6, 29.2), 6.5, 6.5)], 14, TRIM, True, 'head', False, False)
    elif hw == 'scarf':
        b.loft([((0, 0.8, 27.2), 6.0, 6.2), ((0, 0.8, 30.4), 5.2, 5.4), ((0, 1.0, 31.8), 2.6, 2.8)], 14, HC, True, 'head', True, True)
        b.loft([((0, 2.0, 27.5), 5.8, 4.0), ((0, 3.0, 21.0), 6.2, 3.8), ((0, 3.2, 17.0), 6.4, 3.4)], 12, HC, True, 'head',
               arc=(95, 265), double=True)
    elif hw == 'priest':
        b.loft([((0, 0.6, 27.0), 5.8, 5.8), ((0, 0.6, 31.0), 6.4, 6.4), ((0, 0.6, 37.0), 7.2, 7.2), ((0, 0.6, 37.6), 6.0, 6.0)], 14, HC,
               False, 'head', True, True)
        for z in (29.0, 33.0):
            b.loft([((0, 0.6, z), 6.6 + (z - 27) * 0.15, 6.6 + (z - 27) * 0.15), ((0, 0.6, z + 0.9), 6.7 + (z - 27) * 0.15, 6.7 + (z - 27) * 0.15)],
                   14, hexc('#ffd47a', METAL), False, 'head', False, False)
    elif hw == 'horned':
        # the crown of a god: a gold band with three pairs of horns curving up its sides
        b.loft([((0, 0.6, 27.2), 6.0, 6.1), ((0, 0.6, 30.6), 5.8, 5.9), ((0, 0.8, 31.4), 3.0, 3.0)], 14, HC, True, 'head', True, True)
        for k, z in enumerate((27.8, 29.0, 30.2)):
            for sd in (-1, 1):
                p0 = Vector((sd * 5.6, -1.0, z)); p1 = Vector((sd * 7.6, -1.6, z + 2.4)); p2 = Vector((sd * 7.0, -2.4, z + 5.0))
                b.limb(p0, p1, [0.8, 0.6], 6, wf.hexc('#fff0c0', METAL), True, 'head')
                b.limb(p1, p2, [0.6, 0.25], 6, wf.hexc('#fff0c0', METAL), True, 'head')
    elif hw == 'cap':
        b.loft([((0, 0.6, 27.2), 6.0, 6.1), ((0, 0.8, 29.8), 5.2, 5.4), ((0, 1.0, 31.2), 2.6, 2.8)], 14, HC, True, 'head', True, True)
    # torso
    b.loft([((0, 0, 13.4), 5.4 * W + BEL, 3.8 * W + BEL), ((0, 0, 15.5), 5.6 * W + BEL * 1.4, 3.9 * W + BEL * 1.4),
            ((0, 0, 17.0), 5.9 * W + BEL, 4.0 * W + BEL)], 14, TU, True, 'spine')
    b.loft([((0, 0, 17.0), 5.9 * W + BEL, 4.0 * W + BEL), ((0, 0, 19.0), 6.6 * W, 4.1 * W), ((0, 0, 20.4), 5.0 * W, 3.6 * W),
            ((0, 0, 21.0), 2.8, 2.4)], 14, TU, True, 'chest')
    b.loft([((0, 0, 13.0), 5.6 * W + BEL, 3.95 * W + BEL), ((0, 0, 14.4), 5.6 * W + BEL, 3.95 * W + BEL)], 14, hexc(P['belt']), False,
           'hips', False, False)
    if P['sash']:
        b.loft([((0, 0, 14.4), 5.7 * W + BEL, 4.0 * W + BEL), ((0, 0, 15.6), 5.7 * W + BEL, 4.0 * W + BEL)], 14, hexc(P['sash']), True,
               'spine', False, False)
    if P['robe']:
        b.loft([((0, 0, 13.4), 5.4 * W + BEL, 3.8 * W + BEL), ((0, 0.1, 9.0), 6.4 * W + BEL * 0.6, 4.6 * W + BEL * 0.6),
                 ((0, 0.2, 4.0), 7.0 * W, 5.2 * W), ((0, 0.3, 0.8), 7.4 * W, 5.6 * W)], 14, TU, True, 'hips', False, False)
        b.loft([((0, 0.3, 1.6), 7.35 * W, 5.55 * W), ((0, 0.3, 0.8), 7.4 * W, 5.6 * W)], 14, TRIM, False, 'hips', False, False)
    else:
        b.loft([((0, 0, 13.4), 5.4 * W + BEL, 3.8 * W + BEL), ((0, 0, 12.0), 5.8 * W + BEL, 4.1 * W + BEL), ((0, 0.1, 10.0), 6.4 * W, 4.6 * W),
                ((0, 0.2, 8.4), 6.8 * W, 5.0 * W)], 14, TU, True, 'hips', False, False)
        b.loft([((0, 0.2, 8.9), 6.75 * W, 4.95 * W), ((0, 0.2, 8.4), 6.8 * W, 5.0 * W)], 14, TUD, False, 'hips', False, False)
    if P.get('stars'):
        # a robe of night sky: gold stars sewn all over it
        import random
        rnd = random.Random(7)
        for i in range(70):
            z = rnd.uniform(1.5, 20.0)
            a = rnd.uniform(-120, 120) * D2R
            t = min(1.0, max(0.0, (13.4 - z) / 12.6)) if z < 13.4 else 0.0
            rx = (5.4 + t * 2.0) * W + BEL * (0.6 if z < 13.4 else 1.0)
            ry = (3.8 + t * 1.8) * W + BEL * (0.6 if z < 13.4 else 1.0)
            if z >= 13.4:
                rx, ry = 6.0 * W + BEL, 4.0 * W + BEL
            grp = 'hips' if z < 13.4 else ('spine' if z < 17 else 'chest')
            big = rnd.random() < 0.18
            b.box((math.sin(a) * (rx + 0.2), -math.cos(a) * (ry + 0.2), z), (0.9 if big else 0.6, 0.6, 0.9 if big else 0.6),
                  wf.hexc('#fff0b0' if big else '#f6c85a', GLOW), grp)
    if P['apron']:
        b.box((0, -4.6 * W - BEL, 10.5), (7.0, 0.8, 8.0), hexc(P['apron']), 'hips', rot=(-6, 0, 0))
        b.box((0, -4.3 * W - BEL, 16.0), (5.0, 0.8, 4.0), hexc(P['apron']), 'spine')
    # arms and legs
    for s, side in ((-1, 'R'), (1, 'L')):
        sh, el, wr = Vector((s * 7.2 * W, 0, 19)), Vector((s * 7.8 * W, 0, 15)), Vector((s * 8.0 * W, -0.5, 11))
        b.limb(sh, el, [2.0 * W, 1.8 * W, 1.6 * W], 8, TU if P['robe'] else SK, True, 'upperarm.' + side)
        b.limb(el, wr, [1.7 * W, 1.6 * W, 1.4 * W], 8, SK, True, 'forearm.' + side)
        b.ellipsoid((s * 8.0 * W, -0.6, 9.9), (1.9, 2.0, 2.1), 8, 5, SK, True, 'hand.' + side)
        if not P['robe']:
            hip, knee, ank = Vector((s * 2.8, 0, 12)), Vector((s * 2.9, 0, 7)), Vector((s * 2.9, 0.3, 2.2))
            b.limb(hip, knee, [2.3, 2.2, 2.0], 8, SK, True, 'thigh.' + side)
            b.limb(knee, ank, [2.0, 1.9, 1.6], 8, SK, True, 'shin.' + side)
        b.box((s * 2.95, -1.0, 1.2), (3.8, 6.4, 2.6), hexc(P['boots']), 'foot.' + side, taper=0.85)
    if P['cloak']:
        C, CD = hexc(P['cloak']), hexc(P['cloak_d'] or P['cloak'])
        b.loft([((0, 0.6, 21.6), 3.6, 3.2), ((0, 0.6, 20.8), 7.2 * W, 4.8 * W), ((0, 0.8, 19.0), 9.0 * W, 5.6 * W), ((0, 1.0, 17.6), 9.3 * W, 5.9 * W)],
               16, C, True, 'chest', arc=(-148, 148), double=True, color_in=CD)
        b.loft([((0, 1.4, 19.6), 6.6 * W, 4.2 * W), ((0, 1.8, 16.4), 7.6 * W, 5.2 * W), ((0, 2.0, 13.0), 8.0 * W, 5.6 * W)], 14, C, True, 'cape1',
               arc=(108, 252), double=True, color_in=CD)
        b.loft([((0, 2.0, 13.0), 8.0 * W, 5.6 * W), ((0, 2.3, 9.0), 8.6 * W, 6.1 * W), ((0, 2.6, 5.4), 9.0 * W, 6.6 * W)], 14, CD, True, 'cape2',
               arc=(108, 252), double=True, color_in=CD)
    # what they carry
    c = P['carry']
    if c == 'spear':
        sx = -(8.0 * W + 0.8)
        b.limb((sx, -1.6, 0.0), (sx, -1.6, 34.0), [0.6, 0.6], 6, hexc('#7a4a2a'), False, 'root')
        b.box((sx, -1.6, 35.4), (1.8, 0.9, 3.4), hexc('#ffd47a', METAL), 'root', taper=0.1)
        b.box((sx, -1.6, 33.6), (1.3, 1.3, 0.8), hexc('#a2672a', METAL), 'root')
    elif c == 'spear_held':
        b.limb((-8.0 * W, -1.0, 2.0), (-8.0 * W, -1.0, 33.0), [0.6, 0.6], 6, hexc('#7a4a2a'), False, 'hand.R')
        b.box((-8.0 * W, -1.0, 34.6), (1.8, 0.9, 3.6), wf.hexc('#ffd47a', METAL), 'hand.R', taper=0.1)
        sc = Vector((9.6 * W, -0.8, 13.0))
        M = Matrix.Translation(sc) @ Euler((0, 90 * D2R, 0)).to_matrix().to_4x4()
        b.loft([((0, 0, -0.5), 5.4, 5.4), ((0, 0, 0.0), 5.6, 5.6), ((0, 0, 0.8), 4.0, 4.0), ((0, 0, 1.1), 2.0, 2.0)], 16,
               wf.hexc('#e2a64e', METAL), False, 'forearm.L', True, True, xf=M)
    elif c == 'staff':
        b.limb((8.0 * W, -0.6, -1.0), (8.0 * W, -0.6, 30.0), [0.6, 0.6], 6, hexc('#5a3a26'), False, 'hand.L')
        b.ellipsoid((8.0 * W, -0.6, 31.0), (1.6, 1.6, 1.6), 8, 5, hexc('#ffd47a', METAL), False, 'hand.L')
    elif c == 'bread':
        b.ellipsoid((0, -6.0, 12.5), (4.0, 2.4, 1.8), 10, 5, hexc('#d8a050'), True, 'hand.R')
    elif c == 'pot':
        b.loft([((0, -6.0, 9.0), 2.0, 2.0), ((0, -6.0, 11.5), 3.6, 3.6), ((0, -6.0, 14.5), 2.2, 2.2), ((0, -6.0, 15.4), 1.6, 1.6)], 10,
               hexc('#b8704a'), True, 'hand.R')
    elif c == 'blanket':
        b.box((0, -5.0, 13.0), (9.0, 1.4, 8.0), hexc('#c8bce8'), 'hand.R', rot=(-10, 0, 0))
    elif c == 'net':
        b.ellipsoid((0, -5.5, 12.0), (4.0, 1.6, 3.0), 8, 5, hexc('#a89a70'), True, 'hand.R')


def eyes(b: Builder, mode, P=None):
    """'closed' (asleep), 'open' (awake: tired slits), 'wide' (a frightened child)."""
    EYE = hexc('#1a1016')
    for s in (-1, 1):
        if mode == 'closed':
            b.box((s * 2.1, -4.95, 24.8), (1.8, 0.8, 0.55), hexc('#4a2a26'), 'head')
        elif mode == 'wide':
            b.box((s * 2.1, -4.95, 25.0), (1.3, 0.8, 1.9), EYE, 'head')
            b.box((s * 2.5, -5.05, 25.6), (0.55, 0.6, 0.55), hexc('#fff4e0'), 'head')
        elif mode == 'glow':
            b.box((s * 2.0, -4.95, 24.9), (1.2, 0.8, 1.2), hexc('#ffd060', GLOW), 'head')
        else:
            b.box((s * 2.0, -4.95, 24.9), (0.95, 0.8, 1.45), EYE, 'head')


def npc_anims():
    A = []
    a = Anim('idle', 60, True)       # standing, breathing, arms loose
    a.key(0, upperarm_R=(2, 5, 0), forearm_R=(-10, 0, 0), upperarm_L=(2, -5, 0), forearm_L=(-10, 0, 0), neck=(2, 0, 0), head=(4, 0, 0),
          thigh_R=(-3, 0, 1), shin_R=(5, 0, 0), loc={'hips': (0.006, 0, 0)})
    a.key(30, upperarm_R=(2, 6, 0), forearm_R=(-13, 0, 0), upperarm_L=(2, -6, 0), forearm_L=(-13, 0, 0), chest=(-3, 0, 0), neck=(2, 0, 0),
          head=(1, 0, 2), thigh_R=(-3, 0, 1), shin_R=(6, 0, 0), loc={'hips': (0.006, 0, 0.012)})
    A.append(a)
    a = Anim('sleep', 60, True)      # asleep on their feet: slow sway, head down, deep breaths
    base = dict(neck=(6, 0, 0), upperarm_R=(4, 4, 0), forearm_R=(-10, 0, 0), upperarm_L=(4, -4, 0), forearm_L=(-10, 0, 0),
                thigh_R=(-4, 0, 0), shin_R=(8, 0, 0), thigh_L=(-4, 0, 0), shin_L=(8, 0, 0))
    a.key(0, head=(14, 0, -5), chest=(3, 0, 0), spine=(0, 3, 0), loc={'hips': (0, 0, -0.01)}, **base)
    a.key(30, head=(19, 0, 5), chest=(7, 0, 0), spine=(0, -3, 0), loc={'hips': (0, 0, -0.03)}, **base)
    A.append(a)
    a = Anim('sleepwalk', 40, True)  # shuffling, arms out in front, head lolling
    arms = dict(upperarm_R=(-80, 6, 0), forearm_R=(-6, 0, 0), upperarm_L=(-80, -6, 0), forearm_L=(-6, 0, 0))
    a.key(0, head=(26, 0, 8), thigh_R=(-14, 0, 0), shin_R=(8, 0, 0), thigh_L=(10, 0, 0), shin_L=(14, 0, 0), loc={'hips': (0, 0, -0.01)}, **arms)
    a.key(10, head=(30, 0, 0), thigh_R=(-4, 0, 0), shin_R=(10, 0, 0), thigh_L=(2, 0, 0), shin_L=(24, 0, 0), loc={'hips': (0, 0, 0.01)}, **arms)
    a.mirrored(20, {0, 10})
    A.append(a)
    a = Anim('knead', 24, True)      # pushing dough that isn't there
    a.key(0, upperarm_R=(-50, 4, 0), forearm_R=(-40, 0, 0), upperarm_L=(-30, -4, 0), forearm_L=(-60, 0, 0), chest=(14, 0, 0), head=(20, 0, 0))
    a.key(12, upperarm_R=(-30, 4, 0), forearm_R=(-60, 0, 0), upperarm_L=(-50, -4, 0), forearm_L=(-40, 0, 0), chest=(18, 0, 0), head=(24, 0, 0))
    A.append(a)
    a = Anim('talk', 30, True)       # a dream-self who finally has something to say
    a.key(0, upperarm_R=(-30, 20, 0), forearm_R=(-60, 0, -20), head=(-4, 0, 6), chest=(-3, 0, 4))
    a.key(10, upperarm_R=(-55, 24, 0), forearm_R=(-40, 0, -30), upperarm_L=(-20, -14, 0), forearm_L=(-50, 0, 0), head=(2, 0, -4), chest=(-2, 0, -4))
    a.key(20, upperarm_R=(-20, 16, 0), forearm_R=(-70, 0, -10), upperarm_L=(-35, -20, 0), forearm_L=(-60, 0, 20), head=(-6, 0, 2), chest=(-4, 0, 2))
    A.append(a)
    a = Anim('lie', 60, True)        # asleep on the ground, on one side, facing the viewer, head to the right
    lie = dict(hips=(0, 90, 0), thigh_R=(-24, 0, 0), shin_R=(34, 0, 0), thigh_L=(-14, 0, 0), shin_L=(22, 0, 0),
               upperarm_R=(-46, 0, 0), forearm_R=(-24, 0, 0), upperarm_L=(-70, 0, 0), forearm_L=(-70, 0, 0), neck=(4, 8, 0))
    a.key(0, head=(6, 10, 0), chest=(2, 0, 0), loc={'hips': (-4.0 / 15, 0, -2.6 / 15)}, **lie)
    a.key(30, head=(6, 10, 0), chest=(6, 0, 0), loc={'hips': (-4.0 / 15, 0, -2.6 / 15)}, **lie)
    A.append(a)
    a = Anim('lean', 60, True)       # dozing against his spear, head tipped onto the shaft
    lean = dict(upperarm_R=(-14, 8, 0), forearm_R=(-48, 0, 0), spine=(0, -5, 0), thigh_L=(-6, 0, 0), shin_L=(12, 0, 0),
                upperarm_L=(4, -4, 0), forearm_L=(-12, 0, 0))
    a.key(0, head=(12, -12, -4), neck=(4, -4, 0), chest=(3, -2, 0), loc={'hips': (-0.02, 0, -0.01)}, **lean)
    a.key(30, head=(16, -14, -6), neck=(5, -4, 0), chest=(6, -2, 0), loc={'hips': (-0.02, 0, -0.03)}, **lean)
    A.append(a)
    a = Anim('cower', 40, True)      # a child afraid of the dark, hugging a blanket
    a.key(0, upperarm_R=(-40, -10, 0), forearm_R=(-100, 0, 0), upperarm_L=(-40, 10, 0), forearm_L=(-100, 0, 0), head=(14, 0, 0), chest=(12, 0, 0),
          thigh_R=(-30, 0, 0), shin_R=(50, 0, 0), thigh_L=(-30, 0, 0), shin_L=(50, 0, 0), loc={'hips': (0, 0, -0.12)})
    a.key(20, upperarm_R=(-42, -10, 0), forearm_R=(-102, 0, 0), upperarm_L=(-42, 10, 0), forearm_L=(-102, 0, 0), head=(18, 0, 4), chest=(14, 0, 0),
          thigh_R=(-30, 0, 0), shin_R=(50, 0, 0), thigh_L=(-30, 0, 0), shin_L=(50, 0, 0), loc={'hips': (0, 0, -0.13)})
    A.append(a)
    return A


def build(recipe, scale=1.0):
    """Returns the rig and the eye meshes {'closed': ob, 'open': ob} (one is hidden per render)."""
    wf.reset()
    ao = wf.armature("Rig", BONES)
    P = dict(DEFAULT)
    P.update(recipe)
    parts = {}
    b = Builder()
    person(b, **recipe)
    parts['body'] = b
    for mode in ('closed', 'open') if P['eyes'] not in ('wide', 'glow') else (P['eyes'],):
        e = Builder()
        eyes(e, mode, P)
        parts[mode] = e
    obs = {}
    for k, bb in parts.items():
        if scale != 1.0:
            bb.v = [v * scale for v in bb.v]
        mo = bb.mesh_object("Body" if k == 'body' else "Eyes_" + k)
        wf.bind(mo, ao)
        obs[k] = mo
    walk = [a for a in azar.anims() if a.name == 'walk'][0]
    for (f, r, l) in walk.keys:
        for bn in ('forearm.L', 'forearm.R'):
            if bn in r:
                x, y, z = r[bn]
                r[bn] = (max(x, -16), y, z)
        r.pop('cape1', None)
    anims = [a for a in azar.anims() if a.name in ('shrug', 'point', 'sigh', 'itemget', 'hurt')] + [walk] + npc_anims()
    for a in anims:
        a.keys = [(f, r, {bn: (v[0] * azar_px.LOC_SCALE * scale, v[1] * azar_px.LOC_SCALE * scale, v[2] * azar_px.LOC_SCALE * scale)
                          for bn, v in l.items()}) for (f, r, l) in a.keys]
    if scale != 1.0:
        import bpy
        bpy.context.view_layer.objects.active = ao
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in ao.data.edit_bones:
            eb.head = eb.head * scale
            eb.tail = eb.tail * scale
        bpy.ops.object.mode_set(mode='OBJECT')
    wf.apply_anims(ao, anims)
    return ao, obs


# ------------------------------------------------------------------ the cast
CAST = {
    'captain': dict(width=1.25, belly=0.8, tunic='#3a5a3a', tunic_d='#26402a', skin='#c88d62', hair='#1c1418', beard='full',
                    beard_col='#1c1418', headwear='helmet', head_col='#c88a3c', cloak='#8a2a2e', cloak_d='#5a1a20', carry='spear',
                    eyes='closed', belt='#4a2c1a', boots='#3a2416'),
    'captain_child': dict(width=0.95, tunic='#d8d0f0', tunic_d='#a8a0c8', robe=True, trim='#9a90c0', skin='#e2aa7e', hair='#1c1418',
                          hair_style='curly', carry='blanket', eyes='wide'),
    'baker': dict(width=1.15, belly=1.2, tunic='#b8665a', tunic_d='#8a4a42', skin='#d29468', hair='#5a3a2a', hair_style='bun',
                  headwear='scarf', head_col='#e8e0d0', apron='#ece2cc', eyes='closed', robe=True, trim='#8a4a42'),
    'potter': dict(width=1.0, tunic='#8a6a4a', tunic_d='#5e4630', skin='#b87a52', hair='#cfc6c0', beard='long', beard_col='#d8d0cc',
                   headwear='cap', head_col='#6a5a7a', carry='pot', eyes='closed'),
    'oracle': dict(width=0.95, tunic='#4a3a7a', tunic_d='#2e2456', robe=True, trim='#d8b04a', skin='#c48a62', hair='#e8e4ec',
                   hair_style='long', headwear=None, carry='staff', eyes='closed', sash='#d8b04a'),
    'fisher': dict(width=1.05, tunic='#3a6a8a', tunic_d='#26485e', skin='#a86e48', hair='#2a1d1a', beard='stubble', headwear='turban',
                   head_col='#d8c8a0', carry='net', eyes='closed'),
    'priest': dict(width=1.1, belly=0.6, tunic='#e8dcc0', tunic_d='#b8a888', robe=True, trim='#d8a038', skin='#c48a62', hair='#2a1d1a',
                   beard='long', beard_col='#2a1d1a', headwear='priest', head_col='#e8dcc0', eyes='closed', sash='#b03030'),
    'sleeper_a': dict(tunic='#6a4a7a', tunic_d='#4a3256', skin='#d6a07a', hair='#3a2a1a', eyes='closed'),
    'sleeper_b': dict(tunic='#7a6a3a', tunic_d='#564a28', skin='#b07a52', hair='#1a1418', beard='stubble', headwear='cap',
                      head_col='#a0503a', eyes='closed'),
    'sleeper_c': dict(tunic='#3a6a6a', tunic_d='#264a4a', skin='#e0aa82', hair='#6a3a20', hair_style='long', robe=True, trim='#c8a24a',
                      eyes='closed'),
}
