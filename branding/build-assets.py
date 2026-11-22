#!/usr/bin/env python3
"""Generate every Slate image asset into overlay/ (run with: python3 -I branding/build-assets.py).

Uses the logo geometry from render.py (PIL only, no SVG tools needed).
Optional: --spinner DIR  recolors Plymouth's 'spinner' theme frames (from Debian's
plymouth-themes package) to Slate lime and copies them into the Slate Plymouth theme.
"""
import importlib.util, json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location('render', os.path.join(HERE, 'render.py'))
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
spec = importlib.util.spec_from_file_location('ascii_rocks', os.path.join(HERE, 'ascii_rocks.py'))
rocks = importlib.util.module_from_spec(spec); spec.loader.exec_module(rocks)

OV = os.path.join(ROOT, 'overlay')
def out(*p):
    path = os.path.join(OV, *p); os.makedirs(os.path.dirname(path), exist_ok=True); return path

# --- Wallpapers: one Plasma wallpaper package each (Plasma picks the best-fitting size) ---
from PIL import ImageFilter
INK = (0x11, 0x12, 0x14, 255); BASE = r.DARK; LIGHT = (0xe9, 0xea, 0xec, 255)
GRAY = (0x5a, 0x5c, 0x62, 255)

def hatch_layer(W, H, step, width, color):
    """Full-size layer of 45-degree lines (same direction as the logo hatch)."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k = 0
    while k < W + H:
        d.line([(k, 0), (k - H, H)], fill=color, width=width); k += step
    return lay

def wp_hatch(W, H):
    """Faint hatch texture with one solid lime diagonal band."""
    img = Image.new('RGBA', (W, H), BASE)
    img.alpha_composite(hatch_layer(W, H, max(8, W // 160), max(1, W // 960), (182, 242, 58, 40)))
    band = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(band)
    t = W * 0.06; x0 = W * 0.62
    d.polygon([(x0, 0), (x0 + t, 0), (x0 + t - H, H), (x0 - H, H)], fill=r.LIME)
    img.alpha_composite(band)
    return img

def wp_bigs(W, H):
    """Oversized S glyph bleeding off the right edge."""
    img = Image.new('RGBA', (W, H), INK)
    s = H * 0.9 / 160
    r.draw_glyphs(img, 'S', W * 0.58, (H - 160 * s) / 2, s)
    return img

def wp_glow(W, H):
    """Soft lime glow from the bottom-left corner, small round mark top-right."""
    img = Image.new('RGBA', (W, H), INK)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(glow)
    rad = W * 0.32
    d.ellipse([-rad, H - rad, rad, H + rad], fill=(182, 242, 58, 90))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W * 0.09)))
    m = r.round_mark(max(32, W // 30))
    img.alpha_composite(m, (int(W * 0.94 - m.width), int(H * 0.08)))
    return img

def wp_mono(W, H):
    """Calm: gray wordmark, no lime."""
    img = Image.new('RGBA', (W, H), BASE)
    s = W * 0.22 / 580
    r.draw_glyphs(img, 'SLATE', (W - 580 * s) / 2, (H - 160 * s) / 2, s, color=GRAY)
    return img

def wp_light(W, H):
    """Light background, dark wordmark (pairs with the Slate Light theme)."""
    img = Image.new('RGBA', (W, H), LIGHT)
    s = W * 0.30 / 580
    r.draw_glyphs(img, 'SLATE', (W - 580 * s) / 2, (H - 160 * s) / 2, s, color=INK)
    return img

WALLPAPERS = [  # (package id, display name, draw function)
    ('Slate', 'Slate', r.wallpaper),
    ('Slate-Hatch', 'Slate Hatch', wp_hatch),
    ('Slate-Big-S', 'Slate Big S', wp_bigs),
    ('Slate-Glow', 'Slate Glow', wp_glow),
    ('Slate-Mono', 'Slate Mono', wp_mono),
    ('Slate-Light', 'Slate Light', wp_light),
]
# One ASCII rock wallpaper per release (Slate-Agate, Slate-Basalt, ...); the newest is the default
for rel in rocks.RELEASES:
    WALLPAPERS.append((f'Slate-{rel[1]}', f'Slate {rel[0]} {rel[1]}',
                       lambda w, h, rel=rel: rocks.wallpaper(rel, w, h).convert('RGBA')))
SIZES = [(1920, 1080), (2560, 1440), (3840, 2160), (1920, 1200), (2560, 1600)]
for pid, name, fn in WALLPAPERS:
    WP = ('usr', 'share', 'wallpapers', pid)
    for w, h in SIZES:
        fn(w, h).convert('RGB').save(out(*WP, 'contents', 'images', f'{w}x{h}.png'), optimize=True)
    fn(400, 250).convert('RGB').save(out(*WP, 'contents', 'screenshot.png'))
    with open(out(*WP, 'metadata.json'), 'w') as f:
        json.dump({"KPlugin": {"Id": pid, "Name": name, "License": "CC-BY-SA-4.0",
                               "Authors": [{"Name": "Slate"}]}}, f, indent=2)

def lnf_preview(W, H, bg_fn, shelf, icon_bg):
    """Mock screenshot for the Global Theme picker: wallpaper + floating shelf with round icons."""
    img = bg_fn(W, H)
    d = ImageDraw.Draw(img)
    m = max(4, W // 100); sh = max(24, H // 15)
    d.rounded_rectangle([m, H - m - sh, W - m, H - m], radius=sh // 3, fill=shelf)
    rad = sh * 0.32; cy = H - m - sh / 2
    lm = r.round_mark(int(rad * 2)); img.alpha_composite(lm, (int(m + sh * 0.3), int(cy - rad)))
    for i in range(5):
        cx = W / 2 + (i - 2) * rad * 2.8
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=icon_bg)
    return img

for lnf, bg_fn, shelf, icon_bg in [('org.slate.desktop', lambda w, h: rocks.wallpaper(rocks.CURRENT, w, h).convert('RGBA'), (17, 18, 20, 235), (90, 92, 98, 255)),
                                   ('org.slate.light.desktop', wp_light, (222, 223, 226, 235), (160, 162, 168, 255))]:
    P = ('usr', 'share', 'plasma', 'look-and-feel', lnf, 'contents', 'previews')
    lnf_preview(800, 450, bg_fn, shelf, icon_bg).convert('RGB').save(out(*P, 'preview.png'))
    lnf_preview(1920, 1080, bg_fn, shelf, icon_bg).convert('RGB').save(out(*P, 'fullscreenpreview.jpg'), quality=90)

# --- Round launcher icon (Kickoff button) ---
for size in (16, 22, 24, 32, 48, 64, 128, 256):
    r.round_mark(size).save(out('usr', 'share', 'icons', 'hicolor', f'{size}x{size}', 'apps', 'slate-launcher.png'))

# --- Plasma splash (after login) + look-and-feel preview ---
LNF = ('usr', 'share', 'plasma', 'look-and-feel', 'org.slate.desktop', 'contents')
r.word(1.2, 0).save(out(*LNF, 'splash', 'images', 'slate-wordmark.png'))

# --- Plymouth boot splash ---
PLY = ('usr', 'share', 'plymouth', 'themes', 'slate')
r.word(1.0, 0).save(out(*PLY, 'watermark.png'))

if '--spinner' in sys.argv:
    src = sys.argv[sys.argv.index('--spinner') + 1]
    lime = r.LIME[:3]
    for name in sorted(os.listdir(src)):
        if not name.endswith('.png') or name == 'watermark.png':
            continue
        im = Image.open(os.path.join(src, name)).convert('RGBA')
        if name.startswith(('throbber-', 'animation-')):
            # keep each pixel's alpha and brightness, tint it lime
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    rr, gg, bb, a = px[x, y]
                    v = max(rr, gg, bb) / 255
                    px[x, y] = (int(lime[0] * v), int(lime[1] * v), int(lime[2] * v), a)
        im.save(out(*PLY, name))

print('assets written to', OV)

# --- Release rocks as data: welcome animation (JSON) + terminal logo (fastfetch) ---
for rel in rocks.RELEASES:
    key = rel[1].lower()
    fn = rel[2]
    g = fn(120, 38, aspect=0.5, fill=0.44) if fn is rocks.agate else \
        fn(120, 38, seed=2, mound=(0.5, 1.0, 0.46, 0.75), peak=38 * 0.55)
    with open(out('usr', 'share', 'slate', 'rocks', f'{key}.json'), 'w') as f:
        json.dump({'version': rel[0], 'name': rel[1], **rocks.to_json(g)}, f, separators=(',', ':'))
    with open(out('usr', 'share', 'slate', 'ascii', f'{key}.txt'), 'w') as f:
        f.write(rocks.to_fastfetch(rocks.logo_grid(rel)))

# --- Installed-system GRUB theme (/usr/share/grub/themes/slate): rock, fonts, menu boxes ---
import shutil, subprocess
GT = ('usr', 'share', 'grub', 'themes', 'slate')
cur = rocks.CURRENT
img = rocks.wallpaper(cur, 1920, 1080).convert('RGBA')
img.alpha_composite(Image.new('RGBA', img.size, (0x1a, 0x1b, 0x1e, 120)))
img.convert('RGB').save(out(*GT, 'background.png'), optimize=True)
r.word(0.55, 0).save(out(*GT, 'wordmark.png'))
Image.new('RGBA', (8, 8), (0x11, 0x12, 0x14, 225)).save(out(*GT, 'menu_c.png'))   # menu panel
IH = 40                                                                              # item height
Image.new('RGBA', (4, IH), r.LIME).save(out(*GT, 'select_c.png'))                   # lime pill
for side in ('w', 'e'):
    k = 4; big = Image.new('RGBA', (IH * k, IH * k), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse([0, 0, IH * k - 1, IH * k - 1], fill=r.LIME)
    half = big.resize((IH, IH), Image.LANCZOS)
    half.crop((0, 0, IH // 2, IH) if side == 'w' else (IH // 2, 0, IH, IH)).save(out(*GT, f'select_{side}.png'))
if shutil.which('grub-mkfont'):
    for size in (14, 18):
        for weight, ttf in (('Regular', rocks.FONT), ('Bold', rocks.FONT_BOLD)):
            subprocess.run(['grub-mkfont', '-s', str(size), '-o', out(*GT, f'hack-{weight.lower()}-{size}.pf2'), ttf],
                           check=True)
else:
    print('NOTE: grub-mkfont missing (apt install grub-common): GRUB theme fonts not regenerated')
print('assets written')

# --- Live USB boot menu (bootloaders/splash.svg): the current rock, dimmed, behind the logo ---
import base64, io, re
sp = os.path.join(ROOT, 'bootloaders', 'splash.svg')
svg = open(sp).read()
bg = rocks.wallpaper(cur, 800, 600).convert('RGBA')
bg.alpha_composite(Image.new('RGBA', bg.size, (0x1a, 0x1b, 0x1e, 165)))
buf = io.BytesIO(); bg.convert('RGB').save(buf, 'PNG', optimize=True)
tag = ('<image id="rock" x="0" y="0" width="800" height="600" href="data:image/png;base64,'
       + base64.b64encode(buf.getvalue()).decode() + '"/>')
svg = re.sub(r'<image id="rock"[^>]*/>', '', svg)
svg = svg.replace('<rect width="800" height="600" fill="#1a1b1e"/>',
                  '<rect width="800" height="600" fill="#1a1b1e"/>\n  ' + tag, 1)
open(sp, 'w').write(svg)
print('live splash updated')

# --- Terminal logo of the current release (fastfetch reads ascii/current.txt) ---
shutil.copy(out('usr', 'share', 'slate', 'ascii', f'{cur[1].lower()}.txt'),
            out('usr', 'share', 'slate', 'ascii', 'current.txt'))

# --- Shale, the Slate hermit crab: wears each release's rock as its shell ---
sys.path.insert(0, HERE)
import mascot
for rel in rocks.RELEASES:
    key = rel[1].lower()
    for face in mascot.FACES:
        g = mascot.build(mascot.BIG, rel, face)
        mascot.render(g, font_px=28, pad=8, bg=None).save(out('usr', 'share', 'slate', 'shale', f'{key}-{face}.png'))
        with open(out('usr', 'share', 'slate', 'shale', f'{key}-{face}.txt'), 'w') as f:
            f.write(mascot.to_ansi(g))
    for face in ('happy', 'confused', 'sleepy'):
        g = mascot.build(mascot.SMALL, rel, face)
        with open(out('usr', 'share', 'slate', 'shale', f'{key}-small-{face}.txt'), 'w') as f:
            f.write(mascot.to_ansi(g))
        mascot.render(g, font_px=28, pad=6, bg=None).save(out('usr', 'share', 'slate', 'shale', f'{key}-small-{face}.png'))
# notification / app icon: small Shale on a dark rounded tile (readable in light themes too)
small = mascot.render(mascot.build(mascot.SMALL, cur, 'happy'), font_px=40, pad=0, bg=None)
for size in (48, 128, 256):
    tile = Image.new('RGBA', (size * 4, size * 4), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=size * 4 // 5, fill=INK)
    k = size * 4 * 0.86 / max(small.size)
    s = small.resize((round(small.width * k), round(small.height * k)), Image.LANCZOS)
    tile.alpha_composite(s, ((tile.width - s.width) // 2, (tile.height - s.height) // 2))
    tile.resize((size, size), Image.LANCZOS).save(out('usr', 'share', 'icons', 'hicolor', f'{size}x{size}', 'apps', 'slate-shale.png'))
print('shale written')
