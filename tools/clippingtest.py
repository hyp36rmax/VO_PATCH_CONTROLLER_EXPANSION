#!/usr/bin/env python3
"""V02 synthetic edge tests of a verified Retail clip-code fragment.

Not a replay of physical clipping, and not whole-object culling coverage.
"""
import struct
import sys

import selftest
import geometrytest as gt
import visualprobe
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_EIP


def main(path):
    vp=selftest.load_patcher();data,_=selftest.pristine(path,vp)
    assert data is not None
    assert vp._pe_stamp(data)==vp.RETAIL_STAMP
    pe=vp._PE(data)
    # cmp eax,ebp; jb inside; jl negative; or esi,8; jmp inside; or esi,4
    va=0x5d34de; expected=bytes.fromhex('3bc5720a7c0583ce08eb0383ce04')
    off=pe.off(va-pe.base);code=data[off:off+len(expected)];assert code==expected
    mu=Uc(UC_ARCH_X86,UC_MODE_32);mu.mem_map(0x10000,4096);mu.mem_write(0x10000,code)
    cases=0
    for row in gt.MATRIX:
        w,h=row[:2];g=vp.resolution_geometry(w,h)
        # Same signed/unsigned branch idiom serves an extent, not a hardcoded
        # 640-pixel limit. Width/height are supplied by their runtime globals.
        for extent in (w,h):
            for x in (-32768,-1,0,1,extent-1,extent,extent+1,32767):
                mu.reg_write(UC_X86_REG_EAX,x&0xffffffff)
                mu.reg_write(UC_X86_REG_EBP,extent);mu.reg_write(UC_X86_REG_ESI,0)
                mu.emu_start(0x10000,0x10000+len(code))
                assert mu.reg_read(UC_X86_REG_EIP)==0x10000+len(code)
                assert mu.reg_read(UC_X86_REG_ESI)==(4 if x<0 else 8 if x>=extent else 0)
                cases+=1
        # Mask bit/word/row transitions, meaningful end versus padding.
        if g['patch_size_admitted']:
            pitch=g['mask_row_pitch']
            for x in (0,31,32,63,64,w-1):
                for y in (0,h-1):
                    word=y*pitch+(x//32)*4
                    assert y*pitch<=word<word+4<=y*pitch+g['mask_used_bytes']
                    assert word+4<=h*pitch
            r=visualprobe.static_report(vp,w,h);assert r['result']=='PASS'
        p=vp.presentation_geometry(w,h)
        # Cover sampling can deliberately omit photo rows without an OOB read.
        step=p['photo_step_16'];_,y=p['photo_origin_16']
        assert 0<=y>>16<384
        assert 0<((y+479*step)>>16)<384
    # Fixed stage meshing policy is not a resolution-derived frustum plane.
    for size in ((1920,1080),(2560,1080)):
        sites={off:new for off,_,new in vp.build_sites(*size,0x4000000,0x4100000,0x4200000,(0x4300000,8000))}
        assert struct.unpack('<I',sites[0x1bd799])[0]==0x5800
        assert struct.unpack('<I',sites[0x1bd7aa])[0]==0xb000
    print('PASS',cases,'real Retail clip-code edge cases; mask word/row boundaries; deliberate photo crop; unchanged meshing thresholds. No physical defect reproduced.')


if __name__=='__main__':main(sys.argv[1])
