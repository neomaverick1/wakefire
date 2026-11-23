"""Sounds of the dungeons' rooms: a great chest going back on its hinges, the fanfare for the few
things the whole game turns on, bars lifting and dropping, a sun disc catching the light.
python3 dungeon.py"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/audio')
import numpy as np
import sfx as S

SR = S.SR


def groan(d, f0, f1, amp=1.0):
    """Old wood and bronze hinges taking a weight: a low pitched creak that stutters as it moves."""
    t = S.t_(d)
    f = f0 + (f1 - f0) * (t / d) ** 1.4
    ph = 2 * np.pi * np.cumsum(f) / SR
    stick = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * (9 + 14 * t / d) * t))        # stick and slip
    body = (2 * ((ph / (2 * np.pi)) % 1) - 1) * stick
    return S.bp(body, 180, 1900) * S.env(d, 0.05, d * 0.7) * amp


def gliss(prog, keys, step, tail=1.2, vel=96):
    return S.sf_note(prog, keys, d=tail, vel=vel, step=step)


def fork(f0, d=1.9, shiver=0.0, rate=0.0):
    """A struck tuning fork: the tink of the strike (its clang tone, six and a quarter times the note,
    gone in a moment), then the note itself, pure, ringing down. shiver beats it against itself: the
    fork has found something and cannot keep still."""
    t = S.t_(d)
    note = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 1.9)
    if shiver > 0:
        beat = 1 - shiver + shiver * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t))
        note = note * beat + np.sin(2 * np.pi * f0 * 2.0 * t) * np.exp(-t * 3.2) * 0.2 * shiver * beat
    clang = np.sin(2 * np.pi * f0 * 6.27 * t) * np.exp(-t * 16) * 0.45
    tick = S.bp(S.noise(0.03), 2500, 9000) * S.env(0.03, 0.001, 0.02) * 0.6
    return S.mix(note * 0.9, clang, tick) * S.env(d, 0.002, 0.25)


def build():
    s = S.save
    # ---- a tuning fork, and what it has to say: nothing near (D), a chest shut next door (A, shivering),
    #      a chest shut in this very room (the D above, and it cannot keep still)
    s('fork_0', S.room(fork(293.66), 0.2, 1.2), 0.8)
    s('fork_1', S.room(fork(440.0, d=2.1, shiver=0.5, rate=7.0), 0.22, 1.3), 0.8)
    s('fork_2', S.room(S.mix(fork(587.33, d=2.4, shiver=0.85, rate=11.0), S.at(fork(1174.66, d=1.2, shiver=0.6, rate=13.0) * 0.25, 0.06)), 0.25, 1.4), 0.85)
    # ---- a great chest: the lid is heavy, the hinges are old, and it lands back with a boom
    lid = S.mix(groan(0.9, 70, 150, 0.9), S.at(groan(0.5, 320, 620, 0.35), 0.2),
                S.at(S.lp(S.noise(0.5), 160) * S.env(0.5, 0.004, 0.16) * 3.0, 0.92),            # the lid hits its stop
                S.at(S.bronze(92, 1.4) * 0.5, 0.92), S.at(S.bronze(138, 1.0) * 0.3, 0.94),
                S.at(S.bp(S.noise(0.25), 900, 3800) * S.env(0.25, 0.002, 0.07) * 0.5, 0.93))
    # and what is inside starts to sing before he has it in his hands: harp up through the mode, a bell on top
    D = 50                                         # D3; Hijaz on D: D Eb F# G A Bb C
    mode = [0, 1, 4, 5, 7, 8, 10]
    up = [D + 12 * o + m for o in (0, 1, 2) for m in mode] + [D + 36]
    shimmer = gliss(46, up, 0.045, tail=1.6, vel=84)
    s('bigchest_open', S.room(S.mix(lid, S.at(shimmer * 0.55, 1.15), S.at(S.sf_note(14, [D + 36, D + 43], d=1.6, vel=70) * 0.35, 1.9)), 0.3, 1.6), 0.9)

    # ---- the fanfare: drums rolling up, horns on the open fifth, the tune of the watch climbing to the octave,
    # harp and bells over the top, and a long gold chord to stand in
    roll = S.sf_note(47, [38], d=0.1, vel=60)
    drum = np.zeros(int(1.2 * SR))
    for i in range(22):
        at = int((i / 22) ** 0.8 * 1.05 * SR)
        hit = S.sf_note(47, [38 + (i % 2) * 5], d=0.25, vel=int(46 + i * 3.4))
        n = min(len(hit), len(drum) - at)
        drum[at:at + n] += hit[:n] * (0.3 + 0.7 * i / 22)
    def brass(keys, d, vel=104):
        return S.sf_note(61, keys, d=d, vel=vel)
    def horn(keys, d, vel=96):
        return S.sf_note(60, keys, d=d, vel=vel)
    tune = S.mix(
        S.at(brass([D + 12, D + 19], 0.26), 1.10),            # D A
        S.at(brass([D + 16, D + 19], 0.26), 1.42),            # F# A
        S.at(brass([D + 19, D + 24], 0.26), 1.74),            # A D
        S.at(brass([D + 24, D + 28, D + 31], 2.6, 112), 2.10),     # the octave, held: D F# A
        S.at(horn([D, D + 7, D + 12], 3.4, 90), 1.10),
        S.at(S.sf_note(52, [D + 12, D + 16, D + 19, D + 24], d=2.8, vel=64) * 0.7, 2.10),      # voices under the chord
    )
    top = S.mix(S.at(gliss(46, [D + 24 + m for m in (0, 4, 7, 12, 16, 19, 24)], 0.05, tail=2.4, vel=92) * 0.6, 2.10),
                S.at(S.sf_note(14, [D + 36], d=2.6, vel=88) * 0.5, 2.12), S.at(S.sf_note(14, [D + 43], d=2.2, vel=74) * 0.4, 2.55),
                S.at(S.sf_note(0, [49], d=2.4, vel=96, drums=True) * 0.5, 2.08))               # a crash on the arrival
    s('main_item', S.room(S.mix(drum * 0.8, tune, top), 0.28, 1.9), 0.92)

    # ---- bars: bronze running up into the lintel; bronze coming down and meeting stone
    run = np.zeros(int(0.5 * SR))
    for i in range(9):
        k = S.bronze(520 + i * 46, 0.16) * (0.5 + 0.05 * i)
        at = int(i * 0.045 * SR)
        run[at:at + len(k)] += k[:len(run) - at]
    s('bars_up', S.room(S.mix(run, S.bp(S.noise(0.45), 300, 2200) * S.env(0.45, 0.02, 0.2) * 0.45, S.at(S.bronze(260, 0.6) * 0.7, 0.42),
                              S.at(S.lp(S.noise(0.12), 300) * S.env(0.12, 0.002, 0.05) * 1.6, 0.42)), 0.25, 0.9), 0.75)
    s('bars_down', S.room(S.mix(S.bp(S.noise(0.2), 400, 2600) * S.env(0.2, 0.01, 0.12) * 0.5, S.at(S.bronze(180, 1.1), 0.16), S.at(S.bronze(497, 0.7) * 0.5, 0.16),
                                S.at(S.lp(S.noise(0.3), 200) * S.env(0.3, 0.002, 0.12) * 3.0, 0.16), S.at(S.bronze(180, 0.5) * 0.3, 0.38)), 0.3, 1.1), 0.85)

    # ---- a sun disc catching the light: a struck bowl, and a chord opening over it
    s('disc_lit', S.room(S.mix(S.bronze(587, 2.4) * 0.6, S.bronze(880, 1.8) * 0.35, S.at(S.sf_note(46, [D + 24, D + 28, D + 31, D + 36], d=1.8, vel=80, step=0.06) * 0.6, 0.05),
                               S.at(S.sf_note(14, [D + 48], d=1.6, vel=70) * 0.35, 0.3)), 0.3, 1.5), 0.8)
    print('dungeon sfx done')


if __name__ == '__main__':
    build()
