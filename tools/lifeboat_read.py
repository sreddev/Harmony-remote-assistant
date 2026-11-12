"""Lifeboat, read-only: identify the attached Harmony remote and back up its configuration.

Uses Afterglow's own libconcord wrapper (afterglow/src/afterglow/concord.py). Only two
operations are called - `identity()` and `save_config()` - and neither writes to the
remote. Nothing here can change what is on the remote.

Usage:
    python tools/lifeboat_read.py --dlls <folder with libconcord-6.dll> [--out backups] [--identify-only]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "afterglow" / "src"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dlls", required=True, help="folder holding libconcord-6.dll and its dependencies")
    ap.add_argument("--out", default=str(ROOT / "backups"))
    ap.add_argument("--identify-only", action="store_true")
    args = ap.parse_args()

    dlls = Path(args.dlls).resolve()
    os.add_dll_directory(str(dlls))
    os.environ["AFTERGLOW_LIBCONCORD"] = str(dlls / "libconcord-6.dll")

    from afterglow import concord  # noqa: E402  (needs the DLL path set first)

    def progress(*a):
        pass

    with concord.Remote() as remote:
        ident = remote.identity(progress)
        print(json.dumps(ident, indent=2))
        if args.identify_only:
            return 0
        if not ident.get("config_valid"):
            print("The remote reports no valid configuration; nothing to back up.")
            return 2
        if not ident.get("can_read"):
            print("libconcord says this remote does not support reading its configuration.")
            return 2

        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        out = Path(args.out) / f"harmony-skin{ident['skin']}-{stamp}"
        out.mkdir(parents=True, exist_ok=True)
        ezhex = out / "config.ezhex"
        size = remote.save_config(ezhex, progress)
        raw = remote.read_config(progress)

    (out / "usercfg.bin").write_bytes(raw)
    (out / "identity.json").write_text(json.dumps(ident, indent=2))
    sums = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ezhex, out / "usercfg.bin")}
    (out / "SHA256SUMS.json").write_text(json.dumps(sums, indent=2))
    print(f"\nBacked up {size} bytes to {out}")
    for name, digest in sums.items():
        print(f"  {digest}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
