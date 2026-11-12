import zipfile, sys, os, zlib, struct
src, dst = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(src)
raw = open(src, 'rb').read()
for i in z.infolist():
    name = i.filename.replace('\\', '/')
    if '/' in name:
        continue  # skip satellite resource assemblies
    o = i.header_offset
    n, e = struct.unpack('<HH', raw[o + 26:o + 30])
    s = o + 30 + n + e
    d = raw[s:s + i.compress_size]
    if i.compress_type == 8:
        d = zlib.decompress(d, -15)
    open(os.path.join(dst, name), 'wb').write(d)
