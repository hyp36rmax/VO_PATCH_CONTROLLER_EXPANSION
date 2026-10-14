"""Execute original solid/textured quad and triangle flush paths on valid pre-clipped synthetic records.
Not complete primitive coverage, submission clipping, runtime or game validation.
"""
from pathlib import Path
import sys,hashlib,struct,json
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EBX,UC_X86_REG_EBP
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(sys.argv[3]);O.mkdir(parents=True,exist_ok=True)
import engineering3840,engineering_vs,d01test
v=engineering3840.load_private();md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;results=[]
for edition,path in zip(('retail','jpre'),sys.argv[1:3]):
 raw=Path(path).read_bytes();b=v.BUILDS[hashlib.md5(raw).hexdigest()];assert b.short==edition
 d,_=engineering_vs.build(raw)
 port=None if edition=='retail' else v.PORT['%08x'%v._pe_stamp(raw)]
 addr=lambda a:a if port is None else port['va'][a]
 m,p=d01test.image(d);surface=0x10000000;m.mem_map(surface,0xa00000)
 sec=next(s for s in p.sections if s['name']==b'.vohr');mask=p.base+sec['vaddr']+v.UI_OFF+v.UI_OFF_SIZE
 def put(a,n):m.mem_write(a,struct.pack('<I',n&0xffffffff))
 def call(a,arg=0):
  sp=d01test.STACK+0x8000;put(sp,d01test.RET);put(sp+4,arg);m.reg_write(UC_X86_REG_ESP,sp);m.emu_start(a,d01test.RET,count=3000000);assert m.reg_read(UC_X86_REG_EIP)==d01test.RET
 def dis(a,n):return list(md.disasm(bytes(m.mem_read(a,n)),a))
 desc=d01test.STACK+0x1000;rec=d01test.STACK+0x2000;material=rec+0x100
 for pitch in (7680,7744,8192):
  put(desc+0x24,surface);put(desc+0x10,pitch)
  put(addr(0x6bc948),1);put(addr(0x6bf598),0);put(addr(0x1ae3594),4);put(addr(0x1ae3690),9)
  call(addr(0x5c8317),desc);call(addr(0x5ce180))
  # Known relocated framebuffer row-table operands are patch-site verified by generation.
  translate=lambda x:x if port is None else port['off'][x][0]
  rt_a=struct.unpack_from('<I',d,translate(0x1c4f73))[0]
  rt_b=struct.unpack_from('<I',d,translate(0x1c4fc9))[0]
  for rt in (rt_a,rt_b):m.mem_write(rt,struct.pack('<1080I',*(y*pitch for y in range(1080))))
  m.mem_write(surface,b'\x17\x29'*(pitch*1080//2));m.mem_write(mask,b'\0'*(512*1080))
  for player,original_flush in ((1,0x5d1db0),(2,0x5dcc80)):
   flush=addr(original_flush);instructions=dis(flush,0x50)
   sort=next(i.operands[0].imm for i in instructions if i.mnemonic=='call')
   count=next(i.operands[1].mem.disp for i in instructions if i.mnemonic=='mov' and i.op_str.startswith('edi, dword ptr ['))
   table=next(i.operands[1].mem.disp for i in instructions if i.mnemonic=='mov' and i.op_str.startswith('esi, dword ptr [edi*4'))
   bits=next(i.operands[1].mem.disp for i in dis(sort,0x30) if i.mnemonic=='mov' and i.op_str.startswith('eax, dword ptr [ecx*4'))
   for x,y,triangle,textured in [(x,y,t,z) for t in (0,1) for z in (0,1) for x,y in ((0,0),(1908,0),(0,1068),(1908,1068))]:
    # Reset only this view for the next overlapping primitive; retain other-view coverage.
    for row in range(1080):m.mem_write(mask+row*512+(player-1)*240,b'\0'*240)
    before_mask=bytes(m.mem_read(mask,512*1080))
    m.mem_write(bits,b'\0'*1024);m.mem_write(material,b'\0'*16)
    put(rec,textured);put(rec+4,material);put(rec+8,triangle);put(rec+12,0)
    cache=next(i.operands[1].mem.disp for i in dis(flush,0x90) if i.mnemonic=='mov' and i.op_str.startswith('edx, dword ptr [ecx*4'))
    builder=[i.operands[0].imm for i in dis(flush,0x120) if i.mnemonic=='call'][1]
    copier=next(i.operands[0].imm for i in dis(builder,0x80) if i.mnemonic=='call')
    texture_base=next(i.operands[0].mem.disp for i in dis(copier,0x30) if i.mnemonic=='mov' and i.op_str.startswith('byte ptr [eax +'))
    m.mem_write(texture_base+1,b'\x39\x67'*2048);put(cache,1)
    m.mem_write(rec+0x20,b'\0'*16)
    for i,(xx,yy) in enumerate(((x,y),(x+10,y),(x+10,y+10),(x,y+10))):put(rec+16+4*i,(yy<<16)|xx)
    put(count,1);put(table,rec)
    writes=[];maskwrites=[];scratch_pages=set()
    def write(mu,access,a,size,value,user):
     if p.base<=a<surface and not mask<=a<mask+512*1080:scratch_pages.add(a&~4095)
     if surface<=a<surface+0xa00000:
      z=a-surface;assert 0<=z//pitch<1080 and (player-1)*3840<=z%pitch and z%pitch+size<=player*3840,(player,hex(a),size)
      writes.append((z,size))
     if mask<=a<mask+512*1080:
      z=a-mask;assert (player-1)*240<=z%512 and z%512+size<=player*240,(player,'mask',z,size)
      maskwrites.append((z,size))
    h=m.hook_add(UC_HOOK_MEM_WRITE,write)
    try:call(flush)
    except Exception:
     print('FAILED',edition,player,pitch,x,y,triangle,textured,hex(m.reg_read(UC_X86_REG_EIP)),hex(m.reg_read(UC_X86_REG_EBX)),hex(m.reg_read(UC_X86_REG_EBP)));raise
    finally:m.hook_del(h)
    assert writes and maskwrites,'vacuous flush'
    after_mask=bytes(m.mem_read(mask,512*1080))
    other=240 if player==1 else 0
    assert all(before_mask[row*512+other:row*512+other+240]==after_mask[row*512+other:row*512+other+240] for row in range(1080))
    assert min(z%pitch for z,n in writes)==((player-1)*1920+x)*2, 'viewport origin applied more than once'
    results.append(dict(edition=edition,player=player,triangle=triangle,textured=textured,pitch=pitch,x=x,y=y,framebuffer_writes=len(writes),mask_writes=len(maskwrites),scratch_pages=[hex(a) for a in sorted(scratch_pages)],flush=hex(flush)))
(O/'isolation.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS',len(results),'guarded original solid/textured quad/triangle flushes; limited synthetic material coverage')
