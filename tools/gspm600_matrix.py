"""Fingerprint matrix: which Harmony 600 slot does each Harmony One section parser accept?

Read-only and offline. For every One section parser, every 600 slot is offered as that
section (all other One sections fall back to a default guess), and the parser's own
validation decides. A slot accepted by exactly one parser - with a plausible result size -
is a strong identification.

Usage: python tools/gspm600_matrix.py backups/<folder>/usercfg.bin
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "afterglow" / "src"))

from afterglow.backends.harmony_one import (  # noqa: E402
    activity_index, command_index, font_index, gspm, importing, key_index, named_index,
    structures, ui_index)

BASE_600, HEADER_600, LWJL_600, SLOTS_600 = 0x030000, 0x1400, 0x5B, 18


def slot_ranges(payload: bytes) -> list[tuple[int, int]]:
    starts = [struct.unpack_from("<I", payload, 0x0C + 4 * i)[0] - BASE_600
              for i in range(SLOTS_600)]
    end = len(payload) - 6
    bounds = sorted(starts) + [end]
    return [(s, bounds[bounds.index(s) + 1]) for s in starts]


PARSERS = {
    0: ("named_index.inspect", named_index.inspect),
    3: ("structures.read_stamp", structures.read_stamp),
    5: ("command_index.section5_layout", command_index.section5_layout),
    6: ("ui_index.screen_slots", ui_index.screen_slots),
    7: ("font_index.fonts", font_index.fonts),
    10: ("activity_index.contexts", activity_index.contexts),
    11: ("command_index.objects", command_index.objects),
    12: ("ui_index.section12_programs", ui_index.section12_programs),
    13: ("importing.timers", importing.timers),
    14: ("activity_index.engine_records", activity_index.engine_records),
    15: ("importing.switch_tables", importing.switch_tables),
    17: ("importing.number_senders", importing.number_senders),
    19: ("ui_index.touch_templates", ui_index.touch_templates),
}


def size_of(value) -> str:
    try:
        return str(len(value))
    except TypeError:
        return "1"


def main() -> int:
    payload = Path(sys.argv[1]).read_bytes()
    slots = slot_ranges(payload)
    default = {n: slots[min(n, SLOTS_600 - 1)] for n in range(20)}
    saved = (gspm.BASE, gspm.HEADER_CONSTANT, gspm.BUTTON_MAP_OFFSET,
             gspm.section_ranges, gspm.validate)
    gspm.BASE, gspm.HEADER_CONSTANT, gspm.BUTTON_MAP_OFFSET = BASE_600, HEADER_600, LWJL_600
    gspm.validate = lambda p: {"ok": True}
    current: dict[int, tuple[int, int]] = {}
    gspm.section_ranges = lambda p: dict(current)
    print("One section parser                  accepted 600 slots (result size)")
    try:
        for number, (label, parser) in PARSERS.items():
            hits = []
            for slot, rng in enumerate(slots):
                current.clear()
                current.update(default)
                current[number] = rng
                try:
                    hits.append(f"{slot}({size_of(parser(payload))})")
                except Exception:  # noqa: BLE001 - rejection is the signal
                    pass
            print(f"  {number:2d} {label:32s} {' '.join(hits) or '-'}")
    finally:
        (gspm.BASE, gspm.HEADER_CONSTANT, gspm.BUTTON_MAP_OFFSET,
         gspm.section_ranges, gspm.validate) = saved
    return 0


if __name__ == "__main__":
    sys.exit(main())
