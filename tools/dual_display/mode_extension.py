"""Opt-in F04 adaptations of the pinned wrapper. F03C build stays available."""
from pathlib import Path

def apply(out):
    def edit(name,old,new):
        p=out/name;s=p.read_text();assert s.count(old)==1,(name,old);p.write_text(s.replace(old,new))
    dd=out/'src/dd.c';dd.write_text('#include <stdio.h>\n'+dd.read_text())
    edit('src/dd.c','GetEnvironmentVariableA("VO_DUAL_DISPLAY", vo_native, sizeof vo_native)', 'GetEnvironmentVariableA("VO_PRIVATE_DISPLAY", vo_native, sizeof vo_native)')
    # Launcher passes the discovered, current desktop rectangle. This changes
    # window placement and presentation size, never Windows display settings.
    edit('src/dd.c','    BOOL zooming = g_ddraw.zoom.enabled;', '''    BOOL vo_selected_desktop=FALSE;
    char vo_desktop[128]={0}; int vo_x,vo_y,vo_w,vo_h; char vo_tail;
    if (g_config.windowed && GetEnvironmentVariableA("VO_DESKTOP",vo_desktop,sizeof vo_desktop)>0 &&
        sscanf(vo_desktop,"%9d,%9d,%9d,%9d%c",&vo_x,&vo_y,&vo_w,&vo_h,&vo_tail)==4 &&
        vo_w>0 && vo_h>0 && vo_w<=32768 && vo_h<=32768 && vo_x>=-32768 && vo_x<=32768 && vo_y>=-32768 && vo_y<=32768)
    {
        vo_selected_desktop=TRUE;
        g_ddraw.mode.dmPelsWidth=vo_w; g_ddraw.mode.dmPelsHeight=vo_h;
        g_config.window_rect.left=vo_x; g_config.window_rect.top=vo_y;
        g_config.window_rect.right=vo_w; g_config.window_rect.bottom=vo_h;
    }
    BOOL zooming = g_ddraw.zoom.enabled;''')
    edit('src/dd.c','            x = y = 0;', '            x = vo_selected_desktop ? vo_x : 0; y = vo_selected_desktop ? vo_y : 0;')
    edit('src/dd.c','                y = real_GetSystemMetrics(SM_CYMENU);', '                y += real_GetSystemMetrics(SM_CYMENU);')
    # The upstream movie stub already uses real physical client pixels. The
    # wrapper's legacy child-GDI path applies framebuffer scaling a second time.
    # Bypass that transform ONLY for this process's direct AVI child in F04.
    p=out/'src/winapi_hooks.c';s=p.read_text()
    first='BOOL WINAPI fake_StretchBlt('
    helper='''static BOOL vo_native_movie(HWND hwnd)
{
    char enabled[2]={0},name[32]={0}; DWORD pid=0;
    if(GetEnvironmentVariableA("VO_PRIVATE_DISPLAY",enabled,2)!=1 || enabled[0]!='1' ||
       !hwnd || !g_ddraw.hwnd || GetParent(hwnd)!=g_ddraw.hwnd ||
       !(real_GetWindowLongA(hwnd,GWL_STYLE)&WS_CHILD))return FALSE;
    GetWindowThreadProcessId(hwnd,&pid);
    return pid==GetCurrentProcessId() && GetClassNameA(hwnd,name,sizeof name) && !strcmp(name,"AVIWnd32");
}

'''
    assert s.count(first)==1;s=s.replace(first,helper+first)
    functions={
      'fake_StretchBlt':('hdcDest','real_StretchBlt(hdcDest,xDest,yDest,wDest,hDest,hdcSrc,xSrc,ySrc,wSrc,hSrc,rop)'),
      'fake_BitBlt':('hdc','real_BitBlt(hdc,x,y,cx,cy,hdcSrc,x1,y1,rop)'),
      'fake_SetDIBitsToDevice':('hdc','real_SetDIBitsToDevice(hdc,xDest,yDest,w,h,xSrc,ySrc,StartScan,cLines,lpvBits,lpbmi,ColorUse)'),
      'fake_StretchDIBits':('hdc','real_StretchDIBits(hdc,xDest,yDest,DestWidth,DestHeight,xSrc,ySrc,SrcWidth,SrcHeight,lpBits,lpbmi,iUsage,rop)')}
    for name,(dc,call) in functions.items():
        start=s.index('WINAPI '+name+'(');at=s.index('    HWND hwnd = WindowFromDC('+dc+');',start)
        at+=len('    HWND hwnd = WindowFromDC('+dc+');')
        s=s[:at]+'\n    if(vo_native_movie(hwnd))return '+call+';'+s[at:]
    p.write_text(s)
    edit('inc/presentation.h','vo_dual.mirror = GetPrivateProfileIntW(L"Presentation", L"MirrorPlayer1", 0, config) == 1;',
         'vo_dual.mirror = GetPrivateProfileIntW(L"Presentation", L"Mode", 1, config) == 2;')

    edit('inc/presentation.h','    if (!discover()) goto fail;',
         '    WCHAR session_config[MAX_PATH]; DWORD session_len=GetEnvironmentVariableW(L"VO_SESSION_CONFIG",session_config,MAX_PATH);\n    if(session_len>=MAX_PATH)goto fail;\n    if(session_len)wcscpy(config,session_config);\n    if (!discover()) goto fail;')
    edit('inc/presentation.h','    int mirror;', '    int mirror; BOOL strict_stopped;')
    edit('inc/presentation.h','static LRESULT CALLBACK vo_output_proc', 'static void vo_strict_stop(void)\n{\n    char strict[2]={0};\n    if(vo_dual.attempted && vo_dual.disabled && !vo_dual.strict_stopped &&\n       GetEnvironmentVariableA("VO_STRICT_MODE",strict,sizeof strict)==1 && strict[0]==\'1\'){\n        vo_dual.strict_stopped=TRUE;\n        PostMessageA(g_ddraw.hwnd,WM_CLOSE,0,0);\n    }\n}\nstatic LRESULT CALLBACK vo_output_proc')
    edit('inc/presentation.h','    if (vo_dual.disabled || GetForegroundWindow()', '    vo_strict_stop();\n    if (vo_dual.disabled || GetForegroundWindow()')
    edit('inc/presentation.h','done:\n    if (vo_dual.disabled)', 'done:\n    vo_strict_stop();\n    if (vo_dual.disabled)')
    edit('inc/presentation.h','                vo_policy_log(log);', '                fprintf(log,"strict_test_stopped=%d\\n",vo_dual.strict_stopped);\n                vo_policy_log(log);')

    # Full-composition Mirror uses the selected Single image. Environment is a
    # validated launch projection; configuration Mode must agree before output.
    edit('inc/presentation.h','static struct {', 'static BOOL vo_complete_mirror(void){\n char value[2]={0};return GetEnvironmentVariableA("VO_COMPLETE_MIRROR",value,2)==1&&value[0]==\'1\';\n}\nstatic BOOL vo_source_ready(void){\n if(!vo_complete_mirror())return g_ddraw.width==3840&&g_ddraw.height==1080;\n char size[64]={0},tail;int w,h;\n return GetEnvironmentVariableA("VO_SOURCE_SIZE",size,sizeof size)>0&&\n sscanf(size,"%9d,%9d%c",&w,&h,&tail)==2&&w>0&&h>0&&\n g_ddraw.width==w&&g_ddraw.height==h;\n}\nstatic struct {')
    edit('inc/presentation.h','g_ddraw.width != 3840 || g_ddraw.height != 1080 || g_ddraw.bpp != 16) goto fail;', '!vo_source_ready() || g_ddraw.bpp != 16) goto fail;')
    edit('inc/presentation.h','!vo_dual.attempted && (g_ddraw.width != 3840 || g_ddraw.height != 1080 || g_ddraw.bpp != 16)', '!vo_dual.attempted && (!vo_source_ready() || g_ddraw.bpp != 16)')
    edit('inc/presentation.h','if (g_ddraw.width != 3840 || g_ddraw.height != 1080 || g_ddraw.bpp != 16) {', 'if (!vo_source_ready() || g_ddraw.bpp != 16) {')
    edit('inc/presentation.h','    char a[VO_ID_CHARS], b[VO_ID_CHARS];', '    if(vo_dual.mirror!=vo_complete_mirror())goto fail;\n    char a[VO_ID_CHARS], b[VO_ID_CHARS];')
    edit('inc/presentation.h','BOOL eligible=vo_dual.last_phase==VO_PRIMARY_ONLY && vo_completed_policy()==VO_PRIMARY_ONLY;', 'BOOL eligible=vo_complete_mirror() || (vo_dual.last_phase==VO_PRIMARY_ONLY && vo_completed_policy()==VO_PRIMARY_ONLY);')
    edit('inc/presentation.h','        if(!vo_route(vo_dual.policy[texture_index],vo_dual.mirror,i,monitor,&o,&black)){hr=E_FAIL;goto restore;}', '        if(vo_complete_mirror()){\n            o.source=(VoRect){0,0,g_ddraw.width,g_ddraw.height};\n            if(!vo_fit_source(monitor,o.source.w,o.source.h,&o.destination)){hr=E_FAIL;goto restore;}\n        }else if(!vo_route(vo_dual.policy[texture_index],0,i,monitor,&o,&black)){hr=E_FAIL;goto restore;}')
    edit('inc/presentation.h','                vo_policy_log(log);', '                fprintf(log,"complete_mirror=%d source_size=%dx%d\\n",vo_complete_mirror(),g_ddraw.width,g_ddraw.height);\n                vo_policy_log(log);')

    edit('inc/presentation.h','vo_dual.phase_pairs[3],vo_dual.mirror);','vo_dual.phase_pairs[3],0);')
