"""What the bad dreams of Ashkel sound like: a bronze snuffer on three legs, lamp flames that
have left their lamps, a net that went on fishing, shadows with nobody to throw them, and a
yawn that is still going round.

  python3 dreams.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S

SR = S.SR


def flutter(d, lo, hi, rate, depth=0.6, phase=0.0):
    """Band noise with something beating in it: a flame in a draught, a net going round."""
    t = S.t_(d)
    return S.bp(S.noise(d), lo, hi) * (1 - depth + depth * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t + phase)))


def clicks(n, d, lo=1800, hi=5000, seed=0):
    """Small hard things knocking together: stones on a rim rope, bronze feet settling."""
    r = np.random.default_rng(100 + seed)
    parts = []
    for i in range(n):
        dd = r.uniform(0.012, 0.03)
        parts.append(S.at(S.bp(S.noise(dd), lo, hi) * S.env(dd, 0.0005, dd * 0.3) * r.uniform(0.4, 1.0), r.uniform(0, d)))
    return S.mix(*parts)


def vowel(f0, f1, d, formants=((700, 110), (1150, 120), (2500, 160)), breath=0.35):
    """A mouth, open: a falling voice through an 'aah', with air round it."""
    t = S.t_(d)
    src = S.sweep(f0, f1, d, 'saw') * (0.8 + 0.2 * np.sin(2 * np.pi * 5.1 * t))
    air = S.noise(d) * breath
    out = np.zeros(len(t))
    for f, bw in formants:
        out += S.bp(src + air, max(60, f - bw), f + bw)
    return out


def build_sfx():
    s = S.save
    # ---- the Snuffer
    for i, f in enumerate((1245, 932)):
        s(f'snuffer_step{i}', S.room(S.mix(S.bronze(f, 0.16) * 0.55, S.lp(S.noise(0.05), 420) * S.env(0.05, 0.001, 0.018) * 1.6,
                                           S.at(S.bronze(f * 1.5, 0.08) * 0.2, 0.012)), 0.18, 0.35), 0.5)
    t = S.t_(0.7)
    breath = S.bp(S.noise(0.7), 260, 1500) * np.sin(np.pi * t / 0.7) ** 1.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t))
    hollow = np.sin(2 * np.pi * 196 * t) * np.sin(np.pi * t / 0.7) ** 2 * 0.22
    s('snuffer_sniff', S.room(S.mix(breath, hollow), 0.35, 0.9), 0.5)
    t = S.t_(0.6)
    creak = S.bp(S.sweep(170, 330, 0.6, 'saw') * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t)), 150, 1400) * S.env(0.6, 0.12, 0.25)
    s('snuffer_rear', S.mix(creak * 0.8, clicks(4, 0.4, 900, 3000, 1) * 0.4), 0.5)
    s('snuffer_clang', S.room(S.mix(S.bronze(146.8, 1.6), S.bronze(220, 1.3) * 0.7, S.bronze(369.9, 0.9) * 0.4, S.lp(S.noise(0.12), 240) * S.env(0.12, 0.001, 0.05) * 2.6,
                                    S.lp(S.noise(0.05), 2600) * S.env(0.05, 0.0006, 0.012) * 1.4), 0.35, 1.5), 0.9)
    s('snuffer_ring', S.room(S.mix(S.bronze(293.7, 1.3), S.bronze(440, 1.0) * 0.55, S.bronze(739.9, 0.6) * 0.3, S.lp(S.noise(0.04), 3200) * S.env(0.04, 0.0006, 0.01)), 0.3, 1.2), 0.8)
    s('snuffer_hiss', S.mix(S.hp(S.noise(0.5), 2600) * S.env(0.5, 0.004, 0.14), S.bp(S.noise(0.16), 300, 1400) * S.env(0.16, 0.002, 0.05) * 0.9), 0.55)
    roll = S.mix(*[S.at(S.bronze(330 + 40 * (k % 3), 0.5) * (0.8 - 0.09 * k), 0.14 * k + 0.02 * k * k) for k in range(6)])
    s('snuffer_fall', S.room(S.mix(S.bronze(164.8, 1.4), S.bronze(246.9, 1.0) * 0.6, S.lp(S.noise(0.14), 260) * S.env(0.14, 0.001, 0.05) * 2.4, S.at(roll, 0.12)), 0.3, 1.3), 0.9)
    shards = [S.at(S.bronze(f, 0.5) * 0.35, 0.04 + 0.05 * i) for i, f in enumerate((880, 1318, 1046, 1760, 698, 1567, 1174))]
    s('snuffer_break', S.room(S.mix(S.bronze(110, 1.8), S.bronze(155.6, 1.4) * 0.7, S.lp(S.noise(0.3), 300) * S.env(0.3, 0.002, 0.1) * 2.6,
                                    S.hp(S.noise(0.2), 2500) * S.env(0.2, 0.001, 0.05) * 0.9, *shards), 0.4, 1.8), 0.95)
    # ---- Wicks
    s('wick_whip', flutter(0.26, 400, 2600, 31, 0.7) * S.env(0.26, 0.006, 0.09), 0.5)
    t = S.t_(0.4)
    s('wick_dart', S.mix(S.bp(S.noise(0.4), 500, 3600) * np.sin(np.pi * t / 0.4) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 26 * t)),
                         S.sweep(300, 900, 0.4) * np.sin(np.pi * t / 0.4) ** 2 * 0.12), 0.55)
    s('wick_leap', S.mix(flutter(0.45, 300, 2400, 22, 0.5) * S.env(0.45, 0.05, 0.16), clicks(5, 0.35, 2500, 7000, 2) * 0.35), 0.5)
    s('wick_out', S.mix(S.hp(S.noise(0.6), 3000) * S.env(0.6, 0.003, 0.16) * 0.8, S.bp(S.noise(0.3), 200, 900) * S.env(0.3, 0.01, 0.1) * 0.7), 0.5)
    # ---- the Dragnet
    t = S.t_(0.8)
    slither = S.bp(S.noise(0.8), 500, 3800) * np.sin(np.pi * t / 0.8) ** 1.5 * (0.55 + 0.45 * np.sin(2 * np.pi * 13 * t) ** 2)
    rope = S.bp(S.sweep(95, 150, 0.8, 'saw') * (0.5 + 0.5 * np.sin(2 * np.pi * 29 * t)), 80, 900) * S.env(0.8, 0.2, 0.3) * 0.7
    s('net_rise', S.mix(slither * 0.8, rope, clicks(6, 0.6, 1500, 4200, 3) * 0.35), 0.55)
    t = S.t_(0.5)
    s('net_cast', S.bp(S.noise(0.5), 250, 2600) * np.sin(np.pi * t / 0.5) ** 1.5 * (0.45 + 0.55 * np.sin(2 * np.pi * 15 * t) ** 2), 0.6)
    s('net_land', S.mix(S.lp(S.noise(0.18), 300) * S.env(0.18, 0.002, 0.06) * 2.0, S.bp(S.noise(0.3), 600, 3000) * S.env(0.3, 0.004, 0.08) * 0.6, clicks(9, 0.22, 1400, 4500, 4) * 0.6), 0.65)
    s('net_cut', S.mix(S.hp(S.noise(0.07), 1800) * S.env(0.07, 0.0008, 0.018) * 1.3, S.at(S.bp(S.noise(0.12), 300, 1500) * S.env(0.12, 0.002, 0.04), 0.02),
                       S.at(S.tone(140, 0.14, ((1, 1), (2.2, 0.4)), 0.05) * 0.6, 0.01)), 0.6)
    s('net_swish', S.bp(S.noise(0.2), 900, 5200) * S.env(0.2, 0.02, 0.06), 0.4)
    snaps = [S.at(S.hp(S.noise(0.05), 1500) * S.env(0.05, 0.0008, 0.014) * (1 - 0.07 * k), 0.05 * k + 0.012 * k * k) for k in range(8)]
    s('net_die', S.room(S.mix(*snaps, S.bp(S.noise(0.9), 300, 2200) * S.env(0.9, 0.05, 0.35) * 0.5, S.lp(S.noise(0.3), 220) * S.env(0.3, 0.004, 0.1) * 1.4), 0.2, 0.7), 0.7)
    t = S.t_(0.9)
    s('splash', S.room(S.mix(S.lp(S.noise(0.25), 500) * S.env(0.25, 0.002, 0.08) * 2.2, S.bp(S.noise(0.9), 700, 6000) * S.env(0.9, 0.012, 0.28),
                             S.at(clicks(14, 0.5, 2200, 7000, 5) * 0.35, 0.18)), 0.25, 0.8), 0.75)
    # ---- Stay-Ups
    t = S.t_(0.9)
    s('stayup_stir', S.room(S.mix(S.lp(S.noise(0.9), 260) * (t / 0.9) ** 2 * 1.6, np.sin(2 * np.pi * 61.7 * t) * (t / 0.9) ** 2 * 0.5,
                                  S.bp(S.noise(0.9), 1500, 5000) * (t / 0.9) ** 3 * 0.12), 0.35, 1.2), 0.5)
    s('stayup_grip', S.room(S.mix(S.tone(55, 0.5, ((1, 1), (2, 0.4)), 0.2), S.lp(S.noise(0.1), 180) * S.env(0.1, 0.001, 0.04) * 2.2,
                                  S.at(S.bp(S.noise(0.3), 1200, 4200) * S.env(0.3, 0.02, 0.1) * 0.35, 0.03)), 0.3, 1.0), 0.75)
    t = S.t_(0.5)
    s('stayup_tug', S.room(S.mix(np.sin(2 * np.pi * np.cumsum(130 * (0.5) ** (t / 0.5)) / SR) * np.exp(-t * 6) * 1.0, S.lp(S.noise(0.08), 300) * S.env(0.08, 0.001, 0.03) * 1.6), 0.3, 0.9), 0.75)
    t = S.t_(0.6)
    sizzle = S.hp(S.noise(0.6), 3500) * S.env(0.6, 0.01, 0.22) * (0.6 + 0.4 * np.sin(2 * np.pi * 43 * t) ** 2)
    s('stayup_burn', S.mix(sizzle, clicks(7, 0.45, 3000, 8000, 6) * 0.4, S.lp(S.noise(0.3), 300) * S.env(0.3, 0.02, 0.1) * 0.5), 0.5)
    t = S.t_(1.1)
    s('stayup_gone', S.room(S.mix(S.bp(S.noise(1.1), 300, 2000) * S.env(1.1, 0.05, 0.4) * 0.6, np.sin(2 * np.pi * np.cumsum(180 * (0.45) ** (t / 1.1)) / SR) * np.exp(-t * 3) * 0.35,
                                  S.hp(S.noise(0.4), 4000) * S.env(0.4, 0.01, 0.12) * 0.25), 0.4, 1.5), 0.6)
    # ---- the Yawn
    for name, f0, f1, d, vol in (('yawn_near', 150, 92, 1.5, 0.4), ('yawn_pass', 185, 120, 1.0, 0.35), ('yawn_catch', 132, 84, 1.7, 0.6)):
        t = S.t_(d)
        shape = np.sin(np.pi * np.minimum(1, t / d) ** 0.7) ** 1.2
        s(name, S.room(vowel(f0, f1, d) * shape, 0.3, 1.0), vol)
    t = S.t_(0.45)
    s('yawn_back', S.room(S.mix(S.bp(S.noise(0.45), 400, 3000) * np.sin(np.pi * t / 0.45) ** 2, S.bronze(1568, 0.5) * 0.25), 0.3, 0.8), 0.6)
    s('yawn_out', S.mix(S.bp(S.noise(0.35), 300, 1800) * S.env(0.35, 0.01, 0.12), S.hp(S.noise(0.15), 3000) * S.env(0.15, 0.002, 0.04) * 0.4), 0.45)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        S.OUT = os.path.join(sys.argv[1], 'Audio')
    os.makedirs(S.OUT, exist_ok=True)
    build_sfx()
    print('dream sounds ->', S.OUT)
