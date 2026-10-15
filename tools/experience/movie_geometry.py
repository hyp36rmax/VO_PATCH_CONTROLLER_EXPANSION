"""Numeric AVI/header and expected framing evidence; never decode/export frames."""
import hashlib,json,struct
from pathlib import Path
# Retail and JPRE local original files are byte-identical. Upstream's measured
# picture band is rows 30..209; unknown assets are never called characterized.
KNOWN='cf5094ec93879089b2544aa5bc1ff83764a6ab120fb8eac0c77c4b5492fe0c38'
def evidence(root,environ):
 result={'source_width':0,'source_height':0,'picture_verified':0,'geometry_fallback':1}
 try:
  p=Path(root)/'von.avi';size=p.stat().st_size
  with p.open('rb') as f:
   header=f.read(4096)
   if header[:4]!=b'RIFF' or header[8:12]!=b'AVI ':return result
   at=header.find(b'avih');assert at>=12 and at+48<=len(header)
   width,height=struct.unpack_from('<II',header,at+40)
   if not(0<width<=32768 and 0<height<=32768):return result
   result.update(source_width=width,source_height=height)
   digest=hashlib.sha256(header)
   if size==16488200:
    while chunk:=f.read(65536):digest.update(chunk)
   known=size==16488200 and digest.hexdigest()==KNOWN and (width,height)==(320,240)
  version=json.loads((Path(root)/'experience-version.json').read_text())
  enabled=version.get('movie_framing') is True
  result['framing_enabled']=enabled
  if known:result.update(picture_verified=1,picture_x=0,picture_y=30,picture_width=320,picture_height=180)
  x,y,w,h=map(int,environ['VO_DESKTOP'].split(','))
  if not(0<w<=32768 and 0<h<=32768 and -32768<=x<=32768 and -32768<=y<=32768):return result
  result.update(display_x=x,display_y=y,display_width=w,display_height=h)
  if known and enabled:
   rw=min(w,h*16//9);rh=min(h,w*9//16)
   result.update(expected_x=x+(w-rw)//2,expected_y=y+(h-rh)//2,expected_width=rw,expected_height=rh,geometry_fallback=0)
 except (OSError,ValueError,KeyError,AssertionError,struct.error):pass
 return result
