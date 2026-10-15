"""Private pre-entry profile plan, built offline; no running-file replacement.

A common loader layout reserves the largest validated profile. Activation writes
only verified differences from Wide to one selected profile before game startup.
Import/relocation/TLS tables and headers are never runtime write targets.
Not installed by the public patcher until the complete lifecycle passes.
"""
import hashlib
import zlib
import struct
import mode_profiles
import f5_hook


def mapped(data):
    v = mode_profiles.engineering3840.load_private()
    pe = v._PE(data)
    size = struct.unpack_from('<I', data, pe.opt + 56)[0]
    image = bytearray(size)
    for s in pe.sections:
        image[s['vaddr']:s['vaddr']+s['rsize']] = data[s['raddr']:s['raddr']+s['rsize']]
    return image


def spans(a, b):
    # Most of the reserved image is identical zero-filled storage. Compare pages
    # first; only changed pages need byte-level records. Adjacent records are safe.
    for page in range(0, len(a), 4096):
        left, right = a[page:page+4096], b[page:page+4096]
        if left == right:
            continue
        start = None
        for i, (x, y) in enumerate(zip(left, right)):
            if x != y and start is None:
                start = i
            if x == y and start is not None:
                yield page+start, bytes(left[start:i]), bytes(right[start:i])
                start = None
        if start is not None:
            yield page+start, bytes(left[start:]), bytes(right[start:])


def protected(data):
    """Loader-resolved IAT cells as well as all non-resource data directories."""
    v = mode_profiles.engineering3840.load_private(); pe = v._PE(data)
    ranges = [(0, struct.unpack_from('<I', data, pe.opt+60)[0])]
    for i in range(16):
        rva, size = struct.unpack_from('<II', data, pe.opt+96+8*i)
        if rva and size and i not in (2, 4):  # resources and file certificate
            ranges.append((rva, rva+size))
    rva = pe.import_rva
    if rva:
        while True:
            desc = struct.unpack_from('<5I', data, pe.off(rva))
            if not any(desc): break
            source, _, _, _, dest = desc
            source = source or dest
            n = 0
            while struct.unpack_from('<I', data, pe.off(source+4*n))[0]: n += 1
            ranges.append((dest, dest+4*(n+1)))
            rva += 20
    return ranges


def plan(raw, wanted=None):
    v = mode_profiles.engineering3840.load_private()
    images = {name: mode_profiles.build(raw, name, wanted)[0] for name in mode_profiles.PROFILES}
    # Place the existing F5 section at one common address without changing any
    # profile's linked addresses. Padding has no code or persisted configuration.
    largest_pe = v._PE(images['dual'])
    end = struct.unpack_from('<I', images['dual'], largest_pe.opt+56)[0]
    for name, image in list(images.items()):
        image = bytearray(image); pe = v._PE(image)
        own_end = struct.unpack_from('<I', image, pe.opt+56)[0]
        if own_end < end:
            v.add_section(image, end-own_end, name=b'.vofill')
        images[name], _ = f5_hook.install(image, v.BUILDS[hashlib.md5(raw).hexdigest()])
        from unified_overlay.install import install as overlay_install
        images[name], _ = overlay_install(images[name],v.BUILDS[hashlib.md5(raw).hexdigest()],v)
    largest = images['dual']; template = v._PE(largest)
    maps = {n: mapped(data) for n, data in images.items()}
    size = len(maps['dual']); base = maps['wide'] + bytes(size-len(maps['wide']))
    forbidden = protected(largest)
    entries = {}
    for name, data in images.items():
        pe = v._PE(data)
        if pe.base != template.base or pe.entry_rva != template.entry_rva:
            raise ValueError('profile startup chain differs')
        # Loader layout must contain every profile at the same virtual address.
        for s in pe.sections:
            if s['name']==b'.vofill': continue
            target = next((t for t in template.sections if t['name']==s['name']), None)
            if not target or target['vaddr'] != s['vaddr'] or max(s['vsize'],s['rsize']) > max(target['vsize'],target['rsize']):
                raise ValueError('profile section does not fit common loader layout')
        target = maps[name] + bytes(size-len(maps[name]))
        writes = list(spans(base, target))
        for offset, before, after in writes:
            if any(offset < end and offset+len(after) > begin for begin,end in forbidden):
                raise ValueError('activation would overwrite loader-owned memory')
        entries[name] = writes
    return base, entries, {'base':template.base,'entry':template.base+template.entry_rva,
                           'image_size':size,'protected':forbidden,
                           'edition':v.BUILDS[hashlib.md5(raw).hexdigest()].short,
                           'template':largest, 'images':images}


def activate(image, writes):
    """Reference two-pass contract: reject the whole plan before any mutation."""
    for offset, before, after in writes:
        if len(before)!=len(after) or offset<0 or offset+len(after)>len(image):
            raise ValueError('invalid activation range')
        if image[offset:offset+len(before)] != before:
            raise ValueError('pre-initialization image mismatch')
    for offset, before, after in writes:
        image[offset:offset+len(after)] = after


def build(raw, wanted=None):
    """Produce one PE with Wide initial memory and a bounded embedded plan table."""
    import subprocess
    import tempfile
    from pathlib import Path
    base, plans, meta = plan(raw, wanted)
    v = mode_profiles.engineering3840.load_private(); edition = v.BUILDS[hashlib.md5(raw).hexdigest()]
    data = bytearray(meta['template']); pe = v._PE(data)
    for section in pe.sections:
        start, size = section['vaddr'], section['rsize']
        data[section['raddr']:section['raddr']+size] = base[start:start+size]
    # Header: magic/version, mapped-size, profile count; each record is a bounded
    # RVA, length, expected bytes, replacement bytes. No executable paths stored.
    table = bytearray(struct.pack('<5I',0x33504f56,2,len(base),5,0 if wanted is not None and not wanted.get('hires') else 1))
    for name in mode_profiles.PROFILES:
        rows=plans[name]; table += struct.pack('<I',len(rows))
        for offset,before,after in rows:
            table += struct.pack('<II',offset,len(before))+before+after
    address, offset = v.add_section(data,512+len(table),bytes(512)+table,name=b'.voboot')
    source=f'''bits 32
org {address}
pushfd
pushad
push dllname
call [{edition.symbols['LOADLIB']}]
test eax,eax
jz failed
push procname
push eax
call [{edition.symbols['GETPROC']}]
test eax,eax
jz failed
push {zlib.crc32(table)}
push {len(table)}
push {address+512}
push {pe.base}
call eax
test eax,eax
jz failed
popad
popfd
push {meta['entry']}
ret
failed:
; Do not enter a half-activated image. The helper reports activation failures.
; Missing helper is an installation failure, not a hidden Wide fallback.
push kernel
call [{edition.symbols['LOADLIB']}]
push exitname
push eax
call [{edition.symbols['GETPROC']}]
push 1
call eax
ud2
dllname: db 'vodisplay.dll',0
procname: db 'VonDisplayStartup',0
kernel: db 'kernel32.dll',0
exitname: db 'ExitProcess',0
'''
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/'boot.asm';dest=Path(td)/'boot.bin';src.write_text(source)
        subprocess.run(['nasm','-f','bin',str(src),'-o',str(dest)],check=True)
        code=dest.read_bytes()
    assert len(code)<=512
    data[offset:offset+len(code)]=code
    struct.pack_into('<I',data,pe.off_entry,address-pe.base)
    return bytes(data), {'edition':meta['edition'],'entry':address,'original_entry':meta['entry'],
                         'table':address+512,'table_size':len(table),'image_size':len(base),
                         'writes':{name:len(rows) for name,rows in plans.items()}}
