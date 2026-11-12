import sys, zipfile, os, re, hashlib
d=sys.argv[1]; seen={}
for f in sorted(os.listdir(d)):
    p=os.path.join(d,f)
    if not zipfile.is_zipfile(p): continue
    h=hashlib.md5(open(p,'rb').read()).hexdigest()
    if h in seen: print(f"{f}: duplicate of {seen[h]}"); continue
    seen[h]=f
    z=zipfile.ZipFile(p); names=z.namelist()
    m=[n for n in names if n.lower()=='appmanifest.xaml']
    print(f"=== {f} ({os.path.getsize(p)} B, {len(names)} entries)")
    if m:
        t=z.read(m[0]).decode('utf-8','ignore')
        for k in ('EntryPointAssembly','EntryPointType','RuntimeVersion'):
            r=re.search(k+r'="([^"]+)"',t); print(f"  {k}: {r.group(1) if r else '-'}")
        print("  parts:", ", ".join(re.findall(r'Source="([^"]+)"',t)))
    else:
        print("  ", ", ".join(names[:25]))
