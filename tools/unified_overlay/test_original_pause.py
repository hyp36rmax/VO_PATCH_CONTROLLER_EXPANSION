"""Execute the original pause/resume/availability code, doubling external APIs."""
from pathlib import Path
import hashlib,sys,struct
import unicorn
from unicorn import x86_const as r
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_EAX
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from selftest import load_patcher
v=load_patcher();md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
for arg in sys.argv[1:]:
 raw=Path(arg).read_bytes();b=v.BUILDS[hashlib.md5(raw).hexdigest()]
 image,_,_=v.apply_selected(bytearray(raw),dict.fromkeys(v.by_key(b),True),b);pe=v._PE(image)
 symbols={k:v.symbol_va(k,b) for k in ('GPAUSE','GRESUME','SETACTIVE','INACTIVE','BACK','MODE','SUBMODE')}
 def function(address):
  off=pe.off(address-pe.base);out=[]
  for ins in md.disasm(bytes(image[off:off+256]),address):
   out.append(ins)
   if ins.mnemonic=='ret':break
  return out
 calls={};imports=[]
 for name in ('GPAUSE','GRESUME'):
  for ins in function(symbols[name]):
   if ins.mnemonic=='call':calls[ins.address]=ins
 active=function(symbols['SETACTIVE']+5)
 for ins in active:
  if ins.mnemonic=='call':
   calls[ins.address]=ins
   if ins.operands[0].type==X86_OP_MEM:imports.append(ins.address)
 # The original active(1) sequence invokes one device COM method, then two
 # Win32 calls. Preserve their distinct stdcall cleanup sizes.
 assert len(imports)==3
 cleanup=dict(zip(imports,(4,4,16)))
 for name in ('GRESUME',):
  for ins in function(symbols[name]):
   if ins.mnemonic=='call' and ins.operands[0].type==X86_OP_MEM:cleanup[ins.address]=4
 u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32);u.mem_map(0x400000,0x5000000);u.mem_map(0x10000000,0x20000)
 for sec in pe.sections:u.mem_write(pe.base+sec['vaddr'],bytes(image[sec['raddr']:sec['raddr']+sec['rsize']]))
 object_address=0x10004000;u.mem_write(object_address,struct.pack('<I',object_address+256))
 for ins in active:
  if ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].reg==X86_REG_EAX and ins.operands[1].type==X86_OP_MEM and not ins.operands[1].mem.base:
   u.mem_write(ins.operands[1].mem.disp,struct.pack('<I',object_address))
 def put(name,value):u.mem_write(symbols[name],struct.pack('<I',value))
 def value(name):return struct.unpack('<I',u.mem_read(symbols[name],4))[0]
 put('BACK',object_address)
 def hook(cpu,address,size,data):
  ins=calls.get(address)
  if not ins:return
  if ins.operands[0].type==X86_OP_IMM and ins.operands[0].imm==symbols['SETACTIVE']:return
  if ins.operands[0].type==X86_OP_MEM:cpu.reg_write(r.UC_X86_REG_ESP,cpu.reg_read(r.UC_X86_REG_ESP)+cleanup[address])
  cpu.reg_write(r.UC_X86_REG_EAX,1);cpu.reg_write(r.UC_X86_REG_EIP,address+ins.size)
 u.hook_add(unicorn.UC_HOOK_CODE,hook)
 def run(address,args):
  sp=0x10002000;stop=0x10010000;u.reg_write(r.UC_X86_REG_ESP,sp);u.mem_write(sp,struct.pack('<'+'I'*(1+len(args)),stop,*args))
  u.emu_start(address,stop,count=1000);assert u.reg_read(r.UC_X86_REG_EIP)==stop
  assert u.reg_read(r.UC_X86_REG_ESP)==sp+4
 put('INACTIVE',0);run(symbols['GPAUSE'],(0,));assert value('INACTIVE')==1
 run(symbols['GPAUSE'],(0,));assert value('INACTIVE')==1
 run(symbols['GRESUME'],());assert value('INACTIVE')==0
 put('INACTIVE',1);put('BACK',0);run(symbols['GRESUME'],());assert value('INACTIVE')==1
 allowed=0x5c54a0 if b.short=='retail' else 0x5bfd40
 for mode,sub,expected in ((1,0,0),(4,9,1),(4,31,0),(4,34,0)):
  put('MODE',mode);put('SUBMODE',sub);run(allowed,());assert u.reg_read(r.UC_X86_REG_EAX)==expected
 print(b.short+': PASS original GPAUSE sets inactive, repeated pause, GRESUME clears inactive, original missing-back-buffer resume guard, availability predicate')
