"""F04 package/provenance contracts; not native Windows acceptance."""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
import mode_profiles
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('baseline',type=Path);p.add_argument('pristine',type=Path);p.add_argument('--readobj',required=True);a=p.parse_args();root=a.package
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'package-manifest.json').read_text())
for name,h in manifest['files'].items():assert sha(root/name)==h,name
record=json.loads((root/'build-record.json').read_text())
for profile in record['profiles']:
 data,meta=mode_profiles.build(a.pristine.read_bytes(),profile['profile'])
 assert data==(root/'profiles'/(profile['profile']+'.exe')).read_bytes()
 assert meta==profile or {**meta,'internal':list(meta['internal'])}==profile
 assert meta['movie_bytes_changed']==2
for f in (a.baseline/'dual/game').iterdir():
 if f.is_file() and f.name not in ('v_on.exe','ddraw.dll','player-displays.ini','DISPLAY-ASSIGN.exe','D04-P02B-presentation.log'):
  assert f.read_bytes()==(root/'game'/f.name).read_bytes(),f.name
assert not (root/'game/player-displays.ini').exists(), 'fresh default must not ship tester identities'
assert not (root/'game/v_on.exe').exists(), 'launcher must select a verified profile before game startup'
for name in ('MOVIE-OBSERVER.exe','game/DISPLAY-MODES.exe','game/ddraw.dll'):
 report=subprocess.check_output([a.readobj,'--file-headers','--coff-imports',str(root/name)],text=True)
 assert 'IMAGE_FILE_MACHINE_I386' in report and not any(x in report.lower() for x in ('libgcc','libstdc','libwinpthread'))
 if name.endswith('.exe'):
  assert b'level="asInvoker"' in (root/name).read_bytes(),name
  assert 'MANIFEST' in subprocess.check_output([a.readobj,'--coff-resources',str(root/name)],text=True)
launch=(root/'LaunchModes.ps1').read_text();collector=(root/'Collect-Modes.ps1').read_text()
assert launch.index('Get-FileHash')<launch.index("'DISPLAY-MODES.exe'")<launch.index('Copy-Item')<launch.index("'MOVIE-OBSERVER.exe'")
assert 'Wait -PassThru' in launch and '$PSScriptRoot' in launch
assert 'RunAs' not in launch and 'Remove-Item' not in collector
assert collector.index('Copy-Item')<collector.index('Add-Type -AssemblyName System.IO.Compression')
assert 'compression-status.txt' in collector and '/select,' in collector
assert 'RETURN-THIS-D04-P05-F04' in collector
for f in root.glob('START-*.cmd'):assert b'\r\n' in f.read_bytes() and b'%~dp0' in f.read_bytes()
with zipfile.ZipFile(root.with_suffix('.zip')) as z:
 assert z.testzip() is None
 with tempfile.TemporaryDirectory(prefix='VO mode spaces ü ') as td:
  z.extractall(td)
  for name,h in manifest['files'].items():assert sha(Path(td)/root.name/name)==h
print('PASS F04 profile regeneration, only two movie bytes per image, original assets/controller files, i386 dependencies/manifests, shared configuration launch/collection contracts, package hashes/CRC and relocated extraction; native Windows pending')
