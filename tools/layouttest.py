#!/usr/bin/env python3
"""Private S03 mask/canvas layout and S02 byte-preservation checks."""
import struct
import subprocess
import sys
import types

import geometrytest as gt

BASELINE = '1462c3e453fd3d761d983e9daa72be0b31ac8d10'


def reference():
    source = subprocess.check_output(['git', 'show', BASELINE + ':v-on-patcher.py'], cwd=gt.ROOT)
    module = types.ModuleType('s02_reference')
    module.__file__ = str(gt.ROOT / 'v-on-patcher.py')
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    return module


def check(vp, old):
    canvas = vp.canvas_layout()
    offsets = canvas['region_offsets']
    assert offsets == (0x3b00, 0x1e3b00, 0x3c3b00, 0x5a3b00)
    assert canvas['end_offset'] == 0x783b00
    assert canvas['storage_bytes'] == 4 * 4096 * 480
    for a, b in zip(offsets, offsets[1:]):
        assert a + canvas['region_bytes'] == b
    assert offsets[-1] + canvas['region_bytes'] == canvas['end_offset']
    assert vp.UI_CODE == old.UI_CODE and vp.UI_REFS == old.UI_REFS
    for w,h in [(row[0],row[1]) for row in gt.MATRIX] + [(32,8),(2016,480)]:
        g = vp.resolution_geometry(w,h)
        if not g['patch_size_admitted']:
            gt.rejects(vp.mask_layout,g)
            gt.rejects(vp.mask_origin,g)
            continue
        layout = vp.mask_layout(g)
        stride = layout['row_pitch']
        assert layout['mask_bytes'] == stride*h
        assert layout['clear_dwords']*4 == layout['mask_bytes']
        assert layout['row_table_offset'] == layout['mask_bytes']
        assert layout['storage_bytes'] == layout['mask_bytes'] + 4*h
        # First/last meaningful bytes and row stepping stay out of the table.
        for y in (0,h//4,h//2,h-1):
            first = vp.mask_origin(g,y=y)
            last = vp.mask_origin(g,w-8,y)
            assert first == y*stride
            assert last < first+layout['used_bytes'] <= (y+1)*stride
            assert last < layout['row_table_offset']
        assert vp.mask_origin(g,w//2) == w//16
        assert vp.mask_origin(g,w//2,h//2) == (h//2)*stride+w//16
        for x,y in ((-8,0),(w,0),(1,0),(0,-1),(0,h)):
            gt.rejects(vp.mask_origin,g,x,y)
        # Actual generated instructions, not a second allocator model.
        args=(w,h,0x4000000,0x4100000,0x4200000,(0x4300000,8000))
        sites=vp.build_sites(*args)
        assert sites==old.build_sites(*args)
        records={off:new for off,_old,new in sites}
        assert struct.unpack('<I',records[0x1cd5d4][:4])[0]==0x4100000+layout['row_table_offset']
        assert struct.unpack('<I',records[0x1cd60c])[0]==layout['clear_dwords']
        for off in (0x1c7907,0x1c7961,0x1c7a2c,0x1c7a8e,0x1c7b89,0x1c7c0e):
            assert struct.unpack('<I',records[off])[0]==vp.mask_origin(g,w//2)
        for off in (0x1c79bd,0x1c7bd0):
            assert struct.unpack('<I',records[off])[0]==vp.mask_origin(g,y=h//2)
        for off in (0x1c7af4,0x1c7c55):
            assert struct.unpack('<I',records[off])[0]==vp.mask_origin(g,y=h//4)
        expected=b'\xb4\x02\x90' if w==2560 else bytes((0xb0,stride,0x90))
        assert len(vp.MASK_PACK)==10
        assert all(records[off]==expected for off in vp.MASK_PACK)
    g=vp.resolution_geometry(2560,1080)
    alternate=dict(g,mask_row_pitch=768)  # geometry proof only; no generated mode
    assert vp.mask_origin(g,1280)==vp.mask_origin(alternate,1280)==160
    assert vp.mask_origin(g,1280,540)==276640
    assert vp.mask_origin(alternate,1280,540)==414880
    assert vp.mask_layout(g)['storage_bytes']==1080*(512+4)
    # Pair allocation preserves max mask+table storage and separate 2D tables.
    a=vp.resolution_geometry(1280,720)
    assert max(vp.mask_layout(g)['storage_bytes'],vp.mask_layout(a)['storage_bytes'])==557280
    # Paired F4 lists differ only by the three aspect-dependent hangar sites.
    tail=(0x4000000,0x4100000,0x4200000,(0x4300000,8000))
    wide={off for off,_,_ in old.build_sites(1280,720,*tail)}
    for size in ((640,480),(1024,768)):
        narrow={off for off,_,_ in old.build_sites(*size,*tail)}
        assert wide-narrow=={0x2213f0,0x2213f8,0x59e4ea-0x400c00}
        assert not narrow-wide
    print('PASS mask storage/table/clear instructions, all ten packed sites, A/B origins, canvas ownership, unchanged UI/relocations and isolated F4 hangar dependency')


if __name__=='__main__':
    current,baseline=gt.selftest.load_patcher(),reference()
    check(current,baseline)
    for path in sys.argv[1:]:
        gt.images(current,baseline,path)
