"""Execute production x86 hooks with API doubles; never substitute a game run."""
from pathlib import Path
import hashlib,struct,sys
import unicorn
from unicorn import x86_const as r
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dual_display'))
import mode_profiles
from install import install
v=mode_profiles.engineering3840.load_private()
def verify(path):
 raw=path.read_bytes();edition=v.BUILDS[hashlib.md5(raw).hexdigest()]
 for mask in range(8):
  wanted=dict.fromkeys(v.by_key(edition),True)
  for i,k in enumerate(('padxinput','debugbox','credits')):wanted[k]=bool(mask&(1<<i))
  before,_=mode_profiles.build(raw,'wide',wanted);image,meta=install(before,edition,v)
  pe=v._PE(image);old=v._PE(before);s=meta['symbols'];entry=meta['entries']
  permitted=set()
  for patch in meta['patches']:
   off=patch['offset'];a=bytes.fromhex(patch['before']);b=bytes.fromhex(patch['after'])
   assert before[off:off+len(a)]==a and image[off:off+len(b)]==b
   permitted.update(range(off,off+len(a)))
  for off,n in ((pe.pe+6,2),(pe.opt+56,4),(pe.opt+pe.optsz+old.nsec*40,40)):permitted.update(range(off,off+n))
  assert all(a==b or i in permitted for i,(a,b) in enumerate(zip(before,image)))
  for scenario in ('missing-dll','missing-export','closed','open','empty','mouse'):
   u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_32);u.mem_map(0x400000,0x5000000);u.mem_map(0x10000000,0x20000)
   sec=pe.sections[-1];u.mem_write(s['SECTION_VA'],image[sec['raddr']:sec['raddr']+sec['vsize']])
   load,get,step,peek,stop=[0x10010000+i*16 for i in range(5)]
   for name,addr,n in [('LOADLIB',load,1),('GETPROC',get,2),('PEEKMSG',peek,5)]:
    u.mem_write(s[name],struct.pack('<I',addr));u.mem_write(addr,b'\xc2'+struct.pack('<H',4*n))
   u.mem_write(step,b'\xc2\x18\x00')
   for name,n in [('ORIGINAL_WNDPROC',4),('ORIGINAL_PUMP',5),('ORIGINAL_IDLE',0),('FRAME',0),('ORIGINAL_PRESENT',0)]:
    if s[name]:u.mem_write(s[name],b'\xc2'+struct.pack('<H',4*n))
   u.mem_write(s['HWND'],struct.pack('<I',0x1234));u.mem_write(s['PRIMARY'],struct.pack('<I',0x4567))
   msg=0x10004000;u.mem_write(msg,struct.pack('<4I',0x1234,0x200 if scenario=='mouse' else 0x100,0x28,0))
   calls=[]
   def hook(cpu,address,size,data):
    sp=cpu.reg_read(r.UC_X86_REG_ESP)
    if address==load:cpu.reg_write(r.UC_X86_REG_EAX,0 if scenario=='missing-dll' else 1);calls.append('load')
    elif address==get:cpu.reg_write(r.UC_X86_REG_EAX,0 if scenario=='missing-export' else step);calls.append('get')
    elif address==step:
     args=struct.unpack('<6I',cpu.mem_read(sp+4,24));assert args[0]==0x1234
     values=struct.unpack('<21I',cpu.mem_read(args[1],84))
     assert values==(84,*(s[k] for k in ('PRIMARY','BACK','INACTIVE','GAMEMODE','MODE','SUBMODE','MOVIEFLAG','GPAUSE','GRESUME','ALLOWED','FRAME','CUSTOM1','DZTHR1','DEVICES','BINDS1','COND','TWINBINDS','HORIBINDS','MODE2','CDSTOP')))
     calls.append(('step',args[2]));cpu.reg_write(r.UC_X86_REG_EAX,int(scenario in ('open','mouse')))
    elif address==peek or (s['ORIGINAL_PUMP'] and address==s['ORIGINAL_PUMP']):
     assert struct.unpack('<5I',cpu.mem_read(sp+4,20))==(msg,0,0,0,1)
     calls.append('original-poll');cpu.reg_write(r.UC_X86_REG_EAX,0 if scenario=='empty' else 1)
    elif address==s['ORIGINAL_PRESENT']:
     calls.append('original-present');cpu.reg_write(r.UC_X86_REG_EAX,0x4567)
    elif address==s['FRAME']:calls.append('frame')
    elif address==s['ORIGINAL_IDLE']:calls.append('original-idle');cpu.reg_write(r.UC_X86_REG_EAX,77)
    elif address==s['ORIGINAL_WNDPROC']:calls.append('original-wndproc');cpu.reg_write(r.UC_X86_REG_EAX,77)
   u.hook_add(unicorn.UC_HOOK_CODE,hook)
   def execute(name,args):
    regs=(r.UC_X86_REG_EBX,r.UC_X86_REG_EBP,r.UC_X86_REG_ESI,r.UC_X86_REG_EDI)
    for i,reg in enumerate(regs):u.reg_write(reg,0x11220000+i)
    sp=0x10002000;u.reg_write(r.UC_X86_REG_ESP,sp);u.mem_write(sp,struct.pack('<'+'I'*(len(args)+1),stop,*args))
    u.emu_start(entry[name],stop,count=500)
    assert u.reg_read(r.UC_X86_REG_EIP)==stop and u.reg_read(r.UC_X86_REG_ESP)==sp+4+4*len(args)
    for i,reg in enumerate(regs):assert u.reg_read(reg)==0x11220000+i
    return u.reg_read(r.UC_X86_REG_EAX)
   assert execute('pump',(msg,0,0,0,1))==int(scenario!='empty')
   assert calls.count('original-poll')==1
   assert struct.unpack('<I',u.mem_read(msg+4,4))[0]==(0 if scenario=='open' else 0x200 if scenario=='mouse' else 0x100)
   calls.clear();execute('pump',(msg,0,0,0,1));assert 'load' not in calls and 'get' not in calls
   calls.clear();assert execute('idle',())==77;assert 'frame' not in calls;assert calls.count('original-idle')==1
   if scenario not in ('missing-dll','missing-export'):assert calls==[('step',1),'original-idle',('step',5)]
   calls.clear();u.reg_write(r.UC_X86_REG_EFLAGS,0x246);assert execute('present',())==0x4567
   assert u.reg_read(r.UC_X86_REG_EFLAGS)==0x246
   assert ('original-present' in calls)==bool(s['ORIGINAL_PRESENT'])
   assert (('step',3) in calls)==(scenario not in ('missing-dll','missing-export'))
   calls.clear();u.mem_write(s['KEYCHECK'],struct.pack('<I',1));execute('keyboard',())
   assert (('step',4) in calls)==(scenario not in ('missing-dll','missing-export'))
   assert not u.reg_read(r.UC_X86_REG_EFLAGS)&0x40
   u.mem_write(s['KEYCHECK'],struct.pack('<I',0));execute('keyboard',());assert u.reg_read(r.UC_X86_REG_EFLAGS)&0x40
   calls.clear();value=execute('wndproc' ,(0x1234,0x100,0x74,0))
   assert value==(0 if scenario in ('open','mouse') else 77)
 print(edition.short+': PASS 8 option combinations x 6 ABI scenarios; exact hook guards, fallback, poll preservation, context, register/stack balance, render seam')
for arg in sys.argv[1:]:verify(Path(arg))
