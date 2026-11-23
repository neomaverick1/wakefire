"""The high halls of the ziggurat, as the doorkeepers left them: a Medusa (the hair, and the look), a
thurifer's censer going round on its chain, and a burning glass that has not been turned off.

  python3 halls.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S

SR = S.SR


def hiss(d, lo, hi, flutter, seed_shift=0.0):
    """Air through teeth that are not teeth: band noise with a quick uneven flutter in it."""
    t = S.t_(d)
    f = 0.6 + 0.4 * np.sin(2 * np.pi * flutter * t + seed_shift) * np.sin(2 * np.pi * (flutter * 0.37) * t + 1.3)
    return S.bp(S.noise(d), lo, hi) * f


def build_sfx():
    s = S.save
    # ---- a Medusa: eleven snakes noticing somebody, all at once and none of them together
    parts = []
    for i in range(6):
        d = 0.5 + 0.08 * i
        parts.append(S.at(hiss(d, 2400 + 260 * i, 7200 + 300 * i, 17 + 3 * i, i) * S.env(d, 0.04 + 0.01 * i, 0.22) * (0.55 + 0.08 * (i % 3)), 0.03 * i))
    s('medusa_hiss', S.room(S.mix(*parts), 0.25, 0.9), 0.6)
    # the look: the hiss draws in to one note, the note rises, and something cold arrives at the top of it
    t = S.t_(0.95)
    draw = hiss(0.95, 1800, 6400, 23) * (t / 0.95) ** 1.5 * S.env(0.95, 0.5, 0.25)
    whine = np.sin(2 * np.pi * np.cumsum(520 * (2.6) ** (t / 0.95)) / SR) * (t / 0.95) ** 2 * 0.35
    glass = S.at((np.sin(2 * np.pi * 2093 * S.t_(0.7)) + np.sin(2 * np.pi * 2093 * 1.007 * S.t_(0.7)) + 0.4 * np.sin(2 * np.pi * 3136 * S.t_(0.7))) * np.exp(-S.t_(0.7) * 5.5) * 0.5, 0.72)
    s('medusa_stare', S.room(S.mix(draw * 0.8, whine, glass), 0.3, 1.4), 0.7)
    # ---- a censer on a chain: the whoosh of one pass, the clang when it meets bronze, the cough after
    t = S.t_(0.34)
    whoosh = S.bp(S.noise(0.34), 300, 1900) * np.sin(np.pi * t / 0.34) ** 2
    s('censer_pass', S.mix(whoosh * 0.9, S.bronze(392, 0.3) * 0.12), 0.34)
    s('censer_clang', S.room(S.mix(S.bronze(311.1, 1.0), S.bronze(466.2, 0.8) * 0.6, S.lp(S.noise(0.06), 1800) * S.env(0.06, 0.001, 0.02) * 1.5,
                                   S.at(S.bp(S.noise(0.5), 500, 3000) * S.env(0.5, 0.01, 0.2) * 0.35, 0.03)), 0.3, 1.2), 0.8)
    cough = []
    for i, (f, d) in enumerate(((210, 0.16), (190, 0.13), (230, 0.2))):
        tt = S.t_(d)
        c = S.bp(S.noise(d), 300, 2400) * S.env(d, 0.008, 0.05) + S.bp(S.sweep(f, f * 0.7, d, 'saw'), 150, 1200) * S.env(d, 0.006, 0.05) * 0.6
        cough.append(S.at(c, i * 0.24))
    s('censer_cough', S.room(S.mix(*cough), 0.2, 0.6), 0.6)
    # ---- the burning glass: light gathering (a rising glass tone), the beam, and the glass giving
    t = S.t_(1.0)
    gather = (np.sin(2 * np.pi * np.cumsum(880 * 2 ** (t / 1.0)) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(1320 * 2 ** (t / 1.0)) / SR)) * (t / 1.0) ** 2 * 0.3
    fizz = S.hp(S.noise(1.0), 5000) * (t / 1.0) ** 3 * 0.25
    s('glass_gather', S.mix(gather, fizz), 0.5)
    t = S.t_(0.6)
    beam = S.bp(S.noise(0.6), 900, 5200) * S.env(0.6, 0.004, 0.25) * 0.8 + np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 6) * 0.4 + S.lp(S.noise(0.6), 220) * S.env(0.6, 0.004, 0.2) * 1.2
    s('glass_beam', S.room(beam, 0.25, 0.9), 0.75)
    crack = S.mix(S.hp(S.noise(0.05), 3000) * S.env(0.05, 0.0005, 0.012) * 2.0, S.at(S.hp(S.noise(0.04), 4500) * S.env(0.04, 0.0005, 0.01) * 1.3, 0.09),
                  S.at((np.sin(2 * np.pi * 3520 * S.t_(0.5)) + np.sin(2 * np.pi * 4699 * S.t_(0.5))) * np.exp(-S.t_(0.5) * 9) * 0.3, 0.01))
    s('glass_crack', S.room(crack, 0.3, 0.8), 0.8)
    shards = [S.at((np.sin(2 * np.pi * f * S.t_(0.4)) * np.exp(-S.t_(0.4) * 11)) * 0.3, 0.05 + 0.06 * i) for i, f in enumerate((2637, 3951, 3136, 4699, 2093, 5274, 3520))]
    s('glass_break', S.room(S.mix(S.hp(S.noise(0.5), 2500) * S.env(0.5, 0.001, 0.12) * 1.4, S.lp(S.noise(0.2), 400) * S.env(0.2, 0.002, 0.06) * 1.5, *shards), 0.35, 1.3), 0.85)


if __name__ == '__main__':
    res = sys.argv[1] if len(sys.argv) > 1 else '/srv/Wakefire/Assets/Wakefire/Resources'
    os.makedirs(f'{res}/Audio', exist_ok=True)
    S.OUT = f'{res}/Audio'
    build_sfx()
    print('halls sfx written')
