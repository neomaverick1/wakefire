"""What the Seal sounds like: a barrel of lapis rolling over flagstones, wet clay taking a print, a
spearman as deep as a thumbnail, and stone that has stopped too suddenly.

  python3 seal.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S


def build_sfx():
    s = S.save
    # one length of rolling: heavy stone over the joints of the flags
    d = 0.42
    t = S.t_(d)
    rumble = S.lp(S.noise(d), 150) * np.sin(np.pi * t / d) ** 0.7 * 2.2
    grit = S.bp(S.noise(d), 700, 2600) * np.sin(np.pi * t / d) ** 2 * 0.25
    s('seal_roll', S.room(S.mix(rumble, grit, S.at(S.lp(S.noise(0.05), 260) * S.env(0.05, 0.001, 0.02) * 1.6, 0.20)), 0.25, 0.7), 0.6)
    # a print laid: wet clay taking the pattern, and letting go of the stone
    d = 0.3
    t = S.t_(d)
    squelch = S.bp(S.noise(d), 200, 1400) * S.env(d, 0.02, 0.09) * (0.6 + 0.4 * np.sin(2 * np.pi * 22 * t))
    s('seal_print', S.mix(squelch, S.at(S.sweep(420, 180, 0.08) * S.env(0.08, 0.004, 0.03) * 0.5, 0.16)), 0.55)
    # the print gets up: a leaf of clay peeling off the ground
    d = 0.5
    t = S.t_(d)
    peel = S.bp(S.noise(d), 500, 3200) * (t / d) ** 1.2 * np.exp(-(d - t) * 2.0) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 46 * t)))
    s('print_peel', S.room(S.mix(peel, S.at(S.tone(330, 0.12, ((1, 1), (2.4, 0.4)), decay=0.04) * 0.5, d - 0.06)), 0.2, 0.5), 0.5)
    # the spear: thin clay going through air, and a dry tick where it stops
    s('print_thrust', S.mix(S.hp(S.noise(0.16), 2400) * np.sin(np.pi * S.t_(0.16) / 0.16) ** 2 * 0.8, S.at(S.tone(880, 0.05, ((1, 1), (2.7, 0.5)), decay=0.015) * 0.5, 0.13)), 0.5)
    # one blow: a tile dropped
    parts = [S.lp(S.noise(0.06), 900) * S.env(0.06, 0.0006, 0.02) * 1.4]
    r = np.random.default_rng(700)
    for k in range(9):
        f = r.uniform(500, 1500)
        parts.append(S.at(S.tone(f, 0.05, ((1, 1), (2.3, 0.5)), decay=0.014) * r.uniform(0.2, 0.6), r.uniform(0.01, 0.22)))
    s('print_crumble', S.room(S.mix(*parts), 0.2, 0.5), 0.6)
    # the Seal struck: a blade on a barrel of solid stone, low, and no ring to speak of
    s('seal_knock', S.room(S.mix(S.tone(98, 0.5, ((1, 1), (2.2, 0.6), (3.7, 0.3), (5.3, 0.15)), decay=0.14), S.lp(S.noise(0.05), 2200) * S.env(0.05, 0.0005, 0.012) * 1.2), 0.3, 0.9), 0.85)
    # ...and stopped, all at once, by the end of its beat
    thud = S.lp(S.noise(0.4), 100) * S.env(0.4, 0.001, 0.13) * 3.6
    crack = S.bp(S.noise(0.5), 1200, 6000) * S.env(0.5, 0.0005, 0.03) * 1.5
    tail = S.at(S.bp(S.noise(0.5), 2000, 7000) * S.env(0.5, 0.01, 0.12) * 0.35 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 37 * S.t_(0.5)))), 0.06)
    s('seal_crash', S.room(S.mix(thud, crack, tail, S.tone(65.4, 0.6, ((1, 1), (2.1, 0.5)), decay=0.2) * 1.3), 0.45, 1.6), 0.95)
    # in two: the crack going right through, and two halves settling apart
    d = 1.2
    t = S.t_(d)
    tear = S.bp(S.noise(d), 900, 5000) * np.exp(-t * 5) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (30 + 80 * t) * t)))
    s('seal_split', S.room(S.mix(tear * 1.4, S.lp(S.noise(0.3), 110) * S.env(0.3, 0.001, 0.1) * 3.0, S.at(S.lp(S.noise(0.3), 130) * S.env(0.3, 0.001, 0.1) * 2.4, 0.42),
                                 S.at(S.tone(82.4, 0.7, ((1, 1), (2.3, 0.5), (3.1, 0.3)), decay=0.25), 0.42)), 0.5, 1.8), 0.95)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        S.OUT = os.path.join(sys.argv[1], 'Audio')
    os.makedirs(S.OUT, exist_ok=True)
    build_sfx()
    print('seal sounds ->', S.OUT)
