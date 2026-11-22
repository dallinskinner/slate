#!/usr/bin/env python3
"""Shale, the Slate hermit crab: a crab that moves into a new rock every release.

The drawing is a template: '@' cells are the shell and get filled with this release's rock
texture (ascii_rocks field functions), everything else is Shale. E (eyes) and M (mouth)
markers are replaced per expression.
Run with: python3 -I branding/mascot.py   (writes previews to branding/png/)
"""
import os
from PIL import Image, ImageDraw, ImageFont
import ascii_rocks as R

TEXT = (0xe6, 0xe6, 0xe6)

# Big: welcome, website, login screen
BIG = r"""
              _.-~~~~~~-._
          .-'@@@@@@@@@@@@@@'-.
        .'@@@@@@@@@@@@@@@@@@@@'.
       /@@@@@@@@@@@@@@@@@@@@@@@@\
      |@@@@@@@@@@@@@@@@@@@@@@@@@@|
      |@@@@@@@@@@@@@@@@@@@@@@@@@@|
       \@@@@@@@@@@@@@@@@@@@@@@@@/
  .--.  '-.@@@@@@@@@@@@@@@@@@.-'
 ( () )      E              E      .-.
  \  /       \\  .------.  //     ( ) )
   \ \_______ \(    M     )/ _____/ /'
    '--------'  '-.____.-'  '------'
              /_/ /_/  \_\ \_\
"""

# Small: terminal, notifications, error messages
SMALL = r"""
      _.-~~-._
    .'@@@@@@@@'.
   /@@@@@@@@@@@@\
 () E'-.____.-'E ()
  \\_\\(  M  )//_//
       '-.__.-'
      /_/    \_\
"""

FACES = {           # eyes, mouth (big uses 1 char each; small too)
    'happy':    ('o', 'o', 'w'),
    'joy':      ('^', '^', 'v'),
    'sleepy':   ('-', '-', '_'),
    'confused': ('o', 'O', '~'),
    'wink':     ('^', 'o', 'v'),
}


def template(art):
    lines = art.strip('\n').split('\n')
    w = max(len(l) for l in lines)
    return [l.ljust(w) for l in lines]


def build(art, release, face='happy', seed=3):
    """Grid of (char, shade, kind) with kind 'shell' or 'crab'."""
    rows = template(art)
    H, W = len(rows), len(rows[0])
    _ver, _name, field = release
    cells = [(x, y) for y, l in enumerate(rows) for x, c in enumerate(l) if c == '@']
    x0, x1 = min(x for x, _ in cells), max(x for x, _ in cells)
    y0, y1 = min(y for _, y in cells), max(y for _, y in cells)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    big = field(bw * 2, bh * 2, seed=seed)
    def cover(ox, oy):
        return sum(big[oy + y - y0][ox + x - x0][0] != ' ' for x, y in cells)
    ox, oy = max(((ox, oy) for oy in range(0, bh + 1, 2) for ox in range(0, bw + 1, 3)),
                 key=lambda o: cover(*o))
    tex = [[(' ', 0.0)] * W for _ in range(H)]
    for x, y in cells:
        tex[y][x] = big[oy + y - y0][ox + x - x0]
    le, re_, mo = FACES[face]
    out = []
    for y, line in enumerate(rows):
        eyes = 0; row = []
        for x, ch in enumerate(line):
            if ch == '@':
                c, s = tex[y][x]
                if c == ' ': c, s = ':', 0.35   # keep the shell solid
                row.append((c, max(0.35, s), 'shell'))
            elif ch == 'E':
                row.append((le if eyes == 0 else re_, 1.0, 'crab')); eyes += 1
            elif ch == 'M':
                row.append((mo, 1.0, 'crab'))
            elif ch == ' ':
                row.append((' ', 0.0, 'crab'))
            else:
                # the shell's rim (top line, or touching shell cells) takes the rock color
                near = y == 0 or any(0 <= y + dy < H and 0 <= x + dx < W and rows[y + dy][x + dx] == '@'
                                     for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                row.append((ch, 0.95, 'shell') if near else (ch, 1.0, 'crab'))
        out.append(row)
    return out


def to_text(g):
    return '\n'.join(''.join(c for c, _s, _k in row).rstrip() for row in g)


def render(g, font_px=28, pad=24):
    font = ImageFont.truetype(R.FONT, font_px)
    cw = font.getlength('M'); ch = int(font_px * 1.17)
    W = int(cw * len(g[0]) + 2 * pad); H = ch * len(g) + 2 * pad
    img = Image.new('RGB', (W, H), R.BG)
    d = ImageDraw.Draw(img)
    for y, row in enumerate(g):
        for x, (c, s, k) in enumerate(row):
            if c == ' ': continue
            col = R.shade_color(s) if k == 'shell' else TEXT
            d.text((pad + x * cw, pad + y * ch), c, font=font, fill=col)
    return img


if __name__ == '__main__':
    out = os.path.join(R.HERE, 'png', 'mascot'); os.makedirs(out, exist_ok=True)
    for rel in R.RELEASES:
        name = rel[1].lower()
        for face in FACES:
            render(build(BIG, rel, face)).save(os.path.join(out, f'shale-{name}-{face}.png'))
        render(build(SMALL, rel, 'happy'), font_px=32).save(os.path.join(out, f'shale-{name}-small.png'))
        print(to_text(build(BIG, rel))); print(to_text(build(SMALL, rel)))
    print('previews in', out)
