"""Audit private identity tables, frame-lock boundaries and packaging contracts."""
import re,sys,struct,hashlib,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent))
import engineering3840
v=engineering3840.load_private()
package,wrapper=map(Path,sys.argv[1:3])
header=(here/'game_profiles.h').read_text()
rows=[list(map(lambda s:int(s,16),re.findall(r'0x[0-9a-f]+',line))) for line in header.splitlines() if line.startswith('{')]
raw=(package/'dual/game/v_on.exe').read_bytes();pe=v._PE(raw);nt=struct.unpack_from('<I',raw,0x3c)[0]
size=struct.unpack_from('<I',raw,nt+80)[0]
matching=[r for r in rows if r[:3]==[pe.base,v._pe_stamp(raw),size]]
assert len(matching)==1
r=matching[0];off=pe.off(r[3]-pe.base);assert raw[off:off+32]==bytes(r[8:])
for address in r[3:8]:assert pe.base<=address<pe.base+size
s=(wrapper/'src/ddsurface.c').read_text();start=s.index('HRESULT dds_Unlock(');end=s.index('HRESULT dds_GetDDInterface',start);unlock=s[start:end]
assert unlock.index('vo_capture_policy()')<unlock.index('surface_updated')<unlock.index('LeaveCriticalSection(&This->cs)')
assert 'g_config.lock_surfaces && This == g_ddraw.primary' in unlock
render=(wrapper/'src/render_d3d9.c').read_text();start=render.index('!TryEnterCriticalSection');end=render.index('LeaveCriticalSection(&g_ddraw.primary->cs)',start)
assert start<render.index('vo_dual_uploaded(tex_index)',start)<end
assert (package/'Launch.ps1').read_bytes()==subprocess.check_output(['git','show','7c676682175489adfa57c23e6b1335539878547c:tools/dual_display/Launch.ps1'],cwd=here)
collector=(package/'Collect-Results.ps1').read_text()
old=subprocess.check_output(['git','show','7c676682175489adfa57c23e6b1335539878547c:tools/dual_display/Collect-Results.ps1'],cwd=here,text=True)
assert collector==old.replace('D04-P03','D04-P05')
ui=(here/'displays.c').read_text();assert 'Mirror Player 1' in ui and 'GetPrivateProfileIntW(L"Presentation",L"MirrorPlayer1",0,config)' in ui
assert 'WritePrivateProfileStringW(L"Presentation",L"MirrorPlayer1"' in ui
print('PASS exact packaged game signature/address profile, producer capture before publication/unlock, texture policy under same surface lock, unchanged launcher and preserved collector, persistent UI selection contract')
