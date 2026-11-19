"""Export the HUD pieces as pixel sprites for Unity (Resources/UI)."""
import os
from px import Canvas, R, OUTLINE
import hud

OUT = "/srv/Wakefire/Assets/Wakefire/Resources/UI"


def piece(name, w, h, fn):
    cv = Canvas(w, h)
    fn(cv)
    os.makedirs(OUT, exist_ok=True)
    cv.save(f"{OUT}/{name}.png")


def main():
    piece("meter", 12, 34, lambda cv: (hud.frame(cv, 1, 3, 10, 30, (12, 10, 24, 255)),
                                       cv.hline(4, 7, 1, hud.WHITE), cv.px(3, 0, hud.WHITE), cv.px(8, 0, hud.WHITE)))
    piece("itembox", 22, 22, lambda cv: hud.frame(cv, 0, 0, 22, 22))
    piece("icon_lantern", 11, 14, lambda cv: hud.lantern_icon(cv, 5, 8))
    piece("coin", 9, 9, lambda cv: hud.coin_icon(cv, 1, 1))
    piece("key", 7, 10, lambda cv: hud.key_icon(cv, 1, 1))
    piece("life_full", 11, 12, lambda cv: hud.lamp(cv, 1, 1, True))
    piece("life_empty", 11, 12, lambda cv: hud.lamp(cv, 1, 1, False))
    piece("life_label", 64, 10, lambda cv: hud.text(cv, 1, 1, "-- LIFE --"))
    for d in "0123456789":
        piece(f"digit_{d}", 7, 9, lambda cv, d=d: hud.text(cv, 1, 1, d))
    print("hud exported")


if __name__ == "__main__":
    main()
