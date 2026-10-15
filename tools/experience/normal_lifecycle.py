"""Passive normal-game collector. Never launches or reconfigures the game."""
import argparse
import ctypes
import os
from pathlib import Path
import diagnostics as d
import discovery
import movie_geometry

RETURN='RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip'
STATE={'VO_EX_REQUESTED_MODE':'selected_mode','VO_EX_EFFECTIVE_MODE':'effective_mode',
       'VO_EX_PROFILE':'profile','VO_EX_PRIMARY':'primary','VO_EX_SECONDARY':'secondary',
       'VO_EX_FALLBACK':'fallback'}


def run(root, wait, ready, *, environ=None, snapshot=discovery.snapshot):
    root=Path(root);environ=os.environ if environ is None else environ
    marker=root/'diagnostics/session-active'
    if marker.exists():d.event(root,'previous_session_incomplete')
    level=environ.get('VO_EX_DIAGNOSTICS','NORMAL')
    if level not in d.LEVELS:level='NORMAL'
    d.event(root,'startup',{'level':d.LEVELS.index(level)})
    marker.write_text('active\n')
    state={}
    for key,field in STATE.items():
        try:value=int(environ[key])
        except (KeyError,ValueError):continue
        if -1<=value<=65535:state[field]=value
    d.event(root,'selection',state)
    d.event(root,'movie',movie_geometry.evidence(root,environ))
    if state.get('fallback'):d.event(root,'recovery',{'fallback':state['fallback']})
    for cfg in d.configurations(root,root).values():
        if 'scrsize' in cfg:
            d.event(root,'configuration',{'f4_state':cfg['scrsize']&1,'split_preference':cfg['scrsize']&2})
    try:
        info=snapshot()
        d.event(root,'display_discovery',{'count':len(info['displays']),'ok':bool(info['available'])})
        d.event(root,'controller_discovery',{'count':len(info['controllers']),'ok':bool(info['available'])})
        for row in info['displays']:d.event(root,'display_discovery',row)
        for row in info['controllers']:d.event(root,'controller_discovery',row)
    except OSError:d.event(root,'error',{'module':5,'code':3})
    # Parent waits only before renderer entry; no I/O runs on game frame/input paths.
    ready()
    try:code=wait()
    except OSError:
        d.event(root,'error',{'module':5,'exit_known':False})
        raise
    d.event(root,'shutdown',{'exit_known':True,'exit_code':code})
    marker.unlink(missing_ok=True)
    try:return d.export(root,game_directory=root,return_name=RETURN)
    except Exception:
        d.event(root,'error',{'module':5,'code':2,'io_error':True})
        # Existing diagnostics folder is the obvious raw return folder. Never
        # copy arbitrary game files or free-form module logs into a new export.
        (root/'RETURN-THIS-VO-PATCH-EX-F01-P04-F02.txt').write_text(
            'Diagnostic compression failed. Local logs remain in the diagnostics folder.\n')
        raise


def movie_state(pid):
    """Read only class/visibility for this process; never window text or input."""
    from ctypes import wintypes as w
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    user.IsWindowVisible.argtypes=[w.HWND];user.IsWindowVisible.restype=w.BOOL
    user.EnumWindows.argtypes=[callback,w.LPARAM]
    user.EnumChildWindows.argtypes=[w.HWND,callback,w.LPARAM]
    user.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)];user.GetWindowRect.restype=w.BOOL
    found=set();visible=set();seen=set();bounds=[]
    def visit(hwnd,unused):
        if hwnd in seen:return True
        if len(seen)>=256:return False
        seen.add(hwnd)
        owner=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value!=pid:return True
        name=ctypes.create_unicode_buffer(128)
        if user.GetClassNameW(hwnd,name,128) and name.value in ('AVIWnd32','MCIAVI','AVI Window','MCIWndClass','VideoRenderer'):
            found.add(hwnd)
            if user.IsWindowVisible(hwnd):
                visible.add(hwnd)
                rect=w.RECT()
                if user.GetWindowRect(hwnd,ctypes.byref(rect)) and len(bounds)<4:
                    bounds.append((rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top))
        return True
    child=callback(visit)
    def top(hwnd,unused):
        visit(hwnd,unused)
        owner=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value==pid:user.EnumChildWindows(hwnd,child,0)
        return True
    if not user.EnumWindows(callback(top),0):raise ctypes.WinError(ctypes.get_last_error())
    return len(found),len(visible),tuple(sorted(bounds))


def attach(root,pid,event_name):
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.OpenEventW.argtypes=[w.DWORD,w.BOOL,w.LPCWSTR];k.OpenEventW.restype=w.HANDLE
    k.SetEvent.argtypes=[w.HANDLE];k.SetEvent.restype=w.BOOL
    k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
    k.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];k.GetExitCodeProcess.restype=w.BOOL
    k.CloseHandle.argtypes=[w.HANDLE]
    if pid<=0 or not event_name.startswith('Local\\VOEX-'):raise ValueError('invalid lifecycle attachment')
    process=k.OpenProcess(0x100000|0x1000,False,pid)
    if not process:raise ctypes.WinError(ctypes.get_last_error())
    event=None
    try:
        event=k.OpenEventW(2,False,event_name)
        if not event:raise ctypes.WinError(ctypes.get_last_error())
        def ready():
            if not k.SetEvent(event):raise ctypes.WinError(ctypes.get_last_error())
        def wait():
            previous=None;probe_failed=False
            geometry=movie_geometry.evidence(root,os.environ)
            while True:
                result=k.WaitForSingleObject(process,500)
                if result==0:break
                if result!=258:raise ctypes.WinError(ctypes.get_last_error())
                try:
                    current=movie_state(pid)
                    if current!=previous:
                        d.event(root,'movie',{'count':current[0],'visible':current[1],
                                             'event':1 if current[1] and (not previous or not previous[1]) else 3 if previous and previous[1] and not current[1] else 2})
                        for i,(x,y,w,h) in enumerate(current[2]):
                            d.event(root,'movie',{'window_index':i,'window_x':x,'window_y':y,'window_width':w,'window_height':h,
                                                 'geometry_match':not geometry['geometry_fallback'] and (x,y,w,h)==tuple(geometry[k] for k in ('expected_x','expected_y','expected_width','expected_height'))})
                        previous=current
                except OSError:
                    if not probe_failed:d.event(root,'error',{'module':4,'code':1})
                    probe_failed=True
            if previous and previous[0]:d.event(root,'movie',{'count':0,'visible':0,'event':3})
            code=w.DWORD()
            if not k.GetExitCodeProcess(process,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
            return code.value
        return run(root,wait,ready)
    finally:
        if event:k.CloseHandle(event)
        k.CloseHandle(process)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game',type=Path)
    p.add_argument('--pid',type=int);p.add_argument('--ready');p.add_argument('--export',action='store_true')
    a=p.parse_args()
    if a.export:
        try:d.export(a.game,game_directory=a.game,return_name=RETURN)
        except Exception:
            (a.game/'RETURN-THIS-VO-PATCH-EX-F01-P04-F02.txt').write_text('Export failed. Existing diagnostic logs are preserved in the diagnostics folder.\n')
            raise
    elif a.pid and a.ready:attach(a.game,a.pid,a.ready)
    else:p.error('normal lifecycle attachment or export required')
