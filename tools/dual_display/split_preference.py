"""Dedicated Versus effective split without changing the original saved bit.

Uses unused space in the existing .vovs allocation; no new configuration key or
section. Original F5/INI continuations remain the consumers of staged flags.
"""
from pathlib import Path
import struct
import subprocess
import tempfile
import mode_profiles
engineering3840 = mode_profiles.engineering3840


def install(image, edition):
    v = engineering3840.load_private()
    data = bytearray(image); pe = v._PE(data)
    ui = next(s for s in pe.sections if s['name'] == b'.vohr')
    vs = next(s for s in pe.sections if s['name'] == b'.vovs')
    uv = pe.base + ui['vaddr']
    port = None if edition.short == 'retail' else v.PORT['%08x' % v._pe_stamp(data)]
    def offset(raw): return raw if port is None else port['off'][raw][0]
    def address(va): return va if port is None else port['va'][va]
    flags = address(0x6bf598)
    hooks = []
    for name, site, target in (
        ('dialog_init',0x427ec4,v.UI_DLG_INIT),('dialog_ok',0x42823c,v.UI_DLG_OK),
        ('ini_load',0x50bcc1,v.UI_INI_LOAD),('ini_save',0x50c0c6,v.UI_INI_SAVE)):
        off=offset(site-0x400c00);va=v._va_at(pe,off)
        assert data[off]==0xe9 and va+5+struct.unpack_from('<i',data,off+1)[0]==uv+target
        hooks.append((name,off,va,uv+target))
    # Capture defaults before the existing frame or either marker forces vertical.
    for name, raw in (('frame',0x1c751b),('marker_a',0x5485c0-0x400c00),('marker_b',0x475930-0x400c00)):
        if name=='frame':off=offset(raw)
        else:off=pe.off((0x5485c0 if name=='marker_a' else 0x475930)-pe.base) if port is None else pe.off((0x543d60 if name=='marker_a' else 0x474940)-pe.base)
        va=v._va_at(pe,off);assert data[off] in (0xe8,0xe9)
        target=va+5+struct.unpack_from('<i',data,off+1)[0]
        assert pe.base+vs['vaddr']<=target<pe.base+vs['vaddr']+vs['vsize']
        hooks.append((name,off,va,target))
    used=len(bytes(data[vs['raddr']:vs['raddr']+vs['rsize']]).rstrip(b'\0'))
    used=(used+15)&~15;start=pe.base+vs['vaddr']+used
    lines=['bits 32',f'org {start}',
      'seed:', 'cmp dword [initialized],0','jne seeded','push eax',f'mov eax,[{flags}]','and eax,2','mov [preference],eax','mov dword [initialized],1','pop eax','seeded:','ret']
    for name,off,va,target in hooks:
        lines += [name+':']
        if name in ('frame','marker_a','marker_b','dialog_init','ini_save'):
            lines += ['pushfd','call seed','popfd']
        if name=='dialog_init':lines += ['and eax,0xfffffffd','or eax,[preference]',f'jmp {target}']
        elif name=='dialog_ok':lines += ['push eax','and eax,2','mov [preference],eax','mov dword [initialized],1','pop eax','and eax,0xfffffffd',f'jmp {target}']
        elif name=='ini_load':lines += ['pushfd','push eax',f'mov eax,[{flags}]','and eax,2','mov [preference],eax','mov dword [initialized],1',f'and dword [{flags}],0xfffffffd','pop eax','popfd',f'jmp {target}']
        elif name=='ini_save':lines += [f'mov eax,[{flags}]','and eax,0xfffffffd','or eax,[preference]',f'or eax,[{uv+v.UI_F4MODE}]',f'jmp {address(0x50c0cb)}']
        else:lines += [f'jmp {target}']
    lines += ['align 4','preference: dd 0','initialized: dd 0','labels:','dd '+','.join([h[0] for h in hooks]+['preference','initialized'])]
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/'split.asm';dest=Path(td)/'split.bin';src.write_text('\n'.join(lines)+'\n')
        subprocess.run(['nasm','-f','bin',str(src),'-o',str(dest)],check=True);blob=dest.read_bytes()
    if used+len(blob)>vs['rsize']:raise ValueError('split preference exceeds verified VS allocation')
    labels=struct.unpack('<'+'I'*(len(hooks)+2),blob[-4*(len(hooks)+2):])
    data[vs['raddr']+used:vs['raddr']+used+len(blob)]=blob
    for (_,off,va,_),entry in zip(hooks,labels):struct.pack_into('<i',data,off+1,entry-va-5)
    return bytes(data),{'flags':flags,'ui':uv,'preference':labels[-2],'initialized':labels[-1],
      'entries':{h[0]:a for h,a in zip(hooks,labels)},'continuations':{h[0]:h[3] for h in hooks},'ini_save_return':address(0x50c0cb)}
