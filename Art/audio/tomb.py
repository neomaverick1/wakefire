"""The king's tomb: the sounds of the Sun Wheel (thrown, in the air, off a wall, called, caught),
the king's vultures, the Ghost Key and the door it opens, and a counterweight going down a hole.

  python3 tomb.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S

SR = S.SR


def whirr(d, f0, f1, rate0, rate1, bright=0.5):
    """A disc turning in the air: a ringing edge that beats as it spins."""
    t = S.t_(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    rate = rate0 + (rate1 - rate0) * t / d
    beat = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
    ring = (np.sin(ph) + 0.5 * np.sin(2.76 * ph) + 0.25 * np.sin(5.4 * ph)) * beat
    air = S.bp(S.noise(d), 1800, 7000) * beat * bright
    return ring * 0.6 + air * 0.4


def cold(freqs, step=0.09, d=1.3, decay=3.0, detune=1.006):
    """Glass notes with a second voice a hair sharp of each: something that is not quite here."""
    parts = []
    for i, f in enumerate(freqs):
        t = S.t_(d)
        v = (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * detune * t) + 0.25 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * decay)
        parts.append(S.at(v * np.minimum(1, t / 0.03), i * step))
    return S.mix(*parts)


def build_sfx():
    s = S.save
    # ---- the Sun Wheel
    t = S.t_(0.3)
    swish = S.bp(S.noise(0.3), 900, 5200) * S.env(0.3, 0.05, 0.12)
    s('wheel_throw', S.mix(swish * 0.8, S.at(S.bronze(1174.7, 0.5) * 0.35, 0.08)), 0.6)
    s('wheel_fly', whirr(1.1, 1568, 1480, 26, 18) * S.env(1.1, 0.04, 0.7), 0.42)
    s('wheel_bank', S.room(S.mix(S.bronze(1760, 0.45), S.bronze(2349.3, 0.3) * 0.5, S.bp(S.noise(0.04), 2500, 8000) * S.env(0.04, 0.001, 0.015) * 0.8), 0.25, 0.8), 0.6)
    s('wheel_call', S.mix(whirr(0.34, 1175, 1760, 20, 34, 0.3) * S.env(0.34, 0.03, 0.3), S.at(S.bronze(2349.3, 0.3) * 0.3, 0.18)), 0.45)
    slap = S.lp(S.noise(0.08), 900) * S.env(0.08, 0.002, 0.03)
    s('wheel_catch', S.mix(slap * 1.2, S.bronze(880, 0.5) * 0.45), 0.6)
    # ---- the king's vultures: a hiss with a rattle in it; wings; feathers
    t = S.t_(0.7)
    rattle = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (34 - 14 * t / 0.7) * t))
    hiss = S.bp(S.noise(0.7), 900, 3600) * rattle * S.env(0.7, 0.05, 0.35)
    croak = S.bp(S.sweep(330, 190, 0.7, 'saw'), 200, 1600) * rattle * S.env(0.7, 0.04, 0.3)
    s('vulture_mark', S.room(S.mix(hiss * 0.8, croak * 0.7), 0.3, 1.2), 0.7)
    t = S.t_(0.75)
    rush = S.bp(S.noise(0.75), 200, 2200) * (t / 0.75) ** 2 * S.env(0.75, 0.3, 0.6)
    flap = S.lp(S.noise(0.75), 420) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)) * S.env(0.75, 0.1, 0.5)
    s('vulture_stoop', S.mix(rush, flap * 0.8), 0.7)
    thump = S.lp(S.noise(0.16), 500) * S.env(0.16, 0.002, 0.05)
    s('vulture_hit', S.mix(thump * 1.4, S.at(S.bp(S.noise(0.3), 1500, 5000) * S.env(0.3, 0.02, 0.12) * 0.5, 0.02), S.at(croak[:int(0.3 * SR)] * 0.5, 0.03)), 0.7)
    # ---- the Ghost Key, and the king's own door
    s('ghost_key', S.room(S.mix(cold((1318.5, 987.77, 783.99, 659.26), 0.14, 1.6, 2.2), S.at(cold((1975.5,), 0.0, 1.6, 2.0) * 0.5, 0.62)), 0.45, 2.4), 0.7)
    t = S.t_(1.6)
    sigh = S.bp(S.noise(1.6), 300, 1500) * np.sin(np.pi * t / 1.6) ** 2
    turn = S.mix(S.at(S.lp(S.noise(0.1), 700) * S.env(0.1, 0.002, 0.04) * 1.5, 0.5), S.at(S.lp(S.noise(0.14), 420) * S.env(0.14, 0.002, 0.06) * 2.0, 0.95))
    s('ghost_door', S.room(S.mix(sigh * 0.6, turn, S.at(cold((261.63, 392.0), 0.2, 1.4, 2.0) * 0.5, 0.3)), 0.45, 2.6), 0.8)
    # ---- a block of stone going down a hole: it goes, it is gone, and then it is heard from
    t = S.t_(0.9)
    drop = S.bp(S.noise(0.9), 300, 2400) * np.exp(-t * 3.5) * 0.6
    boom = S.lp(S.noise(1.2), 160) * S.env(1.2, 0.005, 0.5) * 3.0 + np.sin(2 * np.pi * (48 + 30 * np.exp(-S.t_(1.2) * 9)) * S.t_(1.2)) * S.env(1.2, 0.004, 0.4)
    s('weight_fall', S.room(S.mix(S.lp(S.noise(0.07), 1200) * S.env(0.07, 0.001, 0.02) * 1.2, drop, S.at(boom, 1.15)), 0.45, 2.2), 0.85)


if __name__ == '__main__':
    res = sys.argv[1] if len(sys.argv) > 1 else '/srv/Wakefire/Assets/Wakefire/Resources'
    os.makedirs(f'{res}/Audio', exist_ok=True)
    S.OUT = f'{res}/Audio'
    build_sfx()
    print('tomb sfx written')
