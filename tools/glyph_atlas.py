"""Render every glyph a Harmony 600 image's fonts draw into a labelled PNG atlas.

Read-only and offline. Each row is one font (its attribute number); each cell is one glyph
code, drawn from the image's own pixels with the code printed under it in a tiny built-in
digit font. Used to read the 600's glyph codes by eye where Afterglow's shape table has
no match.

Usage: python tools/glyph_atlas.py backups/<folder>/usercfg.bin out.png [scale]
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "afterglow" / "src"))

from afterglow.backends.harmony_600 import layout  # noqa: E402
from afterglow.backends.harmony_one import font_index, ui_index  # noqa: E402

DIGITS = {  # 3x5 digits for the cell labels
    "0": "111101101101111", "1": "010110010010111", "2": "111001111100111",
    "3": "111001111001111", "4": "101101111001001", "5": "111100111001111",
    "6": "111100111101111", "7": "111001001001001", "8": "111101111101111",
    "9": "111101111001111", "f": "111100110100100",
}


def png(width: int, height: int, pixels: list[bytearray]) -> bytes:
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main() -> int:
    payload = Path(sys.argv[1]).read_bytes()
    out = Path(sys.argv[2])
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    with layout.active():
        fonts = font_index.fonts(payload)
        rows = []
        for font in fonts:
            cells = []
            for code, glyph in sorted(font["glyphs"].items()):
                mask, width = ui_index.glyph_mask(payload, glyph["offset"])
                cells.append((code, mask, width))
            rows.append((font["attribute"], font["height"], cells))
    cell_w, cell_h = 14 * scale, 16 * scale + 8
    columns = max(len(cells) for _, _, cells in rows)
    W, H = 20 + columns * cell_w, len(rows) * cell_h + 4
    img = [bytearray([255]) * W for _ in range(H)]

    def put_text(x, y, s):
        for ch in s:
            pattern = DIGITS.get(ch)
            if pattern:
                for i, bit in enumerate(pattern):
                    if bit == "1" and 0 <= y + i // 3 < H and 0 <= x + i % 3 < W:
                        img[y + i // 3][x + i % 3] = 0
            x += 4

    for r, (attribute, _height, cells) in enumerate(rows):
        y0 = r * cell_h + 2
        put_text(1, y0 + 6, f"f{attribute}")
        for c, (code, mask, width) in enumerate(cells):
            x0 = 20 + c * cell_w
            for gy, line in enumerate(mask):
                for gx in range(min(width, len(line))):
                    if line[gx]:
                        for dy in range(scale):
                            for dx in range(scale):
                                yy, xx = y0 + gy * scale + dy, x0 + gx * scale + dx
                                if yy < H and xx < W:
                                    img[yy][xx] = 0
            put_text(x0, y0 + 16 * scale + 1, str(code))
            for yy in range(y0, y0 + cell_h - 2):   # faint cell separator
                if x0 - 2 >= 0:
                    img[yy][x0 - 2] = 200
    out.write_bytes(png(W, H, img))
    print(f"{out} {W}x{H}, {len(rows)} fonts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
