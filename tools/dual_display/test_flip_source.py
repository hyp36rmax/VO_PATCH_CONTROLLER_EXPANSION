"""Verify original Retail/JPRE render->Flip dispatch; not physical evidence."""
import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engineering3840
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
v=engineering3840.load_private();md=Cs(CS_ARCH_X86,CS_MODE_32)
for edition,path in zip(('retail','jpre'),sys.argv[1:3]):
 raw=Path(path).read_bytes();pe=v._PE(raw)
 port=None if edition=='retail' else v.PORT['%08x'%v._pe_stamp(raw)]
 address=lambda x:x if port is None else port['va'][x]
 back=address(0x1ae5f5c);primary=address(0x1ae5f40)
 needle=b'\xa1'+struct.pack('<I',back)+b'\x50\xe8'
 candidates=[];at=0
 while True:
  at=raw.find(needle,at)
  if at<0:break
  code=raw[at:at+80]
  if b'\xff\x50\x2c' in code and struct.pack('<I',primary) in code:candidates.append(at)
  at+=1
 assert len(candidates)==1,(edition,candidates)
 off=candidates[0];va=v._va_at(pe,off);ins=list(md.disasm(raw[off:off+80],va))
 render=ins[2];assert render.mnemonic=='call'
 renderer=int(render.op_str,16);rop=pe.off(renderer-pe.base)
 renderer_code=list(md.disasm(raw[rop:rop+500],renderer))
 # Original render driver calls DirectDraw Lock/Unlock on its argument.
 assert any(i.mnemonic=='call' and '0x64]' in i.op_str for i in renderer_code)
 assert any(i.mnemonic=='call' and '0x80]' in i.op_str for i in renderer_code)
 flip=next(i for i in ins if i.mnemonic=='call' and '0x2c]' in i.op_str)
 between=[i for i in ins if render.address<i.address<flip.address]
 assert all(i.mnemonic!='call' for i in between)
 assert back!=primary
 # GetAttachedSurface writes the distinct backbuffer variable at creation.
 attach=b'\x68'+struct.pack('<I',back)
 found=[i for i in range(len(raw)) if raw.startswith(attach,i)]
 assert any(b'\xff\x50\x30' in raw[i:i+80] for i in found),edition
 print(edition,'VERIFIED backbuffer pointer',hex(back),'primary pointer',hex(primary),'renderer',hex(renderer),'Flip',hex(flip.address))
 for i in ins:
  if i.address>flip.address:break
  print(hex(i.address),i.mnemonic,i.op_str)
