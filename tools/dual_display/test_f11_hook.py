"""Execute the private F11 bridge ABI for Retail/JPRE, including missing helper.

Does not assert native Windows dialog rendering or normal-startup integration.
"""
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
import mode_profiles
import f5_hook
v = mode_profiles.engineering3840.load_private()
for folder in map(Path, sys.argv[1:]):
    raw = (folder / 'v_on.exe').read_bytes()
    baseline, meta = mode_profiles.build(raw, 'wide')
    edition = v.RETAIL if meta['edition'] == 'retail' else v.JPRE
    image, hook = f5_hook.install(baseline, edition)
    assert hook['f11_enabled']
    at=edition.off(v.cave_va('F11PAUSE',edition))
    assert struct.unpack_from('<I',image,at+0xd)[0]==hook['entry']+256
    oldpe, pe = v._PE(baseline), v._PE(image)
    for section in oldpe.sections:
        if section['name'] == b'.rsrc':
            start, size = section['raddr'], section['rsize']
            assert image[start:start+size] == baseline[start:start+size]
    for missing in (False, True, "symbol"):
        mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(0x400000, 0x4000000)
        mu.mem_map(0x7000000, 0x10000)
        for section in pe.sections:
            mu.mem_write(pe.base+section['vaddr'], image[section['raddr']:section['raddr']+section['rsize']])
        load, getproc, helper, stop, stack = 0x7000100, 0x7000200, 0x7000300, 0x7001000, 0x700f000
        mu.mem_write(edition.symbols['LOADLIB'], struct.pack('<I',load))
        mu.mem_write(edition.symbols['GETPROC'], struct.pack('<I',getproc))
        mu.mem_write(load, b'\xb8'+struct.pack('<I',0 if missing is True else 123)+b'\xc2\x04\x00')
        mu.mem_write(getproc, b'\xb8'+struct.pack('<I',0 if missing=='symbol' else helper)+b'\xc2\x08\x00')
        mu.mem_write(helper,b'\xb8\x09\x00\x00\x00\xc2\x14\x00')
        mu.mem_write(hook['f11_original'],b'\xb8\x07\x00\x00\x00\xc2\x10\x00')
        args=(0x1234,0x111,0x5e00,0x5678)
        mu.mem_write(stack,struct.pack('<5I',stop,*args));mu.reg_write(UC_X86_REG_ESP,stack)
        for reg,value in ((UC_X86_REG_EBX,11),(UC_X86_REG_ESI,22),(UC_X86_REG_EDI,33),(UC_X86_REG_EBP,44)):mu.reg_write(reg,value)
        seen=[]
        def inspect(machine,address,size,user):
            if address in (helper,hook['f11_original']):
                sp=machine.reg_read(UC_X86_REG_ESP)
                actual=struct.unpack('<4I',machine.mem_read(sp+4,16));assert actual==args
                if address==helper:assert struct.unpack('<I',machine.mem_read(sp+20,4))[0]==hook['f11_original']
                seen.append(address)
        mu.hook_add(UC_HOOK_CODE,inspect);mu.emu_start(hook['entry']+256,stop,count=1000)
        assert seen==[hook['f11_original'] if missing else helper]
        assert mu.reg_read(UC_X86_REG_ESP)==stack+20
        assert mu.reg_read(UC_X86_REG_EAX)==(7 if missing else 9)
        for reg,value in ((UC_X86_REG_EBX,11),(UC_X86_REG_ESI,22),(UC_X86_REG_EDI,33),(UC_X86_REG_EBP,44)):assert mu.reg_read(reg)==value
    print('PASS',meta['edition'],'original resource bytes, callback arguments, return value, callee registers/stack and missing-helper fallback')
