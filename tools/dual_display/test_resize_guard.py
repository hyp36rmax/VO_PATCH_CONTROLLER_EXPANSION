"""Actual guard ABI: denial precedes table/surface changes, for all profiles."""
from pathlib import Path
import hashlib,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import mode_profiles,f5_hook
v=mode_profiles.engineering3840.load_private()
for folder in map(Path,sys.argv[1:]):
 raw=(folder/'v_on.exe').read_bytes();e=v.BUILDS[hashlib.md5(raw).hexdigest()]
 for profile in mode_profiles.PROFILES:
  data,_=mode_profiles.build(raw,profile);data,meta=f5_hook.install(data,e);g=meta['resize_guard'];pe=v._PE(data)
  for answer in (-1,0,1):
   mu=Uc(UC_ARCH_X86,UC_MODE_32);mu.mem_map(0x400000,0x4000000);mu.mem_map(0x7000000,0x10000)
   for s in pe.sections:mu.mem_write(pe.base+s['vaddr'],data[s['raddr']:s['raddr']+s['rsize']])
   load,resolve,helper,stop,sp=0x7000100,0x7000200,0x7000300,0x7001000,0x700f000
   mu.mem_write(e.symbols['LOADLIB'],struct.pack('<I',load));mu.mem_write(e.symbols['GETPROC'],struct.pack('<I',resolve));mu.mem_write(e.symbols['HWND'],struct.pack('<I',123))
   mu.mem_write(load,b'\xb8'+struct.pack('<I',0 if answer<0 else 1)+b'\xc2\x04\x00')
   mu.mem_write(resolve,b'\xb8'+struct.pack('<I',helper)+b'\xc2\x08\x00')
   mu.mem_write(helper,b'\xb8'+struct.pack('<I',max(answer,0))+b'\xc2\x04\x00')
   called=[]
   if g['hires']:
    mu.mem_write(g['allowed_target'],b'\xc3')
    destination=g['site']+5 if answer==1 else stop
   else:destination=g['allowed_target'] if answer==1 else g['denied_target']
   def check(m,a,size,user):
    if a==helper:
     stack=m.reg_read(UC_X86_REG_ESP);assert struct.unpack('<I',m.mem_read(stack+4,4))[0]==123
    if a==g['allowed_target']:called.append(a)
   mu.hook_add(UC_HOOK_CODE,check);mu.mem_write(sp,struct.pack('<I',stop));mu.reg_write(UC_X86_REG_ESP,sp)
   for reg,value in ((UC_X86_REG_EAX,91),(UC_X86_REG_EBX,92),(UC_X86_REG_ECX,93),(UC_X86_REG_EDX,94),(UC_X86_REG_ESI,95),(UC_X86_REG_EDI,96),(UC_X86_REG_EBP,97)):mu.reg_write(reg,value)
   # Snapshot every existing section except the guard's function-pointer cache.
   before={s['name']:bytes(mu.mem_read(pe.base+s['vaddr'],s['rsize'])) for s in pe.sections if s['name']!=b'.vof5'}
   mu.emu_start(g['entry'],destination,count=1000)
   if answer!=1:assert not called
   for s in pe.sections:
    if s['name'] in before:assert bytes(mu.mem_read(pe.base+s['vaddr'],s['rsize']))==before[s['name']]
   expected=sp+4 if g['hires'] and answer!=1 else sp
   assert mu.reg_read(UC_X86_REG_ESP)==expected
   for reg,value in ((UC_X86_REG_EAX,91),(UC_X86_REG_EBX,92),(UC_X86_REG_ECX,93),(UC_X86_REG_EDX,94),(UC_X86_REG_ESI,95),(UC_X86_REG_EDI,96),(UC_X86_REG_EBP,97)):assert mu.reg_read(reg)==value
   if g['hires']:
    ini_off=pe.off(g['ini_site']-pe.base)
    assert data[ini_off]==0xe8 and g['ini_site']+5+struct.unpack_from('<i',data,ini_off+1)[0]==g['ini_entry']
    mu.reg_write(UC_X86_REG_ESP,sp);mu.mem_write(sp,struct.pack('<I',stop));called.clear()
    mu.emu_start(g['ini_entry'],stop,count=1000)
    assert mu.reg_read(UC_X86_REG_ESP)==sp+4
    assert bool(called)==(answer==1)
    for section in pe.sections:
     if section['name'] in before:assert bytes(mu.mem_read(pe.base+section['vaddr'],section['rsize']))==before[section['name']]
   else:
    mu.mem_write(g['flags'],struct.pack('<I',7));mu.reg_write(UC_X86_REG_ESP,sp)
    mu.emu_start(g['ini_entry'],g['ini_site']+5,count=1000)
    assert mu.reg_read(UC_X86_REG_ESP)==sp-4
    assert struct.unpack('<I',mu.mem_read(g['flags'],4))[0]==(7 if answer==1 else 3)
  print('PASS',e.short,profile,'hotkey and direct INI allow/deny/missing helper; registers/stack and all existing section bytes preserved by guard')
