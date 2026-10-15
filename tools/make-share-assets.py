# -*- coding: utf-8 -*-
"""生成「尿了吗」分享二维码 + 微信分享卡片"""
import os
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(BASE, '..', 'assets'))
os.makedirs(OUT, exist_ok=True)

# 分享链接：可用环境变量 SITE_URL 覆盖，默认指向线上地址
URL = os.environ.get('SITE_URL', 'https://niaolema-app.app.workbuddy.host/')
BRAND = (14, 165, 233)
BRAND_DARK = (8, 118, 178)
BRAND_LIGHT = (51, 214, 240)
INK = (15, 36, 54)
MUTED = (107, 130, 153)

FONT_BD = 'C:/Windows/Fonts/msyhbd.ttc'
FONT_RG = 'C:/Windows/Fonts/msyh.ttc'


def font(path, size):
    return ImageFont.truetype(path, size, index=0)


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


# ---------------- 二维码 ----------------
def build_qr():
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=1, border=4)
    qr.add_data(URL)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    S = 20
    pad = 40
    size = n * S + pad * 2

    img = Image.new('RGB', (size, size), 'white')
    d = ImageDraw.Draw(img)

    def is_eye(r, c):
        # 三个定位角（去掉 border 偏移）
        b = 4
        rr, cc = r - b, c - b
        inner = n - 2 * b
        if rr < 7 and cc < 7:
            return True
        if rr < 7 and cc >= inner - 7:
            return True
        if rr >= inner - 7 and cc < 7:
            return True
        return False

    rad = int(S * 0.30)
    for r in range(n):
        for c in range(n):
            if not m[r][c]:
                continue
            if is_eye(r, c):
                continue
            x = pad + c * S
            y = pad + r * S
            d.rounded_rectangle([x, y, x + S - 1, y + S - 1], radius=rad, fill=BRAND_DARK)

    # 重绘三个定位角（描边式，更好看）
    b = 4
    inner = n - 2 * b
    for (rr, cc) in [(b, b), (b, inner - 7 + b), (inner - 7 + b, b)]:
        x0, y0 = pad + cc * S, pad + rr * S
        x1, y1 = x0 + 7 * S - 1, y0 + 7 * S - 1
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(S * 1.0), fill=BRAND_DARK)
        p = S
        d.rounded_rectangle([x0 + p, y0 + p, x1 - p, y1 - p], radius=int(S * 1.0), fill='white')
        p2 = 2 * S
        d.rounded_rectangle([x0 + p2, y0 + p2, x1 - p2, y1 - p2], radius=int(S * 0.63), fill=BRAND_DARK)

    # 中心水滴 logo（白底 + 品牌色水滴）
    logo = int(n * S * 0.235)
    lx = ly = size // 2 - logo // 2
    m2 = 14
    d.rounded_rectangle([lx - m2, ly - m2, lx + logo + m2, ly + logo + m2],
                        radius=int(logo * 0.28), fill='white')
    drop = make_droplet(logo, BRAND)
    img.paste(drop, (lx, ly), drop)
    img.save(os.path.join(OUT, 'qr.png'))
    print('qr.png', img.size, 'modules', n)


def make_droplet(px, color):
    """生成水滴形状的 RGBA 图（复用几何：圆头 + 切线锥，切点纬度截断）"""
    import math
    ss = 3
    A = (0.5, 0.10)
    O = (0.5, 0.615)
    R = 0.30
    D = math.hypot(O[0] - A[0], O[1] - A[1])
    CA = math.cos(math.asin(R / D))
    YT = A[1] + D * CA * CA

    def inside(x, y):
        dx, dy = x - O[0], y - O[1]
        if dx * dx + dy * dy <= R * R:
            return True
        if y >= YT:
            return False
        px_, py_ = x - A[0], y - A[1]
        if py_ < 0:
            return False
        L = math.hypot(px_, py_)
        return L < 1e-9 or (py_ / L) >= CA

    img = Image.new('RGBA', (px, px), (0, 0, 0, 0))
    pxs = img.load()
    for j in range(px):
        for i in range(px):
            hit = 0
            for sj in range(ss):
                for si in range(ss):
                    x = (i + (si + .5) / ss) / px
                    y = (j + (sj + .5) / ss) / px
                    if inside(x, y):
                        hit += 1
            if hit:
                pxs[i, j] = (color[0], color[1], color[2], int(255 * hit / (ss * ss)))
    return img


# ---------------- 分享卡片 ----------------
def vgrad(w, h, c1, c2):
    img = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=(
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t)))
    return img


def build_share_card():
    W, H = 1200, 630
    img = vgrad(W, H, (10, 138, 205), (44, 200, 235))

    # 装饰光斑
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-180, -220, 380, 300], fill=(255, 255, 255, 26))
    gd.ellipse([820, 380, 1360, 900], fill=(255, 255, 255, 22))
    img = Image.alpha_composite(img.convert('RGBA'), glow).convert('RGB')

    d = ImageDraw.Draw(img)

    # 左侧文字
    x = 78
    logo = make_droplet(96, (255, 255, 255))
    img.paste(logo, (x, 96), logo)

    d.text((x + 118, 104), '尿了吗', font=font(FONT_BD, 74), fill='white')
    d.text((x + 122, 186), '排尿健康记录', font=font(FONT_RG, 26), fill=(226, 246, 255))

    d.text((x, 268), '随手一记，看懂自己的规律', font=font(FONT_BD, 40), fill='white')

    feats = ['一键记录', '趋势统计', '数据只存本机']
    cy = 348
    f = font(FONT_RG, 23)

    # 半透明标签要画在独立 RGBA 层上再合成，否则 alpha 会被忽略
    chips = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chips)
    cx = 78
    for t in feats:
        tw = d.textlength(t, font=f)
        cd.rounded_rectangle([cx, cy, cx + tw + 40, cy + 46], radius=23, fill=(255, 255, 255, 52))
        cx += tw + 54
    img = Image.alpha_composite(img.convert('RGBA'), chips).convert('RGB')
    d = ImageDraw.Draw(img)

    cx = 78
    for t in feats:
        d.text((cx + 20, cy + 11), t, font=f, fill='white')
        cx += d.textlength(t, font=f) + 54

    d.text((78, 452), '无需下载安装 · 手机浏览器打开即用 · 断网也能记',
           font=font(FONT_RG, 25), fill=(214, 242, 255))

    # 右侧二维码卡片
    box = [790, 88, 1132, 542]
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([box[0] + 6, box[1] + 14, box[2] + 6, box[3] + 14],
                                             radius=34, fill=(4, 60, 92, 70))
    img = Image.alpha_composite(img.convert('RGBA'), shadow).convert('RGB')
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=32, fill='white')

    qr = Image.open(os.path.join(OUT, 'qr.png')).convert('RGB')
    qw = 268
    qr = qr.resize((qw, qw), Image.LANCZOS)
    qx = box[0] + (box[2] - box[0] - qw) // 2
    img.paste(qr, (qx, box[1] + 26))

    tip = '扫码打开'
    tf = font(FONT_BD, 27)
    tw = d.textlength(tip, font=tf)
    d.text(((box[0] + box[2]) / 2 - tw / 2, box[1] + 316), tip, font=tf, fill=INK)
    sub = '长按识别 · 或转发链接'
    sf = font(FONT_RG, 19)
    sw = d.textlength(sub, font=sf)
    d.text(((box[0] + box[2]) / 2 - sw / 2, box[1] + 356), sub, font=sf, fill=MUTED)

    img.save(os.path.join(OUT, 'share-card.png'))
    print('share-card.png', img.size)


build_qr()
build_share_card()
