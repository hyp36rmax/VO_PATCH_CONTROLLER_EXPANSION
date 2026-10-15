"""Private launch profiles; retain the existing generators and full AVI frame."""
import hashlib, importlib.util, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engineering3840, engineering_shared
ROOT=Path(__file__).resolve().parents[2]
PROFILES={'original':None,'wide':(1920,1080),'ultrawide':(2560,1080),'superwide':(3840,1080),'dual':(3840,1080)}

def movie_blob(v):
    sys.path.insert(0,str(ROOT/'asm'))
    spec=importlib.util.spec_from_file_location('private_asm_build',ROOT/'asm/build.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    source=(ROOT/'asm/movie.asm').read_text()
    assert source.count('BAND_TOP    equ 30')==source.count('BAND_ROWS   equ 180')==1
    source=source.replace('BAND_TOP    equ 30','BAND_TOP    equ 0').replace('BAND_ROWS   equ 180','BAND_ROWS   equ 240')
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'movie_full.asm';p.write_text(source)
        frames={n:x for n,x in v.RETAIL.symbols.items() if isinstance(x,int) and x<0}
        a.includes(td,frames)
        blob=a.assemble(str(p),td)
        a.frame_fixups(str(p),td,frames,blob[0],blob[1])
    old=v.BLOBS['MOVIE']
    assert len(blob[0])==len(old[0]) and tuple(blob[1])==tuple(old[1]) and blob[2]==old[2], 'movie layout changed'
    return blob

def build(raw,profile,wanted=None):
    v=engineering3840.load_private();edition=v.BUILDS[hashlib.md5(raw).hexdigest()]
    options=dict.fromkeys(v.by_key(edition),True) if wanted is None else dict(wanted)
    if profile=='dual':
        data,_=engineering_shared.build(raw,options)
        from split_preference import install
        data,_=install(data,edition)
        data=bytearray(data)
    else:
        wanted=dict(options);wanted['hires']=PROFILES[profile] or False
        data,_,skipped=v.apply_selected(bytearray(raw),wanted,edition)
        assert not skipped,skipped
    if options.get('credits'):v.stamp_version(data,edition)
    if not options.get('movie'):
        return bytes(data),{'edition':edition.short,'profile':profile,'internal':PROFILES[profile] or (640,480),'movie_bytes_changed':0,'sha256':hashlib.sha256(data).hexdigest()}
    original=bytes(data);old=v.link('MOVIE',edition);new=v.link('MOVIE',edition,blobs={**v.BLOBS,'MOVIE':movie_blob(v)})
    assert len(old)==len(new) and original.count(old)==1
    offset=original.index(old);data[offset:offset+len(old)]=new
    assert data[:offset]==original[:offset] and data[offset+len(old):]==original[offset+len(old):]
    return bytes(data),{'edition':edition.short,'profile':profile,'internal':PROFILES[profile] or (640,480),'prior_sha256':hashlib.sha256(original).hexdigest(),'movie_offset':offset,'movie_bytes_changed':sum(a!=b for a,b in zip(old,new)),'sha256':hashlib.sha256(data).hexdigest()}
