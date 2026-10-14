#!/usr/bin/env python3
"""Execute original viewport/canvas code: new shared layout versus upstream 1920.
Gameplay is compared with the preserved F01 producer, not a duplicate model.
"""
import hashlib, json, struct, sys
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP
import d01test, engineering3840, engineering_vs, engineering_shared, uibuild
v = engineering3840.load_private()
saved = list(uibuild.LABELS)
uibuild.LABELS += ['set1pre', 'set2pre', 'set1post', 'set2post']
blob, labels = uibuild.assemble((Path(__file__).resolve().parents[1]/'asm/ui.asm').read_text())
uibuild.LABELS = saved
assert blob == v.UI_CODE
results = []
for path in sys.argv[1:3]:
    raw = Path(path).read_bytes()
    before, oldmeta = engineering_vs.build(raw)
    data, meta = engineering_shared.build(raw)
    assert data == engineering_shared.build(raw)[0]
    allowed = {i for c in meta['shared']['changes'] for start in (c['offset'], c['f4_offset']) for i in range(start,start+4)}
    changed = {i for i,(a,b) in enumerate(zip(before,data)) if a!=b}
    assert len(data)==len(before) and changed and changed <= allowed
    pe = v._PE(data)
    sig = pe.off(meta['shared']['signature']-pe.base)
    assert data[sig:sig+32] != before[sig:sig+32]
    build = v.BUILDS[hashlib.md5(raw).hexdigest()]
    wanted = dict.fromkeys(v.by_key(build),True);wanted['hires']=(1920,1080)
    reference,_,skipped = v.apply_selected(bytearray(raw),wanted,build);assert not skipped
    refpe=v._PE(reference);refui=next(s for s in refpe.sections if s['name']==b'.vohr')['vaddr']+refpe.base
    port=None if meta['edition']=='retail' else v.PORT['%08x'%v._pe_stamp(raw)]
    addr=lambda a:a if port is None else port['va'][a]
    machines=[d01test.image(b)[0] for b in (before,data,reference)]
    for mu in machines:mu.mem_map(0x10000000,0xa00000)
    def put(mu,a,n):mu.mem_write(a,struct.pack('<I',n&0xffffffff))
    def get(mu,a):return struct.unpack('<I',mu.mem_read(a,4))[0]
    def call(mu,entry,arg=None):
        sp=d01test.STACK+0x8000;put(mu,sp,d01test.RET)
        if arg is not None:put(mu,sp+4,arg)
        mu.reg_write(UC_X86_REG_ESP,sp);mu.emu_start(entry,d01test.RET,count=60000000)
        assert mu.reg_read(UC_X86_REG_EIP)==d01test.RET
    desc=d01test.STACK+0x1000
    # Geometry globals owned by the original viewport, including both renderer scales.
    globals_=[v.ADDR[k] for k in ('FB_W','FB_H','FB_PITCH','SCALE_A','SCALE_B','CENTRE_AX','CENTRE_BX','CENTRE_A','CENTRE_B')]
    globals_.append(0x6bf5a8) # actual destination pointer, not just width
    count=0
    for split in (0,1):
      for flags in (0,1,2,3):
       for sub in (0,9,10,14,20,21,27,32):
        snapshots=[]
        for index,mu in enumerate(machines):
            for key,value in dict(mode1=4,mode2=4,sub1=sub,sub2=sub,split=split,flags=flags).items():put(mu,meta['state'][key],value)
            put(mu,desc+0x24,0x10000000);put(mu,desc+0x10,7744)
            entry=meta['frame'] if index<2 else refui+v.UI_FRAME
            call(mu,entry,desc)
            ui=meta['ui'] if index<2 else refui
            snapshots.append(([get(mu,addr(a)) for a in globals_],get(mu,ui+0x1e88)))
        shared = not split or snapshots[1][1] != 0
        if shared:
            # Ref UI keeps top/bottom flag but it is irrelevant when shared.
            assert snapshots[1] == snapshots[2], (meta['edition'],split,flags,sub,snapshots)
            # Run the actual pre compositor and compare layout words with 1920 upstream.
            for player in ((1,2) if split else (1,)):
                canvas=[]
                for index in (1,2):
                    mu=machines[index];ui=meta['ui'] if index==1 else refui
                    try:
                        call(mu,ui+labels[f'set{player}pre']);call(mu,ui+labels['pre'])
                    except Exception:
                        print('FAILED CONTEXT',meta['edition'],split,flags,sub,player,index,flush=True);raise
                    canvas.append([get(mu,ui+x) for x in (0x1c28,0x1c2c,0x1c30,0x1c34,0x1c40,0x1c44,0x1c5c,0x1c60,0x1c64,0x1c80,0x1cc8,0x1ccc,0x1cd0,0x1dc8,0x1dcc,0x1dd0,0x1dd4)])
                    # Restore geometry and split before exercising the other player.
                    call(mu,ui+labels['post'])
                assert canvas[0]==canvas[1],(meta['edition'],'canvas',split,flags,sub,player)
        else:
            assert snapshots[0]==snapshots[1], (meta['edition'],'gameplay',split,flags,sub)
        count+=1
    results.append(dict(edition=meta['edition'],cases=count,changed_bytes=len(changed),allowed_operands=meta['shared']['changes'],deterministic=True,shared_matches_upstream_1920=True,gameplay_matches_F01=True))
print(json.dumps(results,indent=2))
