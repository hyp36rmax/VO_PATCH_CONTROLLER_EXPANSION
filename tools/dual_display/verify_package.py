"""Static package/source integration checks. Does not execute Windows APIs."""
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('control',type=Path);p.add_argument('wrapper',type=Path);p.add_argument('--readobj',required=True);a=p.parse_args()
root=a.package.resolve();control=a.control.resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((root/'package-manifest.json').read_text())
for n,h in m['files'].items():assert sha(root/n)==h,n
for f in control.rglob('*'):
 if f.is_file():
  n=f.relative_to(control);assert (root/'control'/n).read_bytes()==f.read_bytes(),str(n)
  if str(n) not in ('game/ddraw.dll','game/ddraw.ini'):assert (root/'dual'/n).read_bytes()==f.read_bytes(),str(n)
for mode in ('dual','control'):
 for n in ('game/v_on.exe','game/ddraw.dll','game/vontanita.dll','OBSERVER.exe'):
  r=subprocess.check_output([a.readobj,'--file-headers','--coff-imports',str(root/mode/n)],text=True)
  assert 'IMAGE_FILE_MACHINE_I386' in r,n
  deps=re.findall(r'  Name: ([^\n]+)',r)
  assert all(not any(x in d.lower() for x in ('libgcc','libstdc','libwinpthread')) for d in deps),deps
  print(mode,n,'i386 dependencies:',','.join(deps))
ini=(root/'dual/game/ddraw.ini').read_text();assert ini.count('renderer=direct3d9')==2 and ini.count('lock_surfaces=true')==2
s=(a.wrapper/'src/render_d3d9.c').read_text()
assert 'TryEnterCriticalSection(&g_ddraw.primary->cs)' in s
retry=s[s.index('!TryEnterCriticalSection'):s.index('if (g_config.vhack)',s.index('!TryEnterCriticalSection'))]
assert retry.index('LeaveCriticalSection')<retry.index('ReleaseSemaphore')<retry.index('Sleep(1)')<retry.index('continue;')
assert s.index('TryEnterCriticalSection(&g_ddraw.primary->cs)')<s.index('blt_clean(')<s.index('vo_dual_uploaded(tex_index)')<s.index('vo_dual_present(tex_index)')
assert s.index('vo_dual_before_reset();')<s.index('IDirect3DDevice9_Reset(')
for f in root.glob('START-*.cmd'):
 b=f.read_bytes();assert b'\r\n' in b and b'\\r\\n' not in b
 assert b'%~dp0Launch.ps1' in b and b'/Users/' not in b
launch=(root/'Launch.ps1').read_text();assert '$PSScriptRoot' in launch and 'Wait=$true; PassThru=$true' in launch
assert '$manifest.mutable_files -contains $entry.Name' in launch
# Same mutable controller files can change between launches without bypassing DLL checks.
assert all(n.endswith('.ini') and not n.endswith('/ddraw.ini') for n in m['mutable_files'])
assert not any(n.endswith('.dll') for n in m['mutable_files'])
collector=(root/'Collect-Results.ps1').read_text()
assert 'RETURN-THIS-D04-P02B-LF01' in collector and 'OpenRead($temporary)' in collector
for bits in range(4):
 present=[mode for i,mode in enumerate(('dual','control')) if bits&(1<<i)]
 entries=['build-record.json','collection-status.txt']+[mode+'/launch-status.txt' for mode in present]
 assert len(entries)==len(set(entries)) # bounded archive-subset model only
with zipfile.ZipFile(root.with_suffix('.zip')) as z:
 assert z.testzip() is None
 with tempfile.TemporaryDirectory(prefix='VO relocated ü ') as tmp:
  z.extractall(tmp);relocated=Path(tmp)/root.name
  for n,h in m['files'].items():assert sha(relocated/n)==h
print('PASS: package hashes/CRC, byte-identical control/game/helper, i386 dependency inspection, upload/presentation order, CRLF launchers, mutable settings policy and relocated extraction; Windows execution NOT performed')
