"""Assemble the private UAT candidate from preserved D03-P04 assets.
Cross-build/package verification is not Windows runtime acceptance.
"""
import argparse, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('control',type=Path);p.add_argument('wrapper',type=Path);p.add_argument('output',type=Path);p.add_argument('--assignment-evidence',type=Path);p.add_argument('--shared-assets',type=Path,required=True);p.add_argument('--cc',required=True);p.add_argument('--windres',required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=a.control.resolve();wrapper=a.wrapper.resolve()
for mode in ('dual','control'):
 shutil.copytree(source,out/mode)
 # Preserve the control; bind the dual observer to its isolated shared image.
 if mode=='dual':
  shutil.copy2(wrapper/'ddraw.dll',out/mode/'game/ddraw.dll')
  shutil.copy2(a.shared_assets/'v_on.exe',out/mode/'game/v_on.exe')
  shutil.copy2(a.shared_assets/'OBSERVER.exe',out/mode/'OBSERVER.exe')
  (out/mode/'VISUAL-INTEGRITY.json').write_text((a.shared_assets/'geometry.json').read_text())
  ini=out/mode/'game/ddraw.ini';text=ini.read_text().replace('renderer=auto','renderer=direct3d9').replace('rgb555=false','rgb555=false\nlock_surfaces=true');ini.write_text(text)
  resource=out/'display-manifest.o'
  subprocess.run([a.windres,str(here/'displays.rc'),str(resource)],cwd=here,check=True)
  subprocess.run([a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-municode',str(here/'displays.c'),str(resource),'-luser32','-Wl,--no-insert-timestamp','-o',str(out/mode/'game/DISPLAY-ASSIGN.exe')],check=True)
  resource.unlink()
if a.assignment_evidence:
 with zipfile.ZipFile(a.assignment_evidence) as evidence:
  names=[n for n in evidence.namelist() if n.replace('\\','/').endswith('/game/player-displays.ini')]
  assert len(names)==1
  (out/'dual/game/player-displays.ini').write_bytes(evidence.read(names[0]))
for n in ('Launch.ps1','Collect-Results.ps1'):shutil.copy2(here/n,out/n)
for mode,name in [('dual','START-DUAL-DISPLAY.cmd'),('control','START-SINGLE-DISPLAY.cmd')]:
 (out/name).write_bytes(('@echo off\r\nsetlocal\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch.ps1" -Mode '+mode+'\r\nif errorlevel 1 pause\r\n').encode('ascii'))
(out/'READ-ME.txt').write_text('''D04-P05-F03C PRIVATE WINDOWS UAT — runtime validation pending

Extract the entire ZIP to a writable folder.
1. Launch START-DUAL-DISPLAY.cmd. The previous monitor assignment is retained.
2. Confirm the intro movie is visible on Display 1 and Display 2 stays black.
   Check original proportions, audio and the usual skip control.
3. Skip normally and confirm the main menu returns without a black screen.
4. Enter Local VS: check mirrored selection, independent P1/P2 gameplay,
   controls, targeting and the existing Mirror Player 1 option if used.
5. Return to menu; check focus/minimize/restore and exit normally.
6. Launch START-SINGLE-DISPLAY.cmd. Check original movie/skip, menu,
   split-screen Local VS, F-key controls and controllers, then exit.
7. Return RETURN-THIS-D04-P05-F03C.zip with observations for BOTH modes.
   If compression fails, the equally named return folder retains raw logs.

This is a targeted occlusion correction, not a decoder replacement. The movie
must be a unique visible AVIWnd32 child of this game, contained on the assigned
Display 1. Otherwise the validated F02 presentation is preserved and rejection
is logged. Different Display 2 dimensions do not affect movie identification.
If the movie remains invisible, report it; do not change Windows configuration.

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
The internal buffer remains 3840x1080; neither monitor needs that display mode.
Shared screens are composed using the upstream 1920x1080 viewport, then fitted
independently to each desktop. Original 4:3 artwork/HUD behavior is retained
inside that composition. Gameplay retains the original independent halves.
Controllers and Local VS cameras are unchanged. Physical F03C behavior NEEDS VALIDATION.
''')
(out/'build-record.json').write_text(json.dumps({'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=here,text=True).strip(),'wrapper':json.loads((wrapper/'private-build.json').read_text()),'control_game_sha256':sha(source/'game/v_on.exe'),'control_observer_sha256':sha(source/'OBSERVER.exe'),'game_sha256':sha(out/'dual/game/v_on.exe'),'observer_sha256':sha(out/'dual/OBSERVER.exe'),'assignment_evidence_sha256':sha(a.assignment_evidence) if a.assignment_evidence else None,'shared_geometry':json.loads((a.shared_assets/'geometry.json').read_text()),'windows_runtime':'NEEDS VALIDATION','physical':'NEEDS VALIDATION'},indent=2)+'\n')
# Include original wrapper provenance/license, and private extension sources.
provenance=source.parent/'Provenance'
if provenance.exists():shutil.copytree(provenance,out/'Provenance')
shutil.copytree(here,out/'Provenance/private-presentation',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(a.shared_assets/'observer-source',out/'Provenance/shared-observer')
shutil.copy2(here.parent/'engineering_shared.py',out/'Provenance/engineering_shared.py')
files={str(f.relative_to(out)).replace('\\','/'):sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
(out/'package-manifest.json').write_text(json.dumps({'files':files,'mutable_files':[n for n in files if '/game/' in n and n.endswith('.ini') and not n.endswith('/ddraw.ini')]},indent=2)+'\n')
with zipfile.ZipFile(out.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file():z.write(f,str(Path(out.name)/f.relative_to(out)))
print(out.with_suffix('.zip'))
