"""Exercise packaged upstream UI backend plus transactional Experience ownership."""
import importlib.util,sys,tempfile,shutil,hashlib
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
package=Path(sys.argv[1]).resolve();sys.path.insert(0,str(package/'_internal'))
import normal_install as adapter

def module():
 spec=importlib.util.spec_from_file_location('private_patcher_test',package/'_internal/v-on-patcher.py')
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

def snapshot(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
for source in map(Path,sys.argv[2:]):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td).resolve()/'game';shutil.copytree(source,root)
  (root/'ddraw.dll').write_bytes(b'pre-existing user wrapper')
  (root/'unrelated.txt').write_bytes(b'keep me')
  (root/'experience-runtime').mkdir();(root/'experience-runtime/user-notes.txt').write_text('keep too')
  original=snapshot(root);v=module();p=v.Patcher();assert p.load(str(root/'v_on.exe'))[1]
  for wanted in (v.default_state(),dict(v.default_state(),hires=False,nodisc=False,debugbox=False,movie=False,credits=False)):
   ok,log=p.apply(wanted);assert ok,log
   assert (root/'vodisplay.dll').is_file() and (root/'EXPORT-DIAGNOSTICS.cmd').is_file()
   assert (root/adapter.JOURNAL/'ownership.json').is_file()
   assert not p.apply(wanted)[0]
   assert not p.load(str(root/'v_on.exe'))[1]
   # Restore remains available after loading the integrated executable.
   assert p.can_restore();log=p.restore()
   for name,data in original.items():assert (root/name).read_bytes()==data,(name,log)
   assert not (root/'vodisplay.dll').exists();assert not (root/adapter.JOURNAL).exists()
   assert not (root/'experience-runtime/normal_lifecycle.py').exists()
   p.restore();assert p.load(str(root/'v_on.exe'))[1]
  before=snapshot(root);real=adapter.atomic;failed=[False]
  def injected(path,data):
   if Path(path)==root/'vodisplay.dll' and not failed[0]:failed[0]=True;raise OSError('injected runtime write failure')
   return real(path,data)
  with patch.object(adapter,'atomic',injected):
   ok,log=p.apply(v.default_state());assert not ok and failed[0],log
  assert snapshot(root)==before,'failed Apply did not roll back exactly'
  assert p.load(str(root/'v_on.exe'))[1]
  ok,log=p.apply(v.default_state());assert ok,log
  (root/'experience-runtime/user-notes.txt').write_text('user changed unrelated note')
  (root/'vodisplay.dll').write_bytes(b'user replacement')
  log=p.restore();assert (root/'vodisplay.dll').read_bytes()==b'user replacement'
  assert (root/'experience-runtime/user-notes.txt').read_text()=='user changed unrelated note'
  assert any('preserved modified vodisplay.dll' in row for row in log)
  assert (root/'v_on.exe').read_bytes()==original['v_on.exe']
  print('PASS',source.name,'Apply/Restore/reapply, selected options, patch-over refusal, exact failure rollback, unrelated and modified-file preservation',flush=True)
