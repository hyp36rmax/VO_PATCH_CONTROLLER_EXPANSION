"""Execute existing F7 bind-page initialization and validation in both editions.
This exercises the original methods with Win32 control doubles, not Windows UAT.
"""
from pathlib import Path
import sys,struct
from test_native_settings import Machine,v
from unicorn import x86_const as r
class ControllerMachine(Machine):
 def hook(self,u,a,size,data):
  name=self.imports.get(a)
  if name not in ('wsprintfA','SetWindowTextA'):
   return super().hook(u,a,size,data)
  sp=u.reg_read(r.UC_X86_REG_ESP)
  args=struct.unpack('<4I',u.mem_read(sp+4,16))
  n=2;result=1
  if name=='wsprintfA':
   template=self.string(args[1]);text=template%args[2];u.mem_write(args[0],text.encode()+b'\0');n=0;result=len(text)
  self.calls.append(name)
  u.reg_write(r.UC_X86_REG_EAX,result);u.reg_write(r.UC_X86_REG_EIP,struct.unpack('<I',u.mem_read(sp,4))[0]);u.reg_write(r.UC_X86_REG_ESP,sp+4+n*4)
 def method(self,address,args):
  self.u.reg_write(r.UC_X86_REG_ECX,0x10030000)
  return self.call(address,args)
 def word(self,address,value):self.u.mem_write(address,struct.pack('<I',value))
for path in sys.argv[1:]:
 m=ControllerMachine(path);j=m.ed.short=='jpre'
 blocks=v.symbol_va('BLOCKS',m.ed);player=v.symbol_va('CURPLAYER',m.ed)
 init_real,init_pad=(0x4960bf,0x496705) if j else (0x497560,0x497ba8)
 command_real,command_pad=(0x49623c,0x496885) if j else (0x4976dd,0x497d28)
 ids_real,ids_pad=(0x669558,0x6695b8) if j else (0x66d5d0,0x66d630)
 real_defaults=0x669528 if j else 0x66d5a0
 for p in range(2):
  for kind in (0,1,3):
   m.controls={};m.word(player,p);m.word(blocks+112*p,kind)
   defaults=real_defaults if kind==0 else v.symbol_va('GAMEPADDEF' if kind==1 else 'SIMPLEDEF',m.ed)
   offset=32 if kind==0 else 8 if kind==1 else 56
   original=bytes(m.u.mem_read(defaults+24*p,24));m.u.mem_write(blocks+112*p+offset,original)
   m.u.mem_write(0x10030000,bytes(32))
   m.method(init_real if kind==0 else init_pad,(1,0,0))
   ids=struct.unpack('<'+'I'*(11 if kind==0 else 12),m.u.mem_read(ids_real if kind==0 else ids_pad,44 if kind==0 else 48))
   for id in ids:
    c=m.control(id);assert len(c['items'])==(20 if kind==1 else 69),(m.ed.short,kind,id,len(c['items']))
    assert 0<=c['selection']<len(c['items']),(m.ed.short,kind,id,c)
   # Original native close method clears the object's HWND on accepted Save.
   # Its callback field is zero, so it does not touch the original modal stack.
   m.method(command_real if kind==0 else command_pad,(1,1017 if kind==0 else 1022,0))
   assert struct.unpack('<I',m.u.mem_read(0x1003000c,4))[0]==0,(m.ed.short,p,kind,'save rejected')
   actual=bytes(m.u.mem_read(blocks+112*p+offset,24));assert actual==original,(m.ed.short,p,kind,actual.hex(),original.hex())
 print(m.ed.short,'PASS original F7 per-player Real/Gamepad/Simple choices and unchanged-default Save through original validation methods')
