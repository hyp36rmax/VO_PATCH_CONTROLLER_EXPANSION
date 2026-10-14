"""Assemble the private UAT candidate from preserved D03-P04 assets.
Cross-build/package verification is not Windows runtime acceptance.
"""
import argparse, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('control',type=Path);p.add_argument('wrapper',type=Path);p.add_argument('output',type=Path);p.add_argument('--cc',required=True);p.add_argument('--windres',required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=a.control.resolve();wrapper=a.wrapper.resolve()
for mode in ('dual','control'):
 shutil.copytree(source,out/mode)
 # Retain immutable assets, observer and its original game identity.
 if mode=='dual':
  shutil.copy2(wrapper/'ddraw.dll',out/mode/'game/ddraw.dll')
  ini=out/mode/'game/ddraw.ini';text=ini.read_text().replace('renderer=auto','renderer=direct3d9').replace('rgb555=false','rgb555=false\nlock_surfaces=true');ini.write_text(text)
  resource=out/'display-manifest.o'
  subprocess.run([a.windres,str(here/'displays.rc'),str(resource)],cwd=here,check=True)
  subprocess.run([a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-municode',str(here/'displays.c'),str(resource),'-luser32','-Wl,--no-insert-timestamp','-o',str(out/mode/'game/DISPLAY-ASSIGN.exe')],check=True)
  resource.unlink()
for n in ('Launch.ps1','Collect-Results.ps1'):shutil.copy2(here/n,out/n)
for mode,name in [('dual','START-DUAL-DISPLAY.cmd'),('control','START-LOCAL-VS-CONTROL.cmd')]:
 (out/name).write_bytes(('@echo off\r\nsetlocal\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch.ps1" -Mode '+mode+'\r\nif errorlevel 1 pause\r\n').encode('ascii'))
(out/'READ-ME.txt').write_text('''D04-P02B-LF01 PRIVATE WINDOWS UAT — runtime validation pending

Extract the entire ZIP to a writable folder.
1. Launch START-DUAL-DISPLAY.cmd. Select the P1 and P2 displays and save.
2. The original game starts automatically. Select original Local VS.
3. Check independent cameras, HUD/targeting, P1/P2 controls, 16:9 shape,
   stable motion and responsiveness. Try Alt+Tab, minimize/restore and exit.
4. Closing the game must close both output windows. The results ZIP is selected.
5. Run START-LOCAL-VS-CONTROL.cmd for the unchanged D03-P04 comparison.
6. Return RETURN-THIS-D04-P02B-LF01.zip and your observations.
   If ZIP creation fails, the equally named return folder retains the logs.

Run normally, not as administrator. No privilege elevation is requested.

Only one game is launched. Display assignments persist between runs.
The observer and launcher consoles may be visible during this private test.
If dual output falls back to the composed game window, report that as a failure
of dual presentation. Do not change display modes, copy DLLs or edit INI files.
A display disconnect/mode change disables dual output for the session; restart
and choose available displays. Driver errors may require normal game closure.

Windows execution, physical output, scanout alignment and latency are unverified.
No measured or zero-latency claim is made. The two outputs use the same uploaded
texture generation, but their presents and physical scanouts are sequential.
Source surface locking is enabled to prevent reading a partially written frame.
No controller/game/renderer/camera code is changed. Menus and other shared screens
are also divided at the midpoint; navigate in the original game as usual.
''')
(out/'build-record.json').write_text(json.dumps({'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=here,text=True).strip(),'wrapper':json.loads((wrapper/'private-build.json').read_text()),'game_sha256':sha(source/'game/v_on.exe'),'observer_sha256':sha(source/'OBSERVER.exe'),'windows_runtime':'NEEDS VALIDATION','physical':'NEEDS VALIDATION'},indent=2)+'\n')
# Include original wrapper provenance/license, and private extension sources.
provenance=source.parent/'Provenance'
if provenance.exists():shutil.copytree(provenance,out/'Provenance')
shutil.copytree(here,out/'Provenance/private-presentation',ignore=shutil.ignore_patterns('__pycache__'))
files={str(f.relative_to(out)).replace('\\','/'):sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
(out/'package-manifest.json').write_text(json.dumps({'files':files,'mutable_files':[n for n in files if '/game/' in n and n.endswith('.ini') and not n.endswith('/ddraw.ini')]},indent=2)+'\n')
with zipfile.ZipFile(out.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file():z.write(f,str(Path(out.name)/f.relative_to(out)))
print(out.with_suffix('.zip'))
