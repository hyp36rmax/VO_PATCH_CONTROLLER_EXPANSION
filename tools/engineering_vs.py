#!/usr/bin/env python3
"""Private 3840 local-VS integration. Never selected by public patcher imports.

Uses the existing frame_setup round predicate at indicator production time.
Existing 1P generators and blobs are unchanged. Requires nasm for this private build.
"""
import hashlib
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import engineering3840
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def build(original):
    vp = engineering3840.load_private()
    edition = vp.BUILDS[hashlib.md5(original).hexdigest()]
    if edition.short not in ('retail', 'jpre'):
        raise ValueError('private VS supports verified Retail/JPRE only')
    wanted = dict.fromkeys(vp.by_key(edition), True)
    wanted['hires'] = (3840, 1080)
    data, _, skipped = vp.apply_selected(bytearray(original), wanted, edition)
    if skipped:
        raise ValueError(skipped)
    port = None if edition.short == 'retail' else vp.PORT['%08x' % vp._pe_stamp(original)]
    offset = lambda x: x if port is None else port['off'][x][0]
    address = lambda x: x if port is None else port['va'][x]
    pe = vp._PE(data)
    ui = next(s for s in pe.sections if s['name'] == b'.vohr')
    ui_va = pe.base + ui['vaddr']
    # Only the dedicated VS image changes this factor; F4's alternate table is intact.
    struct.pack_into('<f', data, ui['raddr'] + vp.UI_KSBS, 1.0)
    geometry = vp.resolution_geometry(3840, 1080)
    vw = geometry['viewport_width'] // 2
    height = geometry['viewport_height']
    bound = 256 * vw / (height / 480) / 640
    margin = math.degrees(math.atan(vw / (height / 480) / 2 / (600 * 1.21875)) - math.atan(320 / (600 * 1.21875)))
    bearing = 0x1500 + round(margin * 65536 / 360)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    markers = []
    for name, entry, lo, positives in (
        ('a', 0x5485c0 if port is None else 0x543d60, 0x205d38, (0x147b60, 0x147cc8)),
        ('b', 0x475930 if port is None else 0x474940, 0x1fb4a0, (0x074ed0, 0x075038)),
    ):
        start = pe.off(entry - pe.base)
        displaced = bytes(data[start:start + 9])
        if displaced != bytes.fromhex('558bec81ece0000000'):
            raise ValueError('unverified marker prologue')
        instructions = []
        for ins in md.disasm(bytes(original[start:start+0x1800]), entry):
            instructions.append(ins)
            if ins.mnemonic == 'ret':
                break
        if not instructions or instructions[-1].mnemonic != 'ret':
            raise ValueError('marker boundary not verified')
        negatives = [pe.off(i.address-pe.base)+1 for i in instructions if bytes(i.bytes)==bytes.fromhex('3d00ebffff')]
        if len(negatives) != 2:
            raise ValueError('unverified bearing comparison count')
        fields = []
        for off, value in ((offset(lo), -bound), (offset(lo+4), bound)):
            fields.append((vp._va_at(pe, off), struct.unpack_from('<I',data,off)[0],struct.unpack('<I',struct.pack('<f',value))[0]))
        for off in [offset(x) for x in positives] + negatives:
            if original[off-1] != 0x3d:
                raise ValueError('unverified bearing instruction')
            value = -bearing if off in negatives else bearing
            fields.append((vp._va_at(pe,off),struct.unpack_from('<I',data,off)[0],value&0xffffffff))
        # Writable code/data already required by existing F4; enforce for every operand.
        for va, _, _ in fields:
            vp._make_writable(data, pe, pe.off(va-pe.base))
        markers.append(dict(name=name,entry=entry,displaced=displaced.hex(),fields=fields))
    blobva, raw = vp.add_section(data,4096,b'\0'*4096,name=b'.vovs')
    # This matches asm/ui.asm frame_setup, using the same live round mask.
    state = {k:address(a) for k,a in dict(split=0x6bc948,flags=0x6bf598,mode1=0x1ae3594,sub1=0x1ae3690,mode2=0x1ef8a90,sub2=0x1ef9eb0).items()}
    lines=['bits 32',f'org {blobva}']
    for marker in markers:
        n=marker['name']
        lines += [f'entry_{n}:','pushfd','pushad',f'cmp dword [{ui_va+vp.UI_MODEW}],3840',f'jne done_{n}']
        # Dedicated VS configuration selects existing Ver layout before production.
        lines += [f'cmp dword [{state["split"]}],0',f'je layout_{n}',f'and dword [{state["flags"]}],0xfffffffd',f'layout_{n}:']
        # Restore baseline for shared/full presentation before considering split.
        lines += [f'mov dword [{va}],{full}' for va,full,_ in marker['fields']]
        lines += [f'cmp dword [{state["split"]}],0',f'je done_{n}',f'test byte [{state["flags"]}],3',f'jnz done_{n}',f'cmp dword [{state["mode1"]}],4',f'jne done_{n}',f'mov edx,[{state["sub1"]}]','call is_round',f'jnz narrow_{n}',f'cmp dword [{state["mode2"]}],4',f'jne done_{n}',f'mov edx,[{state["sub2"]}]','call is_round',f'jz done_{n}',f'narrow_{n}:']
        lines += [f'mov dword [{va}],{half}' for va,_,half in marker['fields']]
        lines += [f'done_{n}:','popad','popfd','db '+','.join(str(x) for x in bytes.fromhex(marker['displaced'])),f'jmp {marker["entry"]+9}']
    lines += ['is_round:','cmp edx,64','jae no_round','mov ecx,edx','and ecx,31','mov eax,1','shl eax,cl','shr edx,5',f'test [{ui_va+vp.UI_SPLITST}+edx*4],eax','ret','no_round:','xor eax,eax','ret','frame_entry:','pushfd',f'cmp dword [{ui_va+vp.UI_MODEW}],3840','jne frame_done',f'cmp dword [{state["split"]}],0','je frame_done',f'and dword [{state["flags"]}],0xfffffffd','frame_done:','popfd',f'jmp {ui_va+vp.UI_FRAME}','labels:','dd entry_a,entry_b,frame_entry']
    source='\n'.join(lines)+'\n'
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/'vs.asm';dest=Path(td)/'vs.bin';src.write_text(source)
        subprocess.run(['nasm','-f','bin',str(src),'-o',str(dest)],check=True)
        blob=dest.read_bytes()
    if len(blob)>4096:
        raise ValueError('private section overflow')
    entries=struct.unpack('<III',blob[-12:]);data[raw:raw+len(blob)]=blob
    for marker,stub in zip(markers,entries):
        off=pe.off(marker['entry']-pe.base)
        data[off:off+9]=b'\xe9'+struct.pack('<i',stub-marker['entry']-5)+b'\x90'*4
        marker['stub']=stub
    frame_off=offset(0x1c751b)
    if data[frame_off]!=0xe8:
        raise ValueError('unverified frame call')
    frame_va=vp._va_at(pe,frame_off)
    if frame_va+5+struct.unpack_from('<i',data,frame_off+1)[0]!=ui_va+vp.UI_FRAME:
        raise ValueError('unexpected existing frame wrapper')
    data[frame_off:frame_off+5]=b'\xe8'+struct.pack('<i',entries[2]-frame_va-5)
    return data, dict(edition=edition.short,markers=markers,state=state,ui=ui_va,section=blobva,frame=entries[2],bearing=bearing,bound=bound,asm=source)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--private-local-vs', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.private_local_vs:
        parser.error('explicit --private-local-vs required')
    if args.output.exists():
        parser.error('refusing to overwrite output')
    image, metadata = build(args.executable.read_bytes())
    args.output.write_bytes(image)
    print(metadata['edition'], hashlib.sha256(image).hexdigest())
