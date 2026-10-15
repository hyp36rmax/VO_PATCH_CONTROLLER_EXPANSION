"""Consent, lifecycle, retained evidence and explicit-export contract."""
from pathlib import Path
import tempfile,json,zipfile
from unittest.mock import patch
import normal_lifecycle as n
import diagnostics as d
with tempfile.TemporaryDirectory(prefix='VO privacy ') as td:
 root=Path(td);cfg=root/'player-displays.ini'
 def choose(value):cfg.write_text('[Diagnostics]\nLevel='+value+'\n')
 hardware=lambda:{'controllers':[{'vid':8015,'pid':36865,'serial':'secret'}],'displays':[{'width':2560,'height':1440}],'available':True}
 for bad in (None,'invalid','4','normal',''):
  if bad is None:cfg.unlink(missing_ok=True)
  else:choose(bad)
  with patch.object(n.discovery,'snapshot',side_effect=AssertionError('Off observer')):
   assert n.run(root,lambda:(_ for _ in ()).throw(AssertionError('Off wait')),lambda:None,snapshot=hardware) is None
  assert not (root/'diagnostics').exists()
  d.event(root,'startup');assert not (root/'diagnostics').exists()
  try:d.export(root)
  except ValueError:pass
  else:raise AssertionError('empty export')
 for level in ('NORMAL','DETAILED','DEVELOPMENT'):
  choose(level);steps=[]
  def ready():
   assert d.safe_events(root/'diagnostics/events.jsonl')[-1]['event'] in d.EVENTS
   steps.append('ready')
  def wait():assert steps==['ready'];steps.append('exit');return 7
  n.run(root,wait,ready,environ={'VO_EX_EFFECTIVE_MODE':'0','VO_EX_FALLBACK':'4'},snapshot=hardware)
  assert steps==['ready','exit'];assert not list(root.glob('*.zip'))
  rows=d.safe_events(root/'diagnostics/events.jsonl')
  assert rows[-1]['fields']['exit_code']==7
  if level=='NORMAL':assert {r['event'] for r in rows}<={'startup','shutdown','recovery'}
  if level=='DETAILED':assert any(r['event']=='controller_discovery' for r in rows)
  if level=='DEVELOPMENT':assert any(r['event']=='movie' for r in rows)
  assert d.level(root)==d.LEVELS.index(level)
 choose('OFF');before=(root/'diagnostics/events.jsonl').read_bytes()
 for name in d.EVENTS:d.event(root,name,{'code':3})
 assert (root/'diagnostics/events.jsonl').read_bytes()==before
 with patch.object(n,'movie_state',side_effect=AssertionError('Off sample')):
  assert n.sample(root,snapshot=lambda:(_ for _ in ()).throw(AssertionError('Off discovery'))) is None
 result=d.export(root,game_directory=root,return_name=n.RETURN)
 with zipfile.ZipFile(result) as z:
  assert z.testzip() is None
  assert b'secret' not in b''.join(z.read(x) for x in z.namelist())
 old=result.read_bytes()
 with patch.object(d.zipfile,'ZipFile',side_effect=OSError('disk failure')):
  try:d.export(root,game_directory=root,return_name=n.RETURN)
  except OSError:pass
  else:raise AssertionError('export failure hidden')
 assert result.read_bytes()==old and (root/'diagnostics/events.jsonl').read_bytes()==before
 choose('NORMAL');(root/'diagnostics/session-active').write_text('interrupted')
 n.run(root,lambda:0,lambda:None,snapshot=hardware)
 assert any(r['event']=='previous_session_incomplete' for r in d.safe_events(root/'diagnostics/events.jsonl'))
 choose('DETAILED');(root/'v_on.ini').write_text('1P Device No.=2\nPassword=secret\n')
 prior=n.sample(root,snapshot=hardware);before=(root/'diagnostics/events.jsonl').read_bytes()
 assert n.sample(root,prior,snapshot=hardware)==prior
 assert (root/'diagnostics/events.jsonl').read_bytes()==before
 (root/'v_on.ini').write_text('1P Device No.=3\n');n.sample(root,prior,snapshot=hardware)
 assert any(r['fields'].get('device')==3 for r in d.safe_events(root/'diagnostics/events.jsonl'))
print('PASS default/missing/invalid Off, no observer/files/export, levels, persisted consent, disabled collection, retained logs, explicit sanitized export, failed export, recovery and assignment changes')

with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 for encoding in ('utf-8-sig','utf-16'):
  (root/'player-displays.ini').write_bytes('[diagnostics]\nlevel=DETAILED\n'.encode(encoding))
  assert d.level(root)==2
print('PASS existing Windows Unicode INI and case-insensitive section/key compatibility')
