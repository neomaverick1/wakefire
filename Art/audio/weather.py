"""The weather: rain on a street and on a roof, the wind that comes with the cold, thunder a long
way off, the rain stick, and the drum the dance ends on.

  python3 weather.py [resources dir]     (default: the game's Resources; Audio/ under it)"""
import os
import sys
import wave
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import sfx as S


def save_loop(name, x, vol, cross=0.6):
    """A loop with no seam: the tail is folded into the head."""
    n = int(cross * S.SR)
    x = np.asarray(x, dtype=np.float64)
    k = np.linspace(0, 1, n)
    body = x[:-n].copy()
    body[:n] = x[:n] * np.sqrt(k) + x[-n:] * np.sqrt(1 - k)
    body = body / (np.abs(body).max() + 1e-9) * vol
    pcm = (np.clip(body, -1, 1) * 32767).astype('<i2')
    with wave.open(f'{S.OUT}/sfx_{name}.wav', 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes(pcm.tobytes())


def ticks(d, n, f0, f1, dur, r, loud=(0.3, 1.0)):
    """n short drops scattered over d seconds, each a few milliseconds of band noise."""
    out = np.zeros(int(d * S.SR))
    m = int(dur * S.SR)
    e = np.exp(-np.arange(m) / (m * 0.3))
    for _ in range(n):
        i = int(r.uniform(0, d - dur - 0.01) * S.SR)
        out[i:i + m] += r.normal(0, 1, m) * e * r.uniform(*loud)
    return S.bp(out, f0, f1)


def build_sfx():
    r = np.random.default_rng(2100)
    # ---- rain on a street: the sheet of it, the patter on stone, and single drops near by
    d = 7.6
    t = S.t_(d)
    sheet = S.bp(r.normal(0, 1, len(t)), 700, 9000) * (0.88 + 0.12 * np.sin(2 * np.pi * t / 3.8 + 1.0))
    patter = S.lp(r.normal(0, 1, len(t)), 1400) * (0.6 + 0.4 * np.abs(S.lp(r.normal(0, 1, len(t)), 6)) * 30)
    near = ticks(d, 520, 1800, 7000, 0.004, r)
    save_loop('rain_loop', S.mix(sheet * 0.55, patter * 0.30, near * 1.6), 0.75)
    # ---- the same rain heard from under a tiled roof: mostly the roof
    d = 7.6
    t = S.t_(d)
    dull = S.lp(r.normal(0, 1, len(t)), 520, 4) * (0.85 + 0.15 * np.sin(2 * np.pi * t / 3.8))
    tiles = ticks(d, 260, 300, 1500, 0.012, r)
    drips = np.zeros(len(t))
    for k in range(5):
        at = r.uniform(0.3, d - 0.6)
        blip = S.sweep(r.uniform(820, 1100), r.uniform(520, 640), 0.07) * S.env(0.07, 0.002, 0.025)
        i = int(at * S.SR)
        drips[i:i + len(blip)] += blip * r.uniform(0.5, 0.9)
    save_loop('rain_roof_loop', S.mix(dull * 2.2, tiles * 1.0, S.room(drips, 0.3, 0.5) * 0.35), 0.7)
    # ---- the wind that comes with the cold: it finds every corner of the city, one at a time
    d = 9.6
    t = S.t_(d)
    src = r.normal(0, 1, len(t))
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 4.8 - 0.6) * np.sin(2 * np.pi * t / 9.6 + 0.4)
    low = S.bp(src, 180, 520) * swell
    high = S.bp(src, 520, 1500) * np.clip(swell - 0.35, 0, 1) ** 1.5
    whistle = S.bp(src, 1900, 2300, 3) * np.clip(np.sin(2 * np.pi * t / 4.8 - 0.9), 0, 1) ** 4 * 0.5
    save_loop('wind_loop', S.mix(low * 1.5, high * 1.1, whistle), 0.7, cross=0.9)
    # ---- thunder a long way off: all roll and no crack
    for k in range(2):
        th = S.lp(S.thunder(seed=40 + k), 260, 3)
        S.save('thunder_far' if k == 0 else 'thunder_far2', S.room(th, 0.4, 2.2), 0.8)
    # ---- the rain stick turned over: every seed in it going down the inside of the cane
    d = 1.9
    t = S.t_(d)
    dens = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6
    seeds = np.zeros(len(t))
    m = int(0.003 * S.SR)
    e = np.exp(-np.arange(m) / (m * 0.3))
    for _ in range(900):
        at = r.beta(2.0, 2.2) * (d - 0.02)
        i = int(at * S.SR)
        seeds[i:i + m] += r.normal(0, 1, m) * e * r.uniform(0.3, 1.0)
    cane = S.bp(seeds, 2400, 7500) + S.bp(seeds, 380, 620) * 0.5
    S.save('rain_stick', S.room(cane * dens, 0.2, 0.5), 0.75)
    # ---- the big drum on the threshing floor: skin, and the hollow under it
    thump = S.sweep(118, 62, 0.7) * S.env(0.7, 0.002, 0.22)
    skin = S.bp(S.noise(0.08), 300, 2400) * S.env(0.08, 0.0006, 0.018) * 0.9
    body = S.tone(92, 0.9, ((1, 1), (1.59, 0.45), (2.14, 0.28), (2.65, 0.14)), decay=0.30) * 0.6
    S.save('drum_big', S.room(S.mix(thump * 1.5, skin, body), 0.35, 1.3), 0.95)
    # ...struck with nothing but a hand: it says so
    S.save('drum_hand', S.room(S.mix(S.sweep(140, 90, 0.25) * S.env(0.25, 0.002, 0.07), S.bp(S.noise(0.05), 500, 3000) * S.env(0.05, 0.0005, 0.012) * 0.7), 0.25, 0.6), 0.6)
    # ---- a fire bowl that will not stay lit in the rain: it catches, and the rain has it
    d = 0.9
    t = S.t_(d)
    catch = S.bp(S.noise(0.18), 300, 1800) * S.env(0.18, 0.02, 0.06) * 0.8
    steam = S.hp(S.noise(d), 3200) * np.exp(-t * 4.2) * np.minimum(1, t / 0.05)
    S.save('fizzle', S.mix(catch, S.at(steam, 0.14) * 0.9), 0.6)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        S.OUT = os.path.join(sys.argv[1], 'Audio')
    os.makedirs(S.OUT, exist_ok=True)
    build_sfx()
    print('weather sounds ->', S.OUT)
