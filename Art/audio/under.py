"""What the Underbed sounds like: one long arm coming out across a stone floor, fingernails, a grip,
and the place under every bed.

  python3 under.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S


def knuckle(seed, d=0.035):
    """One joint, cracking: a dry tick with a little bone in it."""
    r = np.random.default_rng(500 + seed)
    f = r.uniform(900, 1700)
    return (S.tone(f, d, ((1, 1), (2.6, 0.4)), decay=d * 0.3) * 0.6 + S.bp(S.noise(d), 1800, 6000) * S.env(d, 0.0004, 0.006)) * r.uniform(0.5, 1.0)


def drag(d, lo=180, hi=1100, grain=38.0):
    """Something dry going across stone: band noise that catches and lets go."""
    t = S.t_(d)
    catch = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * grain * t + 3 * np.sin(2 * np.pi * 2.3 * t)))
    return S.bp(S.noise(d), lo, hi) * catch


def build_sfx():
    s = S.save
    # it comes out: a long dry slide, and the elbows unfolding one after another
    d = 0.9
    t = S.t_(d)
    slide = drag(d) * np.sin(np.pi * t / d) ** 0.8 * 0.7
    s('reach_out', S.room(S.mix(slide, *[S.at(knuckle(k) * 0.7, 0.08 + 0.095 * k) for k in range(8)]), 0.3, 0.9), 0.55)
    # fingers drumming on the flags at the edge of the light: four nails, little finger first
    s('reach_tap', S.room(S.mix(*[S.at(knuckle(20 + k, 0.03) * (0.6 + 0.12 * k), 0.058 * k) for k in range(4)],
                                *[S.at(S.lp(S.noise(0.02), 500) * S.env(0.02, 0.0005, 0.006) * 0.8, 0.058 * k) for k in range(4)]), 0.25, 0.6), 0.4)
    # the grip: every knuckle at once, and the thud of a hand shutting on something
    s('reach_grab', S.room(S.mix(S.lp(S.noise(0.12), 260) * S.env(0.12, 0.001, 0.04) * 2.2, *[S.at(knuckle(30 + k) * 0.9, 0.006 * k) for k in range(7)],
                                 S.at(drag(0.25, 300, 1500, 55) * S.env(0.25, 0.01, 0.08) * 0.5, 0.05)), 0.3, 0.7), 0.8)
    # a man being pulled across a floor by the ankle: one heave
    d = 0.42
    t = S.t_(d)
    s('reach_drag', S.room(S.mix(drag(d, 140, 800, 26) * np.sin(np.pi * t / d) ** 1.5, S.lp(S.noise(0.08), 200) * S.env(0.08, 0.002, 0.03) * 1.2), 0.25, 0.6), 0.5)
    # cut: it has no mouth to say so with. The whole arm goes back over the stone at once, joints first.
    d = 0.5
    t = S.t_(d)
    s('reach_hurt', S.room(S.mix(drag(d, 300, 2200, 70) * S.env(d, 0.004, 0.14), *[S.at(knuckle(40 + k) * 0.8, 0.02 + 0.03 * k) for k in range(6)]), 0.3, 0.8), 0.7)
    # gone under for good: the slide, slower, and something heavy settling a long way off under the floor
    d = 1.3
    t = S.t_(d)
    settle = S.at(S.lp(S.noise(0.5), 120) * S.env(0.5, 0.02, 0.2) * 2.4, 0.75)
    s('reach_gone', S.room(S.mix(drag(d, 160, 900, 22) * np.exp(-t * 2.2) * 0.9, settle, *[S.at(knuckle(50 + k) * 0.5, 0.1 + 0.11 * k) for k in range(6)]), 0.4, 1.4), 0.7)
    # under the bed: the light going, the floor going, and the sound a room makes from underneath
    d = 1.1
    t = S.t_(d)
    whoosh = S.bp(S.noise(d), 90, 700) * np.sin(np.pi * t / d) ** 0.6 * (1 - 0.5 * t / d)
    hollow = S.sweep(140, 52, d) * np.sin(np.pi * t / d) * 0.5
    s('under_take', S.room(S.mix(whoosh, hollow, S.lp(S.noise(0.1), 300) * S.env(0.1, 0.001, 0.04) * 1.5), 0.5, 1.6), 0.85)
    # ...and out again, from under another one: the same, the other way up, and a body arriving on flagstones
    d = 0.6
    t = S.t_(d)
    s('under_out', S.room(S.mix(S.bp(S.noise(d), 120, 900) * (t / d) ** 1.5 * np.exp(-(d - t) * 3), S.sweep(60, 150, d) * (t / d) * 0.4,
                                S.at(S.lp(S.noise(0.14), 220) * S.env(0.14, 0.001, 0.05) * 2.4, d - 0.05)), 0.4, 1.0), 0.8)


def build_bed():
    s = S.save
    # the bed shaking on its two walls: stone knocking on stone, faster and faster
    parts, t = [], 0.0
    for k in range(14):
        parts.append(S.at(S.mix(S.lp(S.noise(0.05), 420) * S.env(0.05, 0.001, 0.016) * (1.0 + 0.06 * k), knuckle(60 + k) * 0.3), t))
        t += max(0.035, 0.11 - 0.006 * k)
    s('bed_rattle', S.room(S.mix(*parts, drag(0.9, 90, 500, 18) * 0.5), 0.35, 0.9), 0.8)
    # it comes up on its hands: a long creak and every elbow at once
    d = 0.5
    t = S.t_(d)
    creak = S.bp(S.sweep(110, 260, d, 'saw') * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * t)), 100, 1200) * S.env(d, 0.1, 0.2)
    s('bed_hop', S.room(S.mix(creak * 0.9, *[S.at(knuckle(80 + k) * 0.8, 0.02 * k) for k in range(8)]), 0.3, 0.8), 0.75)
    # ...and down: a slab of stone, flat, from the height of a man
    thud = S.lp(S.noise(0.35), 110) * S.env(0.35, 0.001, 0.12) * 3.4
    crack = S.bp(S.noise(0.1), 500, 3500) * S.env(0.1, 0.0005, 0.03) * 1.2
    s('bed_slam', S.room(S.mix(thud, crack, S.tone(73.4, 0.5, ((1, 1), (2.1, 0.5), (3.3, 0.2)), decay=0.16) * 1.2), 0.45, 1.6), 0.95)
    # out of breath, with no mouth: all the air under it going out at once through the gap at the foot
    d = 1.4
    t = S.t_(d)
    s('bed_winded', S.room(S.bp(S.noise(d), 160, 1100) * np.exp(-t * 2.4) * (0.7 + 0.3 * np.sin(2 * np.pi * 6 * t)) + S.sweep(120, 60, d) * np.exp(-t * 3) * 0.4, 0.4, 1.2), 0.7)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        S.OUT = os.path.join(sys.argv[1], 'Audio')
    os.makedirs(S.OUT, exist_ok=True)
    build_sfx()
    build_bed()
    print('underbed sounds ->', S.OUT)
