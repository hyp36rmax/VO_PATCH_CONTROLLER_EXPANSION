"""Execute the linked production movie placer for Retail/JPRE under Unicorn.
Windows/MCI API doubles validate geometry and call arguments, not decoding.
"""
import struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import mode_profiles
v=mode_profiles.engineering3840.load_private();blob=mode_profiles.movie_blob(v)
for edition in (v.RETAIL,next(b for b in v.BUILDS.values() if b.short=='jpre')):
 for width,height in ((640,480),(1600,1200),(2560,1440),(1920,1080),(1280,1024),(3440,1440),(3840,1080),(5120,1440)):
  for query in ("known", "scaled", "failed", "empty"):
   u=Uc(UC_ARCH_X86,UC_MODE_32);pages=set()
   def put(at,data):
    for p in range(at&~4095,(at+len(data)+4095)&~4095,4096):
     if p not in pages:u.mem_map(p,4096);pages.add(p)
    u.mem_write(at,data)
   def word(at,value):put(at,struct.pack('<I',value&0xffffffff))
   def read(at):return struct.unpack('<I',u.mem_read(at,4))[0]
   entry=0x100000;end=0x220000;frame=0x310100;stack=0x320800
   code=v.link('MOVIE',edition,blobs={**v.BLOBS,'MOVIE':blob},base=entry);put(entry,code)
   calls={};api={};names=['GETMODULE','GETPROC','GETCLIENT','MOVEWINDOW','MCISEND']
   for i,name in enumerate(names):
    at=0x200000+i*0x100;api[at]=name;put(at,b'\xc3');word(edition.symbols[name],at)
   native=0x200500;api[native]='NATIVECLIENT';put(native,b'\xc3');put(end,b'\xcc')
   for name,value in [('MOVIEHWND',22),('MOVIEDEV',33),('MOVIEX',0),('MOVIEY',0)]:word(edition.symbols[name],value)
   put(frame-0x100,bytes(0x200));word(frame+8,11);word(frame+16,640);word(frame+20,400)
   put(stack-0x1000,bytes(0x2000));word(stack,end);word(stack+4,frame)
   u.reg_write(UC_X86_REG_ESP,stack)
   saved={UC_X86_REG_EBX:123,UC_X86_REG_ESI:456,UC_X86_REG_EDI:789,UC_X86_REG_EBP:321}
   for r,x in saved.items():u.reg_write(r,x)
   def hook(uc,at,size,user):
    if at not in api:return
    name=api[at];sp=uc.reg_read(UC_X86_REG_ESP);arg=lambda i:read(sp+4+4*i);result=1
    if name=='GETMODULE':argc=1;result=44
    elif name=='GETPROC':argc=2;result=0x200600
    elif name=='DDGETPROC':argc=2;result=native
    elif name in ('NATIVECLIENT','GETCLIENT'):
     assert name=='NATIVECLIENT' and arg(0)==11
     argc=2;put(arg(1),struct.pack('<4i',0,0,width,height))
    elif name=='MOVEWINDOW':
     argc=6;calls['move']=[arg(i) for i in range(argc)];assert arg(0)==22
    elif name=='MCISEND':
     argc=4;assert arg(0)==33;command,flags,parms=arg(1),arg(2),arg(3)
     if command==0x843:assert flags==0x430000;put(parms+4,struct.pack('<4i',0,0,640 if query=='scaled' else 0 if query=='empty' else 320,480 if query=='scaled' else 240))
     else:
      assert command==0x842 and flags in (0x30000,0x50000)
      calls[flags]=struct.unpack('<4i',u.mem_read(parms+4,16))
     result=int(command==0x843 and query=="failed")
    else:raise AssertionError(name)
    uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_ESP,sp+4+4*argc);uc.reg_write(UC_X86_REG_EIP,read(sp))
   api[0x200600]='DDGETPROC';put(0x200600,b'\xc3');u.hook_add(UC_HOOK_CODE,hook)
   u.emu_start(entry,end,count=10000)
   ratio_w,ratio_h=(16,9) if query in ("known","scaled") else (16,10)
   w=min(width,height*ratio_w//ratio_h);h=min(height,width*ratio_h//ratio_w);x=(width-w)//2;y=(height-h)//2
   assert calls['move']==[22,x,y,w,h,1],calls
   if query in ('known','scaled'):assert calls[0x30000]==((0,60,640,360) if query=='scaled' else (0,30,320,180))
   else:assert 0x30000 not in calls
   assert calls[0x50000]==(0,0,w,h)
   assert u.reg_read(UC_X86_REG_ESP)==stack+4
   for r,value in saved.items():assert u.reg_read(r)==value
   if query in ('known','scaled'):
    calls.clear();u.reg_write(UC_X86_REG_ESP,stack);u.emu_start(entry,end,count=10000)
    assert calls['move']==[22,x,y,w,h,1]
    assert calls[0x30000]==((0,60,640,360) if query=='scaled' else (0,30,320,180))
   print('PASS',edition.short,query,width,height,'upstream measured band or unchanged query-failure fallback; centered',x,y,w,h,'callee registers/stack preserved; geometry MCI calls only')
