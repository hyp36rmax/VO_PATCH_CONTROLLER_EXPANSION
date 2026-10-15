"""Execute original F6 procedures, supported choices and Save/Cancel boundaries.
Win32 controls are API doubles; this is not Windows presentation acceptance.
"""
from pathlib import Path
import sys,struct,hashlib,json
import unicorn
from unicorn import x86_const as r
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dual_display'))
import mode_profiles
v=mode_profiles.engineering3840.load_private()
def u32(b,offset=0):return struct.unpack_from('<I',b,offset)[0]
class Machine:
 def __init__(self,path):
  raw=Path(path).read_bytes();self.ed=v.BUILDS[hashlib.md5(raw).hexdigest()]
  self.data,_=mode_profiles.build(raw,'wide',dict.fromkeys(v.by_key(self.ed),True));self.pe=pe=v._PE(self.data)
  self.u=u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32);u.mem_map(0x400000,0x5000000);u.mem_map(0x10000000,0x100000)
  for s in pe.sections:u.mem_write(pe.base+s['vaddr'],self.data[s['raddr']:s['raddr']+s['rsize']])
  self.controls={};self.imports={};self.calls=[]
  sec=next(s for s in pe.sections if s['name'].rstrip(b'\0')==b'.idata')
  p=sec['raddr'];n=0
  def off(rva):return pe.off(rva)
  while True:
   ilt,_,_,name,iat=struct.unpack_from('<5I',self.data,p)
   if not name:break
   k=0
   while True:
    item=u32(self.data,off((ilt or iat)+k*4))
    if not item:break
    name='#'+str(item&65535) if item&0x80000000 else self.data[off(item)+2:].split(b'\0',1)[0].decode()
    address=0x10080000+n*16;n+=1
    self.imports[address]=name;u.mem_write(pe.base+iat+k*4,struct.pack('<I',address));u.mem_write(address,b'\xc3');k+=1
   p+=20
  u.hook_add(unicorn.UC_HOOK_CODE,self.hook)
 def string(self,a):
  data=bytes(self.u.mem_read(a,256));return data.split(b'\0',1)[0].decode('latin1')
 def control(self,id):return self.controls.setdefault(id,{'items':[],'selection':-1,'checked':0})
 def hook(self,u,a,size,data):
  if a not in self.imports:return
  name=self.imports[a];sp=u.reg_read(r.UC_X86_REG_ESP);args=struct.unpack('<6I',u.mem_read(sp+4,24));result=1
  if name=='SendDlgItemMessageA':
   hwnd,id,msg,wp,lp=args[:5];c=self.control(id);n=5
   if msg==0x143:c['items'].append(self.string(lp));result=len(c['items'])-1
   elif msg==0x14e:c['selection']=wp;result=wp
   elif msg==0x147:result=c['selection']
   elif msg==0xf0:result=c['checked']
   elif msg==0xf1:c['checked']=wp
   else:raise RuntimeError((name,hex(msg),args))
  elif name=='CheckDlgButton':n=3;self.control(args[1])['checked']=args[2]
  elif name=='CheckRadioButton':
   n=4
   for id in range(args[1],args[2]+1):self.control(id)['checked']=int(id==args[3])
  elif name=='IsDlgButtonChecked':n=2;result=self.control(args[1])['checked']
  elif name=='GetDlgItem':n=2;result=args[1]
  elif name in ('EnableWindow','ShowWindow','EndDialog'):n=2
  elif name=='SetFocus':n=1
  else:raise RuntimeError((name,args,hex(a)))
  self.calls.append(name);u.reg_write(r.UC_X86_REG_EAX,result&0xffffffff);u.reg_write(r.UC_X86_REG_EIP,u32(u.mem_read(sp,4)));u.reg_write(r.UC_X86_REG_ESP,sp+4+n*4)
 def call(self,addr,args=()):
  sp=0x10010000;stop=0x10070000;self.u.mem_write(sp,struct.pack('<'+'I'*(1+len(args)),stop,*args));self.u.reg_write(r.UC_X86_REG_ESP,sp)
  self.u.emu_start(addr,stop,count=1000000)
  assert self.u.reg_read(r.UC_X86_REG_EIP)==stop,hex(self.u.reg_read(r.UC_X86_REG_EIP))
  return self.u.reg_read(r.UC_X86_REG_EAX)
for path in sys.argv[1:]:
 m=Machine(path);name=m.ed.short;delta=0 if name=='retail' else -0x5760;ptr=0x1ce1dbc if name=='retail' else 0x1cdca64
 m.u.mem_write(ptr,struct.pack('<I',0x10020000));m.call(0x5cbf05+delta)
 result={}
 for page,proc,default in [('1P',0x5cafe0,1012),('2P',0x5cb518,1021),('General',0x5cb95a,1041),('Appendix',0x5cbcc9,1028)]:
  m.controls={};m.call(proc+delta,(1,0x110,0,0));m.call(proc+delta,(1,0x111,default,0));result[page]=m.controls
 assert result['1P'][1000]['items']==[str(n)+'secs' for n in range(30,100,5)]+['DeathMatch']
 assert result['1P'][1004]['items']==['Once','Twice','3 Times','4 Times','5 Times']
 assert result['1P'][1007]['items']==['Easy','Normal','Hard','Very Hard']
 assert [result['1P'][i]['selection'] for i in range(1000,1008)]==[12,6,12,12,0,0,0,1]
 assert result['2P'][1014]['selection']==0  # original Defaults is Once, not captured Twice
 assert all(result['General'][i]['checked']==int(i!=1079) for i in range(1074,1082))
 assert [result['Appendix'][i]['checked'] for i in range(1076,1080)]==[0,0,0,1]
 print(name,'original native F6 initialization/defaults executed',len(m.calls),'native API calls')

 for page,proc,ids in [('1P',0x5cafe0,range(1000,1008)),('2P',0x5cb518,range(1013,1015))]:
  for id in ids:
   for choice in range(len(result[page][id]['items'])):
    m.call(0x5cbf05+delta);m.controls={};m.call(proc+delta,(1,0x110,0,0))
    before=m.control(id)['selection'];m.control(id)['selection']=choice
    m.call(proc+delta,(1,0x111,id|(1<<16),0))
    m.call(0x5cbf05+delta);m.controls={};m.call(proc+delta,(1,0x110,0,0))
    assert m.control(id)['selection']==before,(name,page,id,'cancel')
    m.control(id)['selection']=choice;m.call(proc+delta,(1,0x111,id|(1<<16),0))
    m.call(0x5cbf60+delta);m.call(0x5cbf05+delta);m.controls={};m.call(proc+delta,(1,0x110,0,0))
    assert m.control(id)['selection']==choice,(name,page,id,'save',choice,m.control(id))
 print(name,'PASS every 1P/2P combo value commits through original F6 apply and discards through original snapshot')
 for page,proc,ids in [('General',0x5cb95a,(1074,1075,1076,1079,1080,1081)),('Appendix',0x5cbcc9,(1076,1077))]:
  for id in ids:
   m.call(0x5cbf05+delta);m.controls={};m.call(proc+delta,(1,0x110,0,0))
   before=m.control(id)['checked'];m.call(proc+delta,(1,0x111,id,0))
   m.call(0x5cbf05+delta);m.controls={};m.call(proc+delta,(1,0x110,0,0))
   assert m.control(id)['checked']==before,(name,page,id,'cancel')
   m.call(proc+delta,(1,0x111,id,0));m.call(0x5cbf60+delta)
   m.call(0x5cbf05+delta);m.controls={};m.call(proc+delta,(1,0x110,0,0))
   assert m.control(id)['checked']==1-before,(name,page,id,'save')
 for color in (1078,1079):
  m.call(0x5cbf05+delta);m.call(0x5cbcc9+delta,(1,0x111,color,0));m.call(0x5cbf60+delta)
  m.call(0x5cbf05+delta);m.controls={};m.call(0x5cbcc9+delta,(1,0x110,0,0))
  assert m.control(color)['checked']==1 and m.control(2157-color)['checked']==0
 print(name,'PASS General/Appendix boolean Save/Cancel and both original color formats')
