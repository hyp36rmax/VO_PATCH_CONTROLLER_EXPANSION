"""Build an isolated private extension of the exact pinned cnc-ddraw tree.
No original wrapper checkout, game image, or package is modified.
"""
import argparse, hashlib, json, subprocess, tarfile, io
from pathlib import Path
PIN='279a057ee7e1e4d584b56141c014ab01f3c6ee6d'
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--mode-aware',action='store_true');p.add_argument('--profiles',type=Path);p.add_argument('--cc',required=True);p.add_argument('--windres',required=True)
a=p.parse_args(); source=a.source.resolve();out=a.output.resolve();here=Path(__file__).resolve().parent
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==PIN
out.mkdir(parents=True,exist_ok=False)
archive=subprocess.check_output(['git','archive',PIN],cwd=source)
with tarfile.open(fileobj=io.BytesIO(archive)) as t:t.extractall(out,filter='data')
for name in ('presentation.h','movie_window.h','inventory.h','layout.h','policy.h','state_bridge.h','game_profiles.h'):(out/'inc'/name).write_bytes((here/name).read_bytes())
if a.profiles:(out/'inc/game_profiles.h').write_bytes(a.profiles.read_bytes())
(out/'src/state_bridge.c').write_bytes((here/'state_bridge.c').read_bytes())
f=out/'src/ddsurface.c';body=f.read_text();needle='HRESULT dds_Unlock(IDirectDrawSurfaceImpl* This, LPRECT lpRect)\n{'
assert body.count(needle)==1
body=body.replace(needle,needle+'\n    if (g_config.lock_surfaces && This == g_ddraw.primary) { EnterCriticalSection(&g_ddraw.cs); vo_capture_policy(); LeaveCriticalSection(&g_ddraw.cs); }')
flip='        if (g_config.flipclear && (This->caps & DDSCAPS_PRIMARYSURFACE))'
assert body.count(flip)==1
body=body.replace(flip,'        if (This == g_ddraw.primary) vo_capture_flip_policy();\n\n'+flip)
f.write_text('#include \"state_bridge.h\"\n'+body)
# The pinned wrapper resets the desktop to registry defaults before querying it.
# Private windowed output must observe the current mode, including unsaved modes.
f=out/'src/dd.c';body=f.read_text()
old='    if (!g_ddraw.mode.dmPelsWidth)\n    {\n        ChangeDisplaySettings(NULL, 0);'
new='    if (!g_ddraw.mode.dmPelsWidth)\n    {\n        char vo_native[2] = {0};\n        if (!g_config.windowed || GetEnvironmentVariableA("VO_DUAL_DISPLAY", vo_native, sizeof vo_native) != 1 || vo_native[0] != \'1\')\n            ChangeDisplaySettings(NULL, 0);'
assert body.count(old)==1
f.write_text(body.replace(old,new))
f=out/'src/render_d3d9.c';s=f.read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
replace('static D3D9RENDERER g_d3d9;','static D3D9RENDERER g_d3d9;\n#include "presentation.h"')
replace('                    IDirect3DTexture9_UnlockRect(g_d3d9.surface_tex[tex_index], 0);','                    if (SUCCEEDED(IDirect3DTexture9_UnlockRect(g_d3d9.surface_tex[tex_index], 0))) vo_dual_uploaded(tex_index);')
replace('BOOL d3d9_reset(BOOL windowed)\n{','BOOL d3d9_reset(BOOL windowed)\n{\n    vo_dual_before_reset();')
replace('BOOL d3d9_release_resources()\n{','BOOL d3d9_release_resources()\n{\n    vo_dual_before_reset();')
# Never wait for a game-held surface lock while holding the global lock:
# the game may be dispatching window messages from inside dds_Lock.
replace('            if (g_config.lock_surfaces)\n                EnterCriticalSection(&g_ddraw.primary->cs);',
        '            if (g_config.lock_surfaces && !TryEnterCriticalSection(&g_ddraw.primary->cs))\n            {\n                LeaveCriticalSection(&g_ddraw.cs);\n                ReleaseSemaphore(g_ddraw.render.sem, 1, NULL);\n                Sleep(1);\n                continue;\n            }')
replace('WaitForSingleObject(g_ddraw.render.sem, timeout)','vo_dual_wait(g_ddraw.render.sem, timeout)')
replace('        if (FAILED(IDirect3DDevice9_Present(g_d3d9.device, NULL, NULL, NULL, NULL)))','            vo_dual_present(tex_index);\n\n        if (FAILED(IDirect3DDevice9_Present(g_d3d9.device, NULL, NULL, NULL, NULL)))')
replace('    if (g_config.vhack)\n        InterlockedExchange(&g_ddraw.upscale_hack_active, FALSE);','    vo_dual_end();\n    if (g_config.vhack)\n        InterlockedExchange(&g_ddraw.upscale_hack_active, FALSE);')
f.write_text(s)
if a.mode_aware:
 from mode_extension import apply
 apply(out)
if a.profiles:
 from normal_projection import apply as normal_projection
 normal_projection(out)
version='F04B' if a.mode_aware else 'F03C'
# Avoid git metadata from the outer workspace influencing version metadata.
(out/'inc/git.h').write_text(f'#define GIT_COMMIT "{PIN}-private-D04-P05-{version}"\n#define GIT_BRANCH "private-presentation"\n')
# Compile directly: original Makefile rewrites git.h from its parent checkout.
objects=[]
for c in sorted((out/'src').glob('**/*.c')):
 obj=c.with_suffix('.o');subprocess.run([a.cc,'-I'+str(out/'inc'),'-O2','-Wall','-std=c99','-c',str(c),'-o',str(obj)],check=True);objects.append(str(obj))
subprocess.run([a.windres,'-J','rc',str(out/'res.rc'),str(out/'res.o')],cwd=out,check=True)
subprocess.run([a.cc,'-Wl,--enable-stdcall-fixup','-Wl,--no-insert-timestamp','-s','-static','-shared','-o',str(out/'ddraw.dll'),*objects,str(out/'res.o'),str(out/'exports.def'),'-lgdi32','-lwinmm','-lole32','-lmsimg32','-lavifil32','-luuid'],check=True)
(out/'private-build.json').write_text(json.dumps({'base':PIN,'dll_sha256':hashlib.sha256((out/'ddraw.dll').read_bytes()).hexdigest(),'mode_aware':a.mode_aware,'normal_projection_sha256':hashlib.sha256((here/'normal_projection.py').read_bytes()).hexdigest() if a.profiles else None,'selected_profiles_sha256':hashlib.sha256((out/'inc/game_profiles.h').read_bytes()).hexdigest(),'mode_extension_sha256':hashlib.sha256((here/'mode_extension.py').read_bytes()).hexdigest() if a.mode_aware else None,'extension':{n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in ('presentation.h','movie_window.h','inventory.h','layout.h','policy.h','state_bridge.h','state_bridge.c','game_profiles.h','build_wrapper.py')}},indent=2)+'\n')
