#!/usr/bin/env python3
"""Explicit private offline 3840 1P proof; no public UI/CLI/environment switch."""
import argparse
import hashlib
import json
from pathlib import Path

import selftest
import d01test
import geometrytest


def load_private():
    # A separate module instance: normal patcher imports stay unmodified.
    vp=selftest.load_patcher()
    vp._PRIVATE_3840=True
    return vp


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('executable');p.add_argument('--private-proof',action='store_true')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.private_proof:p.error('explicit --private-proof required')
    public=selftest.load_patcher();private=load_private()
    for size in ((3840,1080),(5120,1440),(3840,720),(3440,1440)):
        try:public._hires_check_size(*size)
        except ValueError:pass
        else:raise AssertionError('public gate broadened')
        if size != (3840,1080):
            try:private._hires_check_size(*size)
            except ValueError:pass
            else:raise AssertionError('private gate broadened')
    g=private.resolution_geometry(3840,1080)
    assert (g['mask_used_words'],g['mask_used_bytes'],g['mask_row_pitch'])==(120,480,512)
    assert (g['hud_composition_width'],g['hud_horizontal_origin'])==(1920,960)
    assert g['canvas_active_width']==1706 and g['framebuffer_min_row_bytes']==7680
    geometrytest.images(private,public,a.executable)
    d01test.main(a.executable,3840,private)
    original,_=selftest.pristine(a.executable,private)
    b=private.BUILDS[hashlib.md5(original).hexdigest()]
    wanted=dict.fromkeys(private.by_key(b),True);wanted['hires']=(3840,1080)
    images=[private.apply_selected(bytearray(original),wanted,b)[0] for _ in range(2)]
    assert images[0]==images[1]
    if a.output:
        a.output.mkdir(parents=True,exist_ok=True)
        dest=a.output/(b.short+'-3840-OFFLINE.exe')
        if dest.exists():raise ValueError('refusing to overwrite proof')
        dest.write_bytes(images[0])
        dest.with_suffix('.json').write_text(json.dumps({'scope':'OFFLINE 1P ONLY; no Windows acceptance; local VS not validated','sha256':hashlib.sha256(images[0]).hexdigest(),'edition':b.short,'deterministic':True},indent=2))
    assert not selftest.load_patcher()._PRIVATE_3840
    print('PASS private gate isolation, deterministic 3840 generation; no public mode enabled')


if __name__=='__main__':main()
