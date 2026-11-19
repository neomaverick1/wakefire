"""WAKEFIRE's score, written note by note and played on a General MIDI soundfont.

Ashkel's music lives in the Hijaz mode (D Eb F# G A Bb C): the augmented second between Eb and
F# is the sound of the old Near East. Each place has a waking arrangement (ney flute, lyre-harp,
oud, frame drums, strings) and a dream arrangement of the very same notes (celesta, choir, glass,
bells, drowned in reverb), rendered to the same length so the game can crossfade between them
mid-phrase when Azar nods off.

Usage: python3 music.py [track ...]"""
import os
import sys
import math
import wave
import numpy as np
import tinysoundfont
from scipy.signal import fftconvolve, butter, sosfilt

SF2 = '/srv/Wakefire/Art/audio/GeneralUser-GS.sf2'
OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Music'
SR = 44100
NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

# General MIDI programs
HARP, NYLON, SITAR, KOTO, NEY, PANFLUTE, FLUTE, OBOE, CLARINET = 46, 24, 104, 107, 77, 75, 73, 68, 71
STRINGS, SLOWSTR, PIZZ, CELLO, CONTRABASS, ABASS = 48, 49, 45, 42, 43, 32
CHOIR, OOHS, PAD_WARM, PAD_CHOIR, GLASS, PAD_NEWAGE = 52, 53, 89, 91, 92, 88
CELESTA, GLOCK, VIBES, MUSICBOX, KALIMBA, BELLS = 8, 9, 11, 10, 108, 14
HORN, BRASS, TRUMPET, TROMBONE, TIMPANI, TAIKO, TOMS = 60, 61, 56, 57, 47, 116, 117
DRUMS = 'drums'
# percussion keys
DOUM, TEK, KA, RIQ, TAMB, CLAP, KICK, SNARE, HAT, CRASH, TRI, SHAKER, FINGER = 64, 62, 63, 70, 54, 39, 36, 38, 42, 49, 81, 82, 80


def key_of(name):
    """'F#4' -> MIDI number."""
    letter = name[0]
    acc = 0
    i = 1
    while i < len(name) and name[i] in '#b':
        acc += 1 if name[i] == '#' else -1
        i += 1
    octave = int(name[i:])
    return 12 * (octave + 1) + NOTE[letter] + acc


class Song:
    def __init__(self, name, bpm, bars, beats=4):
        self.name, self.bpm, self.bars, self.beats = name, bpm, bars, beats
        self.events = []      # (start beat, dur beats, track, key, vel)
        self.tracks = {}      # track name -> (program or DRUMS, volume 0..1, pan -1..1)

    @property
    def length(self):
        return self.bars * self.beats

    def track(self, name, program, vol=1.0, pan=0.0):
        self.tracks[name] = (program, vol, pan)

    def note(self, track, start, dur, key, vel=90):
        if isinstance(key, str):
            key = key_of(key)
        self.events.append((start, dur, track, key, vel))

    def line(self, track, start, text, vel=90, legato=0.96, shift=0):
        """Melody text: 'D5:1.5 Eb5:.5 F#5 G5 | r:2 A5:2' (default duration 1 beat; r = rest; | ignored)."""
        t = start
        for tok in text.split():
            if tok == '|':
                continue
            if ':' in tok:
                n, d = tok.split(':')
                d = float(d)
            else:
                n, d = tok, 1.0
            if n != 'r':
                accent = vel + (6 if abs(t - round(t)) < 1e-6 else 0)
                self.note(track, t, d * legato, key_of(n) + shift, min(127, accent))
            t += d
        return t

    def chord(self, track, start, dur, keys, vel=70):
        for k in keys:
            self.note(track, start, dur, k, vel)

    def hits(self, track, start, pattern, key, vel=90, step=0.5):
        """Drum pattern string: 'x' hit, 'o' soft hit, '.' rest, one char per step."""
        for i, ch in enumerate(pattern):
            if ch == 'x':
                self.note(track, start + i * step, step * 0.9, key, vel)
            elif ch == 'o':
                self.note(track, start + i * step, step * 0.9, key, int(vel * 0.6))


# ------------------------------------------------------------------ harmony helpers
CH = {
    'D': ['D3', 'A3', 'D4', 'F#4', 'A4'], 'Gm': ['G2', 'D3', 'G3', 'Bb3', 'D4'], 'Cm': ['C3', 'G3', 'C4', 'Eb4', 'G4'],
    'Eb': ['Eb3', 'Bb3', 'Eb4', 'G4', 'Bb4'], 'Bb': ['Bb2', 'F3', 'Bb3', 'D4', 'F4'], 'A7': ['A2', 'E3', 'G3', 'C#4', 'E4'],
    'Dm': ['D3', 'A3', 'D4', 'F4', 'A4'], 'F': ['F2', 'C3', 'F3', 'A3', 'C4'], 'C': ['C3', 'G3', 'C4', 'E4', 'G4'],
    'Am': ['A2', 'E3', 'A3', 'C4', 'E4'], 'G': ['G2', 'D3', 'G3', 'B3', 'D4'], 'E': ['E2', 'B2', 'E3', 'G#3', 'B3'],
    'Fm': ['F2', 'C3', 'F3', 'Ab3', 'C4'], 'Bbm': ['Bb2', 'F3', 'Bb3', 'Db4', 'F4'],
    'A': ['A2', 'E3', 'A3', 'C#4', 'E4'], 'Dm7': ['D3', 'A3', 'C4', 'F4', 'A4'], 'Gm7': ['G2', 'D3', 'F3', 'Bb3', 'D4'],
}


def harp_arp(s, track, bar, chord, vel=62, pattern=(0, 1, 2, 3, 4, 3, 2, 1), step=0.5, up=0):
    ks = [key_of(k) + up for k in CH[chord]]
    for i, idx in enumerate(pattern):
        s.note(track, bar * s.beats + i * step, step * 1.8, ks[idx % len(ks)], vel - (i % 2) * 6)


def pad(s, track, bar, chord, bars=1, vel=50, top=4):
    ks = CH[chord]
    s.chord(track, bar * s.beats, bars * s.beats * 0.98, ks[1:top + 1], vel)


def bassline(s, track, bar, chord, vel=78, pattern=((0, 2), (2, 2))):
    root = key_of(CH[chord][0])
    for (t, d) in pattern:
        s.note(track, bar * s.beats + t, d * 0.95, root, vel)


def maqsum(s, bar, vel=80, light=False):
    """The maqsum rhythm on frame drums: DOUM tek . tek DOUM . tek . (in eighths)."""
    st = bar * s.beats
    s.hits('perc', st, 'x..x....' if light else 'x..x....', DOUM, vel)
    s.hits('perc', st, '.o.o..o.' if light else '.x.x..x.', TEK, int(vel * 0.75))
    if not light:
        s.hits('perc', st, 'o.o.o.o.', RIQ, int(vel * 0.35))


# ------------------------------------------------------------------ the tracks
THEME_A = """D5:1.5 Eb5:.5 F#5 G5 | A5:2 G5:.5 F#5:.5 Eb5 | D5 Eb5:.5 D5:.5 C5 Bb4 | A4:3 r |
D5:1.5 Eb5:.5 F#5 A5 | Bb5:2 A5:.5 G5:.5 F#5 | G5 F#5:.5 Eb5:.5 D5 Eb5 | D5:4"""
THEME_B = """G4 A4 Bb4:1.5 A4:.5 | G4 F#4 Eb4:2 | F#4 G4 A4 Bb4:.5 C5:.5 | D5:3 r |
Eb5:1.5 D5:.5 C5 Bb4 | A4 Bb4:.5 A4:.5 G4 F#4 | G4 A4 Bb4:.5 A4:.5 G4:.5 F#4:.5 | D4:3 r"""
HARM = ['D', 'D', 'Cm', 'D', 'D', 'Gm', 'Cm', 'D', 'Gm', 'Eb', 'D', 'Gm', 'Cm', 'D', 'Gm', 'D']


def town(dream=False):
    s = Song('town' + ('_dream' if dream else ''), 84, 16)
    if not dream:
        s.track('mel', NEY, 0.95, 0.1); s.track('harp', HARP, 0.8, -0.3); s.track('oud', NYLON, 0.55, 0.35)
        s.track('pad', SLOWSTR, 0.42, 0); s.track('bass', CELLO, 0.55, -0.1); s.track('perc', DRUMS, 0.6, 0)
    else:
        s.track('mel', PANFLUTE, 0.7, 0.1); s.track('harp', CELESTA, 0.7, -0.3); s.track('oud', MUSICBOX, 0.45, 0.35)
        s.track('pad', CHOIR, 0.5, 0); s.track('bass', GLASS, 0.4, -0.1); s.track('perc', DRUMS, 0.4, 0)
    s.line('mel', 0, THEME_A, 92)
    s.line('mel', 32, THEME_B, 88)
    for b, ch in enumerate(HARM):
        harp_arp(s, 'harp', b, ch, 60 if not dream else 56, up=12 if dream else 0)
        pad(s, 'pad', b, ch, 1, 44)
        bassline(s, 'bass', b, ch, 70)
        st = b * 4
        # oud: a plucked answer on the off-beats
        root = key_of(CH[ch][2])
        for (t, k) in ((1.5, 0), (2.5, 7), (3.5, 12)):
            s.note('oud', st + t, 0.4, root + k - (0 if not dream else -12), 64)
        if dream:
            s.hits('perc', st, 'x.......', FINGER, 60)
            s.hits('perc', st, '....x...', TRI, 40)
        else:
            maqsum(s, b, 72, light=b % 8 in (0, 7))
    return s


def title():
    s = Song('title', 66, 16)
    s.track('mel', NEY, 0.9, 0.1); s.track('harp', HARP, 0.85, -0.25); s.track('pad', SLOWSTR, 0.5, 0); s.track('bass', CONTRABASS, 0.5, 0)
    s.track('perc', DRUMS, 0.4, 0)
    s.line('mel', 16, """D5:1.5 Eb5:.5 F#5 G5 | A5:2 G5:.5 F#5:.5 Eb5 | D5 Eb5:.5 D5:.5 C5 Bb4 | A4:4""", 84)
    s.line('mel', 48, """Eb5:1.5 D5:.5 C5 Bb4 | A4 Bb4:.5 A4:.5 G4 F#4 | G4 A4 Bb4:.5 A4:.5 G4:.5 F#4:.5 | D4:4""", 80)
    for b, ch in enumerate(['D', 'Eb', 'Cm', 'D'] * 4):
        harp_arp(s, 'harp', b, ch, 52, pattern=(0, 2, 3, 4, 3, 2, 1, 2))
        pad(s, 'pad', b, ch, 1, 40)
        s.note('bass', b * 4, 3.8, key_of(CH[ch][0]) - 12, 60)
        if b % 4 == 0:
            s.hits('perc', b * 4, 'x', TIMPANI if False else DOUM, 50)
    return s


def sea(dream=False):
    s = Song('sea' + ('_dream' if dream else ''), 66, 16, beats=3)   # 6/8 felt in dotted quarters: 3 beats = 1 bar of 6 eighths at 2x
    if not dream:
        s.track('mel', OBOE, 0.75, 0.15); s.track('harp', HARP, 0.85, -0.3); s.track('pad', STRINGS, 0.45, 0); s.track('bass', CELLO, 0.5, 0)
        s.track('perc', DRUMS, 0.35, 0)
    else:
        s.track('mel', VIBES, 0.65, 0.15); s.track('harp', CELESTA, 0.75, -0.3); s.track('pad', PAD_CHOIR, 0.55, 0); s.track('bass', GLASS, 0.4, 0)
        s.track('perc', DRUMS, 0.3, 0)
    # A Hijaz: A Bb C# D E F G
    mel = """A4:1.5 Bb4:.5 C#5:.5 D5:.5 | E5:2 D5:1 | C#5:1 Bb4:.5 A4:.5 G4:1 | A4:3 |
E5:1.5 F5:.5 E5:.5 D5:.5 | C#5:1 D5:1 E5:1 | F5:1 E5:.5 D5:.5 C#5:.5 Bb4:.5 | A4:3 |
D5:1 E5:.5 F5:.5 G5:1 | F5:1.5 E5:.5 D5:1 | C#5:1 D5:.5 C#5:.5 Bb4:1 | A4:3 |
G4:1 A4:1 Bb4:1 | C#5:2 D5:1 | E5:1 D5:.5 C#5:.5 Bb4:.5 G4:.5 | A4:3"""
    s.line('mel', 0, mel, 84)
    harm = ['Am', 'Am', 'Gm', 'Am', 'Am', 'A', 'Bb', 'A', 'Dm', 'Dm', 'A', 'Am', 'Gm', 'A', 'Bb', 'A']
    for b, ch in enumerate(harm):
        ks = [key_of(k) + (12 if dream else 0) for k in CH[ch]]
        for i, idx in enumerate((0, 2, 3, 4, 3, 2)):
            s.note('harp', b * 3 + i * 0.5, 1.2, ks[idx], 56 - (i % 3) * 5)
        s.chord('pad', b * 3, 2.95, [key_of(k) for k in CH[ch][1:4]], 40)
        s.note('bass', b * 3, 2.9, key_of(CH[ch][0]), 62)
        s.hits('perc', b * 3, 'x.....' if not dream else 'x.....', SHAKER if not dream else TRI, 40)
    return s


def hills(dream=False):
    s = Song('hills' + ('_dream' if dream else ''), 100, 16)
    if not dream:
        s.track('mel', FLUTE, 0.8, 0.1); s.track('pluck', KOTO, 0.7, -0.3); s.track('pad', STRINGS, 0.45, 0); s.track('bass', ABASS, 0.6, 0)
        s.track('perc', DRUMS, 0.6, 0)
    else:
        s.track('mel', PANFLUTE, 0.7, 0.1); s.track('pluck', KALIMBA, 0.7, -0.3); s.track('pad', PAD_NEWAGE, 0.5, 0); s.track('bass', GLASS, 0.4, 0)
        s.track('perc', DRUMS, 0.35, 0)
    # D dorian, brighter: the hillside in the open air
    mel = """D5:.5 E5:.5 F5 A5 G5 | F5:.5 E5:.5 D5 E5:2 | C5:.5 D5:.5 E5 G5 F5 | E5:3 r |
A5:.5 G5:.5 F5 E5 D5 | C5 D5 E5:2 | F5:.5 E5:.5 D5 C5 A4 | D5:3 r |
F5 G5 A5:1.5 G5:.5 | F5 E5 D5:2 | E5 F5 G5:1.5 F5:.5 | E5:3 r |
D5 F5 A5 C6 | B5:1.5 A5:.5 G5 E5 | F5 E5:.5 D5:.5 C5 E5 | D5:4"""
    s.line('mel', 0, mel, 86)
    harm = ['Dm', 'Dm', 'C', 'Am', 'Dm', 'C', 'F', 'Dm', 'F', 'Dm', 'C', 'Am', 'Dm', 'G', 'C', 'Dm']
    for b, ch in enumerate(harm):
        ks = [key_of(k) + (12 if dream else 0) for k in CH[ch]]
        for i, idx in enumerate((0, 2, 1, 2, 3, 2, 1, 2)):
            s.note('pluck', b * 4 + i * 0.5, 0.45, ks[idx] + 12, 62 - (i % 2) * 8)
        s.chord('pad', b * 4, 3.9, [key_of(k) for k in CH[ch][1:4]], 38)
        s.note('bass', b * 4, 1.4, key_of(CH[ch][0]), 76); s.note('bass', b * 4 + 2.5, 1.4, key_of(CH[ch][0]) + 7, 66)
        if not dream:
            s.hits('perc', b * 4, 'x...x.x.', DOUM, 70); s.hits('perc', b * 4, '..x...x.', TEK, 54); s.hits('perc', b * 4, 'oooooooo', SHAKER, 40)
        else:
            s.hits('perc', b * 4, 'x.......', FINGER, 46)
    return s


def temple(dream=False):
    s = Song('temple' + ('_dream' if dream else ''), 66, 16)
    if not dream:
        s.track('pad', SLOWSTR, 0.6, 0); s.track('choir', CHOIR, 0.5, 0); s.track('harp', HARP, 0.6, -0.2); s.track('bass', CONTRABASS, 0.6, 0)
        s.track('mel', NEY, 0.6, 0.2); s.track('perc', DRUMS, 0.5, 0)
    else:
        s.track('pad', GLASS, 0.55, 0); s.track('choir', PAD_CHOIR, 0.6, 0); s.track('harp', CELESTA, 0.6, -0.2); s.track('bass', GLASS, 0.4, 0)
        s.track('mel', OOHS, 0.55, 0.2); s.track('perc', DRUMS, 0.3, 0)
    harm = ['Gm', 'Gm', 'Eb', 'D', 'Gm', 'Cm', 'Eb', 'D'] * 2
    for b, ch in enumerate(harm):
        s.chord('pad', b * 4, 3.95, [key_of(k) - 12 for k in CH[ch][1:4]], 46)
        if b % 2 == 0:
            s.chord('choir', b * 4, 7.9, [key_of(k) for k in CH[ch][2:5]], 40)
        s.note('bass', b * 4, 3.9, key_of(CH[ch][0]) - 12, 64)
        for i, idx in enumerate((0, 2, 4, 2)):
            s.note('harp', b * 4 + i, 2.0, key_of(CH[ch][idx]) + (12 if dream else 0), 44)
        if b % 4 == 0 and not dream:
            s.hits('perc', b * 4, 'x', DOUM, 70)
    s.line('mel', 32, """G4:3 A4 | Bb4:2 A4 G4 | F#4:4 | r:4 | D5:3 Eb5 | D5:2 C5 Bb4 | A4:4 | r:4""", 70)
    return s


def dungeon(dream=False):
    s = Song('dungeon' + ('_dream' if dream else ''), 108, 16)
    if not dream:
        s.track('ost', PIZZ, 0.75, -0.2); s.track('low', CELLO, 0.6, 0); s.track('brass', BRASS, 0.5, 0.2); s.track('mel', NEY, 0.65, 0.1)
        s.track('perc', DRUMS, 0.7, 0)
    else:
        s.track('ost', MUSICBOX, 0.6, -0.2); s.track('low', GLASS, 0.5, 0); s.track('brass', PAD_CHOIR, 0.5, 0.2); s.track('mel', OOHS, 0.55, 0.1)
        s.track('perc', DRUMS, 0.35, 0)
    # E Hijaz: E F G# A B C D
    harm = ['E', 'E', 'F', 'E', 'Am', 'E', 'F', 'E', 'Dm', 'E', 'F', 'E', 'Am', 'Dm', 'F', 'E']
    ost = [0, 7, 1, 7, 4, 7, 1, 7]
    for b, ch in enumerate(harm):
        root = key_of(CH[ch][0]) + 12
        for i, k in enumerate(ost):
            s.note('ost', b * 4 + i * 0.5, 0.4, root + k + (12 if dream else 0), 70 - (i % 2) * 10)
        s.note('low', b * 4, 3.9, root - 12, 60)
        if b % 4 == 3 and not dream:
            s.chord('brass', b * 4 + 2, 1.5, [root, root + 4, root + 7], 70)
        if not dream:
            s.hits('perc', b * 4, 'x..x..x.', DOUM, 78); s.hits('perc', b * 4, '....x...', TEK, 64); s.hits('perc', b * 4, 'o.o.o.o.', HAT, 30)
        else:
            s.hits('perc', b * 4, 'x.......', TRI, 38)
    s.line('mel', 16, """E5:2 F5 G#5 | A5:3 G#5 | F5:2 E5 D5 | E5:4 | r:16 | B5:2 A5 G#5 | F5:3 E5 | D5 E5 F5 G#5 | E5:4""", 80)
    return s


def summit():
    s = Song('summit', 58, 8)
    s.track('pad', GLASS, 0.6, 0); s.track('choir', PAD_CHOIR, 0.55, 0); s.track('box', MUSICBOX, 0.5, 0.2); s.track('bass', CONTRABASS, 0.45, 0)
    harm = ['D', 'Eb', 'D', 'Cm', 'D', 'Eb', 'Gm', 'D']
    for b, ch in enumerate(harm):
        s.chord('pad', b * 4, 3.95, [key_of(k) for k in CH[ch][1:4]], 44)
        s.note('bass', b * 4, 3.9, key_of(CH[ch][0]) - 12, 52)
        if b % 2 == 0:
            s.chord('choir', b * 4, 7.9, [key_of(k) for k in CH[ch][2:5]], 36)
    s.line('box', 0, """r:2 A5 F#5 | r:2 G5 Eb5 | r:2 F#5 D5 | r:2 Eb5 C5 | r:2 A5 F#5 | r:2 Bb5 G5 | r:2 A5 Bb5 | D6:4""", 54)
    return s


def boss():
    s = Song('boss', 144, 16)
    s.track('str', STRINGS, 0.75, -0.1); s.track('brass', BRASS, 0.7, 0.15); s.track('low', CONTRABASS, 0.7, 0); s.track('mel', TRUMPET, 0.6, 0.2)
    s.track('taiko', TAIKO, 0.8, 0); s.track('perc', DRUMS, 0.75, 0)
    harm = ['D', 'D', 'Eb', 'D', 'Gm', 'Gm', 'Eb', 'D', 'Cm', 'D', 'Eb', 'D', 'Gm', 'Eb', 'Cm', 'D']
    for b, ch in enumerate(harm):
        root = key_of(CH[ch][0])
        for i in range(8):
            s.note('str', b * 4 + i * 0.5, 0.45, root + 12 + (0 if i % 2 == 0 else 7), 82 - (i % 2) * 12)
        s.note('low', b * 4, 1.8, root - 12, 92); s.note('low', b * 4 + 2, 0.9, root - 12, 80); s.note('low', b * 4 + 3, 0.9, root - 5, 80)
        s.hits('perc', b * 4, 'x.x.x.x.', DOUM, 90); s.hits('perc', b * 4, '.x.x.x.x', TEK, 70)
        s.hits('perc', b * 4, 'x...x...', KICK, 92); s.hits('perc', b * 4, '..x...x.', SNARE, 74)
        if b % 2 == 0:
            s.note('taiko', b * 4, 1.0, 48, 110); s.note('taiko', b * 4 + 1.5, 0.5, 48, 90)
        if b % 4 == 3:
            s.chord('brass', b * 4, 1.0, [root, root + 7, root + 12], 100); s.chord('brass', b * 4 + 1.5, 0.5, [root + 1, root + 8, root + 13], 100)
        if b % 8 == 0:
            s.note('perc', b * 4, 2, CRASH, 90)
    s.line('mel', 16, """D5:2 Eb5 F#5 | G5:2 F#5 Eb5 | D5:3 r | r:4 | A5:2 Bb5 A5 | G5 F#5 G5:2 | F#5:3 r | r:4""", 96)
    s.line('mel', 48, """D6:2 C6 Bb5 | A5 G5 F#5:2 | Eb5 F#5 G5 A5 | D5:4""", 100)
    return s


def ending():
    s = Song('ending', 74, 16)
    s.track('mel', FLUTE, 0.8, 0.1); s.track('harp', HARP, 0.85, -0.25); s.track('pad', SLOWSTR, 0.55, 0); s.track('bass', CELLO, 0.5, 0)
    s.track('choir', OOHS, 0.4, 0)
    # the theme resolves into plain D major: the night is over (for now)
    s.line('mel', 0, """D5:1.5 E5:.5 F#5 G5 | A5:2 G5:.5 F#5:.5 E5 | D5 E5:.5 D5:.5 C#5 B4 | A4:3 r |
D5:1.5 E5:.5 F#5 A5 | B5:2 A5:.5 G5:.5 F#5 | G5 F#5:.5 E5:.5 D5 E5 | D5:4""", 86)
    s.line('mel', 32, """B4 C#5 D5:1.5 C#5:.5 | B4 A4 G4:2 | A4 B4 C#5 D5:.5 E5:.5 | F#5:3 r | G5:1.5 F#5:.5 E5 D5 | C#5 D5:.5 C#5:.5 B4 A4 | B4 C#5 D5:.5 E5:.5 F#5:.5 E5:.5 | D5:4""", 82)
    harm = ['D', 'D', 'G', 'A', 'D', 'G', 'A', 'D', 'G', 'A', 'D', 'D', 'G', 'A', 'G', 'D']
    CHM = {'D': ['D3', 'A3', 'D4', 'F#4', 'A4'], 'G': ['G2', 'D3', 'G3', 'B3', 'D4'], 'A': ['A2', 'E3', 'A3', 'C#4', 'E4']}
    for b, ch in enumerate(harm):
        ks = [key_of(k) for k in CHM[ch]]
        for i, idx in enumerate((0, 1, 2, 3, 4, 3, 2, 1)):
            s.note('harp', b * 4 + i * 0.5, 0.9, ks[idx], 56)
        s.chord('pad', b * 4, 3.95, ks[1:4], 42)
        s.note('bass', b * 4, 3.9, ks[0], 58)
        if b >= 8:
            s.chord('choir', b * 4, 3.9, ks[2:5], 36)
    return s


def jingle_itemget():
    s = Song('itemget', 120, 2)
    s.track('brass', BRASS, 0.8, 0); s.track('harp', HARP, 0.8, 0); s.track('choir', CHOIR, 0.5, 0); s.track('perc', DRUMS, 0.5, 0)
    for i, k in enumerate(['D4', 'F#4', 'A4', 'D5']):
        s.note('harp', i * 0.25, 2.5, k, 80)
    s.line('brass', 0, "D4:.5 F#4:.5 A4:.5 D5:2.5", 96)
    s.chord('choir', 1.5, 2.5, [key_of('D4'), key_of('F#4'), key_of('A4')], 70)
    s.note('perc', 1.5, 1, TRI, 70)
    return s


def jingle_secret():
    s = Song('secret', 120, 2)
    s.track('cel', CELESTA, 0.8, 0); s.track('harp', HARP, 0.7, 0)
    s.line('cel', 0, "D5:.25 F#5:.25 A5:.25 D6:.25 Eb6:.25 F#6:.25 A6:2.5", 90)
    s.chord('harp', 1.5, 2.5, [key_of('D4'), key_of('A4'), key_of('F#5')], 70)
    return s


# ------------------------------------------------------------------ rendering
def render(song, loop=True, tail=3.0, rev=0.25, rt=2.2, seed=1):
    syn = tinysoundfont.Synth(gain=-6, samplerate=SR)
    sf = syn.sfload(SF2)
    chans = {}
    for i, (name, (prog, vol, pan)) in enumerate(song.tracks.items()):
        ch = 9 if prog == DRUMS else (i if i < 9 else i + 1)
        chans[name] = ch
        if prog == DRUMS:
            syn.program_select(ch, sf, 128, 0, True)
        else:
            syn.program_select(ch, sf, 0, prog)
        syn.control_change(ch, 7, int(110 * vol))
        syn.control_change(ch, 10, int(64 + pan * 50))
    spb = 60.0 / song.bpm
    L = song.length * spb
    rng = np.random.default_rng(seed)
    reps = 2 if loop else 1
    evs = []
    for r in range(reps):
        for (st, du, tr, k, v) in song.events:
            jit = rng.normal(0, 0.006) if tr != 'perc' else rng.normal(0, 0.003)
            t0 = max(0.0, (st * spb) + r * L + jit)
            evs.append((t0, 1, chans[tr], k, max(1, min(127, int(v + rng.normal(0, 4))))))
            evs.append((t0 + du * spb, 0, chans[tr], k, 0))
    evs.sort(key=lambda e: (e[0], e[1]))
    total = int((reps * L + tail) * SR)
    out = np.zeros((total, 2), np.float32)
    pos = 0
    for (t, on, ch, k, v) in evs:
        s = min(total, int(t * SR))
        if s > pos:
            buf = np.frombuffer(syn.generate(s - pos), dtype=np.float32).reshape(-1, 2)
            out[pos:s] = buf
            pos = s
        if on:
            syn.noteon(ch, k, v)
        else:
            syn.noteoff(ch, k)
    if pos < total:
        out[pos:] = np.frombuffer(syn.generate(total - pos), dtype=np.float32).reshape(-1, 2)
    if rev > 0:
        out = reverb(out, rev, rt)
    if loop:
        n = int(L * SR)
        a = out[n:2 * n].copy()
        # fold the tail of the second pass back over the start: seamless loop
        t = out[2 * n:2 * n + int(tail * SR)]
        a[:len(t)] += 0  # first half's tail already lives in [n:], from the first pass
        out = a
    peak = float(np.abs(out).max()) + 1e-9
    out = out / peak * 0.89
    return out


def reverb(x, mix, rt):
    n = int(rt * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    env = np.exp(-6.9 * t / rt)
    ir = np.stack([rng.normal(0, 1, n) * env, rng.normal(0, 1, n) * env], axis=1)
    sos = butter(2, 5200, 'low', fs=SR, output='sos')
    ir = sosfilt(sos, ir, axis=0)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-9
    wet = np.stack([fftconvolve(x[:, 0], ir[:, 0])[:len(x)], fftconvolve(x[:, 1], ir[:, 1])[:len(x)]], axis=1)
    return (x * (1 - mix * 0.5) + wet * mix * 1.6).astype(np.float32)


def write_wav(path, a):
    a = np.clip(a, -1, 1)
    pcm = (a * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


TRACKS = {
    'title': lambda: (title(), dict(rev=0.35)),
    'town': lambda: (town(False), dict(rev=0.22)),
    'town_dream': lambda: (town(True), dict(rev=0.6, rt=3.4)),
    'sea': lambda: (sea(False), dict(rev=0.25)),
    'sea_dream': lambda: (sea(True), dict(rev=0.6, rt=3.4)),
    'hills': lambda: (hills(False), dict(rev=0.2)),
    'hills_dream': lambda: (hills(True), dict(rev=0.55, rt=3.2)),
    'temple': lambda: (temple(False), dict(rev=0.4, rt=3.0)),
    'temple_dream': lambda: (temple(True), dict(rev=0.65, rt=3.8)),
    'dungeon': lambda: (dungeon(False), dict(rev=0.3, rt=2.6)),
    'dungeon_dream': lambda: (dungeon(True), dict(rev=0.6, rt=3.4)),
    'summit': lambda: (summit(), dict(rev=0.55, rt=3.8)),
    'boss': lambda: (boss(), dict(rev=0.2, rt=1.8)),
    'ending': lambda: (ending(), dict(rev=0.35, rt=2.8)),
}
JINGLES = {'itemget': jingle_itemget, 'secret': jingle_secret}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(TRACKS) + list(JINGLES)
    for n in names:
        if n in TRACKS:
            song, kw = TRACKS[n]()
            a = render(song, loop=True, **kw)
            write_wav(f'/tmp/{n}.wav', a)
            os.system(f'ffmpeg -loglevel error -y -i /tmp/{n}.wav -c:a libvorbis -q:a 6 {OUT}/{n}.ogg && rm /tmp/{n}.wav')
            print(n, round(len(a) / SR, 1), 's', flush=True)
        elif n in JINGLES:
            a = render(JINGLES[n](), loop=False, tail=2.0, rev=0.3)
            write_wav(f'/srv/Wakefire/Assets/Wakefire/Resources/Audio/sfx_{n}.wav', a)
            print(n, round(len(a) / SR, 1), 's', flush=True)
