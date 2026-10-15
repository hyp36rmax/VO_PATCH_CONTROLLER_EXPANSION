"""Compare overlay bookkeeping text to original Windows bookkeeping pages."""
from pathlib import Path
import sys,subprocess,tempfile,struct,re
from test_direct_settings import DirectMachine
from unicorn import x86_const as r
class ScoresMachine(DirectMachine):
 def hook(self,u,a,size,data):
  name=self.imports.get(a);sp=u.reg_read(r.UC_X86_REG_ESP)
  if name=='wsprintfA':
   dest,fmt=struct.unpack('<2I',u.mem_read(sp+4,8));fmt=self.string(fmt);args=[]
   for i,t in enumerate(re.findall(r'%(?:[0-9]+)?[sdu]',fmt)):
    value=struct.unpack('<I',u.mem_read(sp+12+i*4,4))[0];args.append(self.string(value) if t.endswith('s') else value)
   text=fmt%tuple(args);u.mem_write(dest,text.encode()+b'\0');self.return_(len(text),0);return
  if name=='SetDlgItemTextA':
   _,id,text=struct.unpack('<3I',u.mem_read(sp+4,12));self.texts[id]=self.string(text);self.return_(1,3);return
  return super().hook(u,a,size,data)
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 dll=Path(td)/'direct.dll';cc=here.parents[1]/'../llvm-mingw-20260908-ucrt-macos-universal/bin/i686-w64-mingw32-clang'
 subprocess.run([str(cc.absolute()),'-shared','-O2','-Wl,--export-all-symbols','-Wl,--image-base,0x60000000',str(here/'native_settings.c'),'-o',str(dll),'-luser32'],check=True)
 for path in sys.argv[1:]:
  m=ScoresMachine(path);m.load(dll);j=m.ed.short=='jpre';state=0x10040000;mode=0x1adcdf0 if j else 0x1ae3594;ptr=0x1cdca64 if j else 0x1ce1dbc
  assert m.ccall('vo_native_begin',state,1,mode,5)
  scratch=state+12;m.word(ptr,scratch)
  for i in range(10):
   m.u.mem_write(scratch+0x14c+8*i,bytes([65+i,124,90,i])+struct.pack('<I',0xffffffff if i==9 else i*3900+31))
   m.u.mem_write(scratch+0x19c+12*i,bytes([65+i,124,90,i])+struct.pack('<2I',i*5,i))
   m.word(scratch+0xac+16*i,(i*7)%11)
  for group,(proc,base,count) in enumerate(zip((0x51c920,0x51cb24,0x51ccd3) if j else (0x5205b0,0x5207b4,0x520963),(1130,1101,1121),(10,10,8))):
   m.texts={};m.call(proc,(1,0x110,0,0))
   for i in range(count):
    assert m.ccall('vo_native_score',state,group,i,0x10060000,256)
    assert m.string(0x10060000)==m.texts[base+i],(j,group,i,m.string(0x10060000),m.texts[base+i])
  assert m.ccall('vo_native_defaults',state)
  assert bytes(m.u.mem_read(scratch+0xac,0xa0))==bytes(0xa0)
  assert bytes(m.u.mem_read(scratch+0x14c,0x50))==bytes(m.u.mem_read(0x5f35e8 if j else 0x601d08,0x50))
  assert bytes(m.u.mem_read(scratch+0x19c,0x78))==bytes(m.u.mem_read(0x5f3638 if j else 0x601d58,0x78))
  print(m.ed.short,'PASS all 28 direct bookkeeping rows match original pages; original Clear records preserved')
