"""Automatic export lifecycle with process-wait doubles; native wait remains UAT."""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile
import collect_process as c
import diagnostics as d

with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 (root/'v_on.ini').write_text('ScrSize=3\nSSHoriz=0\nPassword=never-export\n')
 (root/'player-displays.ini').write_text('[Presentation]\nMode=2\nGameAspect=3\n[Players]\nPlayer1=private-monitor-identity\n')
 d.event(root,'configuration',{'selected_mode':2,'effective_mode':0,'profile':3,'secondary':1,'f4_state':0,'split_preference':2,'restart_required':True,'raw_input':'forbidden'})
 def exited(pid):
  assert pid==123
  return 0
 result=c.collect(root,123,wait=exited)
 assert result.name==c.RETURN
 with zipfile.ZipFile(result) as z:
  assert z.testzip() is None
  payload=''.join(z.read(n).decode() for n in z.namelist())
  assert 'never-export' not in payload and 'private-monitor-identity' not in payload and 'raw_input' not in payload
  cfg=json.loads(z.read('configuration.json'));assert cfg['v_on.ini']['scrsize']==3
  events=json.loads(z.read('events.json'));assert events[-1]['event']=='shutdown' and events[-1]['fields']['exit_code']==0
  assert events[0]['fields']['effective_mode']==0 and events[0]['fields']['selected_mode']==2
 previous=result.read_bytes();raw=(root/'diagnostics/events.jsonl').read_bytes()
 with patch.object(d.zipfile,'ZipFile',side_effect=OSError('compression unavailable')):
  try:c.collect(root,123,wait=exited)
  except OSError:pass
  else:raise AssertionError('compression failure hidden')
 assert result.read_bytes()==previous and (root/'diagnostics/events.jsonl').read_bytes().startswith(raw)
 def unavailable(pid):raise OSError('already exited')
 c.collect(root,123,wait=unavailable)
 with zipfile.ZipFile(result) as z:
  events=json.loads(z.read('events.json'));assert any(e['fields'].get('exit_known') is False for e in events)
print('PASS process-exit export, direct installed-game configuration, numeric state allowlist, unavailable-process reporting and raw/prior-archive preservation on compression failure')
