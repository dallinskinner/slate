#!/usr/bin/env python3
"""ASCII-art rocks, one per Slate release (stones and minerals, alphabetical).

Each rock is a function (cols, rows, seed) -> grid of (char, shade) cells, shade 0..1.
The same grid feeds the release wallpaper (rendered in Hack, lime on dark), the welcome
animation (JSON) and the terminal logo (fastfetch). To add a release, write a field
function and add it to RELEASES.
Run with: python3 -I branding/ascii_rocks.py  (writes previews to branding/png/)
"""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'fonts', 'Hack-Regular.ttf')
FONT_BOLD = os.path.join(HERE, 'fonts', 'Hack-Bold.ttf')
LIME = (0xb6, 0xf2, 0x3a)
BG = (0x1a, 0x1b, 0x1e)
EMPTY = (' ', 0.0)

def blank(cols, rows):
    return [[EMPTY] * cols for _ in range(rows)]

def smooth_noise(seed, n=6):
    """Cheap smooth 2D noise: sum of a few random sine waves."""
    rnd = random.Random(seed)
    waves = [(rnd.uniform(0.5, 3) * rnd.choice((-1, 1)), rnd.uniform(0.5, 3), rnd.uniform(0, 6.3),
              1 / (k + 1)) for k in range(n)]
    norm = sum(w[3] for w in waves)
    return lambda x, y: sum(a * math.sin(fx * x * 3 + fy * y * 3 + p) for fx, fy, p, a in waves) / norm


# --- 0.1 Agate: a sliced agate geode. Wobbly concentric bands around a crystal cavity. ---
def agate(cols, rows, seed=1, aspect=0.5, fill=0.46):
    """aspect = character width / height (Hack ~ 0.5 with line spacing)."""
    rnd = random.Random(seed)
    g = blank(cols, rows)
    wob = smooth_noise(seed + 7, 3)
    bands = '@%#*+=-:'                          # one character per band, cycling inward
    nb = 11
    cx, cy = cols / 2, rows / 2
    ry = rows * fill; rx = min(ry / aspect * 1.25, cols * 0.47)   # a slightly wide oval
    for y in range(rows):
        for x in range(cols):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            th = math.atan2(dy, dx)
            r = math.hypot(dx, dy) * (1 + 0.06 * math.sin(3 * th + 0.6) + 0.03 * math.sin(5 * th + 2)
                                      + 0.03 * wob(dx * 0.6, dy * 0.6))
            if r > 1.0:
                continue
            if r > 0.94:                                    # rough outer rind
                g[y][x] = ('#' if rnd.random() < 0.7 else '%', 0.3); continue
            if r < 0.24:                                    # druzy quartz cavity
                if rnd.random() < 0.5:
                    g[y][x] = (rnd.choice("^*'.`"), 0.35 + 0.65 * rnd.random() * (1 - r / 0.24))
                continue
            t = (r - 0.24) / 0.70 * nb                      # band coordinate (0 = cavity edge)
            i = int(t)
            bright = (1.0, 0.45, 0.75, 0.3, 0.9, 0.55)[i % 6]   # irregular banding like real agate
            g[y][x] = (bands[i % len(bands)], bright)
    return g


# --- 0.2 Basalt: Giant's-Causeway hexagonal columns, a stepped mound seen from the front. ---
HEX_TOP = ['  ____  ',
           ' /    \\ ',
           ' \\____/ ']

def basalt(cols, rows, seed=2, mound=(0.5, 1.0, 0.46, 0.75), peak=None):
    """Honeycomb of column tops, nearer columns drawn later (they hide the ones behind).
    Hex cell: 8 wide x 3 tall; a column every 5 chars, odd ones 1 row lower.
    mound = (center x, ground y, half width, height) as fractions of the grid: columns exist
    inside that half-ellipse and are tallest in its middle, so the sides show as steps."""
    rnd = random.Random(seed)
    g = blank(cols, rows)
    mx, my, mw, mh = mound
    peak = peak or rows * 0.55
    def put(x, y, ch, s):
        if 0 <= x < cols and 0 <= y < rows:
            g[y][x] = (ch, s)
    hexes = []
    for j in range(0, rows // 2 + 3):
        for i in range(-1, cols // 5 + 2):
            x0 = i * 5; base = j * 2 + (i % 2)
            u = (x0 + 4) / cols - mx
            v = (base + 1) / rows
            # inside the mound footprint (a band of floor rows at the bottom of the screen)
            if abs(u) > mw * (0.75 + 0.25 * math.sin(v * 9 + seed)) or v < my - mh * 0.35:
                continue
            k = 1 - (abs(u) / mw) ** 1.6                 # 1 in the middle, 0 at the sides
            h = peak * max(0.0, k) ** 0.8 * rnd.uniform(0.55, 1.0) + rnd.uniform(0, 2)
            hexes.append((base, x0, int(h)))
    hexes.sort()
    for base, x0, h in hexes:
        top = base - h
        lit = 0.45 + 0.55 * min(1, max(0, base / rows))  # nearer = brighter
        for dy, line in enumerate(HEX_TOP):
            for dx, ch in enumerate(line):
                x, y = x0 + dx, top + dy
                if ch != ' ':
                    put(x, y, ch, lit)
                elif dy == 1 and 2 <= dx <= 5:            # top face
                    put(x, y, '.' if (dx + x0 + top) % 3 == 0 else ' ', lit * 0.4)
        joint = rnd.randint(3, 5)
        for k in range(1, rows):                         # column body down to the ground
            y = top + 2 + k
            if y >= rows: break
            jr = (k % joint == 0)
            body = '|_.._|' if jr else '|:##:|'
            for dx, ch in enumerate(body):
                sh = {'|': 0.5, '_': 0.42, ':': 0.3, '#': 0.2, '.': 0.25}[ch] * lit
                put(x0 + 1 + dx, y, ch if not (ch == '#' and (y + dx) % 2) else '=', sh)
    return g


RELEASES = [  # (version, name, field function)
    ('0.1', 'Agate', agate),
    ('0.2', 'Basalt', basalt),
]
CURRENT = RELEASES[-1]


def vignette(g, strength=0.75, cx=0.5, cy=0.5):
    rows, cols = len(g), len(g[0])
    out = []
    for y, row in enumerate(g):
        nr = []
        for x, (ch, s) in enumerate(row):
            d = math.hypot((x / cols - cx) * 1.2, (y / rows - cy) * 1.4)
            nr.append((ch, s * max(0.0, 1 - strength * d * d * 2)))
        out.append(nr)
    return out


def shade_color(s, bg=BG, fg=LIME):
    s = max(0.0, min(1.0, s))
    return tuple(int(b + (f - b) * s) for b, f in zip(bg, fg))


def render(g, W, H, font_px, bg=BG, fg=LIME, x0=None, y0=None):
    """Draw a grid onto a WxH image, centered unless x0/y0 given."""
    font = ImageFont.truetype(FONT, font_px)
    cw = font.getlength('M'); ch_h = int(font_px * 1.2)
    img = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(img)
    rows, cols = len(g), len(g[0])
    if x0 is None: x0 = (W - cols * cw) / 2
    if y0 is None: y0 = (H - rows * ch_h) / 2
    for y, row in enumerate(g):
        for x, (c, s) in enumerate(row):
            if c != ' ' and s > 0.02:
                d.text((x0 + x * cw, y0 + y * ch_h), c, font=font, fill=shade_color(s, bg, fg))
    return img


def grid_size(W, H, font_px):
    font = ImageFont.truetype(FONT, font_px)
    return int(W / font.getlength('M')) + 1, int(H / int(font_px * 1.2)) + 1


def wallpaper(release, W, H):
    """Full-bleed rock at a resolution-independent density (about 150 columns wide)."""
    ver, name, fn = release
    font_px = max(8, round(W / 150 / 0.6))
    cols, rows = grid_size(W, H, font_px)
    if fn is agate:
        g = fn(cols, rows, aspect=0.5, fill=0.40)
    else:
        g = vignette(fn(cols, rows), 0.35, 0.5, 0.6)
    img = render(g, W, H, font_px, x0=0, y0=0)
    # small release tag bottom-right: "SLATE 0.2 Basalt"
    d = ImageDraw.Draw(img)
    tf = ImageFont.truetype(FONT_BOLD, max(12, H // 60))
    tag = f'SLATE {ver} {name.upper()}'
    tw = tf.getlength(tag); pad = H // 30
    d.text((W - tw - pad, H - pad - tf.size), tag, font=tf, fill=shade_color(0.75))
    return img


def logo_grid(release, cols=34, rows=15):
    """Small version for the terminal logo / animation."""
    ver, name, fn = release
    if fn is agate:
        return fn(cols, rows, aspect=0.5, fill=0.48)
    return fn(cols, rows, seed=5, mound=(0.5, 1.0, 0.5, 0.9), peak=rows * 0.5)


def to_json(g):
    return {'cols': len(g[0]), 'rows': len(g),
            'text': [''.join(c for c, _ in row) for row in g],
            'shade': [[round(s, 2) for _, s in row] for row in g]}


def to_fastfetch(g):
    """fastfetch 'file' logo: $1 bright, $2 mid, $3 dim lime."""
    lines = []
    for row in g:
        cur = None; out = ''
        for c, s in row:
            lvl = '1' if s > 0.66 else '2' if s > 0.4 else '3'
            if c == ' ':
                out += ' '; continue
            if lvl != cur:
                out += '$' + lvl; cur = lvl
            out += '$$' if c == '$' else c
        lines.append(out.rstrip())
    while lines and not lines[-1].strip(): lines.pop()
    while lines and not lines[0].strip(): lines.pop(0)
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    out = os.path.join(HERE, 'png'); os.makedirs(out, exist_ok=True)
    for rel in RELEASES:
        wallpaper(rel, 1920, 1080).save(f'{out}/rock-{rel[1].lower()}.png')
        g = logo_grid(rel)
        print(rel[1]); print('\n'.join(''.join(c for c, _ in r) for r in g))
