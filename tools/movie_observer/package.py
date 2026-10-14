"""Package untouched F02 game assets with an external normal-launch observer."""
import argparse,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('binary',type=Path);p.add_argument('output',type=Path);p.add_argument('--assignment-evidence',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
shutil.copytree(a.baseline/'dual/game',out/'game')
# Preserve the owner's last returned assignment; do not open setup or alter displays.
with zipfile.ZipFile(a.assignment_evidence) as z:
 names=[n for n in z.namelist() if n.replace('\\','/').endswith('/dual/game/player-displays.ini')]
 assert len(names)==1
 (out/'game/player-displays.ini').write_bytes(z.read(names[0]))
shutil.copy2(a.binary,out/'MOVIE-OBSERVER.exe')
for n in ('Launch.ps1','Collect-Results.ps1'):shutil.copy2(here/n,out/n)
(out/'START-MOVIE-OBSERVATION.cmd').write_bytes(b'@echo off\r\nsetlocal\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch.ps1"\r\nif errorlevel 1 pause\r\n')
(out/'READ-ME.txt').write_text('''PRIVATE F03B MOVIE WINDOW OBSERVATION — Windows observation pending

1. Extract the ZIP completely.
2. Run START-MOVIE-OBSERVATION.cmd normally.
3. Let the movie start, wait about 10 seconds, then skip normally.
4. Confirm the main menu appears and exit the game.
5. Return the automatically selected RETURN-THIS-D04-P05-F03B.zip.

No display changes, controller remapping, INI editing or administrator rights.
The previously returned display assignment is included. The F02 game, movie,
wrapper and helper are unchanged. This package does not fix the invisible movie.
Window metadata cannot prove that decoded pixels are visible or identify the
native decoder's drawing API. Sampling lasts until game exit, bounded to one
hour / 16 MiB; exhaustion is logged. Short-lived windows may fall between samples.
Times are observations, not inferred movie/menu state changes.
If compression fails, raw logs and the return folder remain beside this launcher.
''')
record={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=here,text=True).strip(),'baseline_head':'81f1eae4dfcfbb5698ac98b971e9071c96af8a15','observer_sha256':sha(a.binary),'assignment_evidence_sha256':sha(a.assignment_evidence),'baseline_game_files':{str(f.relative_to(a.baseline/'dual/game')):sha(f) for f in (a.baseline/'dual/game').rglob('*') if f.is_file()},'physical':'NEEDS VALIDATION'}
(out/'build-record.json').write_text(json.dumps(record,indent=2)+'\n')
shutil.copytree(here,out/'observer-source',ignore=shutil.ignore_patterns('__pycache__'))
files={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()}
(out/'package-manifest.json').write_text(json.dumps({'files':files,'mutable_files':[n for n in files if n.startswith('game/') and n.endswith('.ini') and n!='game/ddraw.ini']},indent=2)+'\n')
with zipfile.ZipFile(out.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in out.rglob('*'):
  if f.is_file():z.write(f,str(Path(out.name)/f.relative_to(out)))
print(out.with_suffix('.zip'))
