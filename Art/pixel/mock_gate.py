"""Compose the Gate Square of Ashkel at native resolution (480x216) to judge the art."""
import json
import sys
import numpy as np
from PIL import Image
from px import Canvas, R, OUTLINE
import ashkel_art as A
import hud

W, H = 480, 216
SHEET = "/srv/Wakefire/Assets/Wakefire/Resources/Sprites/azar.png"
META = "/srv/Wakefire/Assets/Wakefire/Resources/Sprites/azar.json"


def sprite(anim, d, i):
    meta = json.load(open(META))
    row = [a for a in meta["anims"] if a["name"] == anim and a["dir"] == d][0]["row"]
    s = meta["size"]
    im = Image.open(SHEET).crop((i * s, row * s, i * s + s, row * s + s))
    c = Canvas(s, s)
    c.a = np.array(im.convert('RGBA'))
    return c, meta["pivot"]


def compose():
    cv = Canvas(W, H, R['grass'][3])
    A.grass(cv, 0, 0, W, H, seed=3, dense=0.8, flowers=0.0)
    # paved square in front of the gate
    sq = (150, 62, 182, 154)
    A.pavers(cv, *sq)
    inside = lambda x, y: sq[0] <= x < sq[0] + sq[2] and sq[1] <= y < sq[1] + sq[3]
    A.edge_line(cv, inside, sq[0] - 2, sq[1] - 2, sq[2] + 4, sq[3] + 4, R['grass'][1])
    # the city wall across the top, towers and the gate
    A.city_wall(cv, 0, 12, W, face_h=34, top_h=10)
    A.tower(cv, 174, 2, 38, 60, seed=11)
    A.tower(cv, 268, 2, 38, 60, seed=12)
    A.gate(cv, 240, 22, 46, 40)
    A.torch_bracket(cv, 192, 30, 0)
    A.torch_bracket(cv, 288, 30, 2)
    # left: a mudbrick house, olive tree, bushes, flowers, pots
    A.mud_house(cv, 18, 62, 76, 26, 34, seed=4, ladder=True)
    A.pot(cv, 104, 124, big=True); A.pot(cv, 113, 126)
    A.olive_tree(cv, 128, 150, seed=5)
    A.bush(cv, 30, 150, seed=1); A.bush(cv, 46, 158, seed=2, flowers=True); A.bush(cv, 22, 172, seed=3)
    A.flower_bed(cv, 64, 176, 44, 16)
    A.sign(cv, 140, 206)
    # right: market stall, well, cypresses, bushes
    A.stall(cv, 392, 70, 44)
    A.well(cv, 372, 150)
    A.cypress(cv, 458, 132, 48, seed=3)
    A.cypress(cv, 342, 104, 40, seed=4)
    A.bush(cv, 440, 176, seed=6); A.bush(cv, 456, 188, seed=7, flowers=True)
    A.pot(cv, 440, 108); A.pot(cv, 449, 110, big=True)
    # braziers in the square, still dark
    for (x, y) in ((196, 116), (284, 116), (240, 196)):
        A.brazier(cv, x, y)
    # Azar
    spr, piv = sprite('idle', 'down', 0)
    A.soft_shadow(cv, 242, 160, 7, 2.5)
    cv.blit(spr, 240 - int(piv[0]), 160 - int(piv[1]))
    hud.draw(cv)
    return cv


if __name__ == "__main__":
    cv = compose()
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/wfmock/gate.png"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cv.save(out)
    big = cv.image().resize((W * 3, H * 3), Image.NEAREST)
    label = Image.new('RGBA', (big.width, big.height + 30), (20, 16, 24, 255))
    label.paste(big, (0, 30))
    from PIL import ImageDraw
    ImageDraw.Draw(label).text((8, 8), "INTERNAL TEST - art pass 1, not final", fill=(255, 220, 120, 255))
    label.save(out.replace('.png', '_x3.png'))
    print("saved", out)
