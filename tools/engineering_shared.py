#!/usr/bin/env python3
"""Private dual-output variant: upstream 1920 shared composition in a 3840 surface.

Only non-split viewport width operands and their primary F4 values change.
The baseline VS generator, split branches, pitch and allocation remain intact.
"""
import struct
import engineering_vs
import engineering3840


def build(original, wanted=None):
    data, meta = engineering_vs.build(original, wanted)
    v = engineering3840.load_private()
    port = None if meta['edition'] == 'retail' else v.PORT['%08x' % v._pe_stamp(original)]
    pe = v._PE(data)
    ui = next(s for s in pe.sections if s['name'] == b'.vohr')
    changes = []
    for retail, before, after in ((0x1c7da5, 3840, 1920),
                                  (0x1c7d77, 3840, 1920),
                                  (0x1c7d68, 2976, 1488)):
        off = retail if port is None else port['off'][retail][0]
        assert struct.unpack_from('<I', data, off)[0] == before
        struct.pack_into('<I', data, off, after)
        va = v._va_at(pe, off)
        cursor = ui['raddr'] + v.UI_F4TAB_OFF
        end = cursor + v.UI_F4TAB_SIZE
        found = []
        while cursor + 4 <= end:
            target, = struct.unpack_from('<I', data, cursor)
            if not target:
                break
            size, = struct.unpack_from('<I', data, cursor + 4)
            assert 0 < size and cursor + 8 + 2 * size <= end
            if target == va:
                assert size == 4 and struct.unpack_from('<I', data, cursor + 8)[0] == before
                struct.pack_into('<I', data, cursor + 8, after)
                found.append(cursor + 8)
            cursor += 8 + 2 * size
        assert len(found) == 1, (hex(va), found)
        changes.append(dict(offset=off, address=va, before=before, after=after, f4_offset=found[0]))
    # This signature includes the corrected full shared width. An F01 executable
    # must not be interpreted as having the new source composition.
    meta['shared'] = dict(source=[0, 0, 1920, 1080], changes=changes,
                          signature=changes[0]['address'] - 6)
    return data, meta
