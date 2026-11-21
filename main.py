#!/usr/bin/env python3
"""Passport spread of the Republic of Meridia (MRD), a country that isn't there.

Draws a 1024x1024 open passport spread with PIL: a data page (portrait,
fields, ICAO 9303 machine-readable zone with computed check digits) and a
visa page (arrival/departure stamps with a consistent travel history, a
seaman's endorsement, and a small map of the Meridia archipelago).

Deterministic: no randomness, no timestamps, fixed seed-free geometry.
Output: <MAKEFUN_OUTPUT_DIR or /output>/entry.png (1024x1024 PNG).
"""

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (245, 239, 224)
INK = (28, 35, 51)
NAVY = (30, 58, 95)
GRAY_LABEL = (107, 107, 107)
TABLE_TOP = (143, 136, 122)
TABLE_BOTTOM = (122, 114, 100)

LIB = "/usr/share/fonts/truetype/liberation/"
DEJ = "/usr/share/fonts/truetype/dejavu/"


def load_font(names, size):
    """Load the first available TTF from the candidate list."""
    for path in names:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def serif_bold(size):
    return load_font([LIB + "LiberationSerif-Bold.ttf",
                      DEJ + "DejaVuSerif-Bold.ttf"], size)


def sans(size):
    return load_font([LIB + "LiberationSans-Regular.ttf",
                      DEJ + "DejaVuSans.ttf"], size)


def sans_bold(size):
    return load_font([LIB + "LiberationSans-Bold.ttf",
                      DEJ + "DejaVuSans-Bold.ttf"], size)


def mono(size):
    return load_font([LIB + "LiberationMono-Regular.ttf",
                      DEJ + "DejaVuSansMono.ttf"], size)


def serif_italic(size):
    return load_font([LIB + "LiberationSerif-Italic.ttf",
                      DEJ + "DejaVuSerif.ttf"], size)


# ---------------------------------------------------------------- MRZ (ICAO 9303)

def mrz_value(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - ord("A") + 10


def mrz_check(text):
    """ICAO 9303 check digit: weights 7, 3, 1 repeating, sum mod 10."""
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(text):
        total += mrz_value(ch) * weights[i % 3]
    return str(total % 10)


def build_mrz():
    """Two MRZ lines, 44 chars each, check digits computed in code."""
    surname = "HALVORSEN"
    given = "ELENA<MARIS"
    line1 = ("P<MRD" + surname + "<<" + given).ljust(44, "<")

    doc = "MRD847291"
    dob = "860414"        # 14 APR 1986
    expiry = "340311"     # 11 MAR 2034
    personal = "<" * 14
    c_doc = mrz_check(doc)
    c_dob = mrz_check(dob)
    c_exp = mrz_check(expiry)
    c_pers = mrz_check(personal)
    composite_src = doc + c_doc + dob + c_dob + expiry + c_exp + personal + c_pers
    c_comp = mrz_check(composite_src)
    line2 = doc + c_doc + "MRD" + dob + c_dob + "F" + expiry + c_exp + personal + c_pers + c_comp
    assert len(line1) == 44 and len(line2) == 44
    return line1, line2


# ---------------------------------------------------------------- helpers

def spaced_text(draw, cx, y, text, font, fill, spacing=3):
    """Draw letterspaced text centred on cx."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + spacing


def field(draw, x, y, label, value, value_font=None, value_fill=INK):
    """One passport field: small caps label above its value."""
    draw.text((x, y), label, font=sans_bold(10), fill=GRAY_LABEL)
    draw.text((x, y + 14), value, font=value_font or sans(15), fill=value_fill)


def star_points(cx, cy, r_out, r_in, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_star(draw, cx, cy, r_out, r_in, fill):
    draw.polygon(star_points(cx, cy, r_out, r_in), fill=fill)


def guilloche(draw, x0, y0, x1, y1, color=(216, 210, 192)):
    """Faint sine-wave security lines across a page."""
    y = y0 + 14
    while y < y1 - 8:
        pts = []
        x = x0 + 8
        while x <= x1 - 8:
            pts.append((x, y + 5 * math.sin((x - x0) / 26.0)))
            x += 6
        draw.line(pts, fill=color, width=1)
        y += 46


def emblem(draw, cx, y, w=64, h=76):
    """Meridia coat of arms: shield, lighthouse, waves, star."""
    # Shield outline.
    shield = [(cx - w // 2, y), (cx + w // 2, y),
              (cx + w // 2, y + h - 26), (cx, y + h),
              (cx - w // 2, y + h - 26)]
    draw.polygon(shield, fill=(253, 246, 227), outline=NAVY, width=3)
    # Light beams from the lamp.
    draw.polygon([(cx, y + 16), (cx - 26, y + 2), (cx - 24, y + 12)],
                 fill=(250, 225, 140))
    draw.polygon([(cx, y + 16), (cx + 26, y + 2), (cx + 24, y + 12)],
                 fill=(250, 225, 140))
    # Lighthouse tower.
    draw.rectangle([cx - 7, y + 20, cx + 7, y + 50], fill=(255, 255, 255),
                   outline=NAVY, width=2)
    draw.rectangle([cx - 7, y + 28, cx + 7, y + 34], fill=(198, 40, 40))
    draw.rectangle([cx - 7, y + 42, cx + 7, y + 48], fill=(198, 40, 40))
    draw.rectangle([cx - 5, y + 13, cx + 5, y + 20], fill=NAVY)
    draw.polygon([(cx - 7, y + 13), (cx + 7, y + 13), (cx, y + 6)],
                 fill=(198, 40, 40))
    # Waves.
    for wy in (y + 56, y + 63):
        draw.arc([cx - 22, wy - 5, cx + 22, wy + 5], start=200, end=340,
                 fill=NAVY, width=2)
    # Star above the shield.
    draw_star(draw, cx, y - 10, 7, 3, fill=(212, 160, 32))


def portrait(img, box):
    """Flat procedural portrait of the holder (not a real person's photo)."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # Draw on a full-size layer, then crop to the box: nothing may spill
    # past the photo frame onto the fields below it.
    layer = Image.new("RGB", img.size)
    # Blue-grey gradient background.
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int(185 + (219 - 185) * t) if k == 0 else
                  int(200 + (228 - 200) * t) if k == 1 else
                  int(212 + (234 - 212) * t) for k in range(3))
        layer.paste(c, (x0, y0 + i, x1, y0 + i + 1))
    d = ImageDraw.Draw(layer)
    skin = (232, 185, 141)
    skin_dark = (201, 143, 95)
    hair = (59, 42, 30)
    jacket = (31, 77, 74)
    # Shoulders / jacket.
    d.ellipse([x0 - 30, y0 + h - 62, x1 + 30, y0 + h + 60], fill=jacket)
    # Neck.
    d.rectangle([x0 + w // 2 - 13, y0 + 108, x0 + w // 2 + 13, y0 + 138],
                fill=skin_dark)
    # Shirt V.
    d.polygon([(x0 + w // 2 - 16, y0 + h - 52), (x0 + w // 2 + 16, y0 + h - 52),
               (x0 + w // 2, y0 + h - 22)], fill=(245, 245, 240))
    # Hair back (bob, to chin level).
    d.rounded_rectangle([x0 + 34, y0 + 14, x0 + 116, y0 + 112], radius=26,
                        fill=hair)
    # Ears.
    d.ellipse([x0 + 36, y0 + 62, x0 + 48, y0 + 86], fill=skin)
    d.ellipse([x0 + 102, y0 + 62, x0 + 114, y0 + 86], fill=skin)
    # Face.
    d.ellipse([x0 + 42, y0 + 28, x0 + 108, y0 + 108], fill=skin)
    # Fringe.
    d.ellipse([x0 + 42, y0 + 6, x0 + 108, y0 + 50], fill=hair)
    # Eyebrows.
    d.arc([x0 + 54, y0 + 56, x0 + 70, y0 + 66], start=200, end=340,
          fill=hair, width=2)
    d.arc([x0 + 80, y0 + 56, x0 + 96, y0 + 66], start=200, end=340,
          fill=hair, width=2)
    # Eyes.
    for ex in (62, 88):
        d.ellipse([x0 + ex - 4, y0 + 68, x0 + ex + 4, y0 + 74],
                  fill=(40, 26, 18))
        d.ellipse([x0 + ex + 1, y0 + 68, x0 + ex + 3, y0 + 70],
                  fill=(255, 255, 255))
    # Nose.
    d.line([x0 + 75, y0 + 78, x0 + 75, y0 + 88], fill=skin_dark, width=2)
    d.line([x0 + 72, y0 + 88, x0 + 78, y0 + 88], fill=skin_dark, width=2)
    # Mouth (neutral).
    d.arc([x0 + 65, y0 + 92, x0 + 85, y0 + 100], start=15, end=165,
          fill=(138, 74, 58), width=2)
    # Blush.
    d.ellipse([x0 + 48, y0 + 82, x0 + 58, y0 + 88], fill=(224, 150, 120))
    d.ellipse([x0 + 92, y0 + 82, x0 + 102, y0 + 88], fill=(224, 150, 120))
    # Frame.
    d.rectangle(box, outline=(60, 60, 60), width=2)
    # Crop to the photo box and paste: the shoulders stay inside the frame.
    img.paste(layer.crop(box), (x0, y0))


def rect_stamp(lines, color, angle, w=200, h=140):
    """Rectangular ink stamp on its own layer, rotated by a fixed angle."""
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = color + (215,)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=8,
                        outline=ink, width=3)
    d.rounded_rectangle([25, 25, 15 + w, 15 + h], radius=6,
                        outline=ink, width=1)
    cx = 20 + w // 2
    y = 30
    for text, size in lines:
        f = sans_bold(size)
        d.text((cx, y), text, font=f, fill=ink, anchor="ma")
        y += size + 6
    return layer.rotate(angle, expand=True, resample=Image.BICUBIC)


def circle_stamp(lines, color, angle, d0=150):
    """Circular ink stamp on its own layer, rotated by a fixed angle."""
    layer = Image.new("RGBA", (d0 + 40, d0 + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = color + (215,)
    d.ellipse([20, 20, 20 + d0, 20 + d0], outline=ink, width=3)
    d.ellipse([28, 28, 12 + d0, 12 + d0], outline=ink, width=1)
    cx = 20 + d0 // 2
    y = 20 + d0 // 2 - (len(lines) * 20) // 2
    for text, size in lines:
        f = sans_bold(size)
        d.text((cx, y), text, font=f, fill=ink, anchor="ma")
        y += size + 7
    return layer.rotate(angle, expand=True, resample=Image.BICUBIC)


def draw_map(draw, box):
    """Small map of the Meridia archipelago with Port Aurelia marked."""
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(214, 232, 240), outline=NAVY, width=2)
    draw.text((x0 + 10, y0 + 6), "MERIDIA — SOUTH ATLANTIC",
              font=sans_bold(11), fill=NAVY)
    # Islands (fixed blobs).
    islands = [
        [(x0 + 60, y0 + 90), (x0 + 110, y0 + 62), (x0 + 150, y0 + 78),
         (x0 + 140, y0 + 108), (x0 + 96, y0 + 118), (x0 + 62, y0 + 108)],
        [(x0 + 200, y0 + 52), (x0 + 240, y0 + 42), (x0 + 268, y0 + 58),
         (x0 + 252, y0 + 82), (x0 + 214, y0 + 80)],
        [(x0 + 300, y0 + 96), (x0 + 340, y0 + 88), (x0 + 356, y0 + 108),
         (x0 + 322, y0 + 122), (x0 + 296, y0 + 114)],
        [(x0 + 150, y0 + 140), (x0 + 190, y0 + 132), (x0 + 208, y0 + 148),
         (x0 + 178, y0 + 162), (x0 + 148, y0 + 156)],
    ]
    for isl in islands:
        draw.polygon(isl, fill=(168, 198, 134), outline=(90, 130, 80), width=2)
    # Port Aurelia star on the main island; label clear of the star.
    px, py = x0 + 104, y0 + 88
    draw_star(draw, px, py, 8, 3, fill=(198, 40, 40))
    draw.text((px + 16, py - 6), "PORT AURELIA", font=sans_bold(11),
              fill=(198, 40, 40))
    # Compass rose.
    ccx, ccy = x1 - 34, y0 + 36
    draw.ellipse([ccx - 14, ccy - 14, ccx + 14, ccy + 14], outline=NAVY, width=1)
    draw.polygon([(ccx, ccy - 12), (ccx - 4, ccy), (ccx, ccy + 12),
                  (ccx + 4, ccy)], fill=NAVY)
    draw.text((ccx, ccy - 26), "N", font=sans_bold(10), fill=NAVY, anchor="ma")
    draw.text((x0 + 10, y1 - 20), "Scale 1 : 2 400 000",
              font=sans(9), fill=GRAY_LABEL)


# ---------------------------------------------------------------- pages

def draw_data_page(img):
    x0, y0, x1, y1 = 20, 20, 512, 1004
    d = ImageDraw.Draw(img)
    guilloche(d, x0, y0, x1, y1)
    cx = (x0 + x1) // 2
    # Header.
    d.text((cx, 44), "REPUBLIC OF MERIDIA", font=serif_bold(25), fill=NAVY,
           anchor="ma")
    spaced_text(d, cx, 76, "PASSPORT · PASSEPORT", sans_bold(12), NAVY, 3)
    emblem(d, cx, 108)
    d.line([x0 + 26, 196, x1 - 26, 196], fill=NAVY, width=2)
    # Photo.
    portrait(img, (46, 212, 196, 402))
    # Fields right of the photo.
    field(d, 212, 212, "TYPE", "P")
    field(d, 268, 212, "CODE", "MRD")
    field(d, 340, 212, "PASSPORT No.", "MRD-847291")
    field(d, 212, 262, "SURNAME", "HALVORSEN", sans_bold(16))
    field(d, 212, 312, "GIVEN NAMES", "ELENA MARIS", sans_bold(16))
    field(d, 212, 362, "NATIONALITY", "MERIDIAN")
    field(d, 380, 362, "SEX", "F")
    # Fields below.
    field(d, 46, 424, "DATE OF BIRTH", "14 APR 1986")
    field(d, 212, 424, "PLACE OF BIRTH", "PORT AURELIA, MERIDIA")
    field(d, 46, 474, "DATE OF ISSUE", "12 MAR 2024")
    field(d, 212, 474, "DATE OF EXPIRY", "11 MAR 2034")
    field(d, 46, 524, "AUTHORITY",
          "MINISTRY OF THE INTERIOR — PORT AURELIA")
    # Occupation line: ties the portrait to the country's character.
    d.line([x0 + 26, 586, x1 - 26, 586], fill=(180, 172, 148), width=1)
    field(d, 46, 598, "OBSERVATIONS",
          "HOLDER IS A LIGHTHOUSE KEEPER — PORT AURELIA")
    # Signature.
    d.line([46, 700, 300, 700], fill=INK, width=1)
    d.text((46, 668), "E. M. Halvorsen", font=serif_italic(20), fill=INK)
    d.text((46, 706), "HOLDER'S SIGNATURE", font=sans_bold(9),
           fill=GRAY_LABEL)
    # Small note.
    d.text((cx, 830),
           "This passport remains the property of the Republic of Meridia.",
           font=serif_italic(11), fill=GRAY_LABEL, anchor="ma")
    # MRZ strip.
    d.rectangle([36, 872, 476, 952], fill=(255, 255, 255),
                outline=(150, 142, 122), width=1)
    line1, line2 = build_mrz()
    f_mrz = mono(16)
    d.text((46, 884), line1, font=f_mrz, fill=INK)
    d.text((46, 914), line2, font=f_mrz, fill=INK)


def draw_visa_page(img):
    x0, y0, x1, y1 = 512, 20, 1004, 1004
    d = ImageDraw.Draw(img)
    guilloche(d, x0, y0, x1, y1)
    # Faint diagonal watermark.
    wm = Image.new("RGBA", (420, 90), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wd.text((210, 45), "MERIDIA", font=serif_bold(56), fill=(30, 58, 95, 22),
            anchor="mm")
    wm = wm.rotate(-28, expand=True, resample=Image.BICUBIC)
    img.paste(wm, (x0 + 40, y0 + 380), wm)
    d = ImageDraw.Draw(img)
    # Header.
    d.text((538, 44), "VISAS", font=serif_bold(22), fill=NAVY)
    d.text((978, 50), "12", font=sans_bold(12), fill=GRAY_LABEL, anchor="ra")
    d.line([538, 78, 978, 78], fill=NAVY, width=2)

    green = (46, 125, 50)
    blue = (21, 101, 192)
    purple = (106, 27, 154)
    red = (198, 40, 40)

    stamps = [
        # (stamp image, paste position)
        (rect_stamp([("CALEBRA", 14), ("ARRIVAL", 13),
                     ("PORTO VERDE", 11), ("03 JUN 2024", 13)], green, -4),
         (538, 100)),
        (rect_stamp([("CALEBRA", 14), ("DEPARTURE", 13),
                     ("PORTO VERDE", 11), ("18 JUN 2024", 13)], green, 5),
         (778, 100)),
        (rect_stamp([("SKARLAND", 14), ("VISA — GRANTED", 12),
                     ("MULTIPLE ENTRY · 90 DAYS", 9),
                     ("22 AUG 2025", 13)], blue, 3),
         (538, 262)),
        (circle_stamp([("SKARLAND", 12), ("ENTRY", 14),
                       ("NORDHAVEN", 10), ("09 SEP 2025", 12)], blue, -6),
         (790, 258)),
        (circle_stamp([("SKARLAND", 12), ("EXIT", 14),
                       ("NORDHAVEN", 10), ("21 SEP 2025", 12)], blue, 4),
         (548, 424)),
        (rect_stamp([("VOSTRIA", 14), ("ENTRY", 13),
                     ("TARNOW", 11), ("02 FEB 2026", 13)], purple, -3),
         (778, 428)),
        (rect_stamp([("VOSTRIA", 14), ("EXIT", 13),
                     ("TARNOW", 11), ("14 FEB 2026", 13)], purple, 6),
         (538, 592)),
    ]
    for stamp, pos in stamps:
        img.paste(stamp, pos, stamp)

    # The telling detail: seaman's endorsement, red, rotated.
    endorse = rect_stamp([("SEAMAN'S ENDORSEMENT", 13),
                          ("WINDJAMMER FLEET", 13),
                          ("VALID 2024 — 2034", 12)], red, -11, w=230, h=110)
    img.paste(endorse, (716, 600), endorse)

    # Map at the bottom.
    draw_map(d, (538, 800, 978, 968))


def main():
    img = Image.new("RGB", (W, H), TABLE_TOP)
    d = ImageDraw.Draw(img)
    # Table: vertical gradient.
    for i in range(H):
        t = i / (H - 1)
        c = tuple(int(TABLE_TOP[k] + (TABLE_BOTTOM[k] - TABLE_TOP[k]) * t)
                  for k in range(3))
        d.line([(0, i), (W, i)], fill=c)
    # Soft shadow under the spread.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([28, 28, 1012, 1012], fill=(0, 0, 0, 90))
    from PIL import ImageFilter
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB"),
              (0, 0))
    # Pages.
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 512, 1004], fill=PAPER)
    d.rectangle([512, 20, 1004, 1004], fill=PAPER)
    draw_data_page(img)
    draw_visa_page(img)
    # Spine shadow + centre line.
    d = ImageDraw.Draw(img)
    for i in range(10):
        a = 26 - i * 2
        d.line([(512 - 10 + i, 20), (512 - 10 + i, 1004)],
               fill=(120, 110, 88))
        d.line([(512 + i, 20), (512 + i, 1004)], fill=(120, 110, 88))
    d.line([(512, 20), (512, 1004)], fill=(90, 82, 64), width=2)
    # Outer border.
    d.rectangle([20, 20, 1004, 1004], outline=(70, 62, 48), width=2)

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "entry.png"
        img.save(out_path, "PNG")
    except OSError:
        out_dir = Path("output")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "entry.png"
        img.save(out_path, "PNG")
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes, {img.size})")


if __name__ == "__main__":
    main()
