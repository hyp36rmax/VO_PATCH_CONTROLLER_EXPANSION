"""Private startup-plan extension, guarded against exact upstream hook bytes."""
from pathlib import Path
import struct
import subprocess
import tempfile
HERE=Path(__file__).resolve().parent

def install(data,edition,v):
 data=bytearray(data);pe=v._PE(data)
 symbols={n:v.symbol_va(n,edition) for n in ('LOADLIB','GETPROC','GPAUSE','GRESUME','PRIMARY','BACK','INACTIVE','GAMEMODE','MODE','SUBMODE','HWND','CUSTOM1','DZTHR1','DEVICES','PEEKMSG','BINDS1','COND')}
 symbols.update(TWINBINDS=v.symbol_va(('TWIN','binds'),edition),HORIBINDS=v.symbol_va(('TWIN','horibinds'),edition),SECTION_VA=pe.base+pe.next_rva(),
  ORIGINAL_WNDPROC=v.symbol_va(('DEBUGBOX','hook'),edition),
  ORIGINAL_PUMP=v.symbol_va(('PADX','pump'),edition),
  ORIGINAL_IDLE=v.symbol_va(('ACTIVATE','idle'),edition),
  ORIGINAL_PRESENT=v.symbol_va(('TITLEVER','titlever'),edition),
  FRAME=0x5c6441 if edition.short=='retail' else 0x5c0d10,
  MOVIEFLAG=0x6bc598 if edition.short=='retail' else 0x6b82f8,
  ALLOWED=0x5c54a0 if edition.short=='retail' else 0x5bfd40)
 sites={k:v.site_in(o,edition) for k,o in (('wndproc',0x1c4d7e),('pump',0x1c530e),('idle',0x1c5412),('present',0x1c5900))}
 if data[sites['wndproc']:sites['wndproc']+4]==struct.pack('<I',v.symbol_va('ORIGWNDPROC',edition)):
  symbols['ORIGINAL_WNDPROC']=v.symbol_va('ORIGWNDPROC',edition)
 expected={'wndproc':struct.pack('<I',symbols['ORIGINAL_WNDPROC'])}
 for key in ('pump','idle','present'):
  at=v._va_at(pe,sites[key]);expected[key]=b'\xe8'+struct.pack('<i',symbols['ORIGINAL_'+key.upper()]-at-5)+(b'\x90' if key=='pump' else b'')
 if data[sites['pump']:sites['pump']+6]==b'\xff\x15'+struct.pack('<I',symbols['PEEKMSG']):
  symbols['ORIGINAL_PUMP']=0;expected['pump']=bytes(data[sites['pump']:sites['pump']+6])
 if data[sites['present']:sites['present']+5]==b'\xa1'+struct.pack('<I',symbols['PRIMARY']):
  symbols['ORIGINAL_PRESENT']=0;expected['present']=bytes(data[sites['present']:sites['present']+5])
 for key,offset in sites.items():
  if data[offset:offset+len(expected[key])]!=expected[key]:raise ValueError('Overlay hook identity mismatch: '+key)
 with tempfile.TemporaryDirectory() as td:
  binary=Path(td)/'entry.bin'
  subprocess.run(['nasm','-f','bin',*(f'-D{k}={x}' for k,x in symbols.items()),'-o',str(binary),str(HERE/'entry.asm')],check=True)
  blob=binary.read_bytes()
 entries=dict(zip(('wndproc','pump','idle','present','context'),struct.unpack_from('<5I',blob)))
 address,offset=v.add_section(data,len(blob),blob,name=b'.vouo')
 assert address==symbols['SECTION_VA']
 patches=[]
 for key,off in sites.items():
  new=struct.pack('<I',entries[key]) if key=='wndproc' else b'\xe8'+struct.pack('<i',entries[key]-v._va_at(pe,off)-5)+(b'\x90' if key=='pump' else b'')
  data[off:off+len(new)]=new;patches.append(dict(name=key,offset=off,before=expected[key].hex(),after=new.hex()))
 # Only the already linked helper-name literals change. The original helper
 # remains installed; the private shim forwards its API without reassignment.
 old=b'vontanita.dll\0';new=b'voinputux.dll\0';assert len(old)==len(new)
 pos=0
 while True:
  at=data.find(old,pos)
  if at<0:break
  patches.append(dict(name='input-forwarder',offset=at,before=old.hex(),after=new.hex()))
  data[at:at+len(old)]=new;pos=at+len(old)
 return bytes(data),dict(symbols=symbols,entries=entries,patches=patches,raw=offset)
