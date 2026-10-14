"""Launcher/package contracts and host fallback model; NOT PowerShell execution."""
import argparse,subprocess,tempfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('previous',type=Path);p.add_argument('--readobj',required=True);a=p.parse_args();root=a.package;old=a.previous
utility=root/'dual/game/DISPLAY-ASSIGN.exe'
resources=subprocess.check_output([a.readobj,'--coff-resources',str(utility)],text=True)
assert 'Type: MANIFEST (ID 24)' in resources and 'Name: (ID 1)' in resources
assert b'level="asInvoker" uiAccess="false"' in utility.read_bytes()
assert not (root/'dual/game/DISPLAY-SETUP.exe').exists()
old_resources=subprocess.check_output([a.readobj,'--coff-resources',str(old/'dual/game/DISPLAY-SETUP.exe')],text=True)
assert 'MANIFEST' not in old_resources
for mode in ('dual','control'):
 for f in (old/mode).rglob('*'):
  if f.is_file() and f.name!='DISPLAY-SETUP.exe':assert (root/mode/f.relative_to(old/mode)).read_bytes()==f.read_bytes(),str(f)
launch=(root/'Launch.ps1').read_text();collect=(root/'Collect-Results.ps1').read_text()
assert '-Verb RunAs' not in launch and '__COMPAT_LAYER' not in launch
assert 'NativeErrorCode' in launch and '$script:stage' in launch
assert 'Remove-Item' not in launch and 'Remove-Item' not in collect
assert collect.index('Copy-Item -LiteralPath')<collect.index('Add-Type -AssemblyName System.IO.Compression\n')<collect.index('[System.IO.Compression.ZipFile]::CreateFromDirectory')
assert 'Add-Type -AssemblyName System.IO.Compression.FileSystem' in collect
assert '$selected = $returnFolder' in collect and 'compression-status.txt' in collect
assert launch.index("'OBSERVER.exe'")<launch.index("'Collect-Results.ps1'")
# Bounded host model: success, missing core assembly, missing FileSystem, ZIP I/O
# failure. Validate raw preservation and return-folder payload at every failure.
for fault in ('none','core-assembly','filesystem-assembly','zip-write'):
 with tempfile.TemporaryDirectory(prefix='LF01 space ü ') as tmp:
  tmp=Path(tmp);original=tmp/'original.log';original.write_bytes(b'raw\r\n\x00diagnostic')
  folder=tmp/'RETURN-THIS-D04-P02B-LF01';folder.mkdir();copy=folder/'original.log';copy.write_bytes(original.read_bytes())
  if fault=='none':
   with zipfile.ZipFile(tmp/'result.zip','w') as z:z.write(copy,'original.log')
   with zipfile.ZipFile(tmp/'result.zip') as z:assert z.read('original.log')==original.read_bytes()
  else:assert not (tmp/'result.zip').exists()
  assert copy.read_bytes()==original.read_bytes()==b'raw\r\n\x00diagnostic'
print('PASS: embedded asInvoker, old missing manifest reproduced, unchanged game/wrapper/observer/helper, no elevation verb, stage/native error logging, copies-before-compression contract, four host fallback scenarios. Windows/PowerShell execution NOT performed.')
