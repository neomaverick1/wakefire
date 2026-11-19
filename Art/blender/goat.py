"""The goat. A real goat, not a cute one: off-white coat gone grey at the legs, curled horns,
a beard, and the amber eyes with flat black pupils that make it look like it knows something.
It is the only other thing in Ashkel that is awake. Pixel units, faces -Y, Z up."""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from wf import Builder, Anim, hexc
from mathutils import Vector

COAT = hexc('#d9d0bc')
COAT_D = hexc('#a99e8a')
LEG = hexc('#8c7d6a')
HOOF = hexc('#2e2420')
HORN = hexc('#857560')
HORN_L = hexc('#a8987e')
NOSE = hexc('#6a5450')
EYE = hexc('#e0a020')
PUPIL = hexc('#120c10')
BEARD = hexc('#bfb5a0')

BONES = [
    ("root", (0, 0, 0), (0, 0, 2), None),
    ("body", (0, 6.0, 11.5), (0, -4.5, 11.5), "root"),
    ("neck", (0, -4.5, 12.5), (0, -7.6, 16.8), "body"),
    ("head", (0, -7.6, 16.8), (0, -11.8, 15.2), "neck"),
    ("jaw", (0, -9.0, 15.0), (0, -12.4, 13.8), "head"),
    ("tail", (0, 6.6, 12.6), (0, 7.4, 15.0), "body"),
    ("fleg.L", (2.5, -4.2, 9.5), (2.5, -4.4, 4.6), "body"),
    ("fshin.L", (2.5, -4.4, 4.6), (2.5, -4.4, 0.4), "fleg.L"),
    ("fleg.R", (-2.5, -4.2, 9.5), (-2.5, -4.4, 4.6), "body"),
    ("fshin.R", (-2.5, -4.4, 4.6), (-2.5, -4.4, 0.4), "fleg.R"),
    ("bleg.L", (2.5, 4.4, 9.5), (2.5, 5.4, 4.8), "body"),
    ("bshin.L", (2.5, 5.4, 4.8), (2.5, 4.8, 0.4), "bleg.L"),
    ("bleg.R", (-2.5, 4.4, 9.5), (-2.5, 5.4, 4.8), "body"),
    ("bshin.R", (-2.5, 5.4, 4.8), (-2.5, 4.8, 0.4), "bleg.R"),
]


def body(b: Builder):
    # barrel and chest
    b.ellipsoid((0, 0.8, 11.4), (4.0, 7.6, 4.1), 14, 9, COAT, True, 'body')
    b.ellipsoid((0, -3.8, 11.8), (3.6, 3.4, 3.8), 12, 7, COAT, True, 'body')
    b.ellipsoid((0, 5.2, 11.6), (3.7, 2.8, 3.7), 12, 7, COAT, True, 'body')
    b.ellipsoid((0, 0.8, 8.4), (3.0, 6.0, 1.6), 12, 6, COAT_D, True, 'body')      # belly in shadow
    # neck and head
    b.limb((0, -4.6, 12.6), (0, -7.6, 16.8), [2.7, 2.3, 2.0], 10, COAT, True, 'neck')
    b.ellipsoid((0, -8.8, 16.6), (2.2, 2.6, 2.3), 10, 7, COAT, True, 'head')
    b.box((0, -11.2, 15.6), (2.6, 3.6, 2.2), COAT, 'head', rot=(-14, 0, 0), taper=0.85)       # long face
    b.box((0, -12.8, 15.0), (2.0, 0.9, 1.2), NOSE, 'head', rot=(-14, 0, 0))                    # nose
    b.box((0, -11.6, 14.3), (1.8, 2.6, 0.9), COAT_D, 'jaw', rot=(-12, 0, 0))                   # lower jaw
    b.box((0, -11.2, 12.4), (1.3, 1.3, 2.8), BEARD, 'jaw', rot=(-10, 0, 0), taper=0.35)      # beard
    for s in (-1, 1):
        b.box((s * 1.95, -9.6, 17.1), (0.8, 1.5, 1.1), EYE, 'head')                             # amber eye
        b.box((s * 2.2, -9.6, 17.1), (0.5, 1.2, 0.35), PUPIL, 'head')                           # the flat pupil
        b.box((s * 3.1, -8.4, 17.0), (2.6, 1.2, 1.0), COAT_D, 'head', rot=(0, s * -18, s * -20))  # ears out sideways
        # horns sweep up and back, then curl down
        pts = [Vector((s * 1.1, -8.8, 18.4)), Vector((s * 1.5, -7.6, 20.6)), Vector((s * 2.0, -5.8, 21.4)),
               Vector((s * 2.4, -4.4, 20.4)), Vector((s * 2.5, -4.2, 19.0))]
        rad = [0.95, 0.8, 0.62, 0.45, 0.3]
        for i in range(len(pts) - 1):
            b.limb(pts[i], pts[i + 1], [rad[i], rad[i + 1]], 6, HORN if i % 2 == 0 else HORN_L, True, 'head')
    # legs: thin, grey-brown, black hooves
    for s, side in ((1, 'L'), (-1, 'R')):
        b.limb((s * 2.5, -4.2, 10.2), (s * 2.5, -4.4, 4.6), [1.5, 1.2, 1.0], 8, COAT, True, 'fleg.' + side)
        b.limb((s * 2.5, -4.4, 4.6), (s * 2.5, -4.4, 0.8), [1.0, 0.9, 0.85], 8, LEG, True, 'fshin.' + side)
        b.box((s * 2.5, -4.6, 0.5), (1.6, 1.8, 1.0), HOOF, 'fshin.' + side)
        b.limb((s * 2.5, 4.4, 10.2), (s * 2.5, 5.4, 4.8), [1.8, 1.4, 1.0], 8, COAT, True, 'bleg.' + side)
        b.limb((s * 2.5, 5.4, 4.8), (s * 2.5, 4.8, 0.8), [1.0, 0.9, 0.85], 8, LEG, True, 'bshin.' + side)
        b.box((s * 2.5, 4.6, 0.5), (1.6, 1.8, 1.0), HOOF, 'bshin.' + side)
    b.limb((0, 6.8, 12.8), (0, 7.4, 15.0), [0.9, 0.6, 0.3], 6, COAT_D, True, 'tail')


def anims():
    A = []
    a = Anim('idle', 60, True)       # chewing, unbothered
    a.key(0, jaw=(0, 0, 0), head=(0, 0, 0), tail=(0, 0, 0))
    a.key(8, jaw=(6, 0, 4), head=(-2, 0, 0))
    a.key(16, jaw=(0, 0, -4), head=(0, 0, 0))
    a.key(24, jaw=(6, 0, 4), head=(-2, 0, 0))
    a.key(32, jaw=(0, 0, 0), head=(0, 0, 0), tail=(0, 0, 20))
    a.key(46, jaw=(0, 0, 0), head=(0, 0, 0), tail=(0, 0, -20))
    A.append(a)
    a = Anim('stare', 60, True)      # it turns and looks at you. it keeps looking.
    a.key(0, neck=(0, 0, 40), head=(-6, 0, 34), jaw=(0, 0, 0))
    a.key(30, neck=(0, 0, 41), head=(-6, 0, 35), jaw=(3, 0, 0))
    A.append(a)
    a = Anim('walk', 24, True)       # diagonal pairs
    a.key(0, fleg_L=(-24, 0, 0), fshin_L=(10, 0, 0), bleg_R=(-14, 0, 0), bshin_R=(-10, 0, 0),
          fleg_R=(18, 0, 0), fshin_R=(30, 0, 0), bleg_L=(20, 0, 0), bshin_L=(-24, 0, 0), head=(4, 0, 0), loc={'body': (0, 0, 0)})
    a.key(6, fleg_L=(0, 0, 0), bleg_R=(0, 0, 0), fleg_R=(-6, 0, 0), fshin_R=(40, 0, 0), bleg_L=(4, 0, 0), bshin_L=(-30, 0, 0),
          head=(0, 0, 0), loc={'body': (0, 0, 0.6)})
    a.mirrored(12, {0, 6})
    A.append(a)
    a = Anim('eat', 40, True)        # head down in the grass
    a.key(0, neck=(64, 0, 0), head=(30, 0, 0), jaw=(0, 0, 0), fleg_L=(-6, 0, 0), fleg_R=(-6, 0, 0))
    a.key(10, neck=(66, 0, 0), head=(32, 0, 0), jaw=(10, 0, 0), fleg_L=(-6, 0, 0), fleg_R=(-6, 0, 0))
    a.key(20, neck=(64, 0, 0), head=(30, 0, 2), jaw=(0, 0, 0), fleg_L=(-6, 0, 0), fleg_R=(-6, 0, 0))
    a.key(30, neck=(66, 0, 0), head=(32, 0, -2), jaw=(10, 0, 0), fleg_L=(-6, 0, 0), fleg_R=(-6, 0, 0))
    A.append(a)
    a = Anim('bleat', 30)            # head up, mouth wide: MEH.
    a.key(0, neck=(0, 0, 0), head=(0, 0, 0), jaw=(0, 0, 0))
    a.key(6, neck=(-24, 0, 0), head=(-20, 0, 0), jaw=(30, 0, 0))
    a.key(22, neck=(-26, 0, 0), head=(-22, 0, 0), jaw=(32, 0, 0))
    a.key(30, neck=(0, 0, 0), head=(0, 0, 0), jaw=(0, 0, 0))
    A.append(a)
    a = Anim('butt', 20)             # rears, then drives the horns forward
    a.key(0, body=(0, 0, 0))
    a.key(6, body=(-22, 0, 0), neck=(-10, 0, 0), head=(-10, 0, 0), fleg_L=(-40, 0, 0), fleg_R=(-34, 0, 0), fshin_L=(60, 0, 0),
          fshin_R=(60, 0, 0), loc={'body': (0, 1.2, 0)})
    a.key(11, body=(10, 0, 0), neck=(30, 0, 0), head=(36, 0, 0), fleg_L=(-10, 0, 0), fleg_R=(-10, 0, 0), loc={'body': (0, -2.4, -0.4)})
    a.key(20, body=(0, 0, 0))
    A.append(a)
    return A


def build():
    wf.reset()
    ao = wf.armature("Goat", BONES)
    b = Builder()
    body(b)
    mo = b.mesh_object("GoatBody")
    wf.bind(mo, ao)
    wf.apply_anims(ao, anims())
    return ao, {'body': mo}
