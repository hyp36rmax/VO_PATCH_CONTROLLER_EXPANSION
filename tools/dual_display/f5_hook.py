"""Opt-in private F5 callback bridge; not installed by the normal patcher yet.

Fail closed until normal-startup Display/F4 integration is validated. Used only
for internal hook tests. Original F5 resources and callback remain untouched.
"""
from pathlib import Path
import struct
import subprocess
import tempfile
import mode_profiles

SITES = {'retail': (0x5c747d, 0x427e00), 'jpre': (0x5c1d4c, 0x427a60)}

def install(data, edition):
    v = mode_profiles.engineering3840.load_private()
    data = bytearray(data)
    pe = v._PE(data)
    site, original = SITES[edition.short]
    offset = pe.off(site - pe.base)
    if data[offset:offset + 5] != b'\x68' + struct.pack('<I', original):
        raise ValueError('unverified F5 callback argument')
    address, raw = v.add_section(data, 1024, b'\0' * 1024, name=b'.vof5')
    f11_at = edition.off(v.cave_va('F11PAUSE', edition))
    f11_original = v.link('F11PAUSE', edition)
    template = next((sec for sec in pe.sections if sec['name']==b'.voxt'),None)
    if template:
        f11_original=f11_original.replace(struct.pack('<I',v.MAGIC_TEMPLATE),struct.pack('<I',pe.base+template['vaddr']))
    f11_enabled = template is not None and data[f11_at:f11_at+len(f11_original)] == f11_original
    if template and not f11_enabled:raise ValueError('unverified F11 callback')
    f11_callback = struct.unpack_from('<I', f11_original, 0xd)[0]
    assert f11_original[0xc] == 0x68
    source = f'''bits 32
org {address}
entry:
    cmp dword [function],0
    jne ready
    push dllname
    call [{edition.symbols['LOADLIB']}]
    test eax,eax
    jz fallback
    push procname
    push eax
    call [{edition.symbols['GETPROC']}]
    test eax,eax
    jz fallback
    mov [function],eax
ready:
    push dword {original}
    push dword [esp+20]
    push dword [esp+20]
    push dword [esp+20]
    push dword [esp+20]
    call [function]
    ret 16
fallback:
    jmp {original}
align 4
function: dd 0
dllname: db 'vodisplay.dll',0
procname: db 'VonDisplayF5',0
times 256-($-$$) db 0
f11entry:
    cmp dword [f11function],0
    jne f11ready
    push dllname
    call [{edition.symbols['LOADLIB']}]
    test eax,eax
    jz f11fallback
    push f11name
    push eax
    call [{edition.symbols['GETPROC']}]
    test eax,eax
    jz f11fallback
    mov [f11function],eax
f11ready:
    push dword {f11_callback}
    push dword [esp+20]
    push dword [esp+20]
    push dword [esp+20]
    push dword [esp+20]
    call [f11function]
    ret 16
f11fallback:
    jmp {f11_callback}
align 4
f11function: dd 0
f11name: db 'VonDiagnosticsF11',0
'''
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'hook.asm'; dest = Path(td) / 'hook.bin'
        src.write_text(source)
        subprocess.run(['nasm', '-f', 'bin', str(src), '-o', str(dest)], check=True)
        code = dest.read_bytes()
    assert len(code) <= 512
    data[raw:raw + len(code)] = code
    struct.pack_into('<I', data, offset + 1, address)
    if f11_enabled:struct.pack_into('<I', data, f11_at + 0xd, address + 256)
    from resize_guard import install as guard
    image, guard_meta = guard(data, edition)
    return image, dict(entry=address, f11_original=f11_callback, f11_enabled=f11_enabled, original=original, site=site, raw=raw, code=code.hex(), resize_guard=guard_meta)
