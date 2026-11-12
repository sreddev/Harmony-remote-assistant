import sys,re
data=open(sys.argv[1],'rb').read(); n=int(sys.argv[2]) if len(sys.argv)>2 else 6
a=set(m.decode() for m in re.findall(rb'[\x20-\x7e]{%d,}'%n,data))
u=set(m.decode('utf-16le') for m in re.findall(rb'(?:[\x20-\x7e]\x00){%d,}'%n,data))
for s in sorted(a|u): print(s)
