"""Read a Harmony 600 backup with Afterglow and report its devices, commands and activities.

Read-only and offline: it opens a `.ezhex` backup file, never the remote. Writes the
imported project as JSON next to the backup (`project.json`) and prints a summary.

Usage: python tools/read_600_config.py backups/<folder>/config.ezhex
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "afterglow" / "src"))

from afterglow import ezhex, importer  # noqa: E402


def main() -> int:
    source = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()):
            ezhex.unpack(str(source), tmp)
        result = importer.import_result(tmp)
    project = result.project
    out = source.with_name("project.json")
    out.write_text(json.dumps(project, indent=1, ensure_ascii=False, default=str), "utf-8")

    print(f"== Devices ({len(project['devices'])})")
    for device in project["devices"]:
        signals = device.get("signals") or {}
        named = [n for n in signals if not n.startswith("Command ")]
        print(f"\n  {device.get('label')}  [{device.get('type')}]  {len(signals)} commands, "
              f"{len(named)} named")
        for key in ("power_cmd", "power_off_cmd", "power_on_cmd", "inputs", "input_cmds"):
            if device.get(key):
                print(f"    {key}: {device[key]}")
        print("    " + ", ".join(sorted(signals)))
    print(f"\n== Activities ({len(project['activities'])})")
    for activity in project["activities"]:
        roles = {k: activity.get(k) for k in ("display", "control", "volume") if activity.get(k)}
        keys = activity.get("keys") or {}
        print(f"\n  {activity.get('label')}  [{activity.get('type')}]  roles {roles}")
        for k in ("startup", "devices", "inputs"):
            if activity.get(k):
                print(f"    {k}: {json.dumps(activity[k], ensure_ascii=False, default=str)[:300]}")
        if keys:
            print(f"    keys ({len(keys)}): " + ", ".join(
                f"{k}->{json.dumps(v, ensure_ascii=False, default=str)[:40]}" for k, v in sorted(keys.items())[:40]))
    if result.warnings:
        print("\n== Notes")
        for note in result.warnings:
            print("  - " + note)
    print(f"\nproject written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
