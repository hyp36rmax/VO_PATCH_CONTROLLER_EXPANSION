"""Build the isolated shared-image variant and rebind the preserved observer identity.
Only the two exact SHA-256 literals in observer.c may change.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engineering_shared,engineering3840,engineering_vs
p=argparse.ArgumentParser();p.add_argument('pristine',type=Path);p.add_argument('observer_source',type=Path);p.add_argument('control',type=Path);p.add_argument('output',type=Path);p.add_argument('--cc',required=True);p.add_argument('--windres',required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
v=engineering3840.load_private();raw=a.pristine.read_bytes();data,meta=engineering_shared.build(raw)
assert meta['edition']=='jpre','UAT observer addresses are JPRE only'
base,_=engineering_vs.build(raw);edition=v.BUILDS[hashlib.md5(raw).hexdigest()]
v.stamp_version(base,edition);assert base==a.control.read_bytes()
v.stamp_version(data,edition);(a.output/'v_on.exe').write_bytes(data)
old=hashlib.sha256(base).hexdigest();new=hashlib.sha256(data).hexdigest()
arr=lambda h:','.join('0x'+h[i:i+2] for i in range(0,64,2))
src=a.output/'observer-source';src.mkdir()
s=(a.observer_source/'observer.c').read_text()
assert s.count(old)==1 and s.count(arr(old))==1
updated=s.replace(old,new).replace(arr(old),arr(new))
assert updated.replace(new,old).replace(arr(new),arr(old))==s
(src/'observer.c').write_text(updated)
for name in ('observer_core.h','log_io.h','observer.manifest','observer.rc'):
 shutil.copy2(a.observer_source/name,src/name)
subprocess.run([a.windres,'observer.rc','observer-res.o'],cwd=src,check=True)
subprocess.run([a.cc,'-O2','-Wall','-Wextra','-Werror','-municode','observer.c','observer-res.o','-o',str(a.output.resolve()/'OBSERVER.exe'),'-lbcrypt','-lpsapi','-lshell32','-lole32','-ladvapi32','-luuid','-Wl,--no-insert-timestamp'],cwd=src,check=True)
(src/'observer-res.o').unlink()
record={'shared':meta['shared'],'internal':[3840,1080,16],'gameplay_sources':[[0,0,1920,1080],[1920,0,1920,1080]],'control_sha256':old,'game_sha256':new,'observer_source_change':'two SHA-256 literals only','physical_status':'NEEDS VALIDATION'}
(a.output/'geometry.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
