"""Host model, binary capability and package integrity checks; not Windows acceptance."""
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('--readobj',required=True);a=p.parse_args();here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as d:
 exe=Path(d)/'test';subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(here/'test_model.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
root=a.package;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();m=json.loads((root/'package-manifest.json').read_text());record=json.loads((root/'build-record.json').read_text())
for n,h in m['files'].items():assert sha(root/n)==h,n
for n,h in record['baseline_game_files'].items():assert sha(root/'game'/n)==h,n
binary=(root/'MOVIE-OBSERVER.exe').read_bytes();assert b'PerMonitorV2' in binary
assert b'asInvoker' in binary and b'requireAdministrator' not in binary
imports=subprocess.check_output([a.readobj,'--file-headers','--coff-imports',str(root/'MOVIE-OBSERVER.exe')],text=True)
assert 'IMAGE_FILE_MACHINE_I386' in imports
for name in ('EnumWindows','EnumChildWindows','GetGUIThreadInfo','GetWindow','GetWindowRect','GetClientRect','GetMonitorInfoW','CreateProcessW','WaitForSingleObject','CloseHandle'):assert re.search(r'\b'+name+r'\b',imports),name
for name in ('WriteProcessMemory','ReadProcessMemory','SetWindowPos','MoveWindow','SetWindowLong','SetParent','SetWindowsHookEx','ChangeDisplaySettings','SendInput','DebugActiveProcess','TerminateProcess'):
 assert name not in imports,name
source=(here/'observer.c').read_text()
assert 'CreateProcessW(exe,cmd,NULL,NULL,FALSE,0,NULL,dir,&si,&pi)' in source
assert source.index('if(fflush(logfile)||io_error)')<source.index('CreateProcessW(exe,cmd')
assert 'WaitForSingleObject(pi.hProcess,250)' in source and 'CloseHandle(pi.hProcess)' in source and 'CloseHandle(pi.hThread)' in source
assert 'if(ok&&!overflow)' in source and 'rank_>=1024' in source
assert 'swprintf(cmd,32768,L"\\\"%ls\\\"",exe)' in source
assert 'GetGUIThreadInfo(w.tid' in source # target GUI thread, not external observer's active window
launch=(root/'Launch.ps1').read_text();assert '-Wait -PassThru' in launch and '-Verb' not in launch and 'DISPLAY-ASSIGN' not in launch
collector=(root/'Collect-Results.ps1').read_text();assert collector.index('Copy-Item')<collector.index('Add-Type') and 'OpenRead($temporary)' in collector and 'movie-windows.log' in collector
assert b'\r\n' in (root/'START-MOVIE-OBSERVATION.cmd').read_bytes()
with zipfile.ZipFile(root.with_suffix('.zip')) as z:
 assert z.testzip() is None
 with tempfile.TemporaryDirectory(prefix='VO movie observer space ü ') as d:
  z.extractall(d)
  for n,h in m['files'].items():assert sha(Path(d)/root.name/n)==h
print('PASS unchanged F02 game/assets/helper/wrapper hashes; read-only observation imports; ordinary-user manifest; normal explicit-path launch; bounded/process-exit contracts; raw-first collector and relocated paths/ZIP integrity. Windows API execution NEEDS VALIDATION.')
