"""Azar v4: heroic proportions, every pixel placed by hand. Rows are (start column, pixels)."""
import os, sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
W = 26

FRONT = [
    [(12, "OO")],
    [(11, "OYYO")],
    [(11, "OyFO")],
    [(10, "OYyFRO")],
    [(10, "OFYFRO")],
    [(10, "ORFFRO")],
    [(9, "OOBWWBOO")],
    [(8, "OBWWBBBbbO")],
    [(7, "OBWBBBBBBbnO")],
    [(7, "OBBBBBBBBbnO")],
    [(7, "OBOSSSSSSOnO")],
    [(7, "OBOPESSEPOnO")],
    [(7, "OBOSSskSSOnO")],
    [(7, "ObOshhhhsOnO")],
    [(7, "OnOOhhhhOOnO")],
    [(4, "OOWBBO"), (10, "OskksO"), (16, "ObnnOO")],
    [(3, "OWBBBbO"), (10, "OCccxO"), (16, "ObbnnNO")],
    [(2, "OcOBBbbnO"), (11, "LUUu"), (15, "OnnnNOxO")],
    [(2, "OcOSskO"), (9, "lLLUUuuV"), (17, "OkskOxO")],
    [(2, "OcOSskO"), (9, "UlmLUuuV"), (17, "OkskOxO")],
    [(2, "OcOSskO"), (9, "ULlGgUuV"), (17, "OkskOxO")],
    [(2, "OcOWBbO"), (9, "UUUlmuuV"), (17, "ObnNOxO")],
    [(2, "OxOBbnO"), (9, "uUUUlmuV"), (17, "OnnNOxO")],
    [(2, "OxOBbnO"), (9, "MlllGglM"), (17, "OnnNOxO")],
    [(2, "OxOSskO"), (9, "LUUuuOZz"), (17, "OkskOxO")],
    [(2, "OXOOOOO"), (9, "UUuuVOzZ"), (17, "OOOOOXO")],
    [(3, "OXO"), (8, "OGgGgGOggO"), (21, "OXO")],
    [(3, "OO"), (8, "OSskOOSskO"), (21, "OO")],
    [(8, "OSskOOSskO")],
    [(8, "OSskOOSskO")],
    [(8, "OWBbOOWBbO")],
    [(8, "OBBnOOBBnO")],
    [(8, "OBbnOOBbnO")],
    [(8, "ObbnOObbnO")],
    [(8, "ObnnOObnnO")],
    [(7, "OMmmMOOMmmMO")],
    [(7, "OOOOO..OOOOO")],
]

SIDE = [
    [(13, "OO")],
    [(11, "OOyYO")],
    [(9, "OOYyFFO")],
    [(7, "OOYFFRRrO")],
    [(6, "OFRRrrQQO")],
    [(5, "ORrQQOBWWBOO")],
    [(5, "OrQOBWWBBBbbO")],
    [(5, "OQOBWBBBBBBbnO")],
    [(7, "OBBBBBBBBBbnO")],
    [(7, "OBBBBBBbSSSSO")],
    [(7, "ObBBBBBbSPESO")],
    [(7, "ObbBBBbbSSSkSO")],
    [(7, "OnbbbbbnshhhO")],
    [(8, "OOnnnnnOhhhO")],
    [(11, "OskkO")],
    [(7, "OcO"), (10, "OWBBBbO")],
    [(6, "OcCO"), (10, "OBWBBbnO")],
    [(5, "OcCxO"), (9, "OUSskOLuO")],
    [(5, "OcCxO"), (9, "OUSskOLUuO")],
    [(5, "OcCxO"), (9, "OUSskOUUuO")],
    [(5, "OcCxO"), (9, "OUSskOUuVO")],
    [(5, "OcCxO"), (9, "OUWBbOuVO")],
    [(5, "OxCxO"), (9, "OMBbnOMlO")],
    [(5, "OxcxO"), (9, "OUSskOUuO")],
    [(5, "OXxXO"), (9, "OUOOOOuVO")],
    [(5, "OXxXO"), (9, "OLUUuuVO")],
    [(6, "OXO"), (9, "OGgGgGgO")],
    [(7, "OO"), (9, "OskSskO")],
    [(9, "OskSskO")],
    [(9, "OskSskO")],
    [(9, "ObnWBbO")],
    [(9, "ObnBBnO")],
    [(9, "ObnBbnO")],
    [(9, "OnNbbnO")],
    [(9, "OnNbnnO")],
    [(8, "OMmmMmmmMO")],
    [(8, "OOOOOOOOOO")],
]

BACK = [
    [(12, "OO")],
    [(11, "OYYO")],
    [(11, "OyFO")],
    [(10, "OYyFRO")],
    [(10, "OFYFRO")],
    [(10, "ORFFRO")],
    [(9, "OOBWWBOO")],
    [(8, "OBWWBBBbbO")],
    [(7, "OBWBBBBBBbnO")],
    [(7, "OBBBBBBBBbnO")],
    [(7, "OBBBBBBBBbnO")],
    [(7, "ObBBBBBBbnnO")],
    [(7, "ObbbbbbbbnnO")],
    [(7, "OnbbbbbbnnNO")],
    [(8, "OnnNNNNnnO")],
    [(4, "OOWBBO"), (10, "OCCcxO"), (16, "ObnnOO")],
    [(3, "OWBBBbO"), (10, "OCCcxO"), (16, "ObbnnNO")],
    [(2, "OcOBBbbnO"), (11, "CCcx"), (15, "OnnnNOxO")],
    [(2, "OcOSskO"), (9, "CCCcccxx"), (17, "OkskOxO")],
    [(2, "OcOSskO"), (9, "CCcccxxx"), (17, "OkskOxO")],
    [(2, "OcOSskO"), (9, "CCcccxxx"), (17, "OkskOxO")],
    [(2, "OcOWBbO"), (9, "CcccxxxX"), (17, "ObnNOxO")],
    [(2, "OxOBbnO"), (9, "CcccxxxX"), (17, "OnnNOxO")],
    [(2, "OxOBbnO"), (9, "CcccxxXX"), (17, "OnnNOxO")],
    [(2, "OxOSskO"), (9, "CcccxxXX"), (17, "OkskOxO")],
    [(2, "OXOOOOO"), (9, "CcccxxXX"), (17, "OOOOOXO")],
    [(3, "OXO"), (8, "OCcccxxXXO"), (21, "OXO")],
    [(3, "OO"), (8, "OcxXxcxXXO"), (21, "OO")],
    [(8, "OSOOOOOSkO")],
    [(8, "OSskOOSskO")],
    [(8, "OWBbOOWBbO")],
    [(8, "OBBnOOBBnO")],
    [(8, "OBbnOOBbnO")],
    [(8, "ObbnOObbnO")],
    [(8, "ObnnOObnnO")],
    [(7, "OMmmMOOMmmMO")],
    [(7, "OOOOO..OOOOO")],
]


def build(rows):
    out = []
    for segs in rows:
        r = ['.'] * W
        for (c, s) in segs:
            for i, ch in enumerate(s):
                if ch != '.' and 0 <= c + i < W:
                    r[c + i] = ch
        out.append(r)
    return out


if __name__ == '__main__':
    import azar
    from PIL import Image, ImageDraw, ImageFont
    from px import Canvas
    views = [('front', build(FRONT)), ('side', build(SIDE)), ('back', build(BACK))]
    Z = 9
    ims = []
    for n, g in views:
        cv = Canvas(W, len(g))
        for y, r in enumerate(g):
            for x, ch in enumerate(r):
                if ch != '.':
                    cv.a[y, x] = azar.RGB[ch]
        im = Image.new('RGBA', (W, len(g)), (64, 104, 66, 255)); im.alpha_composite(cv.image())
        ims.append(im)
    Hh = max(i.height for i in ims)
    out = Image.new('RGB', (len(ims) * (W * Z + 10) + 10 + len(ims) * (W * 3 + 6), Hh * Z + 50), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - Azar v4', fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18))
    x = 10
    for im in ims:
        out.paste(im.convert('RGB').resize((im.width * Z, im.height * Z), Image.NEAREST), (x, 40)); x += im.width * Z + 10
    for im in ims:
        out.paste(im.convert('RGB').resize((im.width * 3, im.height * 3), Image.NEAREST), (x, 40)); x += im.width * 3 + 6
    out.save('/tmp/claude-0/-home-claude/1ffedf5d-dd37-5c5b-87f2-dac3257dd145/scratchpad/internal-test-azar4.png')
    print(out.size)
