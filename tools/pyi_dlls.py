"""Extract only the .dll entries from a PyInstaller onefile executable (no code is run).

Usage: python -I pyi_dlls.py <exe> <out_dir> [name-filter-substring ...]
"""
import os
import struct
import sys
import zlib

MAGIC = b"MEI\014\013\012\013\016"

exe, out = sys.argv[1], sys.argv[2]
filters = [f.lower() for f in sys.argv[3:]]
data = open(exe, "rb").read()
pos = data.rfind(MAGIC)
if pos < 0:
    sys.exit("not a PyInstaller archive")
# Cookie: magic(8) len(4) toc_offset(4) toc_len(4) pyver(4) [pylib name(64) in newer versions]
pkg_len, toc_off, toc_len, pyver = struct.unpack("!IIII", data[pos + 8:pos + 24])
cookie_size = 24 + 64 if data[pos + 24:pos + 88].rstrip(b"\0").endswith(b".dll") or b"python" in data[pos + 24:pos + 88] else 24
start = pos + cookie_size - pkg_len
toc = data[start + toc_off:start + toc_off + toc_len]
os.makedirs(out, exist_ok=True)
i, names = 0, []
while i < len(toc):
    (entry_len,) = struct.unpack("!I", toc[i:i + 4])
    e_off, c_len, u_len, flag, typ = struct.unpack("!IIIBc", toc[i + 4:i + 18])
    name = toc[i + 18:i + entry_len].rstrip(b"\0").decode("utf-8", "replace")
    i += entry_len
    if not name.lower().endswith(".dll"):
        continue
    names.append(name)
    if filters and not any(f in name.lower() for f in filters):
        continue
    blob = data[start + e_off:start + e_off + c_len]
    if flag:
        blob = zlib.decompress(blob)
    dest = os.path.join(out, os.path.basename(name))
    open(dest, "wb").write(blob)
    print(f"extracted {name} ({len(blob)} B)")
print(f"{len(names)} dlls in archive", file=sys.stderr)
