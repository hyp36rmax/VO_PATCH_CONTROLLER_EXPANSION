"""Execute generated PE startup chaining/ABI; helper itself tested separately."""
import sys,struct,json
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import mode_profiles
v=mode_profiles.engineering3840.load_private();out=Path(sys.argv[1])
for name,edition in [('retail',v.RETAIL),('jpre',v.JPRE)]:
 data=(out/(name+'-internal.exe')).read_bytes();meta=json.loads((out/(name+'-startup.json')).read_text());pe=v._PE(data)
 for failure in ('none','load','symbol','helper'):
  u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(pe.base,0x4000000);u.mem_map(0x8000000,0x10000)
  for s in pe.sections:u.mem_write(pe.base+s['vaddr'],data[s['raddr']:s['raddr']+s['rsize']])
  load,get,helper,quit=[0x8000100+i*0x100 for i in range(4)]
  for a in (load,get,helper,quit):u.mem_write(a,b'\xc3')
  u.mem_write(edition.symbols['LOADLIB'],struct.pack('<I',load));u.mem_write(edition.symbols['GETPROC'],struct.pack('<I',get))
  stack=0x800f000;u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_EFLAGS,0x202)
  regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
  for i,r in enumerate(regs):u.reg_write(r,100+i)
  counts={'load':0,'get':0};seen=[]
  def ret(value,args):
   sp=u.reg_read(UC_X86_REG_ESP);target=struct.unpack('<I',u.mem_read(sp,4))[0]
   u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_ESP,sp+4+args*4);u.reg_write(UC_X86_REG_EIP,target)
  def hook(mu,a,size,unused):
   if a==load:
    counts['load']+=1;ret(0 if failure=='load' and counts['load']==1 else 123,1)
   elif a==get:
    counts['get']+=1
    ret(quit if (failure=='load' or counts['get']>1) else (0 if failure=='symbol' else helper),2)
   elif a==helper:
    sp=u.reg_read(UC_X86_REG_ESP);args=struct.unpack('<4I',u.mem_read(sp+4,16))
    assert args[:3]==(pe.base,meta['table'],meta['table_size'])
    import zlib
    assert args[3]==zlib.crc32(u.mem_read(meta['table'],meta['table_size']))
    seen.append('helper');ret(int(failure!='helper'),4)
   elif a==quit:seen.append('exit');u.emu_stop()
   elif a==meta['original_entry']:seen.append('original');u.emu_stop()
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(meta['entry'],0,count=1000)
  if failure=='none':
   assert seen==['helper','original'] and u.reg_read(UC_X86_REG_ESP)==stack
   assert u.reg_read(UC_X86_REG_EFLAGS)==0x202
   for i,r in enumerate(regs):assert u.reg_read(r)==100+i
  else:assert seen[-1]=='exit' and 'original' not in seen
 print('PASS',name,'normal-entry chain, complete register/flags/stack restoration; missing DLL/export and rejected activation stop before game entry')
