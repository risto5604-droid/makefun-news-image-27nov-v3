#!/usr/bin/env python3
"""Friday 27 November 2026 world news, summed up in one 1024x1024 image.

Pure Python standard library only: the picture is painted onto a byte
buffer, the text is drawn with a small bitmap font defined below, and the
PNG bytes are encoded by hand (zlib + struct). No third-party module is
imported, no network is used, and the same bytes come out every run.

Run:  python3 main.py
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""

import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- font
# A 5-wide by 7-tall bitmap font, drawn from scratch for this program.
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is empty. Only the
# characters the front page needs are defined; everything is uppercase.
GLYPHS = {
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
}

GLYPHS.update({
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
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
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
})

GLYPHS.update({
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
})

# Every glyph row must be exactly 5 cells; fail loudly if one is not.
for _ch, _rows in GLYPHS.items():
    assert len(_rows) == 7, _ch
    for _row in _rows:
        assert len(_row) == 5, (_ch, _row)


def text_width(text, scale):
    """Pixel width of text at the given scale (6 units per cell)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# ---------------------------------------------------------------- canvas
# The picture lives in one flat bytearray: 3 bytes (RGB) per pixel.
class Canvas:
    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.buf = bytearray(colour * (width * height))

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = colour * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.width + x0) * 3
            self.buf[off:off + len(row)] = row

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            off = (y * self.width + x) * 3
            self.buf[off:off + 3] = colour

    def fill_circle(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - half, cy + dy, half * 2 + 1, 1, colour)

    def ring(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.set_pixel(cx - half, cy + dy, colour)
            self.set_pixel(cx + half, cy + dy, colour)
        for dx in range(-r, r + 1):
            half = int((r * r - dx * dx) ** 0.5)
            self.set_pixel(cx + dx, cy - half, colour)
            self.set_pixel(cx + dx, cy + half, colour)

    def line(self, x0, y0, x1, y1, colour):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_pixel(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_poly(self, points, colour):
        """Scanline fill of a simple polygon given as [(x, y), ...]."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.height, max(ys) + 1)):
            xs = []
            n = len(points)
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                x0 = max(0, int(xs[i]))
                x1 = min(self.width, int(xs[i + 1]) + 1)
                if x1 > x0:
                    self.fill_rect(x0, y, x1 - x0, 1, colour)

    def draw_text(self, x, y, text, scale, colour):
        """Draw text with the bitmap font; returns the x after the text."""
        cx = x
        for ch in text:
            # The font holds capitals only; fold case at draw time so
            # mixed-case story text still renders in full.
            glyph = GLYPHS.get(ch.upper())
            if glyph is None:
                cx += 6 * scale
                continue
            for row_i, row in enumerate(glyph):
                for col_i, cell in enumerate(row):
                    if cell == "#":
                        self.fill_rect(
                            cx + col_i * scale, y + row_i * scale,
                            scale, scale, colour)
            cx += 6 * scale
        return cx

    def draw_text_centred(self, cx, y, text, scale, colour):
        self.draw_text(cx - text_width(text, scale) // 2, y, text, scale, colour)


# ---------------------------------------------------------------- png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    raw = bytearray()
    row_bytes = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)  # filter: none
        start = y * row_bytes
        raw += canvas.buf[start:start + row_bytes]
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))

# ---------------------------------------------------------------- palette
PAPER = bytes((246, 241, 231))
INK = bytes((20, 33, 61))
NAVY = bytes((20, 33, 61))
CARD = bytes((255, 255, 255))
RED = bytes((178, 34, 34))
TEAL = bytes((14, 124, 123))
GOLD = bytes((201, 150, 54))
SKY = bytes((220, 233, 242))
LAND = bytes((139, 168, 136))
LAND_DARK = bytes((110, 140, 110))
MUTED = bytes((90, 100, 115))
RULE = bytes((200, 192, 175))
OCEAN_LINE = bytes((170, 195, 215))

REGION_COLOURS = {
    "EU": bytes((178, 34, 34)),
    "ME": bytes((201, 120, 20)),
    "NA": bytes((14, 90, 160)),
    "SA": bytes((14, 124, 123)),
    "EA": bytes((120, 60, 140)),
    "AF": bytes((90, 130, 30)),
    "CU": bytes((190, 60, 110)),
    "OC": bytes((30, 120, 140)),
}

# ---------------------------------------------------------------- the news
# Six hero stories, each: (number, region tag, headline, one-line deck,
# pictogram kind). Headlines and decks are shortened from the verified
# digest so they fit their cards; facts and dates are unchanged.
HEROES = [
    (1, "MIDDLE EAST",
     "IRAN DRONE ATTACK KILLS TWO ITALIANS IN KUWAIT",
     "Italy and Kuwait blame Iran; Tehran denies it.",
     "drone"),
    (2, "EUROPE",
     "RUSSIA HITS TWO GRAIN SHIPS OFF ODESA",
     "100,000+ tonnes of grain aboard.",
     "ship"),
    (3, "N. AMERICA",
     "BLACK FRIDAY: CAUTIOUS SHOPPERS BRACE FOR INFLATION",
     "US holiday sales seen topping $1 trillion.",
     "bag"),
    (4, "S. ASIA",
     "KARACHI BUILDING COLLAPSE KILLS 4, 17 MISSING",
     "Built to 7 floors, approved for 3.",
     "building"),
    (5, "EUROPE",
     "SERBIA SETS PRESIDENTIAL VOTE FOR 27 DECEMBER",
     "Vucic resigned in Sep; Student List won 25 Oct.",
     "ballot"),
    (6, "E. ASIA",
     "HONG KONG MARKS A YEAR SINCE FIRE THAT KILLED 168",
     "Wang Fuk Court anniversary in Tai Po.",
     "flame"),
]

# Thirty more dated stories, each: (region code, headline). One line each.
MORE = [
    ("EU", "UK train stabber guilty, 14 counts"),
    ("EU", "Czech urges NATO to down missiles"),
    ("EU", "Lithuania holds 5 in Russian TV case"),
    ("EU", "EU leaders urged to agree bloc budget"),
    ("EU", "Netanyahu: his trial has collapsed"),
    ("EU", "Putin pushes broad AI rollout"),
    ("EU", "Deputy air chief held for graft"),
    ("EU", "Heathrow growth fails climate tests"),
    ("ME", "Houthi hit on Jizan refinery kills 1"),
    ("ME", "Brent tops $94 on Iran mine claims"),
    ("ME", "Iran: two tankers hit mines near Oman"),
    ("ME", "Iraq jails 8 French IS men for life"),
    ("ME", "UN backs Palestinian recovery plan"),
    ("ME", "Israeli drone kills 3 in Gaza City"),
    ("NA", "Trump: Putin must end aggression"),
    ("NA", "US hails Syria Captagon seizures"),
    ("NA", "US markets shut for Thanksgiving"),
    ("SA", "Brazil inflation eases to 4.64%"),
    ("SA", "Brazil condemns Trump tariff plans"),
    ("SA", "Bangladesh police gas wage protesters"),
    ("SA", "India rupee bulls return after 18 mo."),
    ("SA", "Myanmar rejects parts of ICJ ruling"),
    ("EA", "Bank of Korea hikes rate to 3.25%"),
    ("EA", "Thai refinery blast injures 7"),
    ("EA", "China launches Earth-watch satellites"),
    ("EA", "AI fakes target Taiwan polls"),
    ("AF", "Sudan rejects Ethiopia peace plan"),
    ("AF", "Kenya halts US-backed Ebola facility"),
    ("CU", "Duran Duran's Andy Taylor dies at 65"),
    ("OC", "Sandpapergate forum won't lay blame"),
]

# Rough continent outlines as (longitude, latitude) points, drawn
# stylised: recognisable shapes, not survey data.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21),
     (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 49),
     (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-60, 8), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -45), (-70, -55), (-73, -40), (-70, -20),
     (-80, -5), (-80, 5)],
    [(-10, 36), (-9, 43), (0, 44), (-2, 49), (5, 53), (8, 57), (18, 56),
     (21, 55), (28, 60), (30, 70), (40, 68), (45, 60), (40, 50),
     (30, 45), (28, 40), (23, 36), (19, 42), (12, 44), (3, 43), (-2, 37)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31),
     (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -20),
     (30, -30), (20, -35), (15, -27), (12, -18), (9, -1), (9, 4),
     (-8, 5), (-13, 8)],
    [(40, 68), (60, 70), (80, 73), (110, 76), (140, 72), (170, 66),
     (178, 65), (162, 60), (158, 52), (142, 45), (140, 40), (130, 35),
     (127, 40), (122, 38), (120, 30), (110, 20), (105, 10), (100, 8),
     (95, 15), (90, 22), (80, 13), (77, 8), (72, 20), (66, 25),
     (60, 25), (52, 28), (48, 30), (44, 29), (40, 36), (36, 36),
     (30, 36), (27, 40), (30, 45), (35, 50), (40, 55)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32),
     (137, -35), (140, -38), (147, -39), (150, -37), (153, -27),
     (150, -22), (146, -19), (142, -15), (142, -11), (136, -12),
     (132, -12), (126, -14), (122, -17), (118, -20)],
]

# Where the six hero stories happened: (hero number, longitude, latitude).
PINS = [
    (1, 47, 29),
    (2, 30, 46),
    (3, -100, 39),
    (4, 67, 25),
    (5, 21, 44),
    (6, 114, 22),
]

# ---------------------------------------------------------------- pictograms
# Small geometric icons, one per hero story, drawn from primitives.
def draw_pictogram(cv, kind, bx, by, colour):
    if kind == "drone":
        cv.fill_rect(bx + 14, by + 18, 16, 8, colour)
        cv.line(bx + 14, by + 18, bx + 6, by + 10, colour)
        cv.line(bx + 30, by + 18, bx + 38, by + 10, colour)
        cv.line(bx + 14, by + 26, bx + 6, by + 34, colour)
        cv.line(bx + 30, by + 26, bx + 38, by + 34, colour)
        for px, py in ((6, 10), (38, 10), (6, 34), (38, 34)):
            cv.fill_rect(bx + px - 5, by + py - 2, 10, 4, colour)
        cv.fill_circle(bx + 22, by + 22, 3, CARD)
    elif kind == "ship":
        cv.fill_rect(bx + 10, by + 12, 8, 8, colour)
        cv.fill_rect(bx + 20, by + 12, 8, 8, colour)
        cv.fill_rect(bx + 30, by + 12, 8, 8, colour)
        cv.fill_poly([(bx + 4, by + 24), (bx + 40, by + 24),
                      (bx + 34, by + 38), (bx + 10, by + 38)], colour)
        cv.line(bx + 22, by + 12, bx + 22, by + 2, colour)
        cv.fill_rect(bx + 22, by + 2, 8, 5, RED)
    elif kind == "bag":
        cv.fill_rect(bx + 10, by + 16, 24, 24, colour)
        cv.line(bx + 16, by + 16, bx + 16, by + 8, colour)
        cv.line(bx + 28, by + 16, bx + 28, by + 8, colour)
        cv.line(bx + 16, by + 8, bx + 28, by + 8, colour)
        cv.fill_rect(bx + 18, by + 26, 8, 3, CARD)
    elif kind == "building":
        cv.fill_rect(bx + 12, by + 4, 20, 36, colour)
        for wy in (10, 18, 26):
            for wx in (16, 24):
                cv.fill_rect(bx + wx, by + wy, 4, 4, CARD)
        cv.line(bx + 22, by + 4, bx + 18, by + 16, CARD)
        cv.line(bx + 18, by + 16, bx + 24, by + 26, CARD)
        cv.line(bx + 24, by + 26, bx + 20, by + 40, CARD)
    elif kind == "ballot":
        cv.fill_rect(bx + 8, by + 22, 28, 18, colour)
        cv.fill_rect(bx + 16, by + 26, 12, 3, CARD)
        cv.fill_rect(bx + 14, by + 4, 16, 16, colour)
        cv.line(bx + 17, by + 12, bx + 20, by + 15, CARD)
        cv.line(bx + 20, by + 15, bx + 27, by + 7, CARD)
    elif kind == "flame":
        cv.fill_poly([(bx + 22, by + 2), (bx + 34, by + 22),
                      (bx + 30, by + 38), (bx + 14, by + 38),
                      (bx + 10, by + 22)], colour)
        cv.fill_circle(bx + 22, by + 30, 6, GOLD)


# ---------------------------------------------------------------- layout
REGION_CODE = {
    "MIDDLE EAST": "ME", "EUROPE": "EU", "N. AMERICA": "NA",
    "S. ASIA": "SA", "E. ASIA": "EA",
}


def build_image():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    # Banner.
    cv.fill_rect(0, 0, WIDTH, 76, NAVY)
    cv.draw_text(24, 20, "THE WORLD IN ONE DAY", 4, CARD)
    date = "FRIDAY 27 NOVEMBER 2026"
    cv.draw_text(WIDTH - 24 - text_width(date, 2), 30, date, 2, GOLD)
    cv.fill_rect(0, 76, WIDTH, 4, GOLD)

    # Strapline.
    strap = "36 DATED STORIES - 6 HEROES - WORLD MAP - ALL FROM 26-27 NOV 2026"
    cv.draw_text_centred(WIDTH // 2, 90, strap, 2, INK)

    # Six hero cards, two rows of three.
    for i, (num, region, headline, deck, kind) in enumerate(HEROES):
        col = i % 3
        row = i // 3
        x = 16 + col * 328
        y = 112 + row * 184
        accent = REGION_COLOURS[REGION_CODE[region]]
        cv.fill_rect(x, y, 320, 176, CARD)
        cv.fill_rect(x, y, 320, 6, accent)
        cv.fill_circle(x + 20, y + 28, 12, accent)
        cv.draw_text_centred(x + 20, y + 25, str(num), 1, CARD)
        cv.draw_text(x + 40, y + 22, region, 2, accent)
        draw_pictogram(cv, kind, x + 320 - 14 - 44, y + 10, accent)
        lines = wrap_text(headline, 2, 292)
        assert len(lines) <= 3, (headline, lines)
        ly = y + 52
        for line in lines:
            cv.draw_text(x + 14, ly, line, 2, INK)
            ly += 16
        deck_lines = wrap_text(deck, 2, 292)
        assert len(deck_lines) <= 2, (deck, deck_lines)
        ly = y + 108
        for line in deck_lines:
            cv.draw_text(x + 14, ly, line, 2, MUTED)
            ly += 16
        cv.fill_rect(x, y + 168, 320, 2, RULE)

    # Pinned world map.
    cv.fill_rect(16, 484, 992, 140, SKY)
    cv.fill_rect(16, 484, 992, 2, RULE)
    cv.fill_rect(16, 622, 992, 2, RULE)

    def project(lon, lat):
        px = 24 + (lon + 180) * 976 / 360
        py = 498 + (85 - lat) * 104 / 140
        return (int(px), int(py))

    for shape in CONTINENTS:
        cv.fill_poly([project(lon, lat) for lon, lat in shape], LAND)
    for shape in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in shape]
        for i in range(len(pts)):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % len(pts)]
            cv.line(ax, ay, bx, by, LAND_DARK)
    for num, lon, lat in PINS:
        px, py = project(lon, lat)
        cv.fill_circle(px, py, 9, RED)
        cv.ring(px, py, 9, CARD)
        cv.draw_text_centred(px, py - 3, str(num), 1, CARD)
    caption = "1 KUWAIT  2 ODESA  3 USA  4 KARACHI  5 SERBIA  6 HONG KONG"
    cv.draw_text_centred(WIDTH // 2, 606, caption, 2, INK)

    # Thirty more stories, two columns of fifteen.
    cv.draw_text(16, 640, "MORE FROM 26-27 NOVEMBER - 30 STORIES", 2, INK)
    cv.fill_rect(16, 660, 992, 2, RULE)
    for i, (code, headline) in enumerate(MORE):
        col = i // 15
        row = i % 15
        x = 16 + col * 504
        y = 668 + row * 20
        assert text_width(headline, 2) <= 444, headline
        cv.fill_rect(x, y + 3, 8, 8, REGION_COLOURS[code])
        cv.draw_text(x + 14, y, code, 2, REGION_COLOURS[code])
        cv.draw_text(x + 44, y, headline, 2, INK)

    # Sources footer.
    cv.fill_rect(16, 968, 992, 2, RULE)
    cv.draw_text(
        16, 978,
        "SOURCES: REUTERS, CNN, WSJ, NRF, AP - ALL STORIES DATED 26-27 NOV 2026",
        1, MUTED)
    cv.draw_text(
        16, 992,
        "RENDERED BY A PROGRAM - NO PHOTOGRAPHS - EVERY HEADLINE CHECKED AGAINST TWO SOURCES",
        1, MUTED)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    cv = build_image()
    data = encode_png(cv)
    assert len(data) <= 1024 * 1024, len(data)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
