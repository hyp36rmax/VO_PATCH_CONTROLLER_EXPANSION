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
for entry,label in (('single','SINGLE-DISPLAY'),('versus','DUAL-VERSUS'),('mirror','DUAL-MIRROR')):
 (out/f'START-{label}.cmd').write_bytes(('@echo off\r\nsetlocal\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0LaunchModes.ps1" -Entry '+entry+'\r\nif errorlevel 1 pause\r\n').encode())
(out/'READ-ME.txt').write_text("""D04-P05-F04B COMPLETE MIRROR UAT — physical acceptance pending
Mirror uses the selected Single profile and copies its entire final framebuffer.

Extract the ZIP. Three explicit SESSION-ONLY tests:
START-SINGLE-DISPLAY.cmd — Single Display
START-DUAL-VERSUS.cmd — independent P1/P2 gameplay
START-DUAL-MIRROR.cmd — complete Single presentation on both displays

Each launcher fixes its requested mode. Review monitor/aspect selections and
click Launch. Session changes never overwrite saved display preferences.
Dual tests require two separate active displays and the dual profile. If not
available, setup explicitly reports Single Display fallback before launching its
original Local VS profile. Saved dual preferences remain unchanged.
The temporary session file is collected for diagnostics, then discarded.

Single: use Widescreen (16:9) on your 2560x1440 desktop. Check movie centering,
audio/skip, menu, Solo, original Local VS, controller input and exit.
Versus: check movie only on Display 1, black Display 2, mirrored selection,
independent gameplay, return to menu and exit.
Mirror: check shared selection, the full P1/P2 split-screen on both displays, aspect and exit.
Also check focus/minimize/restore. Optional 21:9/32:9 profiles remain single-player.

MOVIE LIMIT: F04 playback is deliberately preserved. The complete 320x240 AVI
frame is 4:3 and already maximally fitted on a 16:9 monitor. Its central 16:9
picture includes embedded black bars. Enlarging that picture to fill the monitor
would crop part of the original frame or distort it, both prohibited in F04B.
This package does not claim a movie enlargement. Actual physical pixel size
remains to be compared with the calculated destination in the collected log.

Original 4:3 uses original 640x480 rendering without the native-widescreen F4
toggle. Widescreen/ultrawide retain their existing F4/F5 behavior. Controller
settings remain shared and unchanged. No expanded 21:9 Local VS is added.

After each exit, results are collected and selected automatically. Return
RETURN-THIS-D04-P05-F04B.zip with observations for all three modes. Raw copies
survive ZIP compression failure. No administrator privileges, INI edits,
manual DLL copies, compilation or Windows display-mode changes are needed.
""")

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
