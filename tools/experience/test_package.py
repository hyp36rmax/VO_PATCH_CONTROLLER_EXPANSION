"""Verify a game-data-free distribution and exercise preparation on private copies."""
import argparse
import json
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
import prepare

p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('retail',type=Path);p.add_argument('jpre',type=Path);p.add_argument('--readobj',required=True);a=p.parse_args()
root=a.package.resolve();prepare.verify(root)
for name in ('session.py','prepare.py','diagnostics.py','discovery.py'):
 assert (root/name).read_bytes()==Path(__file__).with_name(name).read_bytes(), name
manifest=json.loads((root/'package-manifest.json').read_text())['files']
assert set(f.name for f in root.glob('START-*.cmd'))=={'START-SINGLE-DISPLAY.cmd','START-DUAL-VERSUS.cmd','START-DUAL-MIRROR.cmd'}
assert (root/'EXPORT-DIAGNOSTICS.cmd').exists()
assert not (root/'game').exists() and not (root/'profiles').exists()
recipes=json.loads((root/'recipes.json').read_text())
# Check every distribution file, not only filename exclusions.
asset_hashes={h for val in recipes.values() for h in val['assets'].values()}
asset_hashes.update(val['base_sha256'] for val in recipes.values())
asset_hashes.update(entry['sha256'] for val in recipes.values() for entry in val['profiles'])
assert not (asset_hashes & set(manifest.values())), 'game file copied into distribution'
allowed_exe={'MOVIE-OBSERVER.exe','support/DISPLAY-MODES.exe','runtime/python.exe'}
assert {name for name in manifest if name.endswith('.exe')}==allowed_exe
assert not any(name.endswith(('.bin','.avi','.img','.log','.bak')) for name in manifest)
for name in ('MOVIE-OBSERVER.exe','support/DISPLAY-MODES.exe','support/ddraw.dll','support/vontanita.dll'):
 report=subprocess.check_output([a.readobj,'--file-headers','--coff-imports',str(root/name)],text=True)
 assert 'IMAGE_FILE_MACHINE_I386' in report
 assert not any(n in report.lower() for n in ('libgcc','libwinpthread','libstdc'))
 if name=='MOVIE-OBSERVER.exe':
  assert 'SetEnvironmentVariable' not in report, 'observer overrides launcher mode'
 if name.endswith('.exe'):
  assert b'level="asInvoker"' in (root/name).read_bytes()
launch=(root/'LaunchModes.ps1').read_text()
assert "@{single=0;versus=1;mirror=2}" in launch and 'VO_SESSION_CONFIG' in launch
assert "'Collect-Modes.ps1'" not in launch and 'Read-Host' not in launch
assert "$env:VO_DUAL_DISPLAY = $(if ($mode -eq 0) {'0'} else {'1'})" in launch
assert 'beforePreferenceHash' in launch and 'Session mode mismatch' in launch
assert '.previous' not in launch
for f in root.glob('*.cmd'):
 assert b'%~dp0' in f.read_bytes() and b'\r\n' in f.read_bytes()
with zipfile.ZipFile(root.with_suffix('.zip')) as z:
 assert z.testzip() is None
 assert len(z.namelist()) == len(manifest)+1
 with tempfile.TemporaryDirectory(prefix='VO G03 spaces ü ') as td:
  z.extractall(td);prepare.verify(Path(td)/root.name)
print('PASS package hashes/CRC, relocated Unicode extraction, game-file exclusions, PE dependencies and ordinary-user manifests')
for edition in ('retail','jpre'):
 source=getattr(a,edition).resolve()
 before={p.name:prepare.digest(p.read_bytes()) for p in source.iterdir() if p.is_file()}
 with tempfile.TemporaryDirectory(prefix='G03 prepare ü ') as td:
  staged=Path(td)/'package';shutil.copytree(root,staged)
  record=prepare.prepare(staged,source)
  assert record['edition']==edition
  for entry in recipes[edition]['profiles']:
   image=(staged/'profiles'/(entry['profile']+'.exe')).read_bytes()
   assert prepare.digest(image)==entry['sha256']
   assert b'VO PATCH EX 0.1-dev' in image
  assert prepare.prepare(staged,source)==record
  for name in ('scrstfcg.bin','scrstfmp.bin'):
   assert (staged/'game'/(name+'.bak')).read_bytes()==(source/name).read_bytes()
  # Unrelated resources and the original network DLL are exact private copies.
  for name in recipes[edition]['assets']:
   if name not in ('scrstfcg.bin','scrstfmp.bin','escrgame.bin','jscrgame.bin'):
    assert (staged/'game'/name).read_bytes()==(source/name).read_bytes(),name
  assert (staged/'game/dpctrl.dll').read_bytes()==(source/'dpctrl.dll').read_bytes()
  assert not (staged/'game/v_on.exe').exists()
  assert (staged/'game/v_on.exe.bak').read_bytes()==(source/'v_on.exe').read_bytes()
  shutil.copyfile(staged/'profiles/wide.exe',staged/'game/v_on.exe')
  spec=importlib.util.spec_from_file_location('uat_restore',staged/'v-on-patcher.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  patch=module.Patcher();patch.load(str(staged/'game/v_on.exe'));patch.restore()
  assert (staged/'game/v_on.exe').read_bytes()==(source/'v_on.exe').read_bytes()
  for name in ('scrstfcg.bin','scrstfmp.bin',patch.build.art[0]):
   assert (staged/'game'/name).read_bytes()==(source/name).read_bytes()

  broken=staged/'profiles/wide.exe';data=bytearray(broken.read_bytes());data[-1]^=1;broken.write_bytes(data)
  try:prepare.prepare(staged,source)
  except ValueError:pass
  else:raise AssertionError('corrupted profile accepted')
 assert before=={p.name:prepare.digest(p.read_bytes()) for p in source.iterdir() if p.is_file()}
 print('PASS',edition,'all five profile hashes, resource backups and full Restore Original, unchanged source installation, idempotence and corruption rejection')
print('Windows launch, discovery, PowerShell execution and visual acceptance remain pending.')
