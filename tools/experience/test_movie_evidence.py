"""Actual local AVI identity/header and numeric-only geometry evidence."""
import json,sys,tempfile,shutil
from pathlib import Path
from unittest.mock import patch
import movie_geometry as m
for folder in map(Path,sys.argv[1:]):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);shutil.copy2(folder/'von.avi',root/'von.avi');(root/'experience-version.json').write_text(json.dumps({'movie_framing':True}))
  for mode in (0,1,2):
   for x,y,w,h in [(0,0,640,480),(0,0,1920,1080),(-2560,0,2560,1440),(1920,0,3440,1440),(0,-1440,5120,1440)]:
    e=m.evidence(root,{'VO_DESKTOP':f'{x},{y},{w},{h}','VO_EX_EFFECTIVE_MODE':str(mode)})
    assert (e['source_width'],e['source_height'],e['picture_y'],e['picture_height'])==(320,240,30,180)
    assert e['picture_verified']==1 and e['geometry_fallback']==0
    assert e['expected_width']==min(w,h*16//9) and e['expected_height']==min(h,w*9//16)
    assert e['expected_x']==x+(w-e['expected_width'])//2
    assert e['expected_y']==y+(h-e['expected_height'])//2
  (root/'experience-version.json').write_text(json.dumps({'movie_framing':False}))
  assert m.evidence(root,{'VO_DESKTOP':'0,0,1920,1080'})['geometry_fallback']==1
  with patch.object(m,'KNOWN','unknown'):
   assert not m.evidence(root,{'VO_DESKTOP':'0,0,1920,1080'})['picture_verified']
  for bad in ('x','0,0,0,0','0,0,99999999,1440'):
   assert m.evidence(root,{'VO_DESKTOP':bad})['geometry_fallback']==1
  (root/'von.avi').write_bytes(b'invalid')
  assert m.evidence(root,{})['source_width']==0
 print('PASS',folder.name,'actual AVI identity/header; known/unknown/disabled framing, modes, physical sizes/offsets, invalid source and desktop fallback')
