"""Probe: read a Harmony 600 (arch 14) GSPM image with Afterglow's Harmony One reader.

Read-only and offline: works on a backup file, never on the remote.

The 600's image differs from the One's in its base address (0x030000, not 0x040000), its
header constant (0x1400, not 0x1600) and its master index (18 slots, all present, with the
LWJL marker at 0x5B instead of 20 slots with slot 8 absent and LWJL at 0x63). The One
reader addresses sections by the One's numbers, so this probe maps the 600's slots onto
them and asks which mapping the reader's own cross-checks accept.

Usage: python tools/gspm600_probe.py backups/<folder>/usercfg.bin
"""
from __future__ import annotations

import contextlib
import struct
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "afterglow" / "src"))

from afterglow.backends.harmony_one import gspm  # noqa: E402

BASE_600 = 0x030000
HEADER_600 = 0x1400
LWJL_600 = 0x5B
SLOTS_600 = 18


def slots_600(payload: bytes) -> list[int]:
    return [struct.unpack_from("<I", payload, 0x0C + 4 * i)[0] for i in range(SLOTS_600)]


# Candidate maps: One section number -> 600 slot (None = absent on the 600).
def mapping(name: str) -> dict[int, int | None]:
    if name == "shift-after-7":        # 600 lacks One's 8 (absent there too) and 19
        return {**{i: i for i in range(8)}, 8: None, **{i: i - 1 for i in range(9, 19)}, 19: None}
    if name == "identity-0-17":        # 600 = One 0..17; One 18, 19 absent
        return {**{i: i for i in range(18)}, 18: None, 19: None}
    if name == "shift-after-7-drop-18":  # 600 lacks One's 8 and 18
        return {**{i: i for i in range(8)}, 8: None, **{i: i - 1 for i in range(9, 18)},
                18: None, 19: 17}
    raise KeyError(name)


@contextlib.contextmanager
def as_600(name: str):
    """Point the One reader's gspm module at the 600's layout for the duration."""
    saved = {k: getattr(gspm, k) for k in
             ("BASE", "HEADER_CONSTANT", "BUTTON_MAP_OFFSET", "_sections")}
    table = mapping(name)

    def _sections(payload: bytes, checksum_offset: int):
        raw = slots_600(payload)
        out = []
        for one_index in range(gspm.SECTION_COUNT):
            slot = table[one_index]
            if slot is None:
                out.append(None)
                continue
            relative = raw[slot] - BASE_600
            if not 0 <= relative < checksum_offset:
                raise ValueError(f"600 slot {slot} points outside the image")
            out.append(relative)
        return tuple(out)

    gspm.BASE, gspm.HEADER_CONSTANT, gspm.BUTTON_MAP_OFFSET = BASE_600, HEADER_600, LWJL_600
    gspm._sections = _sections
    try:
        yield table
    finally:
        for k, v in saved.items():
            setattr(gspm, k, v)


def try_stage(label, fn):
    try:
        value = fn()
        print(f"  ok    {label}")
        return value
    except Exception as exc:  # noqa: BLE001 - a probe reports every failure
        last = traceback.extract_tb(exc.__traceback__)[-1]
        print(f"  FAIL  {label}: {type(exc).__name__}: {exc}  [{Path(last.filename).name}:{last.lineno}]")
        return None


def main() -> int:
    payload = Path(sys.argv[1]).read_bytes()
    names = sys.argv[2:] or ["shift-after-7", "identity-0-17", "shift-after-7-drop-18"]
    raw = slots_600(payload)
    sizes = [b - a for a, b in zip(sorted(raw), sorted(raw)[1:] + [len(payload) - 6 + BASE_600])]
    print("600 slots (relative offset, size):")
    for i, (a, s) in enumerate(zip(raw, sizes)):
        print(f"  slot {i:2d}  {a - BASE_600:#08x}  {s:8d}")

    from afterglow.backends.harmony_one import inventory, importing, command_index
    for name in names:
        print(f"\nmapping {name}")
        with as_600(name):
            try_stage("validate", lambda: gspm.validate(payload))
            native = try_stage("inventory.inspect", lambda: inventory.inspect(payload))
            image = try_stage("importing.Image", lambda: importing.Image(payload))
            if native and image:
                devices = try_stage("project_devices", lambda: importing.project_devices(
                    image, command_index.portable_devices(
                        native["ownership"], native["keys"], native["ui"]["device_menus"]),
                    [], {}))
                if devices:
                    print(f"  -> {len(devices)} devices: "
                          + ", ".join(d.get('label', '?') for d in devices))
    return 0


if __name__ == "__main__":
    sys.exit(main())
