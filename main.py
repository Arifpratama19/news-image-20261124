#!/usr/bin/env python3
"""THE WORLD TODAY - Tuesday, 24 November 2026.

A program that draws one newspaper front page summing up the world's
news of 24 November 2026.  Python standard library only, no network,
fully deterministic: every run writes the same bytes to /output/entry.png.

Layout (1024 x 1024): masthead, dateline, one lead story, three
illustrated hero stories, and a 4 x 8 grid of 32 more stories -
36 stories from 9 regions in all.
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 227)   # newsprint
INK = (22, 21, 19)       # near-black
RED = (178, 38, 30)
BLUE = (29, 78, 137)
GREEN = (30, 122, 52)
GOLD = (168, 116, 10)
GREY = (107, 101, 96)
PANEL = (235, 229, 211)   # light panel
SKY = (172, 206, 226)
SEA = (46, 111, 148)
DSEA = (28, 74, 104)
SUN = (232, 164, 32)
STONE = (214, 208, 192)
DSTONE = (120, 114, 100)

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def _set(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def fill(c):
    b = bytes(c)
    buf[:] = b * (W * H)


def fill_rect(x, y, w, h, c):
    if w <= 0 or h <= 0:
        return
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, W)
    y1 = min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        buf[i:i + len(row)] = row


def rect(x, y, w, h, c, t=1):
    fill_rect(x, y, w, t, c)
    fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c)
    fill_rect(x + w - t, y, t, h, c)


def hline(x, y, w, c, t=1):
    fill_rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill_rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for a in range(t):
            for b in range(t):
                _set(x0 + a, y0 + b, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=True):
    if r <= 0:
        return
    if fill:
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)
    else:
        x = 0
        y = r
        d = 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                _set(px, py, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1


def poly(points, c):
    """Scanline fill of a simple polygon given as [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(max(min(ys), 0), min(max(ys), H - 1) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[i]), y, max(1, int(xs[i + 1]) - int(xs[i])), 1, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    poly([(x0, y0), (x1, y1), (x2, y2)], c)

# ------------------------------------------------------------------- font
# 5x7 bitmap font: each glyph is 7 rows of 5 bits, top row first.
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ',': (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    '-': (0, 0, 0, 0x0E, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '+': (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '=': (0, 0, 0x1F, 0, 0x1F, 0, 0),
    ';': (0, 0, 0x0C, 0, 0x0C, 0x04, 0x08),
    ':': (0, 0, 0x0C, 0, 0x0C, 0, 0),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '*': (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    '[': (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    ']': (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    'a': (0, 0, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    'b': (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    'c': (0, 0, 0x0E, 0x11, 0x10, 0x11, 0x0E),
    'd': (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    'e': (0, 0, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    'f': (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    'g': (0, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'h': (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    'i': (0x04, 0, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    'j': (0x02, 0, 0x06, 0x02, 0x02, 0x12, 0x0C),
    'k': (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    'l': (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'm': (0, 0, 0x1A, 0x15, 0x15, 0x15, 0x15),
    'n': (0, 0, 0x1E, 0x11, 0x11, 0x11, 0x11),
    'o': (0, 0, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    'p': (0, 0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10),
    'q': (0, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x01),
    'r': (0, 0, 0x16, 0x19, 0x10, 0x10, 0x10),
    's': (0, 0, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    't': (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    'u': (0, 0, 0x11, 0x11, 0x11, 0x13, 0x0D),
    'v': (0, 0, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'w': (0, 0, 0x11, 0x11, 0x15, 0x15, 0x1B),
    'x': (0, 0, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    'y': (0, 0x11, 0x11, 0x0F, 0x01, 0x11, 0x0E),
    'z': (0, 0, 0x1F, 0x02, 0x04, 0x08, 0x1F),
}


def text_w(s, sc):
    return len(s) * 6 * sc


def draw_text(x, y, sc, c, txt, bold=False):
    """Draw text at scale sc (glyph is 5x7 * sc). Unknown chars become space."""
    cx = x
    for ch in txt:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * sc
            continue
        for row in range(7):
            bits = g[row]
            if not bits:
                continue
            for col in range(5):
                if bits & (0x10 >> col):
                    fill_rect(cx + col * sc, y + row * sc, sc, sc, c)
                    if bold and sc >= 2:
                        fill_rect(cx + col * sc + 1, y + row * sc, sc, sc, c)
        cx += 6 * sc
    return cx


def draw_text_center(x, y, w, sc, c, txt, bold=False):
    tw = text_w(txt, sc)
    draw_text(x + max(0, (w - tw) // 2), y, sc, c, txt, bold)


def wrap(txt, width_px, sc):
    """Greedy word wrap; returns a list of lines that fit width_px."""
    adv = 6 * sc
    lines = []
    for para in txt.split('\n'):
        words = para.split(' ')
        cur = ''
        for w in words:
            trial = (cur + ' ' + w) if cur else w
            if len(trial) * adv <= width_px or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def draw_para(x, y, w, sc, c, txt, max_lines, line_h, bold=False):
    lines = wrap(txt, w, sc)[:max_lines]
    for i, ln in enumerate(lines):
        draw_text(x, y + i * line_h, sc, c, ln, bold)
    return y + len(lines) * line_h


# --------------------------------------------------------------------- png
def write_png(path, w, h, rgb):
    raw = b''.join(b'\x00' + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    comp = zlib.compress(raw, 9)

    def chunk(t, data):
        c = t + data
        return struct.pack('>I', len(data)) + c + struct.pack(
            '>I', binascii.crc32(c) & 0xFFFFFFFF)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', comp)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------- illustrations
def draw_courthouse(x, y, w, h):
    """US federal courthouse: pediment, columns, steps, flag."""
    fill_rect(x, y, w, h, SKY)
    circle(x + w - 26, y + 16, 11, SUN)
    # flag pole + flag
    vline(x + 14, y + 8, 34, INK, 2)
    tri(x + 16, y + 8, x + 16, y + 18, x + 34, y + 13, RED)
    # building
    bx = x + 18
    bw = w - 36
    fill_rect(bx, y + h - 46, bw, 40, STONE)
    rect(bx, y + h - 46, bw, 40, DSTONE, 1)
    # pediment
    tri(bx - 4, y + h - 46, bx + bw + 4, y + h - 46, bx + bw // 2, y + h - 66,
        STONE)
    tri(bx + 8, y + h - 48, bx + bw - 8, y + h - 48, bx + bw // 2, y + h - 60,
        RED)
    # columns
    n = 5
    cw = (bw - 16) // n
    for i in range(n):
        cx0 = bx + 8 + i * cw
        fill_rect(cx0, y + h - 44, 7, 38, (250, 249, 244))
        fill_rect(cx0 - 1, y + h - 46, 9, 3, (250, 249, 244))
    # door
    fill_rect(bx + bw // 2 - 6, y + h - 22, 12, 16, (58, 48, 38))
    # steps
    fill_rect(bx - 6, y + h - 6, bw + 12, 3, DSTONE)
    fill_rect(bx - 10, y + h - 3, bw + 20, 3, GREY)


def draw_tanker(x, y, w, h):
    """Oil tanker on the Strait of Hormuz, mines in the water, low sun."""
    fill_rect(x, y, w, h, SKY)
    circle(x + w - 30, y + 18, 13, SUN)
    # distant cliffs
    poly([(x, y + h - 40), (x + 26, y + h - 52), (x + 52, y + h - 42),
          (x + 52, y + h - 40)], (146, 120, 88))
    poly([(x + w - 60, y + h - 40), (x + w - 34, y + h - 54),
          (x + w, y + h - 42), (x + w, y + h - 40)], (146, 120, 88))
    # sea
    fill_rect(x, y + h - 40, w, 40, SEA)
    fill_rect(x, y + h - 40, w, 3, DSEA)
    # waves
    for wx in range(x + 6, x + w - 8, 22):
        line(wx, y + h - 14, wx + 12, y + h - 14, (190, 220, 235), 2)
    for wx in range(x + 16, x + w - 8, 26):
        line(wx, y + h - 26, wx + 12, y + h - 26, (160, 200, 220), 2)
    # tanker hull
    hx = x + 18
    hw = w - 56
    hy = y + h - 62
    poly([(hx, hy), (hx + hw, hy), (hx + hw - 12, hy + 22), (hx, hy + 22)],
         (32, 32, 34))
    fill_rect(hx, hy + 22, hw - 12, 4, RED)
    # deck + containers
    fill_rect(hx + 10, hy - 14, 26, 14, RED)
    fill_rect(hx + 40, hy - 14, 26, 14, GREEN)
    fill_rect(hx + 70, hy - 14, 26, 14, GOLD)
    fill_rect(hx + 100, hy - 14, 26, 14, BLUE)
    # bridge tower
    fill_rect(hx + hw - 26, hy - 26, 16, 26, (240, 240, 235))
    fill_rect(hx + hw - 24, hy - 22, 12, 4, INK)
    # mine (spiked circle) in the water, right side
    mx, my = x + w - 18, y + h - 12
    circle(mx, my, 5, INK)
    for ang in range(0, 360, 45):
        import math
        r1 = 5
        r2 = 9
        a = math.radians(ang)
        line(mx + int(r1 * math.cos(a)), my + int(r1 * math.sin(a)),
             mx + int(r2 * math.cos(a)), my + int(r2 * math.sin(a)), INK, 1)


def draw_chart(x, y, w, h):
    """Taipei skyline under a rising green market chart."""
    fill_rect(x, y, w, h, (198, 224, 240))
    # skyline, back row
    for i, (bx, bw, bh) in enumerate(((0, 26, 34), (30, 20, 48), (54, 30, 30),
                                      (88, 18, 56), (110, 24, 38),
                                      (138, 20, 50), (162, 26, 32),
                                      (192, 18, 44), (214, 26, 30),
                                      (244, 20, 46), (268, 24, 34))):
        fill_rect(x + bx, y + h - bh, bw, bh, (96, 110, 128))
    # Taipei 101 style tower
    tx = x + w // 2 - 14
    for i in range(5):
        fill_rect(tx + i * 2, y + 16 + i * 9, 28 - i * 4, 9, (58, 76, 96))
    tri(tx + 6, y + 4, tx + 22, y + 4, tx + 14, y + 16, (58, 76, 96))
    # lit windows
    for wx in range(x + 6, x + w - 6, 12):
        for wy in range(y + h - 30, y + h - 4, 9):
            fill_rect(wx, wy, 3, 4, SUN)
    # rising chart line
    pts = [(x + 8, y + h - 18), (x + 46, y + h - 30), (x + 84, y + h - 24),
           (x + 122, y + h - 44), (x + 160, y + h - 40), (x + 198, y + h - 58),
           (x + 236, y + h - 52), (x + 274, y + h - 74), (x + w - 10, y + 12)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN, 3)
    # arrow head
    tri(x + w - 10, y + 12, x + w - 22, y + 16, x + w - 12, y + 24, GREEN)
    circle(x + 8, y + h - 18, 3, GREEN)


def draw_globe(x, y, w, h):
    """A warming world: smokestacks, a harsh sun, cracked dry earth."""
    fill_rect(x, y, w, h, (222, 236, 242))
    circle(x + w - 18, y + 13, 9, SUN)
    # smoke puffs
    for sx, sy, sr in ((x + 34, y + 8, 5), (x + 44, y + 4, 6),
                       (x + 56, y + 8, 5), (x + 96, y + 6, 5),
                       (x + 106, y + 3, 6)):
        circle(sx, sy, sr, (200, 200, 196))
    # smokestacks
    fill_rect(x + 30, y + 14, 14, h - 34, (120, 120, 116))
    fill_rect(x + 30, y + 14, 14, 5, RED)
    fill_rect(x + 92, y + 20, 12, h - 40, (140, 140, 136))
    fill_rect(x + 92, y + 20, 12, 4, RED)
    # factory block
    fill_rect(x + 48, y + h - 34, 40, 14, (150, 146, 134))
    # dry ground
    fill_rect(x, y + h - 20, w, 20, (206, 184, 138))
    hline(x, y + h - 20, w, (160, 134, 92), 1)
    # cracks in the earth
    line(x + 150, y + h - 20, x + 158, y + h - 8, (90, 60, 30), 2)
    line(x + 158, y + h - 8, x + 150, y + h - 2, (90, 60, 30), 2)
    line(x + 210, y + h - 20, x + 204, y + h - 10, (90, 60, 30), 2)
    line(x + 204, y + h - 10, x + 212, y + h - 2, (90, 60, 30), 2)
    line(x + 250, y + h - 20, x + 246, y + h - 6, (90, 60, 30), 2)
    # one small green sprout
    line(x + 180, y + h - 20, x + 180, y + h - 30, GREEN, 2)
    poly([(x + 180, y + h - 30), (x + 172, y + h - 34),
          (x + 180, y + h - 26)], GREEN)
    poly([(x + 180, y + h - 30), (x + 188, y + h - 34),
          (x + 180, y + h - 26)], GREEN)


# ------------------------------------------------------------------- stories
# Every story below was first reported on 24 November 2026.
# (tag, headline, summary)

LEAD = (
    'UNITED STATES',
    'HUAWEI GUILTY ON 10 COUNTS IN U.S. SPY CASE',
    'A Brooklyn jury convicts the Chinese telecom giant of trade-secret theft, bank fraud and sanctions breaches. Huawei is cleared of racketeering.',
)

HEROES = [
    ('MIDDLE EAST',
     'FOUR TANKERS HIT BY MINES IN STRAIT OF HORMUZ',
     'Iran says four tankers hit naval mines and caught fire; its navy struck a container ship near Oman as Tehran orders the strait shut.',
     draw_tanker),
    ('TAIWAN',
     'TAIEX SOARS 9% IN BIGGEST ONE-DAY JUMP EVER',
     "Taiwan stocks leap a record 3,310 points to 40,122 as Nvidia's 31% Monday surge, after Jensen Huang returned as CEO, lifts chips worldwide.",
     draw_chart),
    ('CLIMATE',
     'COP31 COLLAPSES WITHOUT A DEAL IN ANTALYA',
     'The longest climate summit ever ends with no deal, the first collapse since 2009, as 90-plus nations reject a draft that drops fossil fuels.',
     draw_globe),
]

GRID = [
    ('UKRAINE',
     'ZAPORIZHZHIA STRIKE KILLS 2, WOUNDS 40',
     'Russian attack hits a block in Kosmichnyi; 2 killed and 40 wounded.'),
    ('POLAND',
     'RUSSIAN DRONE OVER POLAND',
     'A Geran drone flies 20 km into Poland and circles for nine minutes.'),
    ('UKRAINE',
     'UKRAINE HITS RUSSIAN SHIPS',
     'Drones hit the Sparta II in the Gulf of Finland and a corvette off Libya.'),
    ('UKRAINE',
     'ZELENSKY SEEKS PEACE TALKS',
     'Kyiv calls for Ukraine, Russia, the U.S. and Europe to meet soon.'),
    ('NATO',
     'NATO VOWS TO DEFEND SPACE',
     'Rutte vows NATO will defend space after nuclear satellite reports.'),
    ('GERMANY',
     'GERMANY GETS UKRAINE WAR SYSTEM',
     "Berlin signs for access to Delta, Ukraine's battlefield system."),
    ('EUROPE',
     'EU WANTS CURBS ON RUSSIAN TRAVEL',
     'Seven European governments urge limits on Russians entering the EU.'),
    ('GAZA',
     'ISRAEL KILLS HAMAS SECURITY CHIEF',
     'Airstrikes kill Hamas security chief Naeem Abu Nahel and six others.'),
    ('GAZA',
     'MENINGITIS ALERT AS CASES SURGE IN GAZA',
     '272 cases in October, eight times the normal toll; 15 dead this year.'),
    ('SAUDI ARABIA',
     'DRONE HITS RIYADH TOWER; 11 WOUNDED',
     'A suspected Houthi drone strikes the PIF tower in Riyadh, wounding 11.'),
    ('YEMEN',
     'SAUDI STRIKES ON YEMEN KILL 25',
     'Saudi strikes on buses and trucks in Lahj leave 25 dead or missing.'),
    ('YEMEN',
     'HOUTHIS 60 KM FROM ADEN, ARMY WARNS',
     "Yemen's military says Houthi forces are massing 60 km from Aden."),
    ('BRITAIN',
     'UK SANCTIONS HOUTHI LEADERS',
     'London freezes assets and bans travel for four senior Houthi officials.'),
    ('IRAQ',
     'BAGHDAD SEIZES KURD OILFIELDS',
     'Baghdad orders federal control of Kurdish oilfields in Kirkuk.'),
    ('LIBYA',
     'HAFTAR VISITS TURKEY',
     'Libyan commander Khalifa Haftar meets Erdogan in Ankara in a first visit.'),
    ('IRAN',
     'IRAN VOWS TO FIGHT U.S. NAVAL BLOCKADE',
     'Tehran says it will use every tool against the reinstated U.S. blockade.'),
    ('CHINA',
     'DEATH SENTENCE FOR SPYING IN CHINA',
     'Official Ma is sentenced to death for spying for a foreign country.'),
    ('KOREA',
     'RUSSIAN JETS ENTER KOREAN AIR ZONE',
     'South Korea scrambles fighters and orders Ulleungdo residents to shelter.'),
    ('INDONESIA',
     'PRABOWO NAMES TWO VP CANDIDATES',
     'Prabowo nominates Amran Sulaiman and Sugiono to replace VP Gibran.'),
    ('MALAYSIA',
     'MALAYSIA RETURNS MYANMAR MIGRANTS',
     'Kuala Lumpur will return thousands of Myanmar migrants in December.'),
    ('BANGLADESH',
     'HASINA PLANS RETURN FROM EXILE',
     'Ousted ex-PM Hasina plans to return from India on 16 December.'),
    ('VIETNAM',
     'HANOI BLAST KILLS SIX AT HOT-POT SPOT',
     'A suspected gas leak blast kills at least six at a Dong Da restaurant.'),
    ('THE HAGUE',
     'ICJ: MYANMAR GUILTY OF GENOCIDE',
     'UN court finds Myanmar committed genocide against the Rohingya.'),
    ('SINGAPORE',
     'U.S. BLACKLISTS MEGASPEED FIRM',
     'Washington blacklists Singapore firm Megaspeed over the Nvidia scandal.'),
    ('COLOMBIA',
     '25 HELD HOSTAGE IN CARTAGENA',
     'Armed men hold 25 hostage in a Cartagena supermarket.'),
    ('COLOMBIA',
     'CAR BOMB WOUNDS 23 ON EVE OF PEACE DAY',
     'A car bomb injures 23 in Villavicencio on eve of the peace anniversary.'),
    ('MEXICO',
     '"EL CHAPO ISIDRO" CAPTURED IN SINALOA',
     'A U.S. drone helps Mexico capture cartel chief Isidro Meza Flores.'),
    ('SENEGAL',
     'SENEGAL GETS AFCON TITLE BACK',
     'CAS restores Senegal as 2025 Africa Cup champions.'),
    ('DR CONGO',
     'EBOLA TEAMS TRAPPED IN ITURI',
     'Fighting near an Ituri hospital halts Ebola teams; WHO staff evacuate.'),
    ('BRITAIN',
     'UK HEAT DEATHS HIT RECORD 5,258',
     'England records 5,258 heat deaths from May to September, a record.'),
    ('FRANCE',
     'SANOFI BUYS INSMED FOR $41 BILLION',
     "Sanofi's $175-a-share deal for Insmed is the biggest drug deal in years."),
    ('UNITED NATIONS',
     '47,000 WOMEN KILLED BY PARTNERS IN 2025',
     'UN: 47,000 women and girls killed by a partner or family member in 2025.'),
]

REGIONS = {
    'UNITED STATES': RED, 'TAIWAN': GREEN, 'MIDDLE EAST': RED,
    'CLIMATE': GOLD, 'UKRAINE': BLUE, 'POLAND': BLUE, 'NATO': BLUE,
    'GERMANY': BLUE, 'EUROPE': BLUE, 'GAZA': RED, 'SAUDI ARABIA': RED,
    'YEMEN': RED, 'BRITAIN': BLUE, 'IRAQ': RED, 'LIBYA': RED,
    'IRAN': RED, 'CHINA': GREEN, 'KOREA': GREEN, 'INDONESIA': GREEN,
    'MALAYSIA': GREEN, 'BANGLADESH': GREEN, 'VIETNAM': GREEN,
    'THE HAGUE': GOLD, 'SINGAPORE': GREEN, 'COLOMBIA': GOLD,
    'MEXICO': GOLD, 'SENEGAL': GOLD, 'DR CONGO': GOLD,
    'FRANCE': BLUE, 'UNITED NATIONS': GOLD,
}

# ------------------------------------------------------------------- layout
MX = 14                      # outer margin
CW = W - 2 * MX               # content width = 996


def tag_color(tag):
    return REGIONS.get(tag, INK)


def draw_lead(y):
    """Full-width lead story with courthouse illustration on the right."""
    h = 128
    fill_rect(MX, y, CW, h, PANEL)
    rect(MX, y, CW, h, INK, 1)
    tag, head, body = LEAD
    tx = MX + 12
    tw = CW - 12 - 232 - 12
    draw_text(tx, y + 8, 2, tag_color(tag), tag, bold=True)
    draw_text(tx + text_w(tag, 2) + 12, y + 8, 1, GREY,
              'LEAD STORY - 24 NOV 2026', bold=True)
    draw_para(tx, y + 26, tw, 3, INK, head, 2, 24, bold=True)
    draw_para(tx, y + 78, tw, 2, INK, body, 3, 16)
    draw_courthouse(MX + CW - 232, y + 6, 220, h - 12)
    rect(MX + CW - 232, y + 6, 220, h - 12, INK, 1)
    return y + h


def draw_hero(x, y, w, h, story):
    tag, head, body, art = story
    fill_rect(x, y, w, h, PANEL)
    rect(x, y, w, h, INK, 1)
    art(x + 6, y + 6, w - 12, 58)
    rect(x + 6, y + 6, w - 12, 58, INK, 1)
    ty = y + 70
    draw_text(x + 8, ty, 2, tag_color(tag), tag, bold=True)
    draw_para(x + 8, ty + 18, w - 16, 2, INK, head, 2, 16, bold=True)
    draw_para(x + 8, ty + 52, w - 16, 1, INK, body, 3, 9)


def draw_cell(x, y, w, h, story):
    tag, head, body = story
    fill_rect(x, y, w, h, PAPER)
    rect(x, y, w, h, GREY, 1)
    fill_rect(x + 1, y + 1, w - 2, 3, tag_color(tag))
    draw_text(x + 6, y + 8, 1, tag_color(tag), tag, bold=True)
    draw_para(x + 6, y + 17, w - 12, 2, INK, head, 2, 15, bold=True)
    draw_para(x + 6, y + 49, w - 12, 1, INK, body, 2, 9)


def build():
    fill(PAPER)
    # ---- masthead
    draw_text_center(MX, 10, CW, 8, INK, 'THE WORLD TODAY', bold=True)
    hline(MX, 72, CW, INK, 2)
    draw_text_center(MX, 78, CW, 2, INK,
                     'TUESDAY, 24 NOVEMBER 2026', bold=True)
    hline(MX, 98, CW, INK, 1)
    # ---- dateline strip
    draw_text(MX, 102, 1, RED, '36 STORIES', bold=True)
    draw_text(MX + text_w('36 STORIES', 1) + 8, 102, 1, INK,
              'FROM 9 REGIONS - THE WORLD IN ONE DAY', bold=True)
    draw_text(MX + CW - text_w('ALL EVENTS FIRST REPORTED 24 NOV 2026', 1),
              102, 1, GREY, 'ALL EVENTS FIRST REPORTED 24 NOV 2026')
    # ---- lead
    y = draw_lead(114)
    # ---- heroes
    hy = y + 8
    hh = 152
    hw = (CW - 16) // 3
    for i, story in enumerate(HEROES):
        draw_hero(MX + i * (hw + 8), hy, hw, hh, story)
    # ---- grid
    gy = hy + hh + 8
    gh = 1004 - gy
    rows = 8
    cols = 4
    cw = (CW - (cols - 1) * 6) // cols
    ch = gh // rows
    for i, story in enumerate(GRID):
        r, c = divmod(i, cols)
        draw_cell(MX + c * (cw + 6), gy + r * ch, cw, ch - 6, story)
    # ---- footer
    draw_text_center(MX, 1012, CW, 1, GREY,
                     'THE WORLD TODAY - EVERY STORY DATED 24 NOVEMBER 2026')
    return 1 + len(HEROES) + len(GRID)


def main():
    n = build()
    os.makedirs('/output', exist_ok=True)
    size = write_png('/output/entry.png', W, H, buf)
    print('stories:', n)
    print('bytes:', size)
    print('path: /output/entry.png')


if __name__ == '__main__':
    main()
