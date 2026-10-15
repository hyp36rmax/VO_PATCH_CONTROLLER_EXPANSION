"""Run original F5 staging, all visible controls and cancellation in each build."""
import sys,struct
from unicorn import x86_const as r
from test_native_controller_settings import ControllerMachine,v
class GraphicsMachine(ControllerMachine):
 def hook(self,u,a,size,data):
  hardware=(0x5ce180,0x5c8ca0,0x5c56a2,0x5c680b) if self.ed.short=="retail" else (0x5c8a10,0x5c34e6,0x5bff42,0x5c10da)
  if a in hardware:
   sp=u.reg_read(r.UC_X86_REG_ESP);u.reg_write(r.UC_X86_REG_EIP,struct.unpack("<I",u.mem_read(sp,4))[0]);u.reg_write(r.UC_X86_REG_ESP,sp+4);u.reg_write(r.UC_X86_REG_EAX,1);return
  return super().hook(u,a,size,data)
for path in sys.argv[1:]:
 m=GraphicsMachine(path);proc=0x427a60 if m.ed.short=='jpre' else 0x427e00
 site=0x5c1d63 if m.ed.short=='jpre' else 0x5c7494
 assert bytes(m.u.mem_read(site,1))==b"\xe8"
 finish=site+5+struct.unpack("<i",m.u.mem_read(site+1,4))[0]
 ui=next(x for x in m.pe.sections if x['name'].rstrip(b"\0")==b".vohr")
 assert finish==m.pe.base+ui['vaddr']+v.UI_DLG_DONE
 for id in (1075,1077,1079,1078):
  for save in (False,True):
   m.controls={};m.call(proc,(1,0x110,0,0));before=m.control(id)['checked'];m.control(id)['checked']=1-before
   m.call(proc,(1,0x111,id,0));m.call(proc,(1,0x111,1072 if save else 2,0));m.call(finish);m.controls={};m.call(proc,(1,0x110,0,0))
   assert m.control(id)['checked']==(1-before if save else before),(m.ed.short,id,save,m.control(id))
 for group in ((1056,1057),(1058,1059),(1068,1069),(1070,1073)):
  for id in group:
   for save in (False,True):
    m.controls={};m.call(proc,(1,0x110,0,0));before=[m.control(n)['checked'] for n in group]
    for n in group:m.control(n)['checked']=int(n==id)
    m.call(proc,(1,0x111,id,0));m.call(proc,(1,0x111,1072 if save else 2,0));m.call(finish);m.controls={};m.call(proc,(1,0x110,0,0))
    expected=[int(n==id) for n in group] if save else before
    assert [m.control(n)['checked'] for n in group]==expected,(m.ed.short,id,save,expected,m.controls)
 print(m.ed.short,'PASS original F5: Sky, three textures, resolution, field, motion, split; every value Save/Cancel through original procedure')
