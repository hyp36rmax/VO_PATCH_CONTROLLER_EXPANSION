#!/usr/bin/env python3
"""Private, opt-in geometry probe. No game hooks or runtime clipping claims.

Generate a bounded static report before packaging, then collect it alongside
existing UAT logs. Live renderer telemetry is intentionally not implemented.
"""
import argparse
import json
from fractions import Fraction
from pathlib import Path

CATEGORIES = {'MASK_BOUNDS', 'VIEWPORT_BOUNDS', 'CANVAS_BOUNDS', 'HUD_BOUNDS',
              'OBJECT_CULLING', 'RASTERIZER_CLIPPING'}


class Probe:
    def __init__(self, enabled=False, capacity=64):
        if type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError('capacity must be 1..256')
        self.enabled, self.capacity = enabled, capacity
        self.events, self.dropped = [], 0

    def bounds(self, category, observed, expected, source, *, evidence='STATIC',
               operation='geometry', clipping_expected=False):
        if not self.enabled:
            return
        if category not in CATEGORIES or evidence not in ('STATIC', 'RUNTIME'):
            raise ValueError('invalid event category/evidence')
        if operation not in ('geometry', 'memory_access', 'clip'):
            raise ValueError('invalid operation')
        def valid(v):
            return (isinstance(v, (tuple, list)) and len(v) in (2, 4)
                    and all(type(x) is int and abs(x) < 2**63 for x in v)
                    and all(v[i] <= v[i+len(v)//2] for i in range(len(v)//2)))
        classification = 'INSUFFICIENT_EVIDENCE'
        if valid(observed) and valid(expected) and len(observed) == len(expected):
            n = len(observed)//2
            inside = all(expected[i] <= observed[i] <= observed[i+n] <= expected[i+n]
                         for i in range(n))
            if inside:
                return  # A valid bound is not an anomaly event.
            if category in ('OBJECT_CULLING', 'RASTERIZER_CLIPPING'):
                classification = ('EXPECTED_CLIPPING' if clipping_expected and operation == 'clip'
                                  else 'INSUFFICIENT_EVIDENCE')
            elif operation == 'clip':
                classification = 'EXPECTED_CLIPPING' if clipping_expected else 'POTENTIAL_ANOMALY'
            else:
                classification = 'CONFIRMED_VIOLATION'
        event = {'record': '[DISPLAY][VISUAL_INTEGRITY]', 'evidence': evidence,
                 'category': category, 'classification': classification,
                 'source': str(source)[:160], 'operation': operation}
        # Never manufacture missing coordinates, frames or object identities.
        if valid(observed):
            event['observed_bounds'] = list(observed)
        if valid(expected):
            event['expected_bounds'] = list(expected)
        if len(self.events) < self.capacity:
            self.events.append(event)
        else:
            self.dropped = min(self.dropped+1, 2**31-1)

    def report(self):
        return {'schema': 1, 'enabled': self.enabled,
                'live_renderer_observation': 'NOT IMPLEMENTED',
                'capacity': self.capacity, 'dropped_events': self.dropped,
                'events': list(self.events)}


def static_report(vp, width, height):
    g = vp.resolution_geometry(width, height)
    p = vp.presentation_geometry(width, height)
    probe = Probe(True)
    if not g['patch_size_admitted']:
        raise ValueError('diagnostic package requires an admitted mode')
    mask = vp.mask_layout(g)
    for y in (0, height//4, height//2, height-1):
        start = vp.mask_origin(g, y=y)
        probe.bounds('MASK_BOUNDS', (start, start+g['mask_used_bytes']),
                     (y*mask['row_pitch'], (y+1)*mask['row_pitch']), 'static mask row usage')
    for x,y in ((0,0),(width//2,0),(0,height//2),(width//2,height//2)):
        offset = vp.mask_origin(g,x,y)
        probe.bounds('MASK_BOUNDS',(offset,offset+1),(0,mask['row_table_offset']),
                     'static A/B viewport origin')
    canvas = vp.canvas_layout()
    for region in canvas['region_offsets']:
        probe.bounds('CANVAS_BOUNDS',(region,region+479*canvas['pitch']+p['active_row_bytes']),
                     (region,region+canvas['region_bytes']), 'static canvas active rows')
    stage = vp.UI_CANVAS_STAGE
    probe.bounds('CANVAS_BOUNDS',(stage,stage+383*canvas['pitch']+496*2),
                 (stage,stage+canvas['region_bytes']), 'static photo staging')
    hud = p['hud_rect']; assert all(getattr(x,'denominator',1)==1 for x in hud)
    x,y,w,h = map(int,hud)
    probe.bounds('HUD_BOUNDS',(x,y,x+w,y+h),(0,0,width,height),'static HUD composition')
    probe.bounds('VIEWPORT_BOUNDS',(0,0,width,height),(0,0,width,height),'static visible viewport')
    # This is a contract assertion, not observed projected vertices.
    assert g['vertical_projection_scale'] == Fraction(height,480)
    report = probe.report()
    report.update({'evidence':'STATIC', 'resolution':[width,height],
                   'viewport':[0,0,width,height], 'hud_rect':[x,y,w,h],
                   'mask':mask, 'canvas':canvas,
                   'result':'PASS' if not probe.events else 'FAIL',
                   'runtime_clipping_status':'INSUFFICIENT_EVIDENCE'})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostic',action='store_true')
    parser.add_argument('--width',type=int,default=2560)
    parser.add_argument('--height',type=int,default=1080)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    if not a.diagnostic:
        parser.error('explicit --diagnostic required; normal builds produce no probe file')
    import selftest
    report=static_report(selftest.load_patcher(),a.width,a.height)
    a.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
