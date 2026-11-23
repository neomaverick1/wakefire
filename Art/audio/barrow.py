"""The Generals' Barrow: its music, waking and dreaming, and its sounds (the two armies, the Last
Piece being moved, Nod's Pocket and what comes out of it).

  python3 barrow.py [resources dir]     (default: the game's Resources; Music/ and Audio/ under it)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import music as M
import sfx as S
from music import Song, key_of, CH

SR = S.SR


# ------------------------------------------------------------------ music
def barrow(dream=False):
    """G minor at a slow march. Two drums that have never agreed: Ushur's low one on the left keeps
    four, Baltu's high one on the right keeps three, and they only land together once in twelve
    beats. A horn calls from the left; a trumpet answers from the right with the same call, its last
    two notes the other way round."""
    s = Song('barrow' + ('_dream' if dream else ''), 72, 16)
    if not dream:
        s.track('red', M.DRUMS, 0.62, -0.55); s.track('blue', M.DRUMS, 0.5, 0.55)
        s.track('low', M.CONTRABASS, 0.55, 0); s.track('drone', M.CELLO, 0.45, 0)
        s.track('horn', M.HORN, 0.42, -0.35); s.track('trumpet', M.TRUMPET, 0.3, 0.35)
        s.track('mel', M.OBOE, 0.5, 0.05)
    else:
        s.track('red', M.DRUMS, 0.22, -0.55); s.track('blue', M.DRUMS, 0.22, 0.55)
        s.track('low', M.PAD_CHOIR, 0.42, 0); s.track('drone', M.GLASS, 0.4, 0)
        s.track('horn', M.PAD_NEWAGE, 0.36, -0.35); s.track('trumpet', M.CELESTA, 0.4, 0.35)
        s.track('mel', M.OOHS, 0.5, 0.05)
    harm = ['Gm', 'Gm', 'Gm', 'Gm', 'Cm', 'Cm', 'Gm', 'Gm', 'Eb', 'Eb', 'D', 'D', 'Gm', 'Gm', 'D', 'Gm']
    for b, ch in enumerate(harm):
        st = b * 4
        root = key_of(CH[ch][0])
        s.note('low', st, 3.95, root if root >= 31 else root + 12, 54)
        s.chord('drone', st, 3.95, [key_of(CH[ch][1]), key_of(CH[ch][2])], 44)
        if not dream:
            s.hits('red', st, 'x...x.o.', M.DOUM, 66)                       # four, and sure of it
        elif b % 2 == 0:
            s.hits('red', st, 'x', M.TRI, 34)
    # three against it, all the way down
    t = 0.0
    k = 0
    while t < s.length - 0.01:
        if not dream:
            s.note('blue', t, 0.4, M.TEK, 58 if k % 2 == 0 else 40)
            if k % 4 == 3:
                s.note('blue', t + 0.75, 0.3, M.KA, 34)
        elif k % 4 == 1:
            s.note('blue', t, 0.4, M.FINGER, 30)
        t += 1.5; k += 1
    up = 12 if dream else 0
    call = "D4:1.5 G4:.5 Bb4:2 | A4:1 G4:1 D4:2"
    answer = "D4:1.5 G4:.5 Bb4:2 | G4:1 A4:1 Eb4:2"                           # the same call. Nearly.
    s.line('horn', 8, call, 70, shift=up)
    s.line('trumpet', 16, answer, 64, shift=up)
    s.line('horn', 40, "D4:1.5 A4:.5 D5:2 | C5:1 Bb4:1 A4:2", 72, shift=up)
    s.line('trumpet', 48, "D4:1.5 A4:.5 D5:2 | Bb4:1 C5:1 A4:2", 64, shift=up)
    s.line('mel', 24, "G4:2 A4 Bb4 | C5:2 Bb4 A4 | G4:3 F#4 | G4:4", 62, shift=up)
    s.line('mel', 56, "A4:2 Bb4 A4 | G4:4", 60, shift=up)
    return s


TRACKS = {
    'barrow': lambda: (barrow(False), dict(rev=0.4, rt=2.8)),
    'barrow_dream': lambda: (barrow(True), dict(rev=0.65, rt=3.8)),
}


# ------------------------------------------------------------------ sounds
def chime(freqs, step=0.07, d=0.7, decay=6.0):
    """A few glass notes, one after another."""
    parts = []
    for i, f in enumerate(freqs):
        t = S.t_(d)
        parts.append(S.at((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * decay), i * step))
    return S.mix(*parts)


def cloth(d=0.18, lo=500, hi=2600):
    return S.bp(S.noise(d), lo, hi) * S.env(d, 0.02, d * 0.5)


def drag(d, lo=90, hi=900, rate=22):
    """Stone on stone: a low scrape that sticks and slips."""
    t = S.t_(d)
    stick = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * rate * t + 3 * np.sin(2 * np.pi * 3 * t)))
    return S.bp(S.noise(d), lo, hi) * stick * S.env(d, 0.03, d * 0.8)


def knock(f, d=0.22, amp=1.0):
    """A drum, or a knuckle on a board, or a piece of fired clay set down: a short pitched thump."""
    t = S.t_(d)
    body = np.sin(2 * np.pi * (f * (1 + 0.6 * np.exp(-t * 40))) * t) * np.exp(-t * 16)
    return (body + S.lp(S.noise(d), f * 6) * S.env(d, 0.001, 0.02) * 0.5) * amp


def build_sfx():
    s = S.save
    # ---- Nod's Pocket
    s('pocket_in', S.room(S.mix(cloth(0.2) * 0.8, S.at(chime((1318.5, 1046.5, 784.0), 0.06, 0.6), 0.05) * 0.6), 0.2, 0.9), 0.7)
    s('pocket_use', S.room(S.mix(cloth(0.16) * 0.7, S.at(chime((784.0, 1046.5, 1318.5), 0.055, 0.6), 0.04) * 0.6), 0.2, 0.9), 0.7)
    s('pocket_keep', S.room(chime((1046.5, 1568.0), 0.11, 0.8, 5.0), 0.25, 1.1), 0.55)
    s('plank_down', S.room(S.mix(knock(196, 0.3, 0.9), S.at(chime((392.0, 587.33), 0.05, 0.9, 4.0) * 0.5, 0.02), S.lp(S.noise(0.12), 500) * S.env(0.12, 0.002, 0.05)), 0.25, 1.0), 0.8)
    t = S.t_(1.1)
    whoomp = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 5)) * t) * S.env(1.1, 0.06, 0.5)
    s('blue_lit', S.room(S.mix(whoomp * 0.9, S.hp(S.noise(0.9), 3000) * S.env(0.9, 0.12, 0.5) * 0.35, S.at(chime((466.16, 698.46), 0.12, 1.0, 3.5) * 0.4, 0.1)), 0.3, 1.4), 0.8)
    # ---- the camps
    rope = S.bp(S.sweep(900, 500, 0.5, 'saw'), 400, 2400) * S.env(0.5, 0.03, 0.3) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 26 * S.t_(0.5))))
    s('standard_down', S.room(S.mix(rope * 0.5, S.at(cloth(0.5, 300, 1800) * 0.9, 0.25), S.at(S.lp(S.noise(0.2), 240) * S.env(0.2, 0.004, 0.08) * 2.0, 0.7)), 0.2, 0.8), 0.75)
    t = S.t_(0.62)
    whirl = S.bp(S.noise(0.62), 500, 2600) * (0.5 + 0.5 * np.sin(2 * np.pi * (5 + 14 * t / 0.62) * t)) * S.env(0.62, 0.1, 0.5)
    s('sling_wind', whirl, 0.5)
    # ---- the Last Piece: called, lifted, slid, set down; and rocking on its base when the move was not legal
    s('piece_call_a', S.room(S.mix(knock(92, 0.4, 1.0), S.at(knock(92, 0.4, 0.7), 0.16)), 0.3, 1.2), 0.85)
    s('piece_call_b', S.room(S.mix(knock(196, 0.3, 0.9), S.at(knock(196, 0.3, 0.6), 0.11), S.at(knock(196, 0.3, 0.6), 0.22)), 0.3, 1.2), 0.8)
    s('piece_lift', S.room(S.mix(drag(0.22, 200, 1600, 30) * 0.8, S.at(S.sweep(160, 420, 0.2) * S.env(0.2, 0.02, 0.12) * 0.25, 0.02)), 0.25, 0.9), 0.6)
    s('piece_slide', S.room(drag(0.5, 80, 800, 18), 0.25, 1.0), 0.8)
    s('piece_down', S.room(S.mix(knock(64, 0.5, 1.2), S.lp(S.noise(0.3), 300) * S.env(0.3, 0.002, 0.1) * 1.6, S.at(S.bp(S.noise(0.08), 700, 2600) * S.env(0.08, 0.001, 0.03) * 0.5, 0.01)), 0.3, 1.3), 0.9)
    wob = [S.at(knock(150 + 6 * k, 0.16, 1.0 - 0.07 * k), sum(0.2 * 0.84 ** j for j in range(k))) for k in range(11)]
    s('piece_illegal', S.room(S.mix(*wob), 0.25, 1.0), 0.75)


if __name__ == '__main__':
    res = sys.argv[1] if len(sys.argv) > 1 else '/srv/Wakefire/Assets/Wakefire/Resources'
    os.makedirs(f'{res}/Music', exist_ok=True); os.makedirs(f'{res}/Audio', exist_ok=True)
    S.OUT = f'{res}/Audio'
    build_sfx()
    print('sfx written')
    for n in TRACKS:
        song, kw = TRACKS[n]()
        a = M.render(song, loop=True, **kw)
        M.write_wav(f'/tmp/{n}.wav', a)
        os.system(f'ffmpeg -loglevel error -y -i /tmp/{n}.wav -c:a libvorbis -q:a 6 {res}/Music/{n}.ogg && rm /tmp/{n}.wav')
        rms = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
        print(n, round(len(a) / M.SR, 1), 's', 'rms %.1f dB' % rms, flush=True)
