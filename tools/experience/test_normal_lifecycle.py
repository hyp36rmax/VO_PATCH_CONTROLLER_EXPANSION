"""Passive lifecycle ordering/failure/privacy tests; Windows attachment is UAT."""
from pathlib import Path
import tempfile,json,zipfile
from unittest.mock import patch
import normal_lifecycle as n
import diagnostics as d
assert n.RETURN=="RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip"
with tempfile.TemporaryDirectory() as td:
 root=Path(td);steps=[]
 (root/'v_on.ini').write_text('ScrSize=3\nPassword=do-not-export\n')
 def ready():
  rows=d.safe_events(root/'diagnostics/events.jsonl');assert rows[0]['event']=='startup'
  steps.append('ready')
 def wait():assert steps==['ready'];steps.append('exit');return 7
 env={'VO_EX_REQUESTED_MODE':'2','VO_EX_EFFECTIVE_MODE':'0','VO_EX_PROFILE':'1','VO_EX_FALLBACK':'4'}
 hardware=lambda:{'controllers':[{'vid':8015,'pid':36865,'serial':'private'}],'displays':[{'width':2560,'height':1440}],'available':True}
 result=n.run(root,wait,ready,environ=env,snapshot=hardware)
 assert result.name==n.RETURN and steps==['ready','exit']
 assert not (root/'diagnostics/session-active').exists()
 with zipfile.ZipFile(result) as z:
  assert z.testzip() is None
  rows=json.loads(z.read('events.json'))
  assert rows[-1]['fields']['exit_code']==7
  assert any(r['fields'].get('split_preference')==2 for r in rows)
  assert any(r['fields'].get('effective_mode')==0 for r in rows)
  payload=b''.join(z.read(x) for x in z.namelist())
  assert b'do-not-export' not in payload and b'private' not in payload
 old=result.read_bytes()
 with patch.object(d.zipfile,'ZipFile',side_effect=OSError('disk failure')):
  try:n.run(root,lambda:0,lambda:None,environ=env,snapshot=hardware)
  except OSError:pass
  else:raise AssertionError('export failure hidden')
 assert result.read_bytes()==old
 assert (root/'RETURN-THIS-VO-PATCH-EX-F01-P04-F02.txt').is_file()
 assert (root/'diagnostics/events.jsonl').is_file()
 (root/'diagnostics/session-active').write_text('interrupted')
 n.run(root,lambda:0,lambda:None,environ={},snapshot=hardware)
 assert any(r['event']=='previous_session_incomplete' for r in d.safe_events(root/'diagnostics/events.jsonl'))
 for level,expected in [('DETAILED',1),('DEVELOPMENT',2),('invalid',0)]:
  n.run(root,lambda:0,lambda:None,environ={'VO_EX_DIAGNOSTICS':level},snapshot=hardware)
  starts=[r for r in d.safe_events(root/'diagnostics/events.jsonl') if r['event']=='startup']
  assert starts[-1]['fields']['level']==expected
print('PASS startup before readiness, exit/export ordering, selected/effective fields, saved split, privacy, failed export recovery and interrupted-session evidence')
