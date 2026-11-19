"""Small things to pick up and the chests they come in: silver shekels, gold bars, a flame of
life, cedar chests with bronze bands. 16 px tiles, outlined like everything else."""
import math
import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
from px import Canvas, R, OUTLINE

OUT = '/srv/Wakefire/Assets/Wakefire/Resources/Items'


def shekel(frame):
    """A silver ring-money piece, turning: frame 0 face-on, 1 edge-on, 2 half."""
    s = R['white']
    cv = Canvas(8, 8)
    w = [3, 1, 2][frame]
    for y in range(1, 7):
        for x in range(4 - w, 4 + w):
            d = ((x + 0.5 - 4) / max(w, 1)) ** 2 + ((y + 0.5 - 4) / 3) ** 2
            if d <= 1.0:
                cv.px(x, y, s[4] if (x < 4 and y < 4) else s[3] if d < 0.6 else s[2])
    if frame == 0:
        cv.px(3, 3, s[1]); cv.px(4, 4, s[1])
    cv.outline(OUTLINE)
    return cv


def gold_bar():
    g = R['gold']
    cv = Canvas(10, 8)
    for y in range(2, 7):
        inset = 1 if y == 2 else 0
        for x in range(1 + inset, 9 - inset):
            cv.px(x, y, g[4] if y == 2 else g[3] if y < 5 else g[2])
    cv.hline(2, 7, 2, g[5])
    cv.outline(OUTLINE)
    return cv


def flame(frame):
    """A flame of life (restores one LIFE flame)."""
    f = R['fire']
    cv = Canvas(8, 11)
    sway = [0, 1][frame]
    for y in range(1, 10):
        t = (y - 1) / 8
        half = 3.2 * math.sin(min(1.0, t * 1.15) * math.pi * 0.9) + 0.3
        cx = 4 + (sway if y < 4 else 0) * 0.5
        for x in range(8):
            u = abs(x + 0.5 - cx)
            if u <= half:
                c = f[5] if u < half * 0.35 and t > 0.45 else f[4] if u < half * 0.7 else f[3]
                if t < 0.25:
                    c = f[3] if u < half * 0.5 else f[2]
                cv.px(x, y, c)
    cv.outline(OUTLINE)
    return cv


def chest(open_):
    cd = R['cedar']; br = R['bronze']
    cv = Canvas(16, 16)
    # body
    for y in range(7, 15):
        for x in range(1, 15):
            cv.px(x, y, cd[3] if (x // 3) % 2 == 0 else cd[2])
    cv.hline(1, 14, 14, cd[1])
    for x in (1, 14):
        cv.vline(x, 7, 14, br[3])
    cv.hline(1, 14, 10, br[3]); cv.hline(1, 14, 11, br[1])
    if not open_:
        # lid: rounded, banded, with the lock plate
        for y in range(2, 7):
            inset = 1 if y == 2 else 0
            for x in range(1 + inset, 15 - inset):
                cv.px(x, y, cd[4] if y < 4 else cd[3])
        cv.hline(2, 13, 2, cd[4])
        for x in (1, 14):
            cv.vline(x, 3, 6, br[3])
        cv.hline(1, 14, 6, br[2])
        cv.rect(6, 7, 4, 4, br[4]); cv.px(7, 8, OUTLINE); cv.px(8, 8, OUTLINE); cv.px(7, 9, OUTLINE)
        cv.px(6, 7, br[5])
    else:
        # lid thrown back, dark inside
        cv.rect(2, 7, 12, 3, (20, 12, 16, 255))
        for y in range(1, 5):
            for x in range(1, 15):
                cv.px(x, y, cd[2] if y > 1 else cd[3])
        cv.hline(1, 14, 4, br[2])
        cv.hline(2, 13, 7, br[1])
    cv.outline(OUTLINE)
    return cv


if __name__ == '__main__':
    for i in range(3):
        shekel(i).save(f'{OUT}/shekel_{i}.png')
    gold_bar().save(f'{OUT}/gold_bar.png')
    for i in range(2):
        flame(i).save(f'{OUT}/flame_{i}.png')
    chest(False).save(f'/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest.png')
    chest(True).save(f'/srv/Wakefire/Assets/Wakefire/Resources/Objects/chest_open.png')
    print('items saved')
