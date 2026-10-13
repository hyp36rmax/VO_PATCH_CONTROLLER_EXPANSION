#!/usr/bin/env python3
"""Fault injection tests for evidence labels and bounded probe records."""
import json
import visualprobe as v
import selftest


def main():
    vp=selftest.load_patcher()
    for w,h in ((640,480),(1024,768),(1280,720),(1920,1080),(2560,1080)):
        r=v.static_report(vp,w,h)
        assert r['result']=='PASS' and r['events']==[]
        assert r['runtime_clipping_status']=='INSUFFICIENT_EVIDENCE'
    p=v.Probe()
    p.bounds('MASK_BOUNDS',(0,20),(0,10),'disabled')
    assert not p.events and not p.dropped
    p=v.Probe(True,4)
    p.bounds('MASK_BOUNDS',(0,10),(0,10),'valid last byte')
    assert not p.events
    for category in ('MASK_BOUNDS','CANVAS_BOUNDS','HUD_BOUNDS','VIEWPORT_BOUNDS'):
        p.bounds(category,(0,11),(0,10),'injected one-past-end')
    assert all(e['classification']=='CONFIRMED_VIOLATION' and e['evidence']=='STATIC' for e in p.events)
    for _ in range(1000):p.bounds('MASK_BOUNDS',(-1,0),(0,10),'overflow')
    assert len(p.events)==4 and p.dropped==1000
    q=v.Probe(True)
    q.bounds('VIEWPORT_BOUNDS',(-1,0,11,10),(0,0,10,10),'ordinary clip',operation='clip',clipping_expected=True)
    q.bounds('HUD_BOUNDS',(-1,0,11,10),(0,0,10,10),'unexpected clip',operation='clip')
    q.bounds('OBJECT_CULLING',(0,20),(0,10),'no object provenance')
    q.bounds('RASTERIZER_CLIPPING',None,(0,10),'unavailable')
    assert [e['classification'] for e in q.events]==['EXPECTED_CLIPPING','POTENTIAL_ANOMALY','INSUFFICIENT_EVIDENCE','INSUFFICIENT_EVIDENCE']
    encoded=json.dumps(q.report());assert 'frame' not in encoded and 'object_id' not in encoded
    assert json.loads(encoded)==q.report()
    q.bounds('MASK_BOUNDS',(1,0),(0,10),'bad range')
    assert q.events[-1]['classification']=='INSUFFICIENT_EVIDENCE'
    for capacity in (0,257,True):
        try:v.Probe(True,capacity)
        except ValueError:pass
        else:raise AssertionError(capacity)
    print('PASS static modes, injected bounds, expected/anomalous clipping, missing evidence, JSON, bounded events and disabled probe')


if __name__=='__main__':main()
