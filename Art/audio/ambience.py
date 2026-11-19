"""Night ambience beds, 24-second seamless loops: crickets over the town, the sea at the
cliffs, wind on the terraces and in the temple yard, water dripping inside the ziggurat."""
import os
import numpy as np
from scipy.signal import butter, sosfilt
import sfx as S

SR = 44100
OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Audio'
L = 24.0
rng = np.random.default_rng(5)


def loopify(x, fade=2.0):
    """Crossfade the tail over the head so the loop has no seam."""
    n = int(fade * SR)
    body = x[:-n].copy()
    w = np.linspace(0, 1, n)
    body[:n] = body[:n] * w + x[-n:] * (1 - w)
    return body


def stereo(l, r):
    return np.stack([l, r], axis=1)


def crickets(dur):
    out = np.zeros((int(dur * SR), 2))
    for k in range(7):
        f = rng.uniform(3900, 5200)
        pan = rng.uniform(0.15, 0.85)
        vol = rng.uniform(0.15, 0.5)
        t = rng.uniform(0, 1.0)
        rate = rng.uniform(0.7, 1.6)
        while t < dur:
            for c in range(3):
                d = 0.045
                st = int((t + c * 0.075) * SR)
                n = int(d * SR)
                if st + n >= len(out):
                    break
                tt = np.arange(n) / SR
                chirp = np.sin(2 * np.pi * f * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * tt)) * np.sin(np.pi * tt / d)
                out[st:st + n, 0] += chirp * vol * (1 - pan)
                out[st:st + n, 1] += chirp * vol * pan
            t += rate * rng.uniform(0.8, 1.25)
    return out


def sea(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    base = S.lp(rng.normal(0, 1, n), 700) * 0.6
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 6.0) ** 2
    foam = S.hp(rng.normal(0, 1, n), 3000) * 0.18 * np.maximum(0, np.sin(2 * np.pi * t / 6.0 + 0.6)) ** 4
    l = (base * swell + foam)
    r = (S.lp(rng.normal(0, 1, n), 700) * 0.6 * (0.55 + 0.45 * np.sin(2 * np.pi * t / 6.0 + 0.4) ** 2) + foam * 0.8)
    return stereo(l, r)


def wind(dur, low=False):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        x = rng.normal(0, 1, n)
        k = 0.5 + 0.5 * np.sin(2 * np.pi * t / (7.0 + ch) + ch) * np.sin(2 * np.pi * t / 11.0)
        lo = S.lp(x, 380 if low else 600)
        hi = S.bp(rng.normal(0, 1, n), 900, 2200) * 0.25 * (k ** 2)
        out.append(lo * (0.4 + 0.6 * k) + (0 if low else hi))
    return stereo(*out)


def drips(dur):
    n = int(dur * SR)
    out = np.zeros((n, 2))
    hum = S.lp(rng.normal(0, 1, n), 120) * 0.25
    out[:, 0] += hum; out[:, 1] += hum
    t = 0.3
    while t < dur - 1:
        f = rng.uniform(1100, 2300)
        d = 0.25
        tt = np.arange(int(d * SR)) / SR
        plink = np.sin(2 * np.pi * f * (1 - 0.25 * tt / d) * tt) * np.exp(-tt / 0.04)
        plink = S.room(plink, 0.5, 1.2)
        st = int(t * SR)
        pan = rng.uniform(0.2, 0.8)
        e = min(n, st + len(plink))
        out[st:e, 0] += plink[:e - st] * 0.5 * (1 - pan)
        out[st:e, 1] += plink[:e - st] * 0.5 * pan
        t += rng.uniform(0.9, 3.2)
    return out


def write(name, x, vol=0.5):
    x = np.stack([loopify(x[:, 0]), loopify(x[:, 1])], axis=1)
    x = x / (np.abs(x).max() + 1e-9) * vol
    import wave
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    path = f'/tmp/amb_{name}.wav'
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    os.system(f'ffmpeg -loglevel error -y -i {path} -c:a libvorbis -q:a 4 {OUT}/amb_{name}.ogg && rm {path}')


if __name__ == '__main__':
    D = L + 2
    write('night', crickets(D) + wind(D, low=True) * 0.25, 0.42)
    write('sea', sea(D) + crickets(D) * 0.25, 0.5)
    write('hills', wind(D) + crickets(D) * 0.6, 0.45)
    write('temple', wind(D, low=True), 0.4)
    write('dungeon', drips(D), 0.5)
    # footsteps: a soft sandal on stone, two variants
    for i in range(2):
        st = S.mix(S.lp(S.noise(0.08), 900 + i * 300) * S.env(0.08, 0.002, 0.02), S.bp(S.noise(0.05), 2000, 5000) * S.env(0.05, 0.001, 0.01) * 0.3)
        S.save(f'step{i}', st, 0.35)
    print('ambience done')
