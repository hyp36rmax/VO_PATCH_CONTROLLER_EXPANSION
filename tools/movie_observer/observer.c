#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0601
#include <windows.h>
#include <stdio.h>
#include <dwmapi.h>
#include <stdint.h>
#include <stdarg.h>
#include "window_model.h"
static FILE *logfile;
static DWORD pid;static unsigned sample,rank_,count,oldcount,topcount;static int overflow,limited,io_error;
static VoWindow windows_[VO_WINDOWS],old[VO_WINDOWS],tops[VO_WINDOWS];
static ULONGLONG started;static unsigned long bytes;
static void logline(const char *fmt,...){if(limited)return;va_list a;va_start(a,fmt);int n=vfprintf(logfile,fmt,a);va_end(a);if(n<0){io_error=1;return;}bytes+=(unsigned)n;if(bytes>=VO_LOG_LIMIT){fputs("LIMIT log_bytes reached; later window samples omitted\n",logfile);limited=1;}}
static void text(const WCHAR *w){char b[2048];int n=WideCharToMultiByte(CP_UTF8,0,w,-1,b,sizeof b,NULL,NULL);if(!n){logline("<conversion-failed>");return;}for(int i=0;b[i];i++){unsigned char c=(unsigned char)b[i];if(c<32||c=='\\'||c=='"')logline("\\x%02x",c);else logline("%c",c);}}
static VoWindow read_window(HWND h,unsigned rank){VoWindow w={0};RECT r={0};w.hwnd=(uintptr_t)h;w.parent=(uintptr_t)GetAncestor(h,GA_PARENT);w.owner=(uintptr_t)GetWindow(h,GW_OWNER);DWORD process_id=0;w.tid=GetWindowThreadProcessId(h,&process_id);w.pid=process_id;w.rank=rank;w.visible=IsWindowVisible(h);w.bounds_ok=GetWindowRect(h,&r);w.bounds=(VoBounds){r.left,r.top,r.right,r.bottom};return w;}
static void describe(HWND h,VoWindow w){
 WCHAR cls[128]={0},title[512]={0};RECT client={0};POINT origin={0};MONITORINFOEXW mi={0};GUITHREADINFO gi={0};
 GetClassNameW(h,cls,128);GetWindowTextW(h,title,512);BOOL client_ok=GetClientRect(h,&client);BOOL mapped=ClientToScreen(h,&origin);mi.cbSize=sizeof mi;BOOL monok=GetMonitorInfoW(MonitorFromWindow(h,MONITOR_DEFAULTTONEAREST),(MONITORINFO*)&mi);gi.cbSize=sizeof gi;BOOL guiok=GetGUIThreadInfo(w.tid,&gi);
 const char *role="OTHER_TARGET_WINDOW";
 if(!wcscmp(cls,L"VoPrivatePlayerOutput"))role=!wcscmp(title,L"Virtual-On Player 1")?"DISPLAY1":!wcscmp(title,L"Virtual-On Player 2")?"DISPLAY2":"PRESENTATION";
 else if(!_wcsicmp(cls,L"MCIAVI")||!_wcsicmp(cls,L"AVIWnd32")||!_wcsicmp(cls,L"AVI Window")||!_wcsicmp(cls,L"MCIWndClass")||!_wcsicmp(cls,L"VideoRenderer"))role="MOVIE_CLASS_CANDIDATE";
 else if(guiok&&gi.hwndActive==h&&GetAncestor(h,GA_ROOT)==h)role="GAME_INPUT_CANDIDATE";
 DWORD cloaked=0;HRESULT cloak_hr=DwmGetWindowAttribute(h,14,&cloaked,sizeof cloaked);
 logline("ROLE hwnd=%p hint=%s cloak_hr=0x%08lx cloaked=%lu\n",h,role,(unsigned long)cloak_hr,cloaked);
 logline("WINDOW sample=%u hwnd=%p pid=%lu tid=%u parent=%p owner=%p root=%p z_top_rank=%u visible=%d iconic=%d style=0x%08lx exstyle=0x%08lx rect_ok=%d rect=%ld,%ld,%ld,%ld client_ok=%d client=%ld,%ld,%ld,%ld client_screen_ok=%d origin=%ld,%ld foreground=%p active_ok=%d active=%p class=\"",sample,h,(unsigned long)w.pid,w.tid,(void*)w.parent,(void*)w.owner,GetAncestor(h,GA_ROOT),w.rank,w.visible,IsIconic(h),(unsigned long)GetWindowLongPtrW(h,GWL_STYLE),(unsigned long)GetWindowLongPtrW(h,GWL_EXSTYLE),w.bounds_ok,(long)w.bounds.left,(long)w.bounds.top,(long)w.bounds.right,(long)w.bounds.bottom,client_ok,client.left,client.top,client.right,client.bottom,mapped,origin.x,origin.y,GetForegroundWindow(),guiok,gi.hwndActive);
 text(cls);logline("\" prev=%p next=%p title=\"",GetWindow(h,GW_HWNDPREV),GetWindow(h,GW_HWNDNEXT));text(title);logline("\" monitor_ok=%d monitor=\"",monok);text(mi.szDevice);logline("\" monitor_rect=%ld,%ld,%ld,%ld primary=%d\n",mi.rcMonitor.left,mi.rcMonitor.top,mi.rcMonitor.right,mi.rcMonitor.bottom,(mi.dwFlags&MONITORINFOF_PRIMARY)!=0);
}
static BOOL CALLBACK child(HWND h,LPARAM rootrank){VoWindow w=read_window(h,(unsigned)rootrank);if(w.pid!=pid)return TRUE;if(!vo_append(windows_,&count,w)){overflow=1;return FALSE;}describe(h,w);return TRUE;}
static BOOL CALLBACK top(HWND h,LPARAM ignored){(void)ignored;if(rank_>=1024||count==VO_WINDOWS){overflow=1;return FALSE;}VoWindow w=read_window(h,rank_++);if(topcount<VO_WINDOWS)tops[topcount++]=w;else overflow=1;if(w.pid==pid){if(!vo_append(windows_,&count,w)){overflow=1;return FALSE;}describe(h,w);EnumChildWindows(h,child,w.rank);}return TRUE;}
static void capture(void){count=topcount=rank_=0;overflow=0;logline("SAMPLE %u elapsed_ms=%llu foreground=%p\n",sample,(unsigned long long)(GetTickCount64()-started),GetForegroundWindow());BOOL ok=EnumWindows(top,0);
 for(unsigned i=0;i<count;i++){if(!vo_contains(old,oldcount,windows_[i].hwnd))logline("APPEARED sample=%u hwnd=%p (first observed; not creation timestamp)\n",sample,(void*)windows_[i].hwnd);for(unsigned j=0;j<topcount;j++)if(vo_cover_candidate(tops[j],windows_[i]))logline("POSSIBLE_COVER sample=%u target=%p above=%p above_pid=%u above_rank=%u rect=%ld,%ld,%ld,%ld (metadata only)\n",sample,(void*)windows_[i].hwnd,(void*)tops[j].hwnd,tops[j].pid,tops[j].rank,(long)tops[j].bounds.left,(long)tops[j].bounds.top,(long)tops[j].bounds.right,(long)tops[j].bounds.bottom);}
 if(ok&&!overflow)for(unsigned i=0;i<oldcount;i++)if(!vo_contains(windows_,count,old[i].hwnd))logline("DISAPPEARED sample=%u hwnd=%p still_IsWindow=%d (absence not proof of destruction)\n",sample,(void*)old[i].hwnd,IsWindow((HWND)old[i].hwnd));
 logline("ENUM_RESULT sample=%u ok=%d truncated=%d targets=%u tops=%u\n",sample,ok,overflow,count,topcount);memcpy(old,windows_,count*sizeof *old);oldcount=count;if(fflush(logfile))io_error=1;}
int wmain(void){
 WCHAR self[32768],exe[32768],cmd[32768],dir[32768],logpath[32768];DWORD n=GetModuleFileNameW(NULL,self,32768);if(!n||n>=32768)return 2;WCHAR *slash=wcsrchr(self,L'\\');if(!slash)return 2;*slash=0;
 if(wcslen(self)>32000)return 2;swprintf(dir,32768,L"%ls\\game",self);swprintf(exe,32768,L"%ls\\v_on.exe",dir);swprintf(cmd,32768,L"\"%ls\"",exe);swprintf(logpath,32768,L"%ls\\movie-windows.log",self);
 logfile=_wfopen(logpath,L"wb");if(!logfile){MessageBoxW(NULL,L"Observer could not create movie-windows.log. Game was not launched.",L"Movie observation",MB_OK|MB_ICONERROR);return 3;}
 SYSTEMTIME utc;GetSystemTime(&utc);started=GetTickCount64();logline("VO movie window observer v1 UTC=%04u-%02u-%02uT%02u:%02u:%02uZ interval_ms=250 limit_samples=%u limit_bytes=%u\nNo decoded pixel visibility or game-state claim is inferred from window metadata.\n",utc.wYear,utc.wMonth,utc.wDay,utc.wHour,utc.wMinute,utc.wSecond,VO_SAMPLES,VO_LOG_LIMIT);if(fflush(logfile)||io_error){fclose(logfile);return 3;}
 SetEnvironmentVariableW(L"VO_DUAL_DISPLAY",L"1");STARTUPINFOW si={0};PROCESS_INFORMATION pi={0};si.cb=sizeof si;
 /* Normal launch: no debugger, suspension, injection or target memory access. */
 if(!CreateProcessW(exe,cmd,NULL,NULL,FALSE,0,NULL,dir,&si,&pi)){logline("LAUNCH_FAILED error=%lu\n",GetLastError());fclose(logfile);return 4;}
 pid=pi.dwProcessId;CloseHandle(pi.hThread);logline("PROCESS pid=%lu observer_pid=%lu executable=\"",pid,GetCurrentProcessId());text(exe);logline("\"\n");
 DWORD wait=WAIT_TIMEOUT;
 while((wait=WaitForSingleObject(pi.hProcess,0))==WAIT_TIMEOUT){if(sample<VO_SAMPLES&&!limited&&!io_error){capture();sample++;}else if(!limited){logline("LIMIT samples reached; waiting for process exit\n");limited=1;}wait=WaitForSingleObject(pi.hProcess,250);if(wait!=WAIT_TIMEOUT)break;}
 DWORD exitcode=0;BOOL got=GetExitCodeProcess(pi.hProcess,&exitcode);fprintf(logfile,"PROCESS_END elapsed_ms=%llu wait=%lu exit_known=%d exit_code=%lu samples=%u truncated=%d io_error=%d\n",(unsigned long long)(GetTickCount64()-started),wait,got,exitcode,sample,limited,io_error);
 for(unsigned i=0;i<oldcount;i++)fprintf(logfile,"END_WINDOW hwnd=%p still_IsWindow=%d\n",(void*)old[i].hwnd,IsWindow((HWND)old[i].hwnd));
 CloseHandle(pi.hProcess);int bad=fclose(logfile);return wait==WAIT_OBJECT_0&&got&&!io_error&&!bad?0:5;
}
