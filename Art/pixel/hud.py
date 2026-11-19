"""The HUD, drawn the way classic top-down adventures draw it: a framed Drowsiness meter,
the item box, counters with icons, and LIFE as a row of little bronze lamps."""
from px import Canvas, R, OUTLINE, rgb

WHITE = rgb('#f4f0f8')
# 5x7 bitmap font: digits and the capitals the HUD and title need
FONT = {
    '0': ["01110", "11011", "11011", "11011", "11011", "11011", "01110"],
    '1': ["00110", "01110", "00110", "00110", "00110", "00110", "01111"],
    '2': ["01110", "11011", "00011", "00110", "01100", "11000", "11111"],
    '3': ["11110", "00011", "00011", "01110", "00011", "00011", "11110"],
    '4': ["00110", "01110", "11010", "11010", "11111", "00010", "00010"],
    '5': ["11111", "11000", "11110", "00011", "00011", "11011", "01110"],
    '6': ["01110", "11000", "11110", "11011", "11011", "11011", "01110"],
    '7': ["11111", "00011", "00110", "00110", "01100", "01100", "01100"],
    '8': ["01110", "11011", "11011", "01110", "11011", "11011", "01110"],
    '9': ["01110", "11011", "11011", "01111", "00011", "00011", "01110"],
    'L': ["11000", "11000", "11000", "11000", "11000", "11000", "11111"],
    'I': ["1111", "0110", "0110", "0110", "0110", "0110", "1111"],
    'F': ["11111", "11000", "11000", "11110", "11000", "11000", "11000"],
    'E': ["11111", "11000", "11000", "11110", "11000", "11000", "11111"],
    '-': ["000", "000", "000", "111", "000", "000", "000"],
    ' ': ["00", "00", "00", "00", "00", "00", "00"],
}


def text(cv, x, y, s, col=WHITE, outline=True, scale=1):
    layer = Canvas(cv.w, cv.h)
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == '1':
                    for sy in range(scale):
                        for sx in range(scale):
                            layer.px(cx + c * scale + sx, y + r * scale + sy, col)
        cx += (len(g[0]) + 1) * scale
    if outline:
        layer.outline(OUTLINE)
    cv.blit(layer, 0, 0)
    return cx


def frame(cv, x, y, w, h, inner=None):
    br = R['bronze']
    cv.rect(x, y, w, h, OUTLINE)
    cv.rect(x + 1, y + 1, w - 2, h - 2, br[4])
    cv.rect(x + 2, y + 2, w - 4, h - 4, br[2])
    cv.rect(x + 3, y + 3, w - 6, h - 6, inner or OUTLINE)
    cv.hline(x + 1, x + w - 2, y + 1, br[5])


def drowsiness(cv, x, y, level=0.8):
    w, h = 10, 30
    frame(cv, x, y, w, h, rgb('#0c0a18'))
    inner_h = h - 6
    fill = int(inner_h * level)
    bl = R['lapis']
    for k in range(fill):
        yy = y + 3 + inner_h - 1 - k
        cv.hline(x + 3, x + w - 4, yy, bl[4] if k < fill - 2 else bl[5])
    cv.vline(x + 3, y + 3 + inner_h - fill, y + 3 + inner_h - 1, bl[3])
    # a closed eye glyph at the top: the meter is how long he can stay asleep
    cv.hline(x + 3, x + 6, y - 2, WHITE); cv.px(x + 2, y - 3, WHITE); cv.px(x + 7, y - 3, WHITE)


def lantern_icon(cv, cx, cy):
    br = R['bronze']; fr = R['fire']
    layer = Canvas(cv.w, cv.h)
    layer.rect(cx - 1, cy - 7, 3, 1, br[3])
    layer.rect(cx - 3, cy - 6, 7, 2, br[4])
    layer.rect(cx - 3, cy - 4, 7, 7, fr[3])
    layer.rect(cx - 1, cy - 3, 3, 4, fr[5])
    layer.vline(cx - 3, cy - 4, cy + 2, br[2]); layer.vline(cx + 3, cy - 4, cy + 2, br[2])
    layer.rect(cx - 3, cy + 3, 7, 2, br[3])
    layer.outline()
    cv.blit(layer, 0, 0)


def coin_icon(cv, x, y):
    g = R['gold']
    layer = Canvas(cv.w, cv.h)
    for yy in range(7):
        for xx in range(7):
            d = (xx - 3) ** 2 + (yy - 3) ** 2
            if d <= 10:
                layer.px(x + xx, y + yy, g[4] if xx + yy < 5 else (g[3] if d < 6 else g[2]))
    layer.rect(x + 3, y + 2, 1, 3, g[1])
    layer.outline()
    cv.blit(layer, 0, 0)


def key_icon(cv, x, y):
    br = R['bronze']
    layer = Canvas(cv.w, cv.h)
    layer.rect(x, y, 4, 4, br[4]); layer.px(x + 1, y + 1, OUTLINE); layer.px(x + 2, y + 1, OUTLINE)
    layer.rect(x + 1, y + 4, 2, 4, br[3]); layer.px(x + 3, y + 6, br[3]); layer.px(x + 3, y + 7, br[3])
    layer.outline()
    cv.blit(layer, 0, 0)


FLAME = ["000100000", "000110000", "001110000", "001111000", "011111100", "011111110", "111121110", "111222110", "011222100", "001111000"]


def lamp(cv, x, y, full=True):
    """A life flame: bright when full, an ember outline when spent."""
    fr = R['fire']
    layer = Canvas(cv.w, cv.h)
    for r, row in enumerate(FLAME):
        for c, ch in enumerate(row):
            if ch == '0':
                continue
            if full:
                col = fr[5] if ch == '2' else (fr[3] if c < 4 or r < 5 else fr[2])
            else:
                col = (60, 40, 50, 255)
            layer.px(x + c, y + r, col)
    layer.outline()
    cv.blit(layer, 0, 0)


def draw(cv, life=6, life_max=6, coins=27, keys=0, drowse=0.85):
    drowsiness(cv, 8, 8, drowse)
    frame(cv, 22, 6, 22, 22)
    lantern_icon(cv, 33, 17)
    coin_icon(cv, 52, 6); text(cv, 50, 15, f"{coins:03d}")
    key_icon(cv, 79, 5); text(cv, 77, 15, f"{keys:02d}")
    W = cv.w
    n = life_max // 2
    lx = W - 10 - 12 * n
    text(cv, lx - 6, 4, "-- LIFE --")
    for i in range(n):
        full = life >= (i + 1) * 2 or life == i * 2 + 1
        lamp(cv, lx + i * 12, 14, full)
