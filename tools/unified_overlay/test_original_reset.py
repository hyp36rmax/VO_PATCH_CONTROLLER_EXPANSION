"""Execute original negative-mode dispatch and guarded chord bypass, both EXEs.
Original teardown/audio internals require Windows UAT; no simulated game claim.
"""
from pathlib import Path
import sys,hashlib,struct
import unicorn
from unicorn import x86_const as r
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dual_display'))
import mode_profiles
from install import install
v=mode_profiles.engineering3840.load_private();md=Cs(CS_ARCH_X86,CS_MODE_32)
for arg in sys.argv[1:]:
 raw=Path(arg).read_bytes();b=v.BUILDS[hashlib.md5(raw).hexdigest()];pe=v._PE(raw)
 for key,start in zip(('MODE','MODE2'),(0x49f965,0x40f5a0) if b.short=='retail' else (0x49e4a5,0x40f4f0)):
  ins=list(md.disasm(raw[pe.off(start-pe.base):pe.off(start-pe.base)+28],start))
  assert [x.mnemonic for x in ins[:5]]==['cmp','jge','call','call','jmp']
  targets=[int(x.op_str,16) for x in ins[2:4]]
  for value,expected in ((0xffffffff,targets),(4,[])):
   u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32);u.mem_map(0x400000,0x5000000);u.mem_map(0x10000000,0x20000)
   for sec in pe.sections:u.mem_write(pe.base+sec['vaddr'],raw[sec['raddr']:sec['raddr']+sec['rsize']])
   u.mem_write(v.symbol_va(key,b),struct.pack('<I',value));u.reg_write(r.UC_X86_REG_ESP,0x10010000)
   calls=[]
   def hook(cpu,address,size,_):
    if address in targets:
     calls.append(address);sp=cpu.reg_read(r.UC_X86_REG_ESP);ret=struct.unpack('<I',cpu.mem_read(sp,4))[0]
     cpu.reg_write(r.UC_X86_REG_ESP,sp+4);cpu.reg_write(r.UC_X86_REG_EIP,ret)
    elif address in (int(ins[1].op_str,16),int(ins[4].op_str,16)):cpu.emu_stop()
   u.hook_add(unicorn.UC_HOOK_CODE,hook);u.emu_start(start,0,count=30);assert calls==expected
  print(b.short,key,hex(start),'PASS negative dispatch invokes original teardown then boot; nonnegative skips reset')
 # Verify the inactive branch invokes IDLE and jumps back to the pump,
 # while active execution takes the branch into simulation/frame work.
 pattern=b'\x83\x3d'+struct.pack('<I',v.symbol_va('INACTIVE',b))+b'\x00'
 candidates=[];pos=0
 while (pos:=raw.find(pattern,pos))>=0:
  block=list(md.disasm(raw[pos:pos+24],v._va_at(pe,pos)))
  if len(block)>=4 and [x.mnemonic for x in block[:4]]==['cmp','je','call','jmp'] and int(block[2].op_str,16)==v.symbol_va('IDLE',b):candidates.append(block)
  pos+=1
 assert len(candidates)==1
 branch=candidates[0]
 assert int(branch[3].op_str,16)<branch[0].address and int(branch[1].op_str,16)==branch[3].address+branch[3].size
 print(b.short,'PASS original inactive loop skips active work and returns to message pump after IDLE')
 before,_=mode_profiles.build(raw,'wide',dict.fromkeys(v.by_key(b),True));image,meta=install(before,b,v);pe=v._PE(image)
 patch=next(p for p in meta['patches'] if p['name']=='disable-reset-chord');at=patch['offset'];start=v._va_at(pe,at)
 target=start+5+struct.unpack_from('<i',image,at+1)[0]
 u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32);u.mem_map(start&~4095,8192);u.mem_write(start,image[at:at+5])
 for buttons in (0x10,0x100,0x200,0x310,0xffff):
  u.reg_write(r.UC_X86_REG_EBX,buttons);u.emu_start(start,target,count=1)
  assert u.reg_read(r.UC_X86_REG_EIP)==target and u.reg_read(r.UC_X86_REG_EBX)==buttons
 assert image[pe.off(target-pe.base):pe.off(target-pe.base)+2]==b'\x31\xff'
 print(b.short,'PASS chord bypass reaches original key dispatcher and preserves every individual button bit')
