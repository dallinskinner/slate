#!/usr/bin/env python3
"""Render Slate logo PNGs from the geometry in slate-logo.svg (no SVG libs needed).
Outputs into branding/png/. Re-run after changing the logo."""
import math, os
from PIL import Image, ImageDraw

LIME = (0xb6, 0xf2, 0x3a, 255)
DARK = (0x1a, 0x1b, 0x1e, 255)
HERE = os.path.dirname(os.path.abspath(__file__))

def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r*math.cos(math.radians(a0+(a1-a0)*i/n)), cy + r*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]

# Each glyph: list of (polygon in 100x160 glyph units, kind) ; kind 'solid' or 'hatch'
# angles in screen coords (y down): 0=right, 90=down, 180=left, 270=up
GLYPHS = {
 'S': [([(68,64),(100,64),(100,144)] + arc(84,144,16,0,90) + [(0,160),(0,128),(68,128)], 'hatch'),
       ([(16,0),(100,0),(100,32),(32,32),(32,64),(100,64),(100,96),(0,96),(0,16)] + arc(16,16,16,180,270), 'solid')],
 'L': [([(0,0),(32,0),(32,160),(0,160)], 'hatch'),
       ([(0,128),(100,128),(100,160),(0,160)], 'solid')],
 'A': [([(0,160)] + arc(50,50,50,180,270) + [(50,32),(32,32),(32,160)], 'solid'),
       (arc(50,50,50,270,360) + [(100,160),(68,160),(68,32),(50,32)], 'hatch'),
       ([(32,84),(68,84),(68,112),(32,112)], 'solid')],
 'T': [([(0,0),(50,0),(50,32),(0,32)], 'solid'),
       ([(50,0),(100,0),(100,32),(50,32)], 'hatch'),
       ([(34,32),(66,32),(66,160),(34,160)], 'solid')],
 'E': [([(0,0),(32,0),(32,160),(0,160)], 'solid'),
       ([(32,0),(100,0),(100,32),(32,32)], 'hatch'),
       ([(32,64),(88,64),(88,96),(32,96)], 'solid'),
       ([(32,128),(100,128),(100,160),(32,160)], 'hatch')],
}

def draw_glyphs(img, letters, x0, y0, scale, gap=20, color=LIME):
    W, H = img.size
    solid = Image.new('L', (W, H), 0); hatch = Image.new('L', (W, H), 0)
    ds, dh = ImageDraw.Draw(solid), ImageDraw.Draw(hatch)
    for i, ch in enumerate(letters):
        ox = x0 + i*(100+gap)*scale
        for poly, kind in GLYPHS[ch]:
            pts = [(ox+x*scale, y0+y*scale) for x, y in poly]
            (ds if kind == 'solid' else dh).polygon(pts, fill=255)
    # 45-degree hatch lines, period 5 units, stroke 1.6 units (as in the SVG)
    lines = Image.new('L', (W, H), 0); dl = ImageDraw.Draw(lines)
    step = 5*scale*math.sqrt(2); w = max(1, round(1.6*scale))
    k = 0
    while k < W + 2*H:
        dl.line([(k, 0), (k-H, H)], fill=255, width=w); k += step
    hatch = Image.composite(lines, Image.new('L', (W, H), 0), hatch)
    lime = Image.new('RGBA', (W, H), color)
    img.paste(lime, (0, 0), solid); img.paste(lime, (0, 0), hatch)

def word(scale, pad, bg=None, color=LIME):
    w = int((5*100 + 4*20)*scale + 2*pad); h = int(160*scale + 2*pad)
    img = Image.new('RGBA', (w, h), bg or (0, 0, 0, 0))
    draw_glyphs(img, 'SLATE', pad, pad, scale, color=color); return img

def mark(size, bg=DARK):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, size-1, size-1], radius=size//6, fill=bg)
    s = size*0.6/160
    draw_glyphs(img, 'S', (size-100*s)/2, (size-160*s)/2, s); return img

def wallpaper(W=1920, H=1080):
    img = Image.new('RGBA', (W, H), DARK)
    s = W*0.30/580
    lw, lh = 580*s, 160*s
    draw_glyphs(img, 'SLATE', (W-lw)/2, (H-lh)/2, s); return img

def round_mark(size, bg=LIME, fg=(0x11, 0x12, 0x14, 255)):
    """Circular launcher icon: S glyph inside a filled circle (drawn 4x, then downsampled)."""
    k = 4; big = size * k
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([0, 0, big - 1, big - 1], fill=bg)
    s = big * 0.52 / 160
    draw_glyphs(img, 'S', (big - 100 * s) / 2, (big - 160 * s) / 2, s, color=fg)
    return img.resize((size, size), Image.LANCZOS)

if __name__ == '__main__':
    out = os.path.join(HERE, 'png'); os.makedirs(out, exist_ok=True)
    word(2, 0).save(f'{out}/slate-wordmark.png')
    mark(256).save(f'{out}/slate-mark-256.png')
    mark(64).save(f'{out}/slate-mark-64.png')
    wallpaper().save(f'{out}/slate-wallpaper-1920x1080.png')
    wallpaper(3840, 2160).save(f'{out}/slate-wallpaper-3840x2160.png')
    print('ok')
