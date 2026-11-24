#!/usr/bin/env python3
"""Newspaper front-page poster summing up Tuesday 24 November 2026 world news.

Pure Python standard library. Draws everything (text via a hand-defined 5x7
bitmap font, illustrations via basic shapes) onto an RGB pixel canvas and
writes the PNG bytes by hand with zlib + struct. No files read, no network,
no randomness: running it twice gives byte-identical output.

Usage: python3 main.py [output-path]   (or set OUTPUT_PATH)
Default output: /output/entry.png
"""

import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette --
PAPER = (245, 240, 230)
INK = (18, 18, 18)
RED = (178, 34, 34)
BLUE = (28, 68, 128)
GREY = (110, 110, 108)
LIGHT_GREY = (200, 198, 190)
GOLD = (201, 162, 39)
GREEN = (34, 110, 60)
ORANGE = (224, 110, 20)
YELLOW = (240, 200, 40)
SEA = (46, 110, 150)
DARK = (40, 40, 44)

# ------------------------------------------------------------- bitmap font --
# Each glyph is 7 rows of 5 pixels, '#' = on, '.' = off.
FONT = {
    'A': (" .###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '/': ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
}


def text_width(s, scale):
    """Pixel width of string s rendered at the given scale."""
    return len(s) * 6 * scale - scale if s else 0


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines = []
    for para in s.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# ------------------------------------------------------------------ canvas --
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def circle(self, cx, cy, r, c, t=1):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            for k in range(t):
                self.set(cx - dx - k, cy + dy, c)
                self.set(cx + dx + k, cy + dy, c)
                self.set(cx + dy, cy - dx - k, c)
                self.set(cx + dy, cy + dx + k, c)

    def fill_triangle(self, p0, p1, p2, c):
        pts = sorted([p0, p1, p2], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts

        def interp(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)

        for y in range(y0, y2 + 1):
            if y < y1:
                xa = interp(x0, y0, x1, y1, y)
                xb = interp(x0, y0, x2, y2, y)
            else:
                xa = interp(x1, y1, x2, y2, y)
                xb = interp(x0, y0, x2, y2, y)
            lo, hi = (xa, xb) if xa <= xb else (xb, xa)
            self.fill_rect(int(lo), y, int(hi) - int(lo) + 1, 1, c)

    def fill_poly(self, pts, c):
        """Fan-fill a convex polygon."""
        for i in range(1, len(pts) - 1):
            self.fill_triangle(pts[0], pts[i], pts[i + 1], c)

    def starburst(self, cx, cy, r_out, r_in, spikes, c):
        pts = []
        for i in range(spikes * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / spikes - math.pi / 2
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.fill_poly(pts, c)

    # ------------------------------------------------------------ text ----
    def draw_char(self, x, y, ch, scale, c):
        glyph = FONT.get(ch.upper(), FONT['?'])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '#':
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            self.draw_char(cx, y, ch, scale, c)
            cx += 6 * scale
        return cx

    def text_centered(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)

    def paragraph(self, x, y, s, scale, max_w, c, leading=None):
        """Wrapped paragraph; returns y just below the last line."""
        lh = leading if leading is not None else 9 * scale
        for line in wrap_text(s, scale, max_w):
            self.text(x, y, line, scale, c)
            y += lh
        return y

# ------------------------------------------------------------- illustrations --
def draw_ship_explosion(cv, x, y, w, h):
    """Lead illustration: warship at a dock, explosion and fire, sea below."""
    # sky band
    cv.fill_rect(x, y, w, h, (214, 228, 238))
    # distant port buildings
    cv.fill_rect(x + 8, y + h - 108, 46, 58, GREY)
    cv.fill_rect(x + 62, y + h - 96, 34, 46, LIGHT_GREY)
    cv.fill_rect(x + w - 58, y + h - 102, 50, 52, GREY)
    # sea
    cv.fill_rect(x, y + h - 52, w, 52, SEA)
    cv.fill_rect(x, y + h - 52, w, 3, BLUE)
    for wy in (y + h - 38, y + h - 24, y + h - 12):
        for sx in range(x + 10, x + w - 30, 46):
            cv.hline(sx, wy, 26, (180, 210, 225), 2)
    # hull (trapezoid) and deck
    hx, hy = x + 60, y + h - 96
    cv.fill_poly([(hx, hy), (hx + 210, hy), (hx + 188, hy + 34),
                  (hx + 22, hy + 34)], DARK)
    cv.fill_rect(hx + 12, hy - 22, 150, 22, (70, 70, 76))
    cv.fill_rect(hx + 30, hy - 40, 12, 18, DARK)
    cv.fill_rect(hx + 120, hy - 34, 10, 12, DARK)
    # mast
    cv.vline(hx + 82, hy - 66, 46, DARK, 4)
    cv.hline(hx + 62, hy - 66, 44, DARK, 3)
    # funnel with smoke
    cv.fill_rect(hx + 150, hy - 52, 22, 30, (90, 40, 40))
    cv.fill_circle(hx + 165, hy - 62, 12, GREY)
    cv.fill_circle(hx + 180, hy - 76, 15, LIGHT_GREY)
    # explosion starburst over the midship
    ex, ey = hx + 105, hy - 58
    cv.starburst(ex, ey, 52, 24, 9, YELLOW)
    cv.starburst(ex, ey, 38, 18, 9, ORANGE)
    cv.starburst(ex, ey, 22, 10, 8, RED)
    cv.fill_circle(ex, ey, 9, (255, 240, 160))
    # flame tongues and sparks
    cv.fill_triangle((ex - 46, hy - 20), (ex - 30, hy - 64),
                     (ex - 18, hy - 20), ORANGE)
    cv.fill_triangle((ex + 24, hy - 20), (ex + 38, hy - 58),
                     (ex + 50, hy - 20), RED)
    for sx, sy in ((ex - 70, ey - 30), (ex + 72, ey - 44),
                   (ex + 58, ey + 6), (ex - 58, ey + 10)):
        cv.fill_circle(sx, sy, 3, YELLOW)


def draw_chip_arrow(cv, x, y, s):
    """Nvidia: a chip with pins and a rising arrow, inside its s x s box."""
    cs = 32  # chip side
    cv.fill_rect(x, y + 14, cs, cs, DARK)
    cv.rect(x + 8, y + 22, 16, 16, (120, 200, 140), 3)
    cv.fill_rect(x + 14, y + 28, 4, 4, (120, 200, 140))
    for i in range(3):
        off = 6 + i * 10
        cv.fill_rect(x + off, y + 8, 4, 6, DARK)
        cv.fill_rect(x + off, y + 46, 4, 6, DARK)
        cv.fill_rect(x - 2, y + 14 + off, 6, 4, DARK)
    # rising arrow in the space right of the chip
    ax = x + cs + 2
    cv.line(ax, y + s - 10, ax + 9, y + s // 2 + 2, GREEN, 3)
    cv.line(ax + 9, y + s // 2 + 2, ax + 20, y + 6, GREEN, 3)
    cv.fill_triangle((ax + 20, y + 2), (ax + 11, y + 6), (ax + 22, y + 14),
                     GREEN)


def draw_broken_talks(cv, x, y, s):
    """Diplomacy: two speech bubbles that do not meet, crossed out."""
    cv.fill_circle(x + 14, y + 16, 16, BLUE)
    cv.fill_circle(x + s - 14, y + 16, 16, RED)
    cv.fill_triangle((x + 6, y + 28), (x + 18, y + 28), (x + 8, y + 40), BLUE)
    cv.fill_triangle((x + s - 18, y + 28), (x + s - 6, y + 28),
                     (x + s - 8, y + 40), RED)
    cv.fill_rect(x + 8, y + 13, 12, 4, PAPER)
    cv.fill_rect(x + s - 20, y + 13, 12, 4, PAPER)
    cv.fill_rect(x + 8, y + 20, 12, 4, PAPER)
    cv.fill_rect(x + s - 20, y + 20, 12, 4, PAPER)
    cv.line(x + 2, y + s - 2, x + s - 2, y + 2, RED, 4)
    cv.line(x + 2, y + 2, x + s - 2, y + s - 2, RED, 4)


def draw_contamination(cv, x, y, s):
    """Humanitarian: a warning triangle over a droplet."""
    cx = x + s // 2
    cv.fill_triangle((cx, y + 2), (x + 4, y + s - 6), (x + s - 4, y + s - 6),
                     YELLOW)
    cv.fill_triangle((cx, y + 12), (x + 13, y + s - 13),
                     (x + s - 13, y + s - 13), INK)
    cv.fill_rect(cx - 2, y + 22, 4, 16, YELLOW)
    cv.fill_rect(cx - 2, y + 42, 4, 4, YELLOW)
    cv.fill_circle(x + s - 8, y + s - 8, 7, SEA)
    cv.fill_triangle((x + s - 8, y + s - 22), (x + s - 14, y + s - 8),
                     (x + s - 2, y + s - 8), SEA)


def draw_mercury_probe(cv, x, y, s):
    """Space: cratered Mercury with the probe flying past."""
    cx, cy, r = x + 20, y + s - 22, 18
    cv.fill_circle(cx, cy, r, (176, 148, 120))
    for ox, oy, orad in ((-8, -6, 4), (6, 4, 5), (-2, 8, 3), (9, -8, 3)):
        cv.fill_circle(cx + ox, cy + oy, orad, (140, 112, 88))
    # probe body and solar panels
    px, py = x + s - 34, y + 12
    cv.fill_rect(px, py, 18, 12, DARK)
    cv.fill_rect(px - 20, py + 2, 18, 8, BLUE)
    cv.fill_rect(px + 20, py + 2, 18, 8, BLUE)
    cv.line(px + 2, py + 12, cx + 8, cy - 10, GREY, 2)
    cv.fill_circle(px + 9, py + 6, 3, GOLD)
    # orbit arc
    for a in range(0, 121, 6):
        ang = math.radians(a)
        ox = int(cx + (r + 12) * math.cos(ang))
        oy = int(cy - (r + 12) * math.sin(ang) * 0.55)
        cv.fill_rect(ox, oy, 3, 3, GREY)


def draw_trophy_ball(cv, x, y, s):
    """Sport: a trophy cup beside a football."""
    cx = x + 22
    cv.fill_rect(cx - 12, y + 4, 24, 20, GOLD)
    cv.fill_rect(cx - 18, y + 2, 6, 14, GOLD)
    cv.fill_rect(cx + 12, y + 2, 6, 14, GOLD)
    cv.fill_rect(cx - 3, y + 24, 6, 12, GOLD)
    cv.fill_rect(cx - 12, y + 36, 24, 5, GOLD)
    cv.fill_rect(cx - 16, y + 41, 32, 4, GOLD)
    bx, by, br = x + s - 20, y + s - 20, 17
    cv.fill_circle(bx, by, br, (250, 250, 250))
    cv.circle(bx, by, br, INK, 2)
    cv.fill_poly([(bx, by - 7), (bx + 7, by - 2), (bx + 4, by + 7),
                  (bx - 4, by + 7), (bx - 7, by - 2)], INK)
    for dx, dy in ((0, -13), (12, -4), (8, 11), (-8, 11), (-12, -4)):
        cv.line(bx, by, bx + dx, by + dy, INK, 2)


def draw_factory_fire(cv, x, y, s):
    """Asia: a factory building with flames from its roof."""
    cv.fill_rect(x + 4, y + 26, s - 8, s - 30, (120, 110, 100))
    cv.fill_rect(x + 8, y + 6, 8, 20, (120, 110, 100))
    cv.fill_rect(x + 22, y + 2, 8, 24, (120, 110, 100))
    for wx in (x + 12, x + 30, x + 48):
        cv.fill_rect(wx, y + 36, 10, 10, (210, 200, 170))
    cv.fill_rect(x + 4, y + 26, s - 8, 4, DARK)
    fx = x + s // 2
    cv.fill_triangle((fx - 16, y + 28), (fx - 4, y + 2), (fx + 4, y + 28),
                     ORANGE)
    cv.fill_triangle((fx + 2, y + 28), (fx + 12, y + 6), (fx + 20, y + 28),
                     RED)
    cv.fill_triangle((fx - 6, y + 28), (fx, y + 12), (fx + 6, y + 28), YELLOW)


# ------------------------------------------------------------------ layout --
def draw_cell(cv, x, y, w, h, kicker, headline, body, icon_fn):
    cv.rect(x, y, w, h, INK, 2)
    cv.fill_rect(x + 2, y + 2, w - 4, 26, INK)
    cv.text(x + 10, y + 9, kicker, 2, PAPER)
    # icon top-right of the headline zone
    icon_fn(cv, x + w - 74, y + 36, 58)
    hw = w - 92
    hy = y + 38
    for line in wrap_text(headline, 3, hw):
        cv.text(x + 10, hy, line, 3, RED)
        hy += 30
    hy += 6
    cv.paragraph(x + 10, hy, body, 2, w - 20, INK, leading=16)


def build_image():
    cv = Canvas(W, H, PAPER)
    cv.rect(10, 10, W - 20, H - 20, INK, 3)
    cv.rect(16, 16, W - 32, H - 32, INK, 1)

    # masthead
    cv.text_centered(W // 2, 34, "THE WORLD TODAY", 7, INK)
    cv.hline(36, 96, W - 72, INK, 3)
    cv.text_centered(W // 2, 106, "TUESDAY, 24 NOVEMBER 2026", 3, RED)
    cv.text_centered(W // 2, 132, "ONE PAGE  -  SEVEN STORIES  -  THE DAY IN FULL",
                     2, GREY)
    cv.hline(36, 152, W - 72, INK, 3)
    cv.hline(36, 157, W - 72, INK, 1)

    # lead story
    lx, ly = 36, 172
    cv.text(lx, ly, "LEAD STORY  -  THE MEDITERRANEAN", 2, RED)
    cv.text(lx, ly + 26, "RUSSIAN WARSHIP", 4, INK)
    cv.text(lx, ly + 56, "DESTROYED IN LIBYA", 4, INK)
    cv.hline(lx, ly + 92, 500, INK, 2)
    lead_body = ("A RUSSIAN NAVY CORVETTE, BELIEVED TO BE THE MERKURY, "
                 "WAS DESTROYED BY AN EXPLOSION AND FIRE WHILE DOCKED "
                 "AT THE PORT OF BENGHAZI, LIBYA. REPORTED AS A "
                 "SUSPECTED UKRAINIAN SEA-DRONE STRIKE. IT SHOWS THE "
                 "UKRAINE WAR REACHING THE MEDITERRANEAN.")
    cv.paragraph(lx, ly + 106, lead_body, 2, 500, INK, leading=18)
    draw_ship_explosion(cv, 566, ly + 8, 422, 262)

    cv.hline(36, 440, W - 72, INK, 3)

    # six story cells, 3 x 2
    gx, gy = 36, 448
    cw, ch = 304, 244
    gap = 12
    cells = [
        ("BUSINESS", "HUANG RETURNS AS NVIDIA CEO",
         "REINSTATED AFTER AN INVESTIGATION. SHARES SURGED OVER 31% IN "
         "A DAY. VALUE UP ALMOST $1 TRILLION. SENATE HEARING "
         "3 DECEMBER.",
         draw_chip_arrow),
        ("DIPLOMACY", "TRUMP-KIM OUTREACH IGNORED",
         "KIM JONG UN HAS IGNORED OR REJECTED TRUMP'S ATTEMPTS TO "
         "REVIVE DIALOGUE AS PYONGYANG EXPANDS ITS NUCLEAR PROGRAMME.",
         draw_broken_talks),
        ("HUMANITARIAN", "GAZA LEFT TOXICALLY CONTAMINATED",
         "A REPORT BY OXFAM AND THE CONFLICT AND ENVIRONMENT "
         "OBSERVATORY FOUND GAZA'S AIR, SOIL AND WATER DANGEROUSLY "
         "CONTAMINATED.", draw_contamination),
        ("SPACE", "BEPICOLOMBO REACHES MERCURY",
         "THE EUROPE-JAPAN PROBE ENTERED MERCURY ORBIT ON 21 NOVEMBER "
         "AFTER AN EIGHT-YEAR CRUISE. A THRUSTER BURN RAN SHORT BUT "
         "THE CRAFT IS SAFE.", draw_mercury_probe),
        ("SPORT", "WOMEN'S WORLD CUP HOSTS NAMED",
         "THE 2031 EDITION WILL BE IN THE USA, MEXICO, COSTA RICA "
         "AND JAMAICA. THE 2035 EDITION WILL BE IN THE UK.",
         draw_trophy_ball),
        ("ASIA", "DEADLY FIRE AT INDONESIA FACTORY",
         "A FIRE AT A SWEET FACTORY LEFT MORE THAN 30 WORKERS DEAD "
         "OR MISSING.", draw_factory_fire),
    ]
    for i, (kicker, headline, body, icon_fn) in enumerate(cells):
        cx = gx + (i % 3) * (cw + gap)
        cy = gy + (i // 3) * (ch + gap)
        draw_cell(cv, cx, cy, cw, ch, kicker, headline, body, icon_fn)

    # bottom strip
    by = 958
    cv.hline(36, by, W - 72, INK, 3)
    cv.text_centered(W // 2, by + 12,
                     "ALL EVENTS FIRST REPORTED ON TUESDAY, 24 NOVEMBER 2026",
                     2, INK)
    cv.text_centered(W // 2, by + 30, "A ONE-PAGE SUMMARY  -  PAGE 1 OF 1",
                     2, GREY)
    return cv


# --------------------------------------------------------------------- PNG --
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = None
    if len(sys.argv) > 1:
        out = sys.argv[1]
    elif os.environ.get("OUTPUT_PATH"):
        out = os.environ["OUTPUT_PATH"]
    else:
        out = "/output/entry.png"
    cv = build_image()
    size = write_png(cv, out)
    print(f"Wrote {out}: {cv.w}x{cv.h}, {size} bytes")


if __name__ == "__main__":
    main()
