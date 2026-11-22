"""Chapter two's sound: the score for the Hill of Sleepers (the road and the hilltop, the tomb,
the Sleepless King, and the one breath of dawn), the wind that blows over the dead, and every
new noise the chapter makes, written and synthesised the same way as the rest.

  python3 hill.py [music] [sfx] [amb]     (nothing = all three)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import music as M
import sfx as S
import ambience as A
from music import Song, key_of, CH, harp_arp, pad, bassline

XYLO, MARIMBA, TUBULAR, TREMOLO, FRHORN, AAHS = 13, 12, 14, 44, 60, 52

CH.update({
    'Db': ['Db3', 'Ab3', 'Db4', 'F4', 'Ab4'], 'Ab': ['Ab2', 'Eb3', 'Ab3', 'C4', 'Eb4'], 'Bm': ['B2', 'F#3', 'B3', 'D4', 'F#4'],
    'Asus': ['A2', 'E3', 'A3', 'D4', 'E4'],
})


# ------------------------------------------------------------------ the road and the hilltop
def hill(dream=False):
    """D Phrygian, slow: a low reed over a drone, a plucked tick like a clock nobody winds, and now
    and then four dry notes on wood, because there are a great many bones up here."""
    s = Song('hill' + ('_dream' if dream else ''), 76, 16)
    if not dream:
        s.track('mel', M.CLARINET, 0.8, 0.1); s.track('tick', M.PIZZ, 0.6, -0.3); s.track('bones', XYLO, 0.45, 0.35)
        s.track('pad', M.SLOWSTR, 0.42, 0); s.track('bass', M.CONTRABASS, 0.6, 0); s.track('perc', M.DRUMS, 0.5, 0)
    else:
        s.track('mel', M.OOHS, 0.5, 0.1); s.track('tick', M.CELESTA, 0.55, -0.3); s.track('bones', M.MUSICBOX, 0.4, 0.35)
        s.track('pad', M.GLASS, 0.5, 0); s.track('bass', M.GLASS, 0.35, 0); s.track('perc', M.DRUMS, 0.25, 0)
    mel = """D4:2 Eb4 F4 | G4:3 F4 | Eb4:1.5 D4:.5 C4 Eb4 | D4:3 r |
A4:2 Bb4 A4 | G4:2 F4 Eb4 | F4 G4:.5 F4:.5 Eb4 D4 | D4:3 r |
D5:1.5 C5:.5 Bb4 A4 | Bb4:2 A4 G4 | A4 G4:.5 F4:.5 Eb4 F4 | G4:3 r |
F4 G4 A4:1.5 G4:.5 | F4 Eb4 D4:2 | Eb4 F4 Eb4:.5 D4:.5 C4 | D4:4"""
    s.line('mel', 0, mel, 80, shift=12 if dream else 0)
    harm = ['Dm', 'Gm', 'Cm', 'Dm', 'Dm', 'Gm', 'Eb', 'Dm', 'Bb', 'Gm', 'Cm', 'Gm', 'Dm', 'Bb', 'Eb', 'Dm']
    for b, ch in enumerate(harm):
        ks = [key_of(k) for k in CH[ch]]
        st = b * 4
        s.chord('pad', st, 3.95, ks[1:4], 38)
        s.note('bass', st, 3.9, ks[0] - 12, 58)
        # the tick: off the beat, never quite in a hurry
        for (t, k) in ((0.5, 2), (1.5, 3), (2.5, 2), (3.5, 4)):
            s.note('tick', st + t, 0.3, ks[k] + (12 if dream else 0), 58 - (6 if t > 2 else 0))
        if b % 4 == 3:
            for i, k in enumerate((4, 2, 3, 1)):
                s.note('bones', st + 2 + i * 0.5, 0.3, ks[k] + 12, 66 - i * 4)
        if not dream:
            s.hits('perc', st, 'x.......', M.DOUM, 62); s.hits('perc', st, '.....o..', M.TEK, 50)
            if b % 2 == 1:
                s.hits('perc', st, '......oo', M.RIQ, 34)
        elif b % 4 == 0:
            s.hits('perc', st, 'x', M.TRI, 34)
    return s


# ------------------------------------------------------------------ the tomb
def tomb(dream=False):
    """C minor, the second step flat: a cello that will not leave one note alone, a bell every
    fourth bar for whoever is counting, voices a long way off."""
    s = Song('tomb' + ('_dream' if dream else ''), 92, 16)
    if not dream:
        s.track('ost', M.CELLO, 0.7, -0.15); s.track('low', M.CONTRABASS, 0.6, 0); s.track('bell', TUBULAR, 0.5, 0.2); s.track('choir', AAHS, 0.42, 0)
        s.track('mel', M.OBOE, 0.6, 0.15); s.track('perc', M.DRUMS, 0.6, 0)
    else:
        s.track('ost', M.MUSICBOX, 0.55, -0.15); s.track('low', M.GLASS, 0.45, 0); s.track('bell', M.CELESTA, 0.5, 0.2); s.track('choir', M.PAD_CHOIR, 0.5, 0)
        s.track('mel', M.OOHS, 0.5, 0.15); s.track('perc', M.DRUMS, 0.3, 0)
    harm = ['Cm', 'Cm', 'Fm', 'Cm', 'Eb', 'Fm', 'G', 'G', 'Cm', 'Bbm', 'Fm', 'Cm', 'Fm', 'G', 'Cm', 'Cm']
    ost = [0, 0, 7, 0, 1, 0, 7, 0]
    for b, ch in enumerate(harm):
        root = key_of(CH[ch][0])
        st = b * 4
        for i, k in enumerate(ost):
            s.note('ost', st + i * 0.5, 0.42, root + 12 + k + (12 if dream else 0), 72 - (i % 2) * 12)
        s.note('low', st, 3.9, root - 12 if root > 40 else root, 60)
        if b % 4 == 0:
            s.note('bell', st, 3.5, key_of('C4') if not dream else key_of('C6'), 74)
        if b % 2 == 0:
            s.chord('choir', st, 7.9, [key_of(k) for k in CH[ch][2:5]], 34)
        if not dream:
            s.hits('perc', st, 'x.....x.', M.DOUM, 70); s.hits('perc', st, '....o...', M.TEK, 52)
            if b % 4 == 3:
                s.note('perc', st + 3, 1, M.TIMPANI if False else M.DOUM, 84)
        elif b % 2 == 0:
            s.hits('perc', st, 'x', M.TRI, 32)
    s.line('mel', 16, """C5:2 Db5 Eb5 | F5:3 Eb5 | D5:2 C5 B4 | D5:4 | r:16 |
G5:2 F5 Eb5 | Db5:3 C5 | Bb4 C5 Db5 Eb5 | C5:4""", 76, shift=0)
    return s


# ------------------------------------------------------------------ the Sleepless King
def king():
    """G minor at a march: kettledrums, low brass that lands on every bar like a foot coming down,
    and a tune in the horns that is plainly somebody's own idea of his own importance."""
    s = Song('king', 132, 16)
    s.track('str', TREMOLO, 0.7, -0.1); s.track('brass', M.TROMBONE, 0.75, 0.15); s.track('low', M.CONTRABASS, 0.7, 0); s.track('mel', FRHORN, 0.8, 0.1)
    s.track('choir', AAHS, 0.5, 0); s.track('timp', M.TIMPANI, 0.85, 0); s.track('bell', TUBULAR, 0.5, -0.2); s.track('perc', M.DRUMS, 0.7, 0)
    harm = ['Gm', 'Gm', 'Eb', 'D', 'Gm', 'Cm', 'Eb', 'D', 'Cm', 'Gm', 'Eb', 'D', 'Gm', 'Eb', 'Cm', 'D']
    for b, ch in enumerate(harm):
        ks = [key_of(k) for k in CH[ch]]
        root = ks[0]
        st = b * 4
        for i in range(8):
            s.note('str', st + i * 0.5, 0.45, root + 12 + (0, 7, 12, 7)[i % 4], 78 - (i % 2) * 10)
        s.note('low', st, 0.9, root - 12 if root - 12 >= 28 else root, 96); s.note('low', st + 1.5, 0.45, root, 80); s.note('low', st + 2, 0.9, root - 12 if root - 12 >= 28 else root, 90)
        s.note('low', st + 3, 0.9, root - 5, 82)
        s.chord('brass', st, 0.9, [root, root + 7], 98)
        if b % 2 == 1:
            s.chord('brass', st + 2.5, 0.4, [root + 12, root + 19], 92); s.chord('brass', st + 3, 0.9, [root + 12, root + 19], 100)
        # kettledrums: tonic and fifth, the way a procession is paced
        s.note('timp', st, 0.9, key_of('G2'), 104); s.note('timp', st + 1.5, 0.4, key_of('D2') + 12, 84); s.note('timp', st + 2, 0.9, key_of('G2'), 96)
        if b % 4 == 3:
            for i in range(6):
                s.note('timp', st + 2.5 + i * 0.25, 0.22, key_of('D3'), 70 + i * 7)
        s.hits('perc', st, 'x...x...', M.KICK, 96); s.hits('perc', st, '..x...x.', M.SNARE, 70); s.hits('perc', st, 'x.xxx.xx', M.DOUM, 66)
        if b % 4 == 0:
            s.chord('choir', st, 3.9, ks[2:5], 62); s.note('bell', st, 3.8, key_of('G3'), 80)
        if b % 8 == 0:
            s.note('perc', st, 2, M.CRASH, 86)
    s.line('mel', 0, """G4:1.5 G4:.5 Bb4 D5 | Eb5:2 D5:.5 C5:.5 Bb4 | G4:1.5 G4:.5 Bb4 Eb5 | D5:3 r |
G5:1.5 F5:.5 Eb5 D5 | C5:2 Eb5 G5 | F5 Eb5:.5 D5:.5 C5 Bb4 | A4:3 r |
C5:1.5 C5:.5 Eb5 G5 | D5:2 Bb4 G4 | Eb5:1.5 D5:.5 C5 Bb4 | F#4:3 r |
G4:1.5 A4:.5 Bb4 D5 | Eb5:2 G5:2 | C5 Eb5 D5:.5 C5:.5 Bb4 | A4:2 D5:2""", 100)
    return s


# ------------------------------------------------------------------ one breath of dawn
def dawn():
    """The theme, in the major at last and on a horn: alone for four bars, then with everything.
    It ends on the chord before the last one, since so does the morning."""
    s = Song('dawn', 70, 16)
    s.track('horn', FRHORN, 0.9, 0.05); s.track('harp', M.HARP, 0.8, -0.25); s.track('pad', M.SLOWSTR, 0.6, 0); s.track('bass', M.CELLO, 0.55, 0)
    s.track('choir', M.OOHS, 0.45, 0); s.track('mel', M.FLUTE, 0.6, 0.2); s.track('timp', M.TIMPANI, 0.5, 0)
    s.line('horn', 0, """D4:1.5 E4:.5 F#4 A4 | D5:3 r | B4:1.5 A4:.5 F#4 A4 | E4:3 r |
D4:1.5 E4:.5 F#4 G4 | A4:2 G4:.5 F#4:.5 E4 | D4 E4:.5 D4:.5 C#4 B3 | A3:4""", 92)
    s.line('mel', 32, """D5:1.5 E5:.5 F#5 A5 | B5:2 A5:.5 G5:.5 F#5 | G5 F#5:.5 E5:.5 D5 E5 | F#5:3 r |
G5:1.5 F#5:.5 E5 D5 | C#5 D5:.5 C#5:.5 B4 A4 | B4 C#5 D5:.5 E5:.5 F#5:.5 E5:.5 | E5:4""", 84)
    s.line('horn', 32, """F#4:2 A4:2 | D5:2 D5:2 | B4:2 G4:2 | A4:3 r | B4:2 G4:2 | E4:2 A4:2 | G4:2 A4:2 | A4:4""", 78)
    harm = ['D', 'D', 'G', 'A', 'D', 'Bm', 'G', 'A', 'D', 'G', 'G', 'D', 'G', 'A', 'G', 'Asus']
    CHM = {'D': ['D3', 'A3', 'D4', 'F#4', 'A4'], 'G': ['G2', 'D3', 'G3', 'B3', 'D4'], 'A': ['A2', 'E3', 'A3', 'C#4', 'E4'], 'Bm': CH['Bm'], 'Asus': CH['Asus']}
    for b, ch in enumerate(harm):
        ks = [key_of(k) for k in CHM[ch]]
        st = b * 4
        if b >= 4:
            for i, idx in enumerate((0, 1, 2, 3, 4, 3, 2, 1)):
                s.note('harp', st + i * 0.5, 0.9, ks[idx], 54)
            s.chord('pad', st, 3.95, ks[1:4], 40 + (8 if b >= 8 else 0))
            s.note('bass', st, 3.9, ks[0], 58)
        else:
            s.note('bass', st, 3.9, ks[0] - 12 if ks[0] > 40 else ks[0], 40)
        if b >= 8:
            s.chord('choir', st, 3.9, ks[2:5], 38)
        if b in (4, 8, 12):
            for i in range(6):
                s.note('timp', st - 1.5 + i * 0.25, 0.22, key_of('D3') if b != 12 else key_of('A2'), 50 + i * 7)
            s.note('timp', st, 1.5, key_of('D3'), 84)
    return s


TRACKS = {
    'hill': lambda: (hill(False), dict(rev=0.34, rt=2.8)),
    'hill_dream': lambda: (hill(True), dict(rev=0.62, rt=3.6)),
    'tomb': lambda: (tomb(False), dict(rev=0.4, rt=3.0)),
    'tomb_dream': lambda: (tomb(True), dict(rev=0.62, rt=3.6)),
    'king': lambda: (king(), dict(rev=0.24, rt=2.0)),
    'dawn': lambda: (dawn(), dict(rev=0.4, rt=3.0)),
}


def build_music(names=None):
    for n in names or list(TRACKS):
        song, kw = TRACKS[n]()
        a = M.render(song, loop=True, **kw)
        if n == 'king':
            # the kettledrums stand so far above everything else that the march came out quiet: press them down into it
            a = (np.tanh(a * 2.2) / np.tanh(2.2) * 0.80).astype(np.float32)
        M.write_wav(f'/tmp/{n}.wav', a)
        os.system(f'ffmpeg -loglevel error -y -i /tmp/{n}.wav -c:a libvorbis -q:a 6 {M.OUT}/{n}.ogg && rm /tmp/{n}.wav')
        rms = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
        print(n, round(len(a) / M.SR, 1), 's', 'rms %.1f dB' % rms, flush=True)


# ------------------------------------------------------------------ the noises
def horn_call():
    """The Dawn Horn: a goat's horn, so it cracks on the way up, and then it holds, and holds."""
    crack = S.sf_note(FRHORN, [56], 0.12, 84)
    call = S.sf_note(FRHORN, [57, 45], 3.4, 118)
    high = S.at(S.sf_note(FRHORN, [64], 2.4, 92), 1.0)
    breath = S.bp(S.noise(0.25), 400, 2500) * S.env(0.25, 0.02, 0.08) * 0.08
    x = S.mix(breath, crack * 0.5, S.at(call, 0.16), S.at(high * 0.55, 0.16))
    return S.room(x, 0.5, 2.6)


def build_sfx():
    s = S.save
    t = S.t_(0.8)
    # the unremembered: more breath than voice
    moan = S.bp(S.noise(0.8), 260, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 5.5 * t)) * S.env(0.8, 0.2, 0.3)
    s('shade', S.room(S.mix(moan, S.sweep(190, 140, 0.8, 'tri') * S.env(0.8, 0.25, 0.3) * 0.3), 0.45, 1.4), 0.5)
    s('shade_hit', S.room(S.mix(S.bp(S.noise(0.3), 500, 2600) * S.env(0.3, 0.004, 0.09), S.sweep(520, 190, 0.3) * S.env(0.3, 0.004, 0.1) * 0.4), 0.4, 0.9), 0.6)
    # a blade through a ghost: nothing there to hit
    s('ghost_pass', S.room(S.mix(S.hp(S.noise(0.35), 1800) * S.env(0.35, 0.03, 0.1) * 0.7, S.sweep(240, 110, 0.5) * S.env(0.5, 0.05, 0.2) * 0.5), 0.5, 1.2), 0.6)
    # fired clay: struck, and broken
    s('clay_hit', S.mix(S.tone(430, 0.2, ((1, 1), (2.4, 0.5), (4.1, 0.3)), 0.05), S.lp(S.noise(0.1), 700) * S.env(0.1, 0.001, 0.03) * 1.4), 0.75)
    s('clay_wake', S.room(S.mix(*[S.at(S.bp(S.noise(0.08), 900, 3600) * S.env(0.08, 0.001, 0.02) * 0.6, 0.07 * k + S.rng.uniform(0, 0.04)) for k in range(7)],
                               S.lp(S.noise(0.6), 300) * S.env(0.6, 0.05, 0.25) * 1.5), 0.3, 0.8), 0.7)
    s('scarab', S.mix(*[S.at(S.hp(S.noise(0.014), 3200) * S.env(0.014, 0.0005, 0.004), 0.034 * k) * (1 - 0.1 * k) for k in range(6)]), 0.4)
    # the king
    s('king_slam', S.room(S.mix(S.lp(S.noise(1.2), 220) * S.env(1.2, 0.002, 0.4) * 3, S.bronze(92, 1.4) * 0.9, S.sweep(90, 34, 1.0) * S.env(1.0, 0.004, 0.4) * 1.2,
                                S.hp(S.noise(0.2), 1800) * S.env(0.2, 0.001, 0.05) * 0.4), 0.35, 1.4))
    s('king_wave', S.room(S.bp(S.noise(0.7), 180, 1300) * S.env(0.7, 0.12, 0.25) * np.linspace(0.6, 1.3, int(0.7 * S.SR)), 0.3, 0.8), 0.55)
    s('bolt', S.room(S.mix(S.sweep(980, 300, 0.4) * S.env(0.4, 0.004, 0.14) * 0.6, S.hp(S.noise(0.3), 2600) * S.env(0.3, 0.004, 0.08) * 0.5,
                            S.tone(1760, 0.5, ((1, 0.5), (1.5, 0.3)), 0.12) * 0.4), 0.35, 0.9), 0.6)
    s('bolt_burst', S.room(S.mix(*[S.tone(f, 0.35, ((1, 1),), 0.06) * 0.4 for f in (2100, 2790, 3520)], S.hp(S.noise(0.12), 3000) * S.env(0.12, 0.001, 0.03)), 0.35, 0.7), 0.55)
    s('crown_hit', S.room(S.mix(S.bronze(1650, 0.6), S.bronze(2480, 0.4) * 0.5, S.lp(S.noise(0.04), 4000) * S.env(0.04, 0.001, 0.01)), 0.25, 0.6), 0.75)
    s('crown', S.room(S.mix(S.bronze(1480, 1.3), S.bronze(2210, 1.0) * 0.6, S.at(S.bronze(1560, 0.7) * 0.6, 0.24), S.at(S.bronze(1620, 0.5) * 0.4, 0.4),
                            S.at(S.bronze(1660, 0.4) * 0.25, 0.5), S.at(S.lp(S.noise(0.06), 900) * S.env(0.06, 0.001, 0.02), 0.24)), 0.35, 1.2), 0.85)
    s('king_tired', S.room(S.mix(S.lp(S.noise(1.6), 500) * S.env(1.6, 0.3, 0.6) * 1.2, S.sweep(120, 62, 1.6, 'saw') * S.env(1.6, 0.2, 0.6) * 0.3), 0.45, 1.8), 0.6)
    # the hill: a stone name read, a door that has not moved in four hundred years
    s('stone_door', S.room(S.mix(S.lp(S.noise(3.0), 140) * S.env(3.0, 0.3, 1.1) * 3, S.lp(S.sweep(70, 48, 2.8, 'saw'), 300) * S.env(2.8, 0.4, 1.0) * 0.6,
                                 S.bp(S.noise(2.4), 300, 1100) * S.env(2.4, 0.5, 0.7) * 0.25 * (1 + 0.5 * np.sin(2 * np.pi * 19 * S.t_(2.4))),
                                 S.at(S.lp(S.noise(0.3), 200) * S.env(0.3, 0.002, 0.1) * 3, 2.5)), 0.35, 1.6))
    s('lyre', S.room(S.sf_note(M.HARP, [62], 2.4, 96), 0.45, 2.2), 0.75)
    s('ghost_sigh', S.room(S.mix(S.lp(S.noise(3.0), 900) * S.env(3.0, 1.0, 1.0) * 0.8, *[np.sin(2 * np.pi * f * S.t_(3.0) * (1 - 0.12 * S.t_(3.0) / 3.0)) * S.env(3.0, 0.9, 1.0) * 0.12
                                                                                         for f in (220, 277, 330, 440)]), 0.55, 2.4), 0.7)
    # the dawn
    s('horn', horn_call(), 0.95)
    d = 4.5
    tt = S.t_(d)
    swell = sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((146.8, 0.5), (220, 0.4), (293.7, 0.35), (370, 0.3), (440, 0.25), (587.3, 0.15))) * S.env(d, 1.6, 1.3, 0.4)
    glint = sum(np.sin(2 * np.pi * f * tt) * np.exp(-np.maximum(0, tt - 1.6) / 0.9) * np.minimum(1, tt / 1.6) * 0.08 for f in (1175, 1480, 1760))
    s('dawn_swell', S.room(S.mix(swell, glint, S.hp(S.noise(d), 5000) * S.env(d, 1.8, 1.0) * 0.03), 0.5, 2.6), 0.75)
    print('hill sfx done')


def build_amb():
    """Wind over the hill: low, with a hollow note in it where it crosses the mouths of the tombs."""
    D = A.L + 2
    n = int(D * A.SR)
    t = np.arange(n) / A.SR
    w = A.wind(D, low=True) * 0.9
    r = np.random.default_rng(23)
    hollow = []
    for ch in range(2):
        k = np.maximum(0, np.sin(2 * np.pi * t / (9.0 + ch * 2) + ch * 1.3)) ** 3
        hollow.append(S.bp(r.normal(0, 1, n), 300 + ch * 40, 420 + ch * 50, 2) * k * 1.6)
    A.write('wind', w + A.stereo(*hollow), 0.42)
    print('hill ambience done')


if __name__ == '__main__':
    what = sys.argv[1:] or ['music', 'sfx', 'amb']
    names = [w for w in what if w in TRACKS]
    if 'sfx' in what: build_sfx()
    if 'amb' in what: build_amb()
    if 'music' in what: build_music()
    elif names: build_music(names)
