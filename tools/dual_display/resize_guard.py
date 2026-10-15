"""Guard a private F4 transition before any mask/surface mutation.

Uses the F5 helper allocation. Missing helper holds the current presentation.
The helper allows legacy Single transitions and retains dual presentation until
its low-resolution source/GPU contract is validated.
"""
from pathlib import Path
import struct
import subprocess
import tempfile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import mode_profiles


def install(image,edition):
 v=mode_profiles.engineering3840.load_private();data=bytearray(image);pe=v._PE(data)
 holder=next(s for s in pe.sections if s['name']==b'.vof5')
 ui=next((s for s in pe.sections if s['name']==b'.vohr'),None)
 port=None if edition.short=='retail' else v.PORT['%08x'%v._pe_stamp(data)]
 addr=lambda a:a if port is None else port['va'][a]
 if ui:
  base=pe.base+ui['vaddr'];md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
  # First forward call in the retained toggle is f4_switch; its first call is apply.
  code=bytes(data[ui['raddr']+v.UI_F4:ui['raddr']+v.UI_DLG_INIT])
  call=next(i for i in md.disasm(code,base+v.UI_F4) if i.mnemonic=='call' and i.operands[0].imm>i.address+5)
  site=call.operands[0].imm;off=pe.off(site-pe.base);assert data[off]==0xe8
  original=site+5+struct.unpack_from('<i',data,off+1)[0]
  allowed=f'call {original}\njmp {site+5}';denied='ret';length=5
  ini_code=bytes(data[ui['raddr']+v.UI_INI_LOAD:ui['raddr']+v.UI_INI_SAVE])
  ini_calls=[i for i in md.disasm(ini_code,base+v.UI_INI_LOAD) if i.mnemonic=='call' and i.operands[0].imm==original]
  assert len(ini_calls)==1
  ini_site=ini_calls[0].address
 else:
  off=0x1c68ec if port is None else port['off'][0x1c68ec][0];site=v._va_at(pe,off)
  displaced=bytes(data[off:off+7]);assert displaced==b'\xf6\x05'+struct.pack('<I',addr(0x6bf598))+b'\x04'
  allowed='db '+','.join(str(x) for x in displaced)+f'\njmp {site+7}'
  denied=f'jmp {addr(0x5c7dfe)}';original=site+7;length=7
  ini_off=0x50bcc1-0x400c00 if port is None else port['off'][0x50bcc1-0x400c00][0]
  ini_site=v._va_at(pe,ini_off);ini_displaced=bytes(data[ini_off:ini_off+5]);assert ini_displaced[0]==0x68
 used=(len(bytes(data[holder['raddr']:holder['raddr']+holder['rsize']]).rstrip(b'\0'))+16)&~15
 entry=pe.base+holder['vaddr']+used
 source=f'''bits 32
org {entry}
pushfd
pushad
cmp dword [function],0
jne resolved
push dllname
call [{edition.symbols['LOADLIB']}]
test eax,eax
jz deny
push procname
push eax
call [{edition.symbols['GETPROC']}]
test eax,eax
jz deny
mov [function],eax
resolved:
push dword [{edition.symbols['HWND']}]
call [function]
test eax,eax
jz deny
popad
popfd
{allowed}
deny:
popad
popfd
{denied}
align 4
function: dd 0
dllname: db 'vodisplay.dll',0
procname: db 'VonDisplayCanResize',0
'''
 prefix=source[source.index('pushfd'):source.index('popad\npopfd')]
 ini_prefix=prefix.replace('resolved','resolved_ini').replace('deny','deny_ini')
 if ui:
  # Same policy before the direct INI low-resolution apply, but return to its
  # original caller rather than entering surface recreation during startup.
  source+=f"\nini_entry:\n{ini_prefix}popad\npopfd\njmp {original}\ndeny_ini:\npopad\npopfd\nret\nini_label: dd ini_entry\n"
 else:
  continuation='db '+','.join(str(x) for x in ini_displaced)+f'\njmp {ini_site+5}'
  source+=f"\nini_entry:\n{ini_prefix}popad\npopfd\njmp ini_continue\ndeny_ini:\nand dword [{addr(0x6bf598)}],0xfffffffb\npopad\npopfd\nini_continue:\n{continuation}\nini_label: dd ini_entry\n"
 with tempfile.TemporaryDirectory() as td:
  src=Path(td)/'guard.asm';dest=Path(td)/'guard.bin';src.write_text(source)
  subprocess.run(['nasm','-f','bin',str(src),'-o',str(dest)],check=True);blob=dest.read_bytes()
 if used+len(blob)>holder['rsize']:raise ValueError('F4 guard exceeds helper allocation')
 data[holder['raddr']+used:holder['raddr']+used+len(blob)]=blob
 ini_entry=struct.unpack_from('<I',blob,len(blob)-4)[0]
 struct.pack_into('<i',data,pe.off(ini_site-pe.base)+1,ini_entry-ini_site-5)
 if not ui:data[pe.off(ini_site-pe.base)]=0xe9
 data[off:off+length]=b'\xe9'+struct.pack('<i',entry-site-5)+b'\x90'*(length-5)
 return bytes(data),{'entry':entry,'site':site,'allowed_target':original,'denied_target':None if ui else addr(0x5c7dfe),'hires':ui is not None,'ini_entry':ini_entry,'ini_site':ini_site,'flags':addr(0x6bf598)}
