"""Execute the compiled 32-bit adapter together with original Retail/JPRE F7.
Win32 files/windows are fault-injectable doubles, not physical Windows UAT.
"""
from pathlib import Path
import sys,struct,subprocess,tempfile,re
from test_native_controller_settings import ControllerMachine,v
from unicorn import x86_const as r
here=Path(__file__).resolve().parent
class AdapterMachine(ControllerMachine):
 def load(self,dll):
  data=Path(dll).read_bytes();pe=v._PE(data);self.u.mem_map(pe.base,0x100000);self.u.mem_map(0x10100000,0x10000)
  for s in pe.sections:self.u.mem_write(pe.base+s['vaddr'],data[s['raddr']:s['raddr']+s['rsize']])
  def at(rva):return pe.off(rva)
  def word(off):return struct.unpack_from('<I',data,off)[0]
  def string(off):return data[off:].split(b'\0',1)[0].decode()
  cursor=at(word(pe.opt+104));i=0
  while word(cursor+12):
   ilt,_,_,_,iat=struct.unpack_from('<5I',data,cursor);k=0
   while (item:=word(at(ilt+k*4))):
    name=string(at(item)+2);a=0x10100000+i*16;i+=1;self.imports[a]=name;self.u.mem_write(a,b'\xc3');self.word(pe.base+iat+k*4,a);k+=1
   cursor+=20
  self.api={name:a for a,name in self.imports.items()}
  ex=at(word(pe.opt+96));n=word(ex+24);funcs=at(word(ex+28));names=at(word(ex+32));ords=at(word(ex+36));self.exports={}
  for i in range(n):self.exports[string(at(word(names+i*4)))]=pe.base+word(funcs+2*struct.unpack_from('<H',data,ords+i*2)[0]*2)
  self.files={'C:\\Games With Spaces\\v_on.ini':{('Other','Keep'):'yes'}};self.fail_write=False;self.fail_replace=False;self.windows={};self.next_window=0x200
 def ccall(self,name,*args):return self.call(self.exports[name],args)
 def return_(self,result,n):
  u=self.u;sp=u.reg_read(r.UC_X86_REG_ESP);u.reg_write(r.UC_X86_REG_EIP,struct.unpack('<I',u.mem_read(sp,4))[0]);u.reg_write(r.UC_X86_REG_ESP,sp+4+4*n);u.reg_write(r.UC_X86_REG_EAX,result&0xffffffff)
 def hook(self,u,a,size,data):
  name=self.imports.get(a)
  if name is None:return super().hook(u,a,size,data)
  sp=u.reg_read(r.UC_X86_REG_ESP);args=struct.unpack('<12I',u.mem_read(sp+4,48));result=1;n=0
  if name in ('SendDlgItemMessageA','GetDlgItem','CheckDlgButton','CheckRadioButton','IsDlgButtonChecked'):self.controls=self.windows.setdefault(args[0],{})
  if name in ('memcpy','memset','memchr','memcmp','strcpy'):
   if name=='memcpy':u.mem_write(args[0],bytes(u.mem_read(args[1],args[2])));result=args[0]
   elif name=='memset':u.mem_write(args[0],bytes([args[1]&255])*args[2]);result=args[0]
   elif name=='memchr':i=bytes(u.mem_read(args[0],args[2])).find(bytes([args[1]&255]));result=args[0]+i if i>=0 else 0
   elif name=='memcmp':x=bytes(u.mem_read(args[0],args[2]));y=bytes(u.mem_read(args[1],args[2]));result=(x>y)-(x<y)
   else:u.mem_write(args[0],self.string(args[1]).encode()+b'\0');result=args[0]
  elif name=='__stdio_common_vsprintf':
   dest,capacity,fmt,va=args[2],args[3],self.string(args[4]),args[6];values=[]
   for i,match in enumerate(re.finditer(r'%[0-9]*[sudx]',fmt)):
    value=struct.unpack('<I',u.mem_read(va+4*i,4))[0];values.append(self.string(value) if match.group().endswith('s') else value)
   text=fmt%tuple(values);u.mem_write(dest,text[:max(0,capacity-1)].encode()+b'\0');result=len(text)
  elif name=='VirtualQuery':
   n=3;u.mem_write(args[1],struct.pack('<7I',0x3600000,0x3600000,0x40,0x100000,0x1000,0x40,0x1000000));result=28
  elif name in ('GetModuleHandleA','GetModuleHandleW','LoadLibraryA'):n=1
  elif name=='GetProcAddress':
   n=2;api=self.string(args[1]);result=self.api.get(api,0)
   if not result:result=0x10108000+len(self.api)*16;self.api[api]=result;self.imports[result]=api;u.mem_write(result,b'\xc3')
  elif name=='CreateWindowExA':
   n=12;klass=self.string(args[1]);result=args[9]
   if klass=='STATIC':
    result=self.next_window;self.next_window+=1;self.windows[result]={};self.controls=self.windows[result]
   else:self.controls=self.windows[args[8]];self.control(args[9])
  elif name=='DestroyWindow':n=1
  elif name=='SendDlgItemMessageA' and args[2] in (0x146,0x148,0x149,0x14b):
   n=5;c=self.control(args[1]);msg=args[2]
   if msg==0x146:result=len(c['items'])
   elif msg==0x14b:c['items']=[];c['selection']=-1;result=0
   elif msg==0x149:result=len(c['items'][args[3]])
   else:text=c['items'][args[3]];u.mem_write(args[4],text.encode()+b'\0');result=len(text)
  elif name=='GetFullPathNameA':
   n=4;text=self.string(args[0]);u.mem_write(args[2],text.encode()+b'\0');self.word(args[3],args[2]+text.rfind('\\')+1);result=len(text)
  elif name=='GetFileAttributesA':n=1;result=128 if self.string(args[0]) in self.files else 0xffffffff
  elif name=='GetTempFileNameA':n=4;text=self.string(args[0])+'tmp.ini';u.mem_write(args[3],text.encode()+b'\0');self.files[text]={}
  elif name=='CopyFileA':n=3;self.files[self.string(args[1])]=dict(self.files[self.string(args[0])])
  elif name=='WritePrivateProfileStringA':
   n=4
   if args[0]:
    result=int(not self.fail_write)
    if result:self.files[self.string(args[3])][(self.string(args[0]),self.string(args[1]))]=self.string(args[2])
  elif name=='CreateFileA':n=7
  elif name in ('FlushFileBuffers','CloseHandle'):n=1
  elif name=='MoveFileExA':
   n=3;result=int(not self.fail_replace)
   if result:self.files[self.string(args[1])]=self.files.pop(self.string(args[0]))
  elif name=='DeleteFileA':n=1;self.files.pop(self.string(args[0]),None)
  elif name=='GetLastError':result=5
  else:return super().hook(u,a,size,data)
  self.return_(result,n)
with tempfile.TemporaryDirectory() as td:
 dll=Path(td)/'controller.dll';cc=here.parents[1]/'../llvm-mingw-20260908-ucrt-macos-universal/bin/i686-w64-mingw32-clang'
 subprocess.run([str(cc.absolute()),'-shared','-O2','-Wl,--export-all-symbols','-Wl,--image-base,0x60000000',str(here/'controller_settings.c'),'-o',str(dll),'-luser32'],check=True)
 for path in sys.argv[1:]:
  m=AdapterMachine(path);m.load(dll);j=m.ed.short=='jpre';game=0x10050000;state=0x10040000
  symbols={n:v.symbol_va(n,m.ed) for n in ('MODE','CUSTOM1','DZTHR1','DEVICES','BINDS1','BLOCKS','DZSTR1')}
  context=[84,0,0,0,0,symbols['MODE'],0,0,0,0,0,0,symbols['CUSTOM1'],symbols['DZTHR1'],symbols['DEVICES'],symbols['BINDS1'],0,0,0,0,0]
  m.u.mem_write(game,struct.pack('<21I',*context));config=0x1acb7f0 if j else 0x1ad0b98;section=0x1acb9c0 if j else 0x1ad0b70
  m.u.mem_write(config,b'C:\\Games With Spaces\\v_on.ini\0');m.u.mem_write(section,b'Existing section\0')
  m.u.mem_write(symbols['DEVICES'],struct.pack('<2I',4,4))
  assert m.ccall('vo_controller_available',game)==1
  for player in range(2):
   for kind in (0,1,3,4):
    m.word(symbols['DEVICES']+4*player,kind);m.word(symbols['BLOCKS']+112*player,kind)
    if kind!=4:
     defaults=(0x669528 if j else 0x66d5a0) if kind==0 else v.symbol_va('GAMEPADDEF' if kind==1 else 'SIMPLEDEF',m.ed)
     offset=32 if kind==0 else 8 if kind==1 else 56;m.u.mem_write(symbols['BLOCKS']+112*player+offset,bytes(m.u.mem_read(defaults+24*player,24)))
    before=bytes(m.u.mem_read(symbols['BLOCKS'],224));m.u.mem_write(state,bytes(456));assert m.ccall('vo_controller_begin',state,game,1,player,kind)==1
    for slot in range(12):assert m.ccall('vo_controller_count',state,slot)==(21 if kind==4 else 20 if kind==1 else 69)
    assert m.ccall('vo_controller_defaults',state)==1
    used={m.ccall('vo_controller_selected',state,i) for i in range(12)}
    choice=0 if kind==4 else [i for i in range(m.ccall('vo_controller_count',state,0)) if i not in used][player]
    assert m.ccall('vo_controller_select',state,0,choice)==1
    live=symbols['CUSTOM1'] if kind==4 else (0x364c140 if j else 0x3651440) if kind==0 else symbols['BINDS1']
    live_before=bytes(m.u.mem_read(live,48))
    old_file=dict(m.files['C:\\Games With Spaces\\v_on.ini']);m.fail_write=True
    assert m.ccall('vo_controller_save',state)==0 and m.files['C:\\Games With Spaces\\v_on.ini']==old_file
    assert bytes(m.u.mem_read(live,48))==live_before
    m.fail_write=False;m.fail_replace=True;assert m.ccall('vo_controller_save',state)==0 and m.files['C:\\Games With Spaces\\v_on.ini']==old_file
    assert bytes(m.u.mem_read(live,48))==live_before
    m.fail_replace=False;assert m.ccall('vo_controller_save',state)==1,(m.ed.short,player,kind,choice)
    assert m.files['C:\\Games With Spaces\\v_on.ini'][('Other','Keep')]=='yes'
    key=f'{player+1}P '+('Custom Assign' if kind==4 else 'Simple Assign' if kind==3 else 'Keyboard Assign')
    stored=m.files['C:\\Games With Spaces\\v_on.ini'][('Device Settings',key)]
    assert bytes(m.u.mem_read(live+24*player,24)).hex()==stored
    assert bytes(m.u.mem_read(live+24*(1-player),24))==live_before[24*(1-player):24*(2-player)]
    m.ccall('vo_controller_end',state);assert m.string(config)=='C:\\Games With Spaces\\v_on.ini' and m.string(section)=='Existing section'
  m.u.mem_write(symbols['DEVICES'],struct.pack('<2I',0,0));m.u.mem_write(state,bytes(456))
  before_file=dict(m.files['C:\\Games With Spaces\\v_on.ini']);before_live=bytes(m.u.mem_read(0x364c140 if j else 0x3651440,48))
  assert m.ccall('vo_controller_begin',state,game,1,1,0)==1
  assert m.ccall('vo_controller_select',state,0,0)==1  # P1 already owns A
  assert m.ccall('vo_controller_save',state)==0
  assert m.files['C:\\Games With Spaces\\v_on.ini']==before_file and bytes(m.u.mem_read(0x364c140 if j else 0x3651440,48))==before_live
  m.ccall('vo_controller_end',state)
  for p in range(2):
   for kind in range(9):
    old=struct.unpack('<I',m.u.mem_read(symbols['DEVICES']+4*p,4))[0];m.fail_write=True
    assert m.ccall('vo_controller_profile',game,p,kind)==0 and struct.unpack('<I',m.u.mem_read(symbols['DEVICES']+4*p,4))[0]==old
    m.fail_write=False;assert m.ccall('vo_controller_profile',game,p,kind)==1 and struct.unpack('<I',m.u.mem_read(symbols['DEVICES']+4*p,4))[0]==kind
   for value in (5,40,95):assert m.ccall('vo_controller_deadzone',game,p,value)==value and struct.unpack('<I',m.u.mem_read(symbols['DZTHR1']+4*p,4))[0]==327*value
  print(m.ed.short,'PASS compiled production controller adapter + original F7: both players/all four editors/defaults/write failure/replace failure/retry, original INI authority, real F11 deadzone seed')
