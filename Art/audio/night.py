"""The first night's sound: the Crypt of the First Watch, waking and dreaming.

  python3 night.py [outdir]      (default: the game's Resources/Music)"""
import os
import sys
import numpy as np

sys.path.insert(0, '/srv/Wakefire/Art/audio')
import music as M
from music import Song, key_of, CH

FRHORN = 60


def crypt(dream=False):
    """D Hijaz, very slow: the watch's own tune (the title's) an octave down on a low reed, at the
    pace of a man walking his rounds; a drum for his feet; a lyre that answers from the far end of
    the hall and stops; a horn a long way off that calls the hour and is not answered."""
    s = Song('crypt' + ('_dream' if dream else ''), 60, 16)
    if not dream:
        s.track('mel', M.CLARINET, 0.8, 0.1); s.track('lyre', M.HARP, 0.6, -0.3); s.track('drone', M.CELLO, 0.5, 0); s.track('low', M.CONTRABASS, 0.5, 0)
        s.track('horn', FRHORN, 0.38, 0.35); s.track('perc', M.DRUMS, 0.6, 0)
    else:
        s.track('mel', M.OOHS, 0.6, 0.1); s.track('lyre', M.CELESTA, 0.55, -0.3); s.track('drone', M.GLASS, 0.45, 0); s.track('low', M.PAD_CHOIR, 0.4, 0)
        s.track('horn', M.PAD_NEWAGE, 0.35, 0.35); s.track('perc', M.DRUMS, 0.3, 0)
    harm = ['D', 'D', 'Eb', 'D', 'D', 'Eb', 'Cm', 'D', 'Gm', 'Gm', 'Eb', 'D', 'Cm', 'Eb', 'D', 'D']
    for b, ch in enumerate(harm):
        st = b * 4
        root = key_of(CH[ch][0])
        s.note('low', st, 3.95, root - 12 if root - 12 >= 26 else root, 54)
        s.chord('drone', st, 3.95, [key_of(CH[ch][0]), key_of(CH[ch][1])], 46)
        if not dream:
            s.hits('perc', st, 'x.....o.', M.DOUM, 62)                      # a man walking, in no hurry
            if b % 4 == 3:
                s.hits('perc', st, '......xo', M.TEK, 40)
        elif b % 2 == 0:
            s.hits('perc', st, 'x', M.TRI, 30)
        if b % 2 == 1:                                                      # the lyre: three notes up the chord, and it stops
            ks = [key_of(k) for k in CH[ch]]
            for i, idx in enumerate((1, 2, 4)):
                s.note('lyre', st + 2 + i * 0.5, 1.4, ks[idx] + (12 if dream else 0), 56 - i * 5)
        if b in (3, 11):                                                    # the hour, called from a long way off
            s.note('horn', st + 1, 1.4, key_of('D4'), 58); s.note('horn', st + 2.5, 1.5, key_of('A4'), 62)
        if b == 7:
            s.note('horn', st + 1, 1.4, key_of('D4'), 54); s.note('horn', st + 2.5, 1.5, key_of('G4'), 56)
    up = 12 if dream else 0
    s.line('mel', 0, """D4:3 Eb4 | F#4:2 G4:2 | A4:4 | G4 F#4 Eb4:2 | D4:2 Eb4 D4 | C4:2 Bb3:2 | A3:4 | r:4""", 74, shift=up)
    s.line('mel', 32, """Eb4:3 D4 | C4:2 Bb3:2 | A3:2 Bb3 A3 | G3:2 F#3:2 | G3:2 A3:2 | Bb3 A3 G3 F#3 | D3:4 | r:4""", 70, shift=up)
    return s


TRACKS = {
    'crypt': lambda: (crypt(False), dict(rev=0.45, rt=3.4)),
    'crypt_dream': lambda: (crypt(True), dict(rev=0.65, rt=3.8)),
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else M.OUT
    os.makedirs(out, exist_ok=True)
    for n in TRACKS:
        song, kw = TRACKS[n]()
        a = M.render(song, loop=True, **kw)
        M.write_wav(f'/tmp/{n}.wav', a)
        os.system(f'ffmpeg -loglevel error -y -i /tmp/{n}.wav -c:a libvorbis -q:a 6 {out}/{n}.ogg && rm /tmp/{n}.wav')
        rms = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
        print(n, round(len(a) / M.SR, 1), 's', 'rms %.1f dB' % rms, flush=True)
