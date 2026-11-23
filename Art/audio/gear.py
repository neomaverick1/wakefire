"""The sounds of the things Azar uses with his hands: the mirror shield coming up and taking a
blow, the sling, the throwing stick, a gong, and the small noises of the pause screen's pages.
python3 gear.py"""
import sys
sys.path.insert(0, '/srv/Wakefire/Art/audio')
import numpy as np
import sfx as S


def whoosh(d, f0, f1, q=0.6, amp=1.0):
    """Air moving past something: noise in a band that slides."""
    n = S.noise(d)
    out = np.zeros_like(n)
    k = 6
    seg = len(n) // k
    for i in range(k):
        f = f0 + (f1 - f0) * (i + 0.5) / k
        part = S.bp(n, f * (1 - q * 0.5), f * (1 + q * 0.5))
        w = np.zeros(len(n))
        a, b = i * seg, min(len(n), (i + 1) * seg)
        w[a:b] = 1
        w = np.convolve(w, np.hanning(max(8, seg // 2)) / max(1, np.hanning(max(8, seg // 2)).sum()), 'same')
        out += part * w
    return out * amp


def build():
    s = S.save
    # the shield: strap and bronze as it comes up; a blow stopping on it; (fire going back is the old 'reflect')
    up = S.mix(S.bp(S.noise(0.16), 500, 2400) * S.env(0.16, 0.02, 0.06) * 0.6, S.at(S.bronze(520, 0.25) * 0.35, 0.06), S.at(S.lp(S.noise(0.05), 500) * S.env(0.05, 0.001, 0.02) * 0.8, 0.07))
    s('shield_up', up, 0.5)
    block = S.room(S.mix(S.bronze(310, 0.7), S.bronze(742, 0.5) * 0.6, S.bronze(1180, 0.3) * 0.35, S.lp(S.noise(0.07), 900) * S.env(0.07, 0.001, 0.02) * 2.0,
                         S.hp(S.noise(0.03), 3500) * S.env(0.03, 0.0005, 0.008) * 0.8), 0.22, 0.5)
    s('shield_block', block, 0.85)
    # the sling: two turns overhead, the release, the stone arriving
    turn = whoosh(0.2, 300, 900, 0.7) * S.env(0.2, 0.06, 0.07)
    s('sling_whirl', S.mix(turn * 0.7, S.at(turn * 0.9, 0.16)), 0.5)
    s('sling_shot', S.mix(whoosh(0.22, 2600, 700, 0.8) * S.env(0.22, 0.004, 0.08), S.hp(S.noise(0.02), 4000) * S.env(0.02, 0.0005, 0.006) * 0.9,
                          S.lp(S.noise(0.05), 400) * S.env(0.05, 0.001, 0.02) * 0.8), 0.6)
    s('sling_hit', S.mix(S.tone(1900, 0.06, ((1, 1), (1.7, 0.6), (2.9, 0.3)), 0.015), S.bp(S.noise(0.05), 1200, 5000) * S.env(0.05, 0.0005, 0.015) * 0.9,
                         S.lp(S.noise(0.08), 500) * S.env(0.08, 0.001, 0.03) * 0.7), 0.55)
    # the throwing stick: the arm, then wood turning in the air, a knock on stone, back in the hand
    s('stick_throw', S.mix(whoosh(0.2, 500, 1500, 0.8) * S.env(0.2, 0.03, 0.08), S.lp(S.noise(0.06), 350) * S.env(0.06, 0.002, 0.02) * 0.6), 0.5)
    d = 0.62
    t = S.t_(d)
    beat = (0.35 + 0.65 * np.clip(np.sin(2 * np.pi * 13 * t), 0, 1) ** 2)
    s('stick_fly', whoosh(d, 420, 760, 0.9) * beat * S.env(d, 0.04, 0.25), 0.5)
    s('stick_knock', S.mix(S.tone(680, 0.12, ((1, 1), (2.3, 0.45), (3.6, 0.2)), 0.03), S.lp(S.noise(0.05), 800) * S.env(0.05, 0.0006, 0.015) * 1.2), 0.6)
    s('stick_catch', S.mix(S.lp(S.noise(0.07), 900) * S.env(0.07, 0.001, 0.025) * 1.5, S.tone(420, 0.08, ((1, 1), (2.1, 0.3)), 0.02) * 0.5), 0.5)
    # a bronze gong, for the things that are opened by hitting them from across a room
    gong = S.room(S.mix(S.bronze(196, 2.6), S.bronze(294, 2.0) * 0.6, S.bronze(523, 1.4) * 0.35, S.bronze(880, 0.8) * 0.2,
                        S.lp(S.noise(0.06), 700) * S.env(0.06, 0.001, 0.02) * 1.5), 0.4, 1.8)
    s('gong', gong, 0.85)
    print('gear sfx done')


if __name__ == '__main__':
    build()
