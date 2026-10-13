#!/usr/bin/env python3
"""Private S04 HUD/artwork bounds and exact S03 image preservation.

Research-only cases do not execute or authorize unsupported game modes.
Actual 2560 compositor/HUD execution is also covered by d01test/uiemu.
"""
from fractions import Fraction
import struct
import subprocess
import sys
import types

import geometrytest as gt

BASELINE = '8c85742ac651b4db327bcf6abbf609f5bc40054b'


def reference():
    source = subprocess.check_output(['git', 'show', BASELINE + ':v-on-patcher.py'], cwd=gt.ROOT)
    m = types.ModuleType('s03_reference')
    m.__file__ = str(gt.ROOT / 'v-on-patcher.py')
    exec(compile(source, m.__file__, 'exec'), m.__dict__)
    return m


def check(vp, old):
    expected_spread = (0, 0, 160, 240, 240, 320, 240, 320)
    for row, spread in zip(gt.MATRIX, expected_spread):
        w, h, _, _, _, logical, hud, origin, supported = row
        p = vp.presentation_geometry(w, h)
        assert p['hud_rect'] == (origin, 0, hud, h)
        assert p['viewport'] == p['world_indicator_rect'] == (0, 0, w, h)
        assert p['hud_scale'] == min(Fraction(w, 640), Fraction(h, 480))
        assert p['composition_spread'] == spread
        # Timer/total spread stays within the centered HUD policy bounds.
        frame_left = (w-p['hud_frame_width'])/2
        assert frame_left-spread == origin
        assert frame_left+p['hud_frame_width']+spread == origin+hud
        assert p['canvas_logical_width'] == p['canvas_active_width'] == logical
        assert p['active_row_bytes'] <= p['canvas_pitch'] == 4096
        # Every sampled photo coordinate uses the same fixed-point step in
        # both axes and remains inside the staged 496x384 source region.
        step = p['photo_step_16']
        sx, sy = p['photo_origin_16']
        xs = [(sx+x*step)>>16 for x in range(logical)]
        ys = [(sy+y*step)>>16 for y in range(480)]
        assert 0 <= min(xs) <= max(xs) < 496
        assert 0 <= min(ys) <= max(ys) < 384
        canvas = vp.canvas_layout()
        for region in canvas['region_offsets']:
            assert region + 479*4096 + logical*2 <= region+canvas['region_bytes']
        stage = vp.UI_CANVAS_STAGE
        assert stage+383*4096+496*2 <= stage+canvas['region_bytes']
        assert p['patch_size_admitted'] == supported
        if supported:
            assert vp._ui_words(w,h) == old._ui_words(w,h)
            actual = struct.unpack('<I',vp._ui_words(w,h)[vp.UI_SPREADMAX])[0]
            assert actual == p['installed_spread_cap']
            assert actual == (240 if w == 2560 else 0x7fffffff)
        else:
            gt.rejects(vp.hires_install,bytearray(),w,h)
    # Fractional policy is retained exactly; it is not rounded into patch data.
    p = vp.presentation_geometry(2000,1000)
    assert p['hud_rect'][0] == Fraction(1000,9)
    assert p['composition_spread'] == Fraction(2000,9)
    assert p['installed_spread_cap'] == 0x7fffffff
    # Wider allocation is never confused with active artwork or mode admission.
    p = vp.presentation_geometry(8192,480)
    assert p['canvas_logical_width'] == 8192
    assert p['canvas_active_width'] == 2048 and not p['canvas_fits']
    assert not p['patch_size_admitted']
    for bad in (0,-1,True,1.5,None):
        gt.rejects(vp.presentation_geometry,bad,480)
    gt.rejects(vp.presentation_geometry,1,10000)
    assert vp.UI_CODE == old.UI_CODE and vp.UI_REFS == old.UI_REFS
    print('PASS eight HUD/world rectangles, exact spread and rounding, photo sampling bounds, active canvas/staging regions, preserved encoded words and unsupported-mode rejection')


if __name__ == '__main__':
    current, baseline = gt.selftest.load_patcher(), reference()
    check(current, baseline)
    for path in sys.argv[1:]:
        gt.images(current, baseline, path)
