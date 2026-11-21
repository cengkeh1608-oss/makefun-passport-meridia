#!/usr/bin/env python3
"""Passport of the Republic of Meridia — invented passport spread.

Pure Python standard library only: no Pillow, no third-party package, no
font file read from disk. The picture is painted pixel by pixel into an
RGB buffer with hand-written primitives (rect, line, circle, polygon,
rounded rect, 5x7 bitmap text), then encoded to PNG by hand
(zlib + struct + CRC32).

The country is fictional: Republic of Meridia (MRD), a South Atlantic
archipelago whose capital is Port Aurelia. The holder is Elena Maris
Halvorsen, a lighthouse keeper — the portrait, the place name and the
seaman's endorsement all belong to the same seafaring character.
"""

import math
import os
import struct
import zlib
from pathlib import Path

W = H = 1024

# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------
DESK = (124, 116, 100)
SHADOW = (96, 89, 75)
PAPER = (245, 239, 224)
NAVY = (30, 52, 96)
GOLD = (201, 162, 39)
RED = (178, 44, 44)
INK_RED = (185, 30, 30)
TEAL = (36, 82, 82)
SKIN = (232, 198, 168)
HAIR = (62, 45, 32)
SEA = (207, 224, 234)
ISLAND = (140, 180, 120)
GUILLOCHE = (233, 227, 211)
WATERMARK = (229, 223, 208)
GREEN_INK = (34, 139, 34)
BLUE_INK = (30, 90, 180)
PURPLE_INK = (120, 40, 160)
GREY = (110, 105, 90)
BLACK = (20, 20, 20)
MAGENTA = (255, 0, 255)  # transparent sentinel inside stamp buffers

# --------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink.
# Covers A-Z, 0-9, space and < - / . : ( ) & ' ,
# --------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
}


def text_w(s, scale=1, spacing=0):
    """Pixel width of s at the given scale (no trailing spacing)."""
    if not s:
        return 0
    return len(s) * (5 * scale + spacing) - spacing


# --------------------------------------------------------------------------
# Canvas: an RGB bytearray with drawing primitives.
# --------------------------------------------------------------------------
class CV:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + (x1 - x0) * 3] = row

    def rect(self, x0, y0, x1, y1, c, t=1):
        self.fill_rect(x0, y0, x1, y0 + t, c)
        self.fill_rect(x0, y1 - t, x1, y1, c)
        self.fill_rect(x0, y0, x0 + t, y1, c)
        self.fill_rect(x1 - t, y0, x1, y1, c)

    def hline(self, x0, x1, y, c, t=1):
        self.fill_rect(x0, y, x1, y + t, c)

    def vline(self, x, y0, y1, c, t=1):
        self.fill_rect(x, y0, x + t, y1, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, pts, c):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c)

    def poly(self, pts, c):
        """Fill a polygon with a scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[j])), y, int(xs[j + 1]) + 1, y + 1, c)

    def circle(self, cx, cy, r, c, fill=False):
        if r <= 0:
            return
        if fill:
            for y in range(cy - r, cy + r + 1):
                half = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
                self.fill_rect(cx - half, y, cx + half + 1, y + 1, c)
        else:
            n = max(24, int(2 * math.pi * r))
            for i in range(n):
                a = 2 * math.pi * i / n
                self.set(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), c)

    def ellipse(self, cx, cy, rx, ry, c, fill=False):
        if rx <= 0 or ry <= 0:
            return
        if fill:
            for y in range(cy - ry, cy + ry + 1):
                t = 1 - ((y - cy) / ry) ** 2
                half = int(rx * math.sqrt(max(0.0, t)))
                self.fill_rect(cx - half, y, cx + half + 1, y + 1, c)
        else:
            n = max(32, int(2 * math.pi * max(rx, ry)))
            for i in range(n):
                a = 2 * math.pi * i / n
                self.set(cx + int(rx * math.cos(a)), cy + int(ry * math.sin(a)), c)

    def star(self, cx, cy, r, c):
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + int(rr * math.cos(ang)), cy + int(rr * math.sin(ang))))
        self.poly(pts, c)

    def rrect(self, x0, y0, x1, y1, r, c, t=1, fill=False):
        if fill:
            self.fill_rect(x0 + r, y0, x1 - r, y1, c)
            self.fill_rect(x0, y0 + r, x1, y1 - r, c)
            for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                           (x0 + r, y1 - r), (x1 - r, y1 - r)):
                self.circle(cx, cy, r, c, fill=True)
            return
        self.hline(x0 + r, x1 - r, y0, c, t)
        self.hline(x0 + r, x1 - r, y1 - t, c, t)
        self.vline(x0, y0 + r, y1 - r, c, t)
        self.vline(x1 - t, y0 + r, y1 - r, c, t)
        for cx, cy, a0 in ((x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270),
                           (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90)):
            for k in range(t):
                rr = r - k
                for i in range(25):
                    a = math.radians(a0 + 90 * i / 24)
                    self.set(cx + int(rr * math.cos(a)), cy + int(rr * math.sin(a)), c)

    def text(self, x, y, s, c, scale=1, bold=False, slant=0, spacing=0, dy=0):
        """Draw s with the embedded 5x7 font. Returns the x after the last glyph.

        slant shifts each glyph row rightwards towards the top (italic look);
        dy moves each following character down by dy pixels (diagonal text).
        """
        cx = x
        cy = y
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                xoff = (6 - r) * slant
                for col in range(5):
                    if row[col] == "#":
                        bx = cx + xoff + col * scale
                        by = cy + r * scale
                        self.fill_rect(bx, by, bx + scale, by + scale, c)
                        if bold:
                            self.fill_rect(bx + 1, by, bx + scale + 1, by + scale, c)
            cx += 5 * scale + spacing
            cy += dy
        return cx

    def blit_rot(self, src, cx, cy, angle_deg):
        """Blit a stamp buffer centred at (cx, cy), rotated by angle_deg.

        Magenta pixels of the source are transparent.
        """
        a = math.radians(angle_deg)
        ca, sa = math.cos(a), math.sin(a)
        scx, scy = src.w // 2, src.h // 2
        for sy in range(src.h):
            base = sy * src.w * 3
            for sx in range(src.w):
                i = base + sx * 3
                if src.buf[i] == 255 and src.buf[i + 1] == 0 and src.buf[i + 2] == 255:
                    continue
                dx, dy = sx - scx, sy - scy
                rx = dx * ca - dy * sa
                ry = dx * sa + dy * ca
                self.set(cx + int(round(rx)), cy + int(round(ry)),
                         (src.buf[i], src.buf[i + 1], src.buf[i + 2]))


# --------------------------------------------------------------------------
# MRZ (ICAO 9303): weights 7,3,1; A=10..Z=35, '<'=0.
# --------------------------------------------------------------------------
def mrz_check(s):
    total = 0
    for i, ch in enumerate(s):
        if ch == "<":
            v = 0
        elif ch.isdigit():
            v = int(ch)
        else:
            v = ord(ch) - 55
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<MRD" + "HALVORSEN" + "<<" + "ELENA<MARIS"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "MRD847291"
    nat = "MRD"
    dob = "860414"
    sex = "F"
    exp = "340311"
    pers = "<" * 14
    body = (doc + mrz_check(doc) + nat + dob + mrz_check(dob) + sex
            + exp + mrz_check(exp) + pers + mrz_check(pers))
    line2 = body + mrz_check(body)
    return line1, line2


# --------------------------------------------------------------------------
# Portrait: flat passport illustration (not a real person's photo).
# --------------------------------------------------------------------------
def draw_portrait(cv, x0, y0, x1, y1):
    # Blue-grey gradient background.
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        c = (int(176 + (150 - 176) * t),
             int(194 + (170 - 194) * t),
             int(212 + (192 - 212) * t))
        cv.hline(x0, x1, y, c)
    cx = (x0 + x1) // 2
    # Hair mass behind the face.
    cv.ellipse(cx, 292, 56, 66, HAIR, fill=True)
    # Ears.
    cv.circle(cx - 38, 306, 6, SKIN, fill=True)
    cv.circle(cx + 38, 306, 6, SKIN, fill=True)
    # Neck, then shoulders, then shirt.
    cv.fill_rect(cx - 8, 338, cx + 8, 362, SKIN)
    cv.poly([(x0 + 3, y1), (cx - 20, 352), (cx + 20, 352), (x1 - 3, y1)], TEAL)
    cv.poly([(cx - 10, 352), (cx + 10, 352), (cx, 382)], (245, 245, 240))
    # Face.
    cv.ellipse(cx, 302, 40, 50, SKIN, fill=True)
    # Fringe: top half of an ellipse over the forehead, covering the
    # top of the face so no skin crescent shows above the hairline.
    pts = []
    for i in range(25):
        a = math.pi + math.pi * i / 24
        pts.append((cx + int(44 * math.cos(a)), 276 + int(28 * math.sin(a))))
    pts.append((cx + 44, 276))
    pts.append((cx - 44, 276))
    cv.poly(pts, HAIR)
    # Side strands framing the face.
    cv.fill_rect(cx - 44, 300, cx - 28, 360, HAIR)
    cv.fill_rect(cx + 28, 300, cx + 44, 360, HAIR)
    # Brows, eyes, nose, mouth, blush.
    cv.line(cx - 24, 304, cx - 10, 302, HAIR)
    cv.line(cx + 10, 302, cx + 24, 304, HAIR)
    cv.circle(cx - 17, 314, 3, (35, 28, 22), fill=True)
    cv.circle(cx + 17, 314, 3, (35, 28, 22), fill=True)
    cv.line(cx, 318, cx, 328, (200, 160, 130))
    cv.fill_rect(cx - 8, 340, cx + 8, 341, (150, 70, 60))
    cv.circle(cx - 22, 326, 4, (238, 178, 160), fill=True)
    cv.circle(cx + 22, 326, 4, (238, 178, 160), fill=True)


# --------------------------------------------------------------------------
# Shield emblem: lighthouse over waves, gold star above.
# --------------------------------------------------------------------------
def draw_shield(cv, cx, y):
    cv.star(cx, y - 14, 11, GOLD)
    pts = [(cx - 36, y), (cx + 36, y), (cx + 36, y + 30),
           (cx, y + 60), (cx - 36, y + 30)]
    cv.poly(pts, (250, 246, 236))
    cv.polyline(pts + [pts[0]], NAVY)
    cv.polyline([(cx - 36, y + 1), (cx + 36, y + 1), (cx + 36, y + 29),
                 (cx, y + 59), (cx - 36, y + 29), (cx - 36, y + 1)], NAVY)
    # Lighthouse: striped tower, lamp room, light beams.
    cv.poly([(cx - 22, y + 14), (cx - 2, y + 4), (cx + 2, y + 4),
             (cx + 22, y + 14)], (240, 210, 90))
    cv.fill_rect(cx - 7, y + 16, cx + 7, y + 46, (250, 250, 248))
    cv.fill_rect(cx - 7, y + 16, cx + 7, y + 24, RED)
    cv.fill_rect(cx - 7, y + 32, cx + 7, y + 40, RED)
    cv.fill_rect(cx - 8, y + 12, cx + 8, y + 16, (40, 40, 40))
    cv.fill_rect(cx - 4, y + 8, cx + 4, y + 12, GOLD)
    # Waves under the tower.
    for wy in (y + 50, y + 55):
        pts = []
        for x in range(cx - 30, cx + 31, 4):
            pts.append((x, wy + int(2 * math.sin(x / 9.0))))
        cv.polyline(pts, (60, 110, 160))


# --------------------------------------------------------------------------
# Stamps: drawn into small buffers, then rotated onto the spread.
# --------------------------------------------------------------------------
def stamp_rect(w, h, ink, lines, angle, cx, cy, dst):
    s = CV(w, h, MAGENTA)
    s.rrect(6, 6, w - 6, h - 6, 14, ink, t=3)
    s.rrect(12, 12, w - 12, h - 12, 10, ink, t=1)
    y = 24
    for txt, sc, bold in lines:
        tw = text_w(txt, sc)
        s.text((w - tw) // 2, y, txt, ink, scale=sc, bold=bold)
        y += 7 * sc + 6
    dst.blit_rot(s, cx, cy, angle)


def stamp_circle(r, ink, lines, cx, cy, dst):
    d = 2 * r + 16
    s = CV(d, d, MAGENTA)
    cc = d // 2
    s.circle(cc, cc, r, ink)
    s.circle(cc, cc, r - 5, ink)
    total_h = sum(7 * sc + 6 for _, sc, _ in lines) - 6
    y = cc - total_h // 2
    for txt, sc, bold in lines:
        tw = text_w(txt, sc)
        s.text((d - tw) // 2, y, txt, ink, scale=sc, bold=bold)
        y += 7 * sc + 6
    dst.blit_rot(s, cx, cy, 0)


# --------------------------------------------------------------------------
# The spread.
# --------------------------------------------------------------------------
def guilloche(cv, x0, x1):
    for y in range(30, 1000, 26):
        prev = None
        for x in range(x0, x1, 3):
            p = (x, y + int(3 * math.sin(x / 45.0)))
            if prev is not None:
                cv.line(prev[0], prev[1], p[0], p[1], GUILLOCHE)
            prev = p


def field(cv, x, y, label, value, scale=2, bold=True):
    cv.text(x, y, label, GREY, scale=1, bold=False)
    cv.text(x, y + 12, value, BLACK, scale=scale, bold=bold)


def draw_spread(cv):
    # Desk, drop shadows, pages, spine.
    cv.fill_rect(0, 0, W, H, DESK)
    cv.fill_rect(26, 18, 511, 1018, SHADOW)
    cv.fill_rect(525, 18, 1010, 1018, SHADOW)
    cv.fill_rect(20, 12, 505, 1012, PAPER)
    cv.fill_rect(519, 12, 1004, 1012, PAPER)
    cv.fill_rect(505, 12, 519, 1012, (105, 96, 82))
    cv.fill_rect(510, 12, 514, 1012, (88, 80, 68))
    guilloche(cv, 24, 501)
    guilloche(cv, 523, 1000)

    # ---- Left page: data page ----
    title = "REPUBLIC OF MERIDIA"
    tw = text_w(title, 4, spacing=1)
    cv.text(262 - tw // 2, 42, title, NAVY, scale=4, bold=True, spacing=1)
    sub = "PASSPORT - PASSEPORT"
    tw = text_w(sub, 2, spacing=2)
    cv.text(262 - tw // 2, 80, sub, NAVY, scale=2, bold=False, spacing=2)
    draw_shield(cv, 262, 128)
    cv.hline(45, 480, 196, NAVY, t=2)

    # Portrait, framed.
    cv.rect(45, 210, 195, 400, NAVY, t=2)
    draw_portrait(cv, 47, 212, 193, 398)

    # Fields beside the portrait.
    field(cv, 215, 214, "TYPE", "P")
    field(cv, 292, 214, "CODE", "MRD")
    field(cv, 368, 214, "PASSPORT No.", "MRD-847291")
    field(cv, 215, 258, "SURNAME", "HALVORSEN")
    field(cv, 215, 302, "GIVEN NAMES", "ELENA MARIS")
    field(cv, 215, 346, "NATIONALITY", "MERIDIAN")
    field(cv, 380, 346, "SEX", "F")

    # Lower fields, two columns.
    field(cv, 45, 420, "DATE OF BIRTH", "14 APR 1986")
    field(cv, 270, 420, "PLACE OF BIRTH", "PORT AURELIA, MERIDIA")
    field(cv, 45, 470, "DATE OF ISSUE", "12 MAR 2024")
    field(cv, 270, 470, "DATE OF EXPIRY", "11 MAR 2034")
    field(cv, 45, 520, "AUTHORITY", "MINISTRY OF THE INTERIOR - PORT AURELIA")
    cv.hline(45, 480, 560, NAVY, t=1)
    field(cv, 45, 576, "OBSERVATIONS",
          "HOLDER IS A LIGHTHOUSE KEEPER - PORT AURELIA")

    # Signature, slanted like handwriting.
    cv.text(55, 640, "E. M. HALVORSEN", (40, 40, 40), scale=2, bold=False, slant=1)
    cv.hline(50, 300, 668, BLACK, t=1)
    cv.text(55, 676, "HOLDER'S SIGNATURE", GREY, scale=1, bold=False)

    foot = "THIS PASSPORT REMAINS THE PROPERTY OF THE REPUBLIC OF MERIDIA."
    tw = text_w(foot, 1)
    cv.text(262 - tw // 2, 800, foot, GREY, scale=1, bold=False)

    # Machine-readable zone.
    cv.fill_rect(35, 825, 495, 910, (255, 253, 246))
    cv.rect(35, 825, 495, 910, NAVY, t=1)
    line1, line2 = mrz_lines()
    cv.text(40, 840, line1, BLACK, scale=2, bold=False)
    cv.text(40, 868, line2, BLACK, scale=2, bold=False)

    # ---- Right page: visas ----
    cv.text(545, 42, "VISAS", NAVY, scale=3, bold=True)
    cv.text(965, 46, "12", NAVY, scale=2, bold=False)
    cv.hline(545, 980, 76, NAVY, t=2)

    # Faint diagonal watermark.
    cv.text(585, 640, "MERIDIA", WATERMARK, scale=7, bold=True, dy=-7)

    stamp_rect(230, 140, GREEN_INK, [
        ("CALEBRA", 3, True), ("ARRIVAL", 2, True),
        ("PORTO VERDE", 2, False), ("03 JUN 2024", 2, True),
    ], -4, 665, 180, cv)
    stamp_rect(230, 140, GREEN_INK, [
        ("CALEBRA", 3, True), ("DEPARTURE", 2, True),
        ("PORTO VERDE", 2, False), ("18 JUN 2024", 2, True),
    ], 3, 880, 180, cv)
    stamp_rect(240, 135, BLUE_INK, [
        ("SKARLAND", 3, True), ("VISA - GRANTED", 2, True),
        ("MULTIPLE ENTRY - 90 DAYS", 1, False), ("22 AUG 2025", 2, True),
    ], -2, 660, 375, cv)
    stamp_circle(78, BLUE_INK, [
        ("SKARLAND", 2, True), ("ENTRY", 2, True),
        ("NORDHAVEN", 2, False), ("09 SEP 2025", 2, True),
    ], 875, 375, cv)
    stamp_circle(78, BLUE_INK, [
        ("SKARLAND", 2, True), ("EXIT", 2, True),
        ("NORDHAVEN", 2, False), ("21 SEP 2025", 2, True),
    ], 660, 555, cv)
    stamp_rect(220, 135, PURPLE_INK, [
        ("VOSTRIA", 3, True), ("ENTRY", 2, True),
        ("TARNOW", 2, False), ("02 FEB 2026", 2, True),
    ], 4, 880, 555, cv)
    stamp_rect(220, 135, PURPLE_INK, [
        ("VOSTRIA", 3, True), ("EXIT", 2, True),
        ("TARNOW", 2, False), ("14 FEB 2026", 2, True),
    ], -3, 650, 715, cv)
    stamp_rect(250, 125, INK_RED, [
        ("SEAMAN'S ENDORSEMENT", 2, True), ("WINDJAMMER FLEET", 2, True),
        ("VALID 2024 - 2034", 2, False),
    ], -6, 865, 715, cv)

    # Map of the Meridian archipelago.
    cv.fill_rect(545, 800, 980, 985, SEA)
    cv.rect(545, 800, 980, 985, NAVY, t=2)
    cv.text(555, 812, "MERIDIA - SOUTH ATLANTIC", NAVY, scale=1, bold=True)
    cv.poly([(565, 885), (605, 862), (650, 872), (658, 902),
             (628, 928), (580, 922)], ISLAND)
    cv.poly([(700, 852), (742, 842), (772, 856), (752, 880),
             (710, 876)], ISLAND)
    cv.poly([(820, 888), (862, 878), (892, 894), (872, 920),
             (830, 916)], ISLAND)
    cv.poly([(652, 950), (692, 940), (722, 956), (690, 976),
             (656, 966)], ISLAND)
    cv.star(622, 902, 8, INK_RED)
    cv.text(638, 898, "PORT AURELIA", INK_RED, scale=1, bold=True)
    cv.circle(948, 832, 15, NAVY)
    cv.text(944, 808, "N", NAVY, scale=1, bold=True)
    cv.poly([(948, 822), (943, 840), (953, 840)], NAVY)
    cv.text(555, 968, "SCALE 1 : 2 400 000", NAVY, scale=1, bold=False)


# --------------------------------------------------------------------------
# PNG encoder: filter 0 scanlines, zlib, IHDR/IDAT/IEND with CRC32.
# --------------------------------------------------------------------------
def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))


def main():
    cv = CV(W, H, DESK)
    draw_spread(cv)
    data = png_bytes(cv)
    outdir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    try:
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / "entry.png"
        path.write_bytes(data)
    except OSError:
        outdir = Path("output")
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / "entry.png"
        path.write_bytes(data)
    print("wrote %s %d bytes" % (path, len(data)))


if __name__ == "__main__":
    main()
