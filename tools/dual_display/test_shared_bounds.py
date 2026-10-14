"""Audit the existing shared canvas; this is not a shared-routing implementation."""
import sys
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engineering3840
v=engineering3840.load_private()
g=v.presentation_geometry(3840,1080)
assert g['viewport']==(0,0,3840,1080)
assert g['hud_rect']==(960,0,1920,1080)
assert g['world_indicator_rect']==(0,0,3840,1080)
assert g['canvas_active_width']==1706
# ui.asm pre_lw -> fit: logical canvas scaled uniformly by 1080/480.
scale=Fraction(1080,480)
width=int(g['canvas_active_width']*scale)
left=(3840-width)//2
assert (left,width)==(1,3838)
# The center extraction retains only a subset of the photo's source columns.
step=g['photo_step_16']; origin=g['photo_origin_16'][0]
full=(Fraction(origin,65536),Fraction(origin+1706*step,65536))
crop=(full[0]+Fraction(960-left,1)/scale*Fraction(step,65536),
      full[0]+Fraction(2880-left,1)/scale*Fraction(step,65536))
assert full[0]<crop[0]<crop[1]<full[1]
print('VERIFIED HUD region:',g['hud_rect'])
print('VERIFIED shared pre-phase canvas bounds:',(left,0,width,1080))
print('VERIFIED photo source X range:',*[float(x) for x in full])
print('VERIFIED center extraction photo X range:',*[float(x) for x in crop])
print('BLOCKED: HUD region is not a complete shared-frame content boundary; center extraction discards photo columns.')
