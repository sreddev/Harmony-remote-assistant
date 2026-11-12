"""Write the Harmony 600's glyph-shape table from a configuration whose codes were read by eye.

Read-only and offline. Logitech numbers each configuration's characters its own way, so a
code table holds for one image only; what a glyph looks like holds for every 600. This
takes the code -> character table read from the glyph atlas (tools/glyph_atlas.py) of one
image and writes shape fingerprint -> character for every font that draws the code, the
form Afterglow's text reader matches against (labels.known_shapes).

Every code was confirmed in more than one font where it appears: the atlas rows f0, f3,
f4, f7 and f13, laid against each font's non-empty codes in order, agree on every code
they share (t=23, r=25, d=33, i=35, T=48, k=52, F=55, - =67 in all of them).

Usage: python tools/make_600_glyph_shapes.py backups/<folder>/usercfg.bin
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "afterglow" / "src"))

from afterglow.backends.harmony_600 import layout  # noqa: E402
from afterglow.backends.harmony_one import font_index  # noqa: E402

# Code -> character for backups/harmony-skin71-20261111-195845 (read from its atlas).
CODES = {
    1: "H", 2: "y", 3: "/", 4: "(", 5: " ", 6: "0", 7: "s", 8: "e", 9: "c", 10: ")",
    11: ".", 12: "1", 13: "2", 14: "3", 15: "4", 16: "5", 17: "6", 18: "7", 19: "8",
    20: "9", 21: "a", 22: "U", 23: "t", 24: "h", 25: "r", 26: "m", 27: "o", 28: "n",
    29: "u", 30: "p", 31: "f", 32: "w", 33: "d", 34: "A", 35: "i", 36: "v", 37: "b",
    38: "E", 39: "x", 40: "S", 41: "B", 42: "C", 43: "L", 44: "I", 45: "l", 46: "g",
    47: "R", 48: "T", 49: "G", 50: "W", 51: "z", 52: "k", 53: "D", 54: "P", 55: "F",
    56: "M", 57: "q", 58: "\\", 59: "N", 60: "O", 61: "V", 62: "?", 63: "Y", 64: ",",
    65: ">", 66: "=", 67: "-", 68: "ù", 69: "X", 70: "K", 71: "'", 72: "+", 73: "!",
    74: "j",
}
OUT = ROOT / "afterglow" / "src" / "afterglow" / "backends" / "harmony_600" / "glyph-shapes.json"


def main() -> int:
    payload = Path(sys.argv[1]).read_bytes()
    shapes: dict[str, set[str]] = defaultdict(set)
    with layout.active():
        for font in font_index.fonts(payload):
            for code, glyph in font["glyphs"].items():
                if code in CODES:
                    shapes[glyph["shape"]].add(CODES[code])
    clashes = {s: sorted(c) for s, c in shapes.items() if len(c) > 1}
    # a shape this font draws for two characters (I and l) keeps both: the reader
    # settles it image-wide and by neighbours, as it does for Logitech's own fonts
    table = {s: "".join(sorted(c)) for s, c in shapes.items()}
    OUT.write_text(json.dumps({
        "_comment": ("Harmony 600 LCD glyph shapes (ui_index._glyph_shape fingerprints) -> "
                     "character, from tools/make_600_glyph_shapes.py in Harmony-remote-assistant."),
        "shapes": dict(sorted(table.items(), key=lambda kv: kv[1])),
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(table)} shapes -> {len(set(table.values()))} characters; "
          f"{len(clashes)} shapes drawn as two characters: {list(clashes.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
