"""Execute the unchanged twelve-action Custom dialog and original serializer."""
import sys,struct
from test_native_controller_settings import ControllerMachine,v
from unicorn import x86_const as r
class CustomMachine(ControllerMachine):
 def hook(self,u,a,size,data):
  if a==v.symbol_va('WRITELINE',self.ed):
   sp=u.reg_read(r.UC_X86_REG_ESP);ret,key,value=struct.unpack('<3I',u.mem_read(sp,12))
   self.writes.append((self.string(key),self.string(value)));u.reg_write(r.UC_X86_REG_EAX,1);u.reg_write(r.UC_X86_REG_EIP,ret);u.reg_write(r.UC_X86_REG_ESP,sp+4);return
  return super().hook(u,a,size,data)
for path in sys.argv[1:]:
 m=CustomMachine(path);m.writes=[]
 for label,api in [('sendfn','SendDlgItemMessageA'),('titlefn','SetWindowTextA')]:
  found=next((a for a,n in m.imports.items() if n==api),None)
  if found is None:found=0x10090000;m.imports[found]=api;m.u.mem_write(found,b'\xc3')
  m.word(v.symbol_va(('CUSTOM',label),m.ed),found)
 procedure=v.symbol_va(('CUSTOM','procedure'),m.ed);live=v.symbol_va('CUSTOM1',m.ed)
 default=bytes(m.u.mem_read(v.symbol_va(('TWIN','custombinds'),m.ed),24))
 for player in range(2):
  before=bytes(m.u.mem_read(live,48));m.controls={};m.call(procedure,(1,0x110,0,player))
  assert all(len(m.control(100+i)['items'])==21 for i in range(12))
  for choice in range(21):
   for slot in range(12):m.control(100+slot)['selection']=choice
   m.call(procedure,(1,0x111,1,0))
   expected=struct.pack('<12H',*([0 if choice==0 else choice-1+0xe0]*12))
   assert bytes(m.u.mem_read(live+24*player,24))==expected
   assert m.writes[-1]==(f'{player+1}P Custom Assign',expected.hex())
  m.call(procedure,(1,0x111,3,0));m.call(procedure,(1,0x111,1,0))
  assert bytes(m.u.mem_read(live+24*player,24))==default
  other=1-player;assert bytes(m.u.mem_read(live+24*other,24))==before[24*other:24*(other+1)]
  snapshot=bytes(m.u.mem_read(live,48));count=len(m.writes);m.control(100)['selection']=0;m.call(procedure,(1,0x111,2,0))
  assert len(m.writes)==count and bytes(m.u.mem_read(live,48))==snapshot
 print(m.ed.short,'PASS original Custom: 12 independent slots, all 21 choices, defaults, P1/P2 isolation, original INI serialization and Cancel')
