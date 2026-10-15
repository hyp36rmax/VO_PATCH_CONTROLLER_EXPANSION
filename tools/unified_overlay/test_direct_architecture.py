"""Guard overlay UI ownership and the single existing input authority."""
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ('native_settings.c','controller_settings.c','pages.c'):
 s=(p/name).read_text()
 for token in ('CreateDialog','DialogBox','SendDlgItem','WM_INITDIALOG','CB_GET','CB_SET','CreateWindow','VonSelectController','VonCaptureInput','keybd_event','SendInput'):
  assert token not in s,(name,token)
s=(p/'direct_input.h').read_text()
for token in ('DialogBox','CreateWindow','LoadLibrary','XInputGetState','SetupDi','HidD_'):
 assert token not in s,token
for token in ('von_claim(owners','von_start_edge','von_capture','source_start(','raw_state('):assert token in s
bridge=(p/'input_bridge.c').read_text();assert '#include "../../input/controller.c"' in bridge
assert '"../../input/tanita.c"' not in bridge  # compiled exactly once by build.py
build=(p/'build.py').read_text();assert "'../../input/tanita.c'" in build
assert 'vo_pages_capture_active()' in (p/'runtime.c').read_text()
print('PASS no dialog automation/F-key simulation in direct settings paths; overlay capture reuses original readers/ownership; legacy F-key entry points retained')
