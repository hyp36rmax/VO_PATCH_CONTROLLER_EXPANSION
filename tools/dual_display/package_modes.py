"""Self-contained F04 UAT: one game/configuration directory, immutable profiles."""
import argparse,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
import mode_profiles
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('pristine',type=Path);p.add_argument('wrapper',type=Path);p.add_argument('output',type=Path);p.add_argument('--cc',required=True);p.add_argument('--windres',required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(a.baseline/'dual/game',out/'game',ignore=shutil.ignore_patterns('v_on.exe','player-displays.ini','DISPLAY-ASSIGN.exe','D04-P02B-presentation.log'))
shutil.copy2(a.wrapper/'ddraw.dll',out/'game/ddraw.dll')
(out/'profiles').mkdir();records=[]
for profile in mode_profiles.PROFILES:
 data,meta=mode_profiles.build(a.pristine.read_bytes(),profile);records.append(meta);(out/'profiles'/f'{profile}.exe').write_bytes(data)
# Fresh install has no preferences. Existing configurations at game/player-displays.ini
# are authoritative and are never replaced by the launcher.
obj=out/'manifest.o';subprocess.run([a.windres,str(here/'displays.rc'),str(obj)],cwd=here,check=True)
subprocess.run([a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-municode',str(here/'mode_select.c'),str(obj),'-luser32','-Wl,--no-insert-timestamp','-o',str(out/'game/DISPLAY-MODES.exe')],check=True);obj.unlink()
subprocess.run([__import__('sys').executable,str(here.parent/'movie_observer/build.py'),str(out),'--cc',a.cc,'--windres',a.windres],check=True)
(out/'observer-res.o').unlink()
for n in ('LaunchModes.ps1','Collect-Modes.ps1'):shutil.copy2(here/n,out/n)
for entry in ('single','dual'):
 (out/f'START-{entry.upper()}-DISPLAY.cmd').write_bytes(('@echo off\r\nsetlocal\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0LaunchModes.ps1" -Entry '+entry+'\r\nif errorlevel 1 pause\r\n').encode())
(out/'READ-ME.txt').write_text('''D04-P05-F04 PRIVATE WINDOWS ACCEPTANCE — physical validation pending

Extract the whole ZIP. Run START-SINGLE-DISPLAY.cmd.
Both launchers open the same saved display settings; neither overrides them.
Fresh installation defaults to Single Display and Widescreen (16:9).
Choose Single Display / Widescreen for the first test, then Launch.
On a 2560x1440 desktop the initial game profile is 1920x1080, not 3840x1080.
F4 and existing saved game settings may select the profile's upstream alternate.

Check centered, full-frame movie proportions (including its original black bars),
audio and skip. Check menu, Solo, original Local VS horizontal/vertical options,
controllers, focus/minimize/restore, return to menu and clean exit.

Run START-DUAL-DISPLAY.cmd. Choose Dual Display — Versus, assign two different
monitors, then Launch. Check centered movie on Display 1, black Display 2,
mirrored selection, independent P1/P2 gameplay, mixed-resolution scaling,
return to menu and shutdown. Optional: Dual Display — Mirror.

Optional single-player checks: Ultrawide (21:9), Super-ultrawide (32:9).
These reuse existing single-player profiles; expanded ultrawide Local VS is
not added. Use Widescreen or Original for ordinary single-display Local VS.
Original (4:3) uses original 640x480 rendering with the existing non-hires
patches; it does not install the native-widescreen F4 resolution toggle.
The widescreen/ultrawide profiles retain their existing F4/F5 controls.

Settings are stored once in game/player-displays.ini; controller/game settings
remain in the same game directory across all profiles. Display/profile fallback
is recorded in selection.txt and does not erase saved preferences.
If dual rendering fails after launch, F03C's original composed-window fallback
is retained for that session. Exit and select Single Display to change profile;
no second game or automatic restart is launched.

After each exit results are collected automatically. Return the selected
RETURN-THIS-D04-P05-F04.zip with observations for both modes. All runs are retained.
If ZIP compression fails, return its equally named folder with raw logs.
No administrator privileges, compilation, INI edits or DLL copying are required.
Do not change Windows display modes. Internal rendering is separate from desktop.
''')
provenance=out/'Provenance';shutil.copytree(here,provenance/'dual_display',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(here.parent/'movie_observer',provenance/'movie_observer',ignore=shutil.ignore_patterns('__pycache__'))
if (a.baseline/'Provenance').exists():shutil.copytree(a.baseline/'Provenance',provenance/'baseline')
record={'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=here,text=True).strip(),'profiles':records,'wrapper':json.loads((a.wrapper/'private-build.json').read_text()),'movie_sha256':sha(out/'game/von.avi'),'physical':'NEEDS VALIDATION','configuration':'game/player-displays.ini'}
(out/'build-record.json').write_text(json.dumps(record,indent=2)+'\n')
files={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and not(f.parent==out/'game' and f.suffix.lower()=='.ini' and f.name!='ddraw.ini')}
(out/'package-manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
with zipfile.ZipFile(out.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file():z.write(f,str(Path(out.name)/f.relative_to(out)))
print(out.with_suffix('.zip'))
