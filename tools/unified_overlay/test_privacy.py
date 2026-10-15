"""Existing diagnostics consent, bounds and explicit sanitized overlay export."""
from pathlib import Path
import json,sys,tempfile,zipfile
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'experience'));import diagnostics as d
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 d.event(root,'overlay_lifecycle',{'code':1});assert not (root/'diagnostics').exists()
 (root/'player-displays.ini').write_text('[Diagnostics]\nLevel=OFF\n')
 d.event(root,'overlay_lifecycle',{'code':1});assert not (root/'diagnostics').exists()
 for level in ('NORMAL','DETAILED','DEVELOPMENT'):
  (root/'player-displays.ini').write_text('[Diagnostics]\nLevel='+level+'\n')
  d.event(root,'overlay_lifecycle',{'code':1,'buttons':65535,'raw_axis':32767,'path':'private'})
 log=root/'diagnostics/events.jsonl';rows=d.safe_events(log)
 assert len(rows)==3 and all(r=={'event':'overlay_lifecycle','fields':{'code':1}} for r in rows)
 before=log.read_bytes();(root/'player-displays.ini').write_text('[Diagnostics]\nLevel=OFF\n')
 d.event(root,'overlay_lifecycle',{'code':2});assert log.read_bytes()==before
 assert not list(root.glob('*.zip'))
 archive=d.export(root)
 with zipfile.ZipFile(archive) as z:assert json.loads(z.read('events.json'))==rows
native=(here.parent/'dual_display/f5_dialog.c').read_text()
assert 'if(vo_diagnostic_level()<1||code<1||code>11)return;' in native
assert 'size.QuadPart+n<=256*1024' in native
runtime=(here/'runtime.c').read_text()
assert 'fopen(' not in runtime and 'WriteFile(' not in runtime and 'Upload' not in runtime
print('PASS overlay default/explicit Off, all enabled levels, immediate Off retention, numeric lifecycle only, bounded native sink, explicit sanitized export')
