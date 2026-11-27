"""What the Debt sounds like: three hundred years of fired clay tablets, stacked into the shape of
a man, walking; and the one word the Sleeping Watch has left.

  python3 collect.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S


def tablet(seed, f=420.0, d=0.10):
    """One fired tablet knocking on another: a short dull clack with a little ring in it."""
    r = np.random.default_rng(300 + seed)
    f *= r.uniform(0.8, 1.25)
    body = S.tone(f, d, ((1, 1), (2.3, 0.5), (3.9, 0.25)), decay=d * 0.35)
    tick = S.bp(S.noise(d), 1500, 4200) * S.env(d, 0.0005, 0.012)
    return (body * 0.7 + tick * 0.6) * r.uniform(0.6, 1.0)


def build_sfx():
    s = S.save
    # it holds out the sum: one tablet drawn off the top of the stack, and set down on the air
    slide = S.bp(S.noise(0.32), 700, 2600) * S.env(0.32, 0.08, 0.10) * 0.5
    s('debt_bill', S.room(S.mix(slide, S.at(tablet(1, 520), 0.30), S.at(tablet(2, 390) * 0.6, 0.38)), 0.2, 0.5), 0.6)
    # the tablet goes up over its head: the whole stack shifts to let it
    s('debt_lift', S.room(S.mix(*[S.at(tablet(10 + k, 300 + 30 * k) * (0.5 + 0.08 * k), 0.07 * k) for k in range(5)],
                                S.bp(S.noise(0.4), 300, 1200) * S.env(0.4, 0.15, 0.12) * 0.35), 0.2, 0.5), 0.55)
    # ...and comes down: clay on stone, flat, with all of it behind it
    thud = S.lp(S.noise(0.22), 180) * S.env(0.22, 0.001, 0.07) * 3.0
    crack = S.bp(S.noise(0.08), 900, 5200) * S.env(0.08, 0.0005, 0.02) * 1.6
    s('debt_slam', S.room(S.mix(thud, crack, S.tone(196, 0.3, ((1, 1), (2.3, 0.5)), decay=0.09) * 0.8,
                                *[S.at(tablet(20 + k, 600 + 90 * k) * 0.35, 0.10 + 0.05 * k) for k in range(4)]), 0.3, 0.8), 0.9)
    # the pieces finding each other: tablets landing on tablets, quicker and quicker, and the last one squared off
    parts, t = [], 0.0
    for k in range(11):
        parts.append(S.at(tablet(40 + k, 260 + 34 * k) * (0.55 + 0.04 * k), t))
        t += max(0.045, 0.16 - 0.011 * k)
    parts.append(S.at(S.bp(S.noise(0.12), 500, 1800) * S.env(0.12, 0.03, 0.04) * 0.5, t + 0.02))
    s('debt_stack', S.room(S.mix(*parts), 0.25, 0.7), 0.7)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        S.OUT = os.path.join(sys.argv[1], 'Audio')
    os.makedirs(S.OUT, exist_ok=True)
    build_sfx()
    print('debt sounds ->', S.OUT)
