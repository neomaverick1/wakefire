"""Every sound in WAKEFIRE that isn't music, synthesised from scratch (noise, oscillators,
filters, a touch of room) or plucked from the soundfont, then written as 16-bit WAVs.
Bronze rings with inharmonic partials; clay shatters; fire breathes; the goat says MEHHH."""
import os
import sys
import wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import tinysoundfont

SR = 44100
OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Audio'
SF2 = '/srv/Wakefire/Art/audio/GeneralUser-GS.sf2'
rng = np.random.default_rng(11)


def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.normal(0, 1, int(d * SR))


def env(d, a=0.005, decay=0.2, hold=0.0):
    t = t_(d)
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a - hold) / max(decay, 1e-4))
    return e


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)


def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], 'band', fs=SR, output='sos'), x)


def sweep(f0, f1, d, shape='sine'):
    t = t_(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == 'sine':
        return np.sin(ph)
    if shape == 'tri':
        return 2 / np.pi * np.arcsin(np.sin(ph))
    if shape == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    return np.sign(np.sin(ph))


def tone(f, d, partials=((1, 1),), decay=0.3, a=0.002):
    t = t_(d)
    s = sum(amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (decay / (1 + 0.6 * i))) for i, (ratio, amp) in enumerate(partials))
    return s * np.minimum(1, t / a)


def bronze(f, d=0.8):
    """A struck bronze object: inharmonic partials, the high ones dying fast."""
    return tone(f, d, ((1, 1), (2.76, 0.6), (5.4, 0.4), (8.93, 0.25), (13.3, 0.15)), decay=d * 0.5)


def room(x, mix=0.25, rt=0.6):
    n = int(rt * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-6.9 * t / rt)
    ir = lp(ir, 6000)
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    wet = fftconvolve(x, ir)
    out = np.zeros(len(wet))
    out[:len(x)] += x * (1 - mix * 0.4)
    out += wet * mix
    return out


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def at(x, delay):
    return np.concatenate([np.zeros(int(delay * SR)), x])


def save(name, x, vol=0.9):
    x = np.asarray(x, dtype=np.float64)
    # trim trailing silence, short fade out, normalise
    a = np.abs(x)
    idx = np.where(a > 1e-3 * a.max())[0]
    if len(idx):
        x = x[:idx[-1] + 1]
    f = min(len(x), int(0.01 * SR))
    x[-f:] *= np.linspace(1, 0, f)
    x = x / (np.abs(x).max() + 1e-9) * vol
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(f'{OUT}/sfx_{name}.wav', 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


_syn = None


def sf_note(prog, notes, d=1.2, vel=100, drums=False, step=0.0):
    """Render notes (list of MIDI keys) from the soundfont, mono."""
    global _syn
    syn = tinysoundfont.Synth(gain=-3, samplerate=SR)
    sf = syn.sfload(SF2)
    ch = 9 if drums else 0
    syn.program_select(ch, sf, 128 if drums else 0, 0 if drums else prog, drums)
    out = []
    for i, k in enumerate(notes):
        syn.noteon(ch, k, vel)
        if step > 0:
            out.append(np.frombuffer(syn.generate(int(step * SR)), dtype=np.float32).reshape(-1, 2).mean(axis=1))
    for k in notes:
        pass
    out.append(np.frombuffer(syn.generate(int(d * SR)), dtype=np.float32).reshape(-1, 2).mean(axis=1))
    for k in notes:
        syn.noteoff(ch, k)
    out.append(np.frombuffer(syn.generate(int(0.8 * SR)), dtype=np.float32).reshape(-1, 2).mean(axis=1))
    return np.concatenate(out).astype(np.float64)


def goat():
    """MEHHH: a nasal, wobbling, slightly unhinged bleat (formant synthesis)."""
    d = 0.95
    t = t_(d)
    f0 = 330 * (1 + 0.08 * np.sin(2 * np.pi * 7.5 * t)) * (1 + 0.15 * np.exp(-t / 0.08)) * (1 - 0.12 * t / d)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    src = sum(np.sin(k * ph) / k ** 0.6 for k in range(1, 26))
    shaper = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.12) * (0.8 + 0.2 * np.sin(2 * np.pi * 7.5 * t))
    x = src * shaper
    # formants of "eh" with a nasal bump
    y = bp(x, 450, 650) * 1.0 + bp(x, 1600, 2100) * 0.7 + bp(x, 2500, 3100) * 0.35 + bp(x, 900, 1100) * 0.4
    y += noise(d) * 0.02 * shaper
    return room(y, 0.15, 0.3)


def snore(scale=1.0, seed=0):
    """A sleeper's snore: the soft palate rattling on the in-breath, then a slow sigh out through
    the nose. scale > 1 is a smaller animal (faster rattle, higher body)."""
    r = np.random.default_rng(300 + seed)
    d_in = 1.15 / scale ** 0.5
    t = t_(d_in)
    fl = 29 * scale * (1 + 0.06 * np.sin(2 * np.pi * 0.9 * t))
    ph = np.cumsum(fl) / SR
    pulse = np.clip(np.sin(2 * np.pi * ph), 0, 1) ** 4
    src = r.normal(0, 1, len(t)) * (0.25 + pulse)
    body = bp(src, 70 * scale, 380 * scale) * 1.6 + bp(src, 380 * scale, 1000 * scale) * 0.45
    buzz = lp(np.sin(2 * np.pi * np.cumsum(fl * 3.0) / SR) * pulse, 400 * scale) * 0.3
    e_in = np.sin(np.pi * np.clip(t / d_in, 0, 1)) ** 1.5
    inhale = lp(body + buzz, 900 * scale, 4) * e_in
    d_out = 0.95 / scale ** 0.5
    t2 = t_(d_out)
    e_out = np.minimum(1, t2 / 0.12) * np.exp(-t2 / (d_out * 0.38))
    exhale = bp(r.normal(0, 1, len(t2)), 250 * scale, 1400 * scale) * e_out * 0.35
    return room(mix(inhale, at(exhale, d_in + 0.18)), 0.12, 0.3)


def build():
    os.makedirs(OUT, exist_ok=True)
    # --- the khopesh
    for i, (f0, f1, d, g) in enumerate(((2400, 600, 0.17, 1.0), (2000, 500, 0.17, 1.0), (1600, 260, 0.26, 1.3)), start=1):
        w = bp(noise(d), 300, 5000) * env(d, 0.02, d * 0.35) * sweep(1, 1, d)
        w = mix(lp(w * np.linspace(1.4, 0.6, len(w)), f0 * 2), tone(f0 / 6, d, ((1, 0.25),), 0.08) * 0.3)
        save(f'swing{i}', w * g)
    save('cut', mix(hp(noise(0.25), 2000) * env(0.25, 0.002, 0.05), bp(noise(0.3), 400, 2500) * env(0.3, 0.01, 0.1) * 0.6,
                    at(hp(noise(0.06), 3000) * env(0.06, 0.001, 0.015), 0.04) * 0.8))
    save('pot_break', mix(*[at(bp(noise(0.12), 1200 + 500 * k, 4000 + 600 * k) * env(0.12, 0.001, 0.03 + 0.01 * k), 0.025 * k) * (1 - 0.12 * k)
                           for k in range(6)], tone(820, 0.4, ((1, 0.4), (2.3, 0.3), (3.8, 0.2)), 0.08) * 0.5, lp(noise(0.2), 400) * env(0.2, 0.002, 0.05)))
    save('roll', mix(bp(noise(0.36), 200, 1600) * env(0.36, 0.05, 0.12), at(lp(noise(0.1), 180) * env(0.1, 0.002, 0.04) * 2, 0.22)), 0.6)
    save('hurt', mix(lp(noise(0.25), 500) * env(0.25, 0.002, 0.08) * 1.6, sweep(220, 90, 0.25, 'saw') * env(0.25, 0.003, 0.09) * 0.5,
                     bp(noise(0.12), 1500, 4000) * env(0.12, 0.001, 0.03) * 0.5))
    save('deny', lp(sweep(150, 120, 0.22, 'square'), 900) * env(0.22, 0.004, 0.08), 0.5)
    # --- dreaming
    d = 1.6
    pad = sum(np.sin(2 * np.pi * f * t_(d) * (1 + 0.5 * t_(d) / d)) * 0.3 for f in (293.7, 440, 587.3, 740))
    shimmer = sum(np.sin(2 * np.pi * f * t_(d)) * np.exp(-t_(d) / 0.5) * 0.15 for f in (1175, 1480, 1760, 2349))
    save('dream_in', room(mix(pad * env(d, 0.25, 0.5, 0.3), shimmer, hp(noise(d), 4000) * env(d, 0.4, 0.4) * 0.05), 0.45, 1.6))
    pad2 = sum(np.sin(2 * np.pi * f * t_(1.1) * (1 - 0.35 * t_(1.1) / 1.1)) * 0.3 for f in (740, 587.3, 440, 293.7))
    save('dream_out', room(mix(pad2 * env(1.1, 0.02, 0.35), bp(noise(0.5), 300, 2000) * env(0.5, 0.02, 0.15) * 0.4), 0.35, 1.0))
    save('wake_forced', mix(bp(noise(0.3), 800, 5000) * env(0.3, 0.003, 0.07), lp(noise(0.2), 200) * env(0.2, 0.001, 0.05) * 2,
                            sweep(600, 200, 0.3) * env(0.3, 0.002, 0.1) * 0.4))
    # --- fire and lamps
    save('ignite', room(mix(lp(noise(0.8), 900) * env(0.8, 0.03, 0.25) * 1.4,
                            *[at(hp(noise(0.02), 2500) * env(0.02, 0.001, 0.006), 0.1 + 0.06 * k + rng.uniform(0, 0.04)) * 0.5 for k in range(9)]), 0.2, 0.5))
    save('lantern', mix(bp(noise(0.25), 500, 3000) * env(0.25, 0.04, 0.07) * 0.6, at(bronze(1400, 0.3) * 0.3, 0.06)), 0.55)
    save('fireball', mix(lp(noise(0.5), 1400) * env(0.5, 0.02, 0.2), sweep(300, 120, 0.5, 'saw') * env(0.5, 0.01, 0.2) * 0.2), 0.75)
    save('fire_burst', mix(lp(noise(0.4), 1100) * env(0.4, 0.002, 0.12) * 1.3, hp(noise(0.1), 2000) * env(0.1, 0.001, 0.03) * 0.5), 0.75)
    save('reflect', room(mix(bronze(2100, 0.7), bronze(3150, 0.5) * 0.5, sweep(800, 2400, 0.25) * env(0.25, 0.005, 0.08) * 0.3), 0.3, 0.6))
    # --- small things
    save('coin', mix(tone(1975, 0.35, ((1, 1), (2, 0.2)), 0.12), at(tone(2637, 0.45, ((1, 1), (2, 0.2)), 0.18), 0.07)), 0.6)
    save('coin_big', mix(tone(1568, 0.5, ((1, 1), (2, 0.3)), 0.2), at(tone(1975, 0.5, ((1, 1),), 0.2), 0.06), at(tone(2637, 0.7, ((1, 1),), 0.3), 0.12)), 0.65)
    save('coin_bounce', tone(2800, 0.08, ((1, 1), (2.7, 0.3)), 0.025), 0.3)
    save('flame_get', room(mix(lp(noise(0.5), 1500) * env(0.5, 0.05, 0.15) * 0.6, sweep(500, 1500, 0.4) * env(0.4, 0.01, 0.15) * 0.4,
                               at(tone(1760, 0.6, ((1, 1), (2, 0.3)), 0.25) * 0.5, 0.15)), 0.3, 0.8), 0.7)
    save('text_next', tone(1300, 0.05, ((1, 1),), 0.015) * 0.6, 0.35)
    save('menu_move', tone(900, 0.05, ((1, 1), (2, 0.2)), 0.02), 0.4)
    save('menu_ok', room(mix(tone(1175, 0.4, ((1, 1), (2, 0.3)), 0.12), at(tone(1760, 0.5, ((1, 1),), 0.18), 0.07)), 0.3, 0.5), 0.6)
    save('unlock', mix(bronze(900, 0.4) * 0.6, at(lp(noise(0.1), 900) * env(0.1, 0.002, 0.03), 0.12) * 1.5, at(bronze(1300, 0.3) * 0.4, 0.15)), 0.8)
    save('chest_open', room(mix(lp(sweep(180, 120, 0.5, 'saw'), 700) * env(0.5, 0.05, 0.15) * 0.5,
                                at(lp(noise(0.12), 500) * env(0.12, 0.002, 0.04), 0.35), at(sf_note(46, [74, 78, 81, 86], 1.0, 90, step=0.06) * 2.5, 0.38)), 0.25, 0.6))
    save('block_push', mix(bp(noise(0.45), 100, 900) * env(0.45, 0.05, 0.25) * (1 + 0.5 * np.sin(2 * np.pi * 23 * t_(0.45))),
                           at(lp(noise(0.12), 200) * env(0.12, 0.002, 0.05) * 1.5, 0.33)))
    save('plate', mix(lp(noise(0.1), 600) * env(0.1, 0.001, 0.03), at(bronze(600, 0.4) * 0.5, 0.03)), 0.7)
    save('gate_open', room(mix(lp(noise(2.2), 160) * env(2.2, 0.2, 0.8) * 2.5, lp(sweep(90, 60, 2.0, 'saw'), 400) * env(2.0, 0.3, 0.7) * 0.5,
                               bp(sweep(400, 300, 1.5, 'saw'), 300, 1200) * env(1.5, 0.4, 0.4) * 0.3), 0.3, 1.2))
    save('fall', mix(sweep(1400, 300, 0.7) * env(0.7, 0.01, 0.4) * 0.5, at(lp(noise(0.4), 600) * env(0.4, 0.002, 0.12), 0.55)), 0.7)
    save('goat', goat(), 0.9)
    # --- enemies
    save('enemy_hit', mix(lp(noise(0.12), 1600) * env(0.12, 0.001, 0.04) * 1.5, tone(160, 0.15, ((1, 1),), 0.05)), 0.8)
    save('enemy_die', room(mix(lp(noise(0.5), 700) * env(0.5, 0.005, 0.15), sweep(400, 70, 0.5, 'tri') * env(0.5, 0.005, 0.2) * 0.6,
                               hp(noise(0.3), 3000) * env(0.3, 0.01, 0.1) * 0.3), 0.25, 0.6), 0.8)
    save('clank', room(mix(bronze(780, 0.6), bronze(1170, 0.5) * 0.6, lp(noise(0.05), 3000) * env(0.05, 0.001, 0.01)), 0.2, 0.5), 0.8)
    save('crab_snap', mix(hp(noise(0.03), 2000) * env(0.03, 0.001, 0.006), at(hp(noise(0.03), 2500) * env(0.03, 0.001, 0.006), 0.06)), 0.5)
    t = t_(0.6)
    save('jackal_growl', lp((noise(0.6) * 0.6 + sweep(110, 90, 0.6, 'saw')) * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * t)), 900) * env(0.6, 0.06, 0.25), 0.55)
    save('jackal_bark', mix(bp(sweep(900, 500, 0.12, 'saw'), 400, 2400) * env(0.12, 0.004, 0.05), bp(noise(0.12), 800, 3000) * env(0.12, 0.002, 0.04) * 0.6), 0.7)
    t = t_(0.4)
    save('moth', bp(noise(0.4), 300, 1500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 26 * t))) * env(0.4, 0.05, 0.15), 0.45)
    save('sentinel_alert', room(mix(bronze(520, 0.9) * 0.8, at(bronze(780, 0.6) * 0.5, 0.05)), 0.3, 0.8), 0.7)
    # --- the bull, the god
    t = t_(0.8)
    save('bull_snort', mix(bp(noise(0.5), 200, 1800) * env(0.5, 0.02, 0.15) * 1.4, at(bp(noise(0.35), 300, 2200) * env(0.35, 0.02, 0.1), 0.35)), 0.8)
    t = t_(1.4)
    roar = (sweep(95, 70, 1.4, 'saw') + noise(1.4) * 0.5) * (0.7 + 0.3 * np.sin(2 * np.pi * 17 * t))
    save('bull_roar', room(mix(lp(roar, 800) * env(1.4, 0.08, 0.6) * 1.2, bronze(220, 1.4) * 0.3), 0.35, 1.2))
    save('bull_crash', room(mix(lp(noise(1.0), 300) * env(1.0, 0.002, 0.3) * 3, bronze(160, 1.2) * 0.8, bronze(410, 0.8) * 0.4,
                                hp(noise(0.3), 1500) * env(0.3, 0.001, 0.06) * 0.6), 0.3, 1.0))
    save('bull_daze', room(mix(*[at(bronze(1900 + 300 * k, 0.5) * 0.3, 0.12 * k) for k in range(5)]), 0.3, 0.8), 0.6)
    save('boss_hit', mix(bronze(330, 0.6) * 0.8, lp(noise(0.15), 2000) * env(0.15, 0.001, 0.04) * 1.2), 0.85)
    save('boss_burn', room(mix(lp(noise(0.7), 1200) * env(0.7, 0.005, 0.25) * 1.4, bronze(280, 0.8) * 0.6, sweep(500, 150, 0.6, 'saw') * env(0.6, 0.005, 0.2) * 0.3), 0.3, 0.8))
    save('boss_die', room(mix(lp(noise(3.0), 250) * env(3.0, 0.01, 1.2) * 2.5, bronze(110, 3.0) * 0.8, bronze(165, 2.5) * 0.5,
                              sweep(120, 40, 3.0, 'saw') * env(3.0, 0.05, 1.0) * 0.4), 0.4, 2.0))
    save('statue_break', room(mix(lp(noise(1.2), 600) * env(1.2, 0.002, 0.4) * 2, *[at(bp(noise(0.1), 500, 3000) * env(0.1, 0.001, 0.03), 0.05 * k + rng.uniform(0, 0.05)) * 0.6
                                                                                   for k in range(10)], bronze(300, 1.0) * 0.5), 0.3, 1.0))
    save('god_rumble', room(lp(noise(3.0), 120) * env(3.0, 0.6, 1.2) * 3 + sweep(55, 45, 3.0) * env(3.0, 0.5, 1.2), 0.4, 2.0))
    # --- sleepers
    save('snore', snore(1.0, 0), 0.8)
    save('snore_small', snore(1.7, 1), 0.7)
    print('sfx done', len([f for f in os.listdir(OUT) if f.endswith('.wav')]))


if __name__ == '__main__':
    build()
