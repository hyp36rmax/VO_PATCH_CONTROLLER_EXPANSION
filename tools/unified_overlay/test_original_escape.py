"""Execute Retail/JPRE's original Enter/ESC/Space movie-only skip dispatch."""
from pathlib import Path
import hashlib,struct,sys
import unicorn
from unicorn import x86_const as r
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from selftest import load_patcher
v=load_patcher();decoder=Cs(CS_ARCH_X86,CS_MODE_32)
for arg in sys.argv[1:]:
 data=Path(arg).read_bytes();edition=v.BUILDS[hashlib.md5(data).hexdigest()];pe=v._PE(data)
 wnd=v.symbol_va('ORIGWNDPROC',edition)
 def original(address,n):return data[pe.off(address-pe.base):pe.off(address-pe.base)+n]
 slots=wnd+(0x5c6c31-0x5c6857);table=wnd+(0x5c6c1d-0x5c6857)
 targets=[struct.unpack('<I',original(table+4*original(slots+key-13,1)[0],4))[0] for key in (13,27,32)]
 assert len(set(targets))==1
 target=targets[0];instructions=list(decoder.disasm(original(target,41),target))
 assert instructions[0].mnemonic=='test' and original(target,2)==b'\xf6\x05'
 flag=struct.unpack('<I',original(target+2,4))[0]
 assert flag==(0x6bc598 if edition.short=='retail' else 0x6b82f8)
 call=next(i for i in instructions if i.mnemonic=='call');skip=int(call.op_str,16)
 stop=wnd+(0x5c6c97-0x5c6857)
 for movie in (0,1):
  u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32);u.mem_map(0x400000,0x4000000)
  for sec in pe.sections:u.mem_write(pe.base+sec['vaddr'],data[sec['raddr']:sec['raddr']+sec['rsize']])
  u.mem_write(skip,b'\xc3');u.mem_write(flag,struct.pack('<I',movie));u.reg_write(r.UC_X86_REG_ESP,0x3f00000)
  seen=[]
  def visit(cpu,address,size,user):
   if address==skip:seen.append(address)
  u.hook_add(unicorn.UC_HOOK_CODE,visit);u.emu_start(target,stop,count=100)
  assert u.reg_read(r.UC_X86_REG_EIP)==stop and len(seen)==movie
  assert struct.unpack('<I',u.mem_read(flag,4))[0]==0
 print(edition.short+': PASS original Enter/ESC/Space share movie-only skip; non-movie ESC does not pause or quit')
