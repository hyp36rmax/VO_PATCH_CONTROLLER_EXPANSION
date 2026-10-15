"""Reproducible private overlay DLL build; no installation or publication."""
from pathlib import Path
import argparse,subprocess
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--cc',required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;a.output.mkdir(parents=True,exist_ok=True)
for name,sources in (('vooverlay',('runtime.c','render.c','paused.c','pages.c','native_settings.c','controller_settings.c')),('voinputux',('input_bridge.c','../../input/tanita.c'))):
 subprocess.run([a.cc,'-shared','-O2','-Wall','-Wextra','-Werror','-Wl,--kill-at','-Wl,--no-insert-timestamp','-s',*[str(here/s) for s in sources],'-o',str(a.output/(name+'.dll')),'-lgdi32','-luser32','-lhid','-lsetupapi'],check=True)
import hashlib,json
source_names=('runtime.c','runtime.h','render.c','paused.c','model.h','input_bridge.c','build.py','pages.c','pages.h','native_settings.c','native_settings.h','controller_settings.c','controller_settings.h','ini_transaction.h','direct_input.h','../../input/controller.c','../../input/controller_logic.h','../../input/tanita.c','../../input/tanita_map.h','../../input/raphnet_map.h','../../input/twinstick_state.h')
manifest={'milestone':'UX01-P02-F04','sources':{n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in source_names},'files':{n:hashlib.sha256((a.output/n).read_bytes()).hexdigest() for n in ('vooverlay.dll','voinputux.dll')}}
(a.output/'overlay-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
