"""Freeze normal-startup presentation choices until the next process launch."""

def apply(out):
 def replace_once(text,old,new):
  assert text.count(old)==1,(old,text.count(old))
  return text.replace(old,new)
 p=out/'inc/presentation.h';s=p.read_text()
 from pathlib import Path
 (out/'inc/diagnostics_privacy.h').write_bytes(Path(__file__).with_name('diagnostics_privacy.h').read_bytes())
 (out/'inc/diagnostics_runtime.h').write_bytes(Path(__file__).with_name('diagnostics_runtime.h').read_bytes())
 # Mouse forwarding is private overlay-only; use the exact fitted source
 # rectangle already chosen by the validated presentation path.
 mouse_bridge = r'''    typedef int (WINAPI *OverlayVisible)(void);
    HMODULE overlay=GetModuleHandleW(L"vooverlay.dll");
    OverlayVisible visible=overlay?(OverlayVisible)GetProcAddress(overlay,"VonOverlayVisible"):NULL;
    if(visible && visible() && (window==vo_dual.window[0] || vo_dual.mirror)) {
        if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
        if(msg>=WM_MOUSEFIRST && msg<=WM_MOUSELAST) {
            int index=window==vo_dual.window[0]?0:1;
            VoOutput o=vo_dual.output[index];VoRect monitor=monitors[o.monitor].desktop;
            POINT point={(short)LOWORD(l),(short)HIWORD(l)};
            if(msg==WM_MOUSEWHEEL)ScreenToClient(window,&point);
            int x=point.x-(o.destination.x-monitor.x), y=point.y-(o.destination.y-monitor.y);
            if(o.destination.w>0 && o.destination.h>0 && x>=0 && y>=0 && x<o.destination.w && y<o.destination.h) {
                x=o.source.x+x*o.source.w/o.destination.w;y=o.source.y+y*o.source.h/o.destination.h;
                PostMessageA(g_ddraw.hwnd,WM_APP+0x351,(WPARAM)msg|(w&0xffff0000),MAKELPARAM(x,y));
            }
            return 0;
        }
    }
'''
 s=replace_once(s,'    if (msg == WM_MOUSEACTIVATE) return MA_NOACTIVATEANDEAT;',mouse_bridge+'    if (msg == WM_MOUSEACTIVATE) return MA_NOACTIVATEANDEAT;')
 s=replace_once(s,'#include \"policy.h\"','#include \"policy.h\"\n#include \"diagnostics_runtime.h\"')
 s=replace_once(s,'    if(vo_dual.attempted) {','    if(vo_dual.attempted && vo_diagnostic_level()>=2) {')
 s=replace_once(s,'FILE *log=_wfopen(path,L\"a\");','WIN32_FILE_ATTRIBUTE_DATA info;\n            int room=!GetFileAttributesExW(path,GetFileExInfoStandard,&info)||(info.nFileSizeHigh==0&&info.nFileSizeLow<256*1024-32768);\n            FILE *log=room?_wfopen(path,L\"a\"):NULL;')
 s=replace_once(s,'player=%d id=%s source=', 'player=%d source=').replace('i+1,monitors[o.monitor].id,o.source.x','i+1,o.source.x')
 old='    vo_dual.mirror = GetPrivateProfileIntW(L"Presentation", L"Mode", 1, config) == 2;'
 new='''    char effective_mode[2]={0};
    DWORD effective_length=GetEnvironmentVariableA("VO_EX_EFFECTIVE_MODE",effective_mode,2);
    if(effective_length && (effective_length!=1 || (effective_mode[0]!='1' && effective_mode[0]!='2')))goto fail;
    vo_dual.mirror = effective_length ? effective_mode[0]=='2' : GetPrivateProfileIntW(L"Presentation", L"Mode", 1, config) == 2;'''
 assert s.count(old)==1;s=s.replace(old,new)
 old='    load_id(L"Player1", a); load_id(L"Player2", b);'
 new='''    if(effective_length){
        DWORD na=GetEnvironmentVariableA("VO_EX_PRIMARY_ID",a,sizeof a), nb=GetEnvironmentVariableA("VO_EX_SECONDARY_ID",b,sizeof b);
        if(!na||na>=sizeof a||!nb||nb>=sizeof b)goto fail;
    }else{load_id(L"Player1", a); load_id(L"Player2", b);}'''
 assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)

 # Gate optional in-memory traces; essential phase classification stays active.
 p=out/'inc/movie_window.h';text=p.read_text()
 text=replace_once(text,' ++m->total;', ' if(vo_diagnostic_level()<3)return;\n ++m->total;')
 p.write_text(text)
 p=out/'src/state_bridge.c';text=p.read_text()
 text=replace_once(text,'#include "state_bridge.h"','#include "state_bridge.h"\n#include "diagnostics_runtime.h"')
 text=replace_once(text,' ++observation.captures;if(kind==2)++observation.flips;else ++observation.unlocks;', ' unsigned diagnostic=vo_diagnostic_level();\n if(diagnostic>=3){++observation.captures;if(kind==2)++observation.flips;else ++observation.unlocks;}')
 text=replace_once(text,' if(phase==VO_POLICY_UNKNOWN){', ' if(diagnostic>=3 && phase==VO_POLICY_UNKNOWN){')
 text=replace_once(text,' if(observation.captures==1||prior_status!=observation.status||prior_phase!=(unsigned)phase){', ' if(diagnostic>=2 && (observation.captures==1||prior_status!=observation.status||prior_phase!=(unsigned)phase)){')
 p.write_text(text)

 # A narrowly scoped primary-surface transaction for the paused overlay.
 # Uses the same lock as the existing D3D9 upload, without message pumping.
 p=out/'src/ddsurface.c'
 p.write_text(p.read_text()+r'''
BOOL WINAPI VonOverlaySurfaceBegin(IDirectDrawSurfaceImpl *surface)
{
    if (!surface || !g_config.lock_surfaces) return FALSE;
    IDirectDrawSurface_AddRef(surface);
    EnterCriticalSection(&surface->cs);
    return TRUE;
}
void WINAPI VonOverlaySurfaceEnd(IDirectDrawSurfaceImpl *surface)
{
    GdiFlush();
    /* ReleaseDC throttles primary updates shortly after a flip. The paused
     * transaction is now complete, so publish it without a timeout delay. */
    if (surface == g_ddraw.primary && g_ddraw.render.run)
    {
        InterlockedExchange(&g_ddraw.render.surface_updated, TRUE);
        InterlockedExchange(&g_ddraw.render.screen_updated, TRUE);
        ReleaseSemaphore(g_ddraw.render.sem, 1, NULL);
    }
    LeaveCriticalSection(&surface->cs);
    IDirectDrawSurface_Release(surface);
}
''')
 p=out/'exports.def';p.write_text(p.read_text()+'\n    VonOverlaySurfaceBegin\n    VonOverlaySurfaceEnd\n')
