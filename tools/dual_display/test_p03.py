"""P03 preservation gates: retain P2 draw path and LF01 launch corrections."""
from pathlib import Path
import argparse,subprocess
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('previous',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
old=subprocess.check_output(['git','show','d33104b:tools/dual_display/presentation.h'],cwd=here,text=True)
new=(here/'presentation.h').read_text()
# All resource initialization, source geometry, GPU work, Present order, generation
# accounting, reset, cleanup and logs remain exact; only window visibility changes.
assert new[new.index('static BOOL vo_dual_init'):]==old[old.index('static BOOL vo_dual_init'):]
assert new[new.index('static LRESULT CALLBACK vo_output_proc'):new.index('/* EnumWindows')]==old[old.index('static LRESULT CALLBACK vo_output_proc'):old.index('static void vo_dual_visibility')]
assert 'i == 0 ? HWND_TOPMOST : HWND_TOP' in new
assert 'EnumWindows(vo_p1_order' in new
for mode in ('dual','control'):
 for f in (a.previous/mode).rglob('*'):
  if f.is_file() and not (mode=='dual' and f.name=='ddraw.dll'):
   assert (a.package/mode/f.relative_to(a.previous/mode)).read_bytes()==f.read_bytes(),str(f)
assert (a.package/'Launch.ps1').read_bytes()==(a.previous/'Launch.ps1').read_bytes()
assert b'level="asInvoker"' in (a.package/'dual/game/DISPLAY-ASSIGN.exe').read_bytes()
collect=(a.package/'Collect-Results.ps1').read_text();assert 'RETURN-THIS-D04-P03' in collect
assert collect.index('Copy-Item')<collect.index('Add-Type') and 'Remove-Item' not in collect
print('PASS: P1-only stacking edit; P2 resource/geometry/draw/generation path exact; game, control, INI, helper, observer, assignment utility and LF01 launcher preserved; raw-log fallback retained')
