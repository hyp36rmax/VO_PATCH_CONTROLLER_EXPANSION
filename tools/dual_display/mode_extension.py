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
