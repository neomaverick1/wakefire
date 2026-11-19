import sys
sys.path.insert(0, '/srv/Wakefire/Art/pixel')
import azar
from PIL import Image, ImageDraw, ImageFont
W = 26


def load(path='/srv/Wakefire/Art/pixel/azar_v3.txt'):
    blocks, cur = {}, None
    for line in open(path).read().splitlines():
        if line.startswith('#') or not line.strip():
            continue
        if line.startswith('== '):
            cur = line[3:].strip(); blocks[cur] = []; continue
        r = line.rstrip()
        if '|' in r:
            c, body = r.split('|', 1)
            r = ('.' * int(c) + body).ljust(W, '.')
        if len(r) < W:
            st = (W - len(r)) // 2
            r = '.' * st + r + '.' * (W - st - len(r))
        blocks[cur].append(r[:W])
    return blocks


def render(rows):
    from px import Canvas
    cv = Canvas(W, len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                cv.a[y, x] = azar.RGB[ch]
    return cv


if __name__ == '__main__':
    b = load()
    names = sys.argv[1:] or list(b)
    Z = 9
    ims = []
    for n in names:
        cv = render(b[n])
        im = Image.new('RGBA', (cv.w, cv.h), (64, 104, 66, 255)); im.alpha_composite(cv.image())
        ims.append((n, im))
    Hh = max(i.height for _, i in ims)
    out = Image.new('RGB', (sum(i.width * Z + 10 for _, i in ims) + 10 + sum(i.width * 2 + 6 for _, i in ims), Hh * Z + 50), (20, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'INTERNAL TEST - Azar v3 ' + ' '.join(names), fill=(255, 80, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18))
    x = 10
    for n, im in ims:
        out.paste(im.convert('RGB').resize((im.width * Z, im.height * Z), Image.NEAREST), (x, 40)); x += im.width * Z + 10
    for n, im in ims:
        out.paste(im.convert('RGB').resize((im.width * 2, im.height * 2), Image.NEAREST), (x, 40)); x += im.width * 2 + 6
    out.save('azar_view_check.png')
    print(out.size)
