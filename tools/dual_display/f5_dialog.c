/* Private F5 child dialog. No game input polling or live renderer changes. */
#include "inventory.h"
#include "f5_settings.h"
#include "diagnostics_privacy.h"
static volatile LONG diagnostic_level;
__declspec(dllexport) unsigned WINAPI VonDiagnosticsLevel(void){return (unsigned)InterlockedCompareExchange(&diagnostic_level,0,0);}
#define DISPLAY_BUTTON 0x5e00
#define MODE 100
#define PRIMARY 101
#define SECONDARY 102
#define ASPECT 103
static VoPreference saved,pending;
static unsigned dirty;
static int busy;
static HFONT font;
static HWND secondary_label;
static unsigned save_stage;static DWORD save_error;
static void event(unsigned code,int result){
 if(vo_diagnostic_level()<((code==3||code>=20)?1u:2u))return;
 WCHAR path[MAX_PATH];SYSTEMTIME t;GetSystemTime(&t);
 DWORD length=GetModuleFileNameW(NULL,path,MAX_PATH);if(!length||length>=MAX_PATH)return;
 WCHAR *slash=wcsrchr(path,L'\\');if(!slash)return;slash[1]=0;
 if(wcslen(path)+40>=MAX_PATH)return;
 wcscat(path,L"diagnostics");CreateDirectoryW(path,NULL);wcscat(path,L"\\events.jsonl");
 HANDLE h=CreateFileW(path,FILE_APPEND_DATA|GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
 if(h==INVALID_HANDLE_VALUE)return;
 LARGE_INTEGER size;if(GetFileSizeEx(h,&size)&&size.QuadPart<256*1024){
  char line[512];int n=snprintf(line,sizeof line,"{\"event\":\"%s\",\"utc\":\"%04u-%02u-%02uT%02u:%02u:%02uZ\",\"fields\":{\"code\":%u,\"mode\":%d,\"profile\":%d,\"primary\":%d,\"secondary\":%d,\"result\":%d,\"restart_required\":%d,\"save_stage\":%u,\"winerror\":%lu}}\n",code==3?"error":"configuration",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,code,pending.mode,pending.aspect,vo_find(monitors,count,pending.primary),vo_find(monitors,count,pending.secondary),result,code==4,save_stage,(unsigned long)save_error);
  if(code==6)n=snprintf(line,sizeof line,"{\"event\":\"configuration\",\"fields\":{\"code\":6,\"result\":0}}\n");
  if(code>=20)n=snprintf(line,sizeof line,"{\"event\":\"overlay_lifecycle\",\"fields\":{\"code\":%u}}\n",code-20);
  DWORD written;if(n>0&&n<(int)sizeof line&&size.QuadPart+n<=256*1024){WriteFile(h,line,(DWORD)n,&written,NULL);FlushFileBuffers(h);}
 }CloseHandle(h);
}
/* Overlay lifecycle uses the existing bounded event sink and consent. No raw
 * device samples or automatic uploads are recorded. */
__declspec(dllexport) void WINAPI VonOverlayLifecycle(unsigned code){
 if(vo_diagnostic_level()<1||code<1||code>11)return;
 event(20+code,0);
}
static int path_config(void){
 DWORD length=GetModuleFileNameW(NULL,config,MAX_PATH);if(!length||length>=MAX_PATH)return 0;
 WCHAR *slash=wcsrchr(config,L'\\');if(!slash)return 0;slash[1]=0;
 if(wcslen(config)+20>=MAX_PATH)return 0;
 wcscat(config,L"player-displays.ini");return 1;
}
static void read_saved(void){
 load_id(L"Player1",saved.primary);load_id(L"Player2",saved.secondary);
 WCHAR text[32];GetPrivateProfileStringW(L"Presentation",L"Mode",L"",text,32,config);
 int legacy=saved.primary[0]&&saved.secondary[0]?(GetPrivateProfileIntW(L"Presentation",L"MirrorPlayer1",0,config)==1?VO_MIRROR:VO_VERSUS):VO_SINGLE;
 saved.mode=text[0]?(int)GetPrivateProfileIntW(L"Presentation",L"Mode",0,config):legacy;
 char initial[2]={0};int default_aspect=GetEnvironmentVariableA("VO_EX_DEFAULT_ASPECT",initial,2)==1&&initial[0]=='0'?VO_ORIGINAL:VO_WIDE;
 saved.aspect=GetPrivateProfileIntW(L"Presentation",L"GameAspect",default_aspect,config);
 pending=saved;
}
/* Local path-bearing evidence is deliberately excluded from diagnostic exports. */
static void save_trace(unsigned stage,int result,DWORD error){
 save_stage=stage;save_error=error;
 if(vo_diagnostic_level()<3){SetLastError(error);return;}
 WCHAR path[MAX_PATH],dir[MAX_PATH];char location[MAX_PATH*4];
 DWORD length=GetModuleFileNameW(NULL,path,MAX_PATH);if(!length||length>=MAX_PATH)goto done;
 WCHAR *slash=wcsrchr(path,L'\\');if(!slash)goto done;slash[1]=0;
 if(wcslen(path)+40>=MAX_PATH)goto done;
 wcscat(path,L"diagnostics");CreateDirectoryW(path,NULL);wcscat(path,L"\\display-save.log");
 wcscpy(dir,config);slash=wcsrchr(dir,L'\\');if(slash)*slash=0;
 DWORD file_attrs=GetFileAttributesW(config),dir_attrs=GetFileAttributesW(dir);
 if(!WideCharToMultiByte(CP_UTF8,0,config,-1,location,sizeof location,NULL,NULL))goto done;
 HANDLE h=CreateFileW(path,FILE_APPEND_DATA|GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
 if(h==INVALID_HANDLE_VALUE)goto done;
 LARGE_INTEGER size;if(GetFileSizeEx(h,&size)&&size.QuadPart<256*1024){
  char line[2048];int n=snprintf(line,sizeof line,"mode=%d validation=%d stage=%u result=%d winerror=%lu file_attributes=%lu directory_attributes=%lu config=%s\n",pending.mode,vo_settings_validate(monitors,count,&pending,dirty),stage,result,(unsigned long)error,(unsigned long)file_attrs,(unsigned long)dir_attrs,location);
  DWORD written;if(n>0&&n<(int)sizeof line&&size.QuadPart+n<=256*1024)WriteFile(h,line,(DWORD)n,&written,NULL);
 }CloseHandle(h);
 done:SetLastError(error);
}
static int save_step(unsigned stage,int ok){DWORD error=ok?ERROR_SUCCESS:GetLastError();save_trace(stage,ok,error);return ok;}
/* Replace a same-directory copy only after every write succeeds. Unknown keys
 * and the prior file survive failure. No second configuration authority. */
static int save_pending(void){
 WCHAR dir[MAX_PATH],temp[MAX_PATH],number[24],id[VO_ID_CHARS];
 save_trace(0,1,ERROR_SUCCESS);
 wcscpy(dir,config);WCHAR *slash=wcsrchr(dir,L'\\');if(!slash){SetLastError(ERROR_PATH_NOT_FOUND);return save_step(1,0);}slash[1]=0;
 if(!save_step(2,GetTempFileNameW(dir,L"vds",0,temp)!=0))return 0;
 DWORD attrs=GetFileAttributesW(config);int ok=1;
 if(attrs!=INVALID_FILE_ATTRIBUTES)ok=save_step(3,CopyFileW(config,temp,FALSE)!=0);
 else if(GetLastError()!=ERROR_FILE_NOT_FOUND)ok=save_step(3,0);
 if(ok){swprintf(number,24,L"%d",pending.mode);ok=save_step(4,WritePrivateProfileStringW(L"Presentation",L"Mode",number,temp)!=0);}
 if(ok){swprintf(number,24,L"%d",pending.aspect);ok=save_step(5,WritePrivateProfileStringW(L"Presentation",L"GameAspect",number,temp)!=0);}
 if(ok){ok=save_step(6,MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,pending.primary,-1,id,VO_ID_CHARS)>0);if(ok)ok=save_step(6,WritePrivateProfileStringW(L"Players",L"Player1",id,temp)!=0);}
 if(ok){ok=save_step(7,MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,pending.secondary,-1,id,VO_ID_CHARS)>0);if(ok)ok=save_step(7,WritePrivateProfileStringW(L"Players",L"Player2",id,temp)!=0);}
 if(ok){
  /* Cache invalidation can return zero on success; it is NOT a write BOOL.
   * Check an actual file handle/FlushFileBuffers before the atomic commit. */
  int raw=WritePrivateProfileStringW(NULL,NULL,NULL,temp);save_trace(8,raw,ERROR_SUCCESS);
  HANDLE file=CreateFileW(temp,GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
  ok=save_step(9,file!=INVALID_HANDLE_VALUE);
  if(ok){ok=save_step(10,FlushFileBuffers(file)!=0);int closed=CloseHandle(file)!=0;if(ok)ok=save_step(11,closed);}
 }
 if(ok)ok=save_step(12,MoveFileExW(temp,config,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0);
 if(!ok){SetFileAttributesW(temp,FILE_ATTRIBUTE_NORMAL);DeleteFileW(temp);}
 WritePrivateProfileStringW(NULL,NULL,NULL,config);
 return ok;
}
static HWND control(HWND owner,LPCWSTR cls,LPCWSTR text,DWORD style,int id,int x,int y,int w,int h){
 RECT r={x,y,x+w,y+h};MapDialogRect(owner,&r);
 HWND c=CreateWindowW(cls,text,WS_CHILD|WS_VISIBLE|style,r.left,r.top,r.right-r.left,r.bottom-r.top,owner,(HMENU)(INT_PTR)id,NULL,NULL);
 if(c)SendMessageW(c,WM_SETFONT,(WPARAM)font,TRUE);return c;
}
static void add(HWND owner,int id,LPCWSTR value){SendDlgItemMessageW(owner,id,CB_ADDSTRING,0,(LPARAM)value);}
static void state(HWND h){
 int shown=(int)SendDlgItemMessageW(h,MODE,CB_GETCURSEL,0,0);
 int single=shown==VO_SINGLE;
 ShowWindow(GetDlgItem(h,SECONDARY),single?SW_HIDE:SW_SHOW);ShowWindow(secondary_label,single?SW_HIDE:SW_SHOW);
 EnableWindow(GetDlgItem(h,SECONDARY),!single);EnableWindow(GetDlgItem(h,ASPECT),shown!=VO_VERSUS);
 SetDlgItemTextW(h,105,shown==VO_VERSUS?L"Versus uses the two-player layout. Restart required for display changes.":L"Restart required for display changes.");
}
static void select_monitor(HWND h,int id,const char *identity){
 int found=vo_find(monitors,count,identity);
 for(unsigned i=0;i<count;i++)add(h,id,names[i]);
 if(found<0){add(h,id,identity[0]?L"Saved display unavailable (preference retained)":L"Automatic (current primary display)");found=(int)count;}
 SendDlgItemMessageW(h,id,CB_SETCURSEL,found,0);
}
static INT_PTR CALLBACK procedure(HWND h,UINT msg,WPARAM wp,LPARAM lp){
 (void)lp;
 if(msg==WM_INITDIALOG){
  font=(HFONT)GetStockObject(DEFAULT_GUI_FONT);
  const WCHAR *labels[]={L"Display Mode",L"Primary Display",L"Secondary Display",L"Game Aspect Ratio"};
  for(int i=0;i<4;i++){
   HWND label=control(h,L"STATIC",labels[i],0,200+i,10,10+i*35,240,10);if(i==2)secondary_label=label;
   if(!label||!control(h,L"COMBOBOX",L"",WS_TABSTOP|WS_VSCROLL|CBS_DROPDOWNLIST,MODE+i,10,21+i*35,250,110)){EndDialog(h,-1);return TRUE;}
  }
  add(h,MODE,L"Single Display");if(count>1){add(h,MODE,L"Dual Display — Versus");add(h,MODE,L"Dual Display — Mirror");}
  SendDlgItemMessageW(h,MODE,CB_SETCURSEL,count>1&&pending.mode>=0&&pending.mode<=2?pending.mode:0,0);
  select_monitor(h,PRIMARY,pending.primary);select_monitor(h,SECONDARY,pending.secondary);
  const WCHAR *aspects[]={L"4:3",L"16:9",L"21:9",L"32:9"};for(int i=0;i<4;i++)add(h,ASPECT,aspects[i]);
  SendDlgItemMessageW(h,ASPECT,CB_SETCURSEL,pending.aspect>=0&&pending.aspect<=3?pending.aspect:1,0);
  control(h,L"STATIC",L"Restart required for display changes.",0,105,10,153,250,24);
  control(h,L"STATIC",count<2&&saved.mode!=VO_SINGLE?L"One display is available. Saved dual preference is retained until changed.":L"Settings apply on next launch; the running game is unchanged.",0,106,10,179,250,24);
  control(h,L"BUTTON",L"OK",WS_TABSTOP|BS_DEFPUSHBUTTON,IDOK,145,210,50,14);
  control(h,L"BUTTON",L"Cancel",WS_TABSTOP,IDCANCEL,205,210,50,14);
  state(h);event(1,0);return TRUE;
 }
 if(msg==WM_CLOSE||(msg==WM_COMMAND&&LOWORD(wp)==IDCANCEL)){event(5,0);EndDialog(h,0);return TRUE;}
 if(msg==WM_DISPLAYCHANGE){event(3,1);MessageBoxW(h,L"Displays changed. Reopen Display Settings; no changes were saved.",L"Display Settings",MB_OK|MB_ICONINFORMATION);EndDialog(h,0);return TRUE;}
 if(msg!=WM_COMMAND)return FALSE;
 int id=LOWORD(wp);
 if(HIWORD(wp)==CBN_SELCHANGE&&id>=MODE&&id<=ASPECT){
  int choice=(int)SendDlgItemMessageW(h,id,CB_GETCURSEL,0,0);
  if(id==MODE){pending.mode=choice;dirty|=VO_EDIT_MODE;}
  else if(id==ASPECT){pending.aspect=choice;dirty|=VO_EDIT_ASPECT;}
  else if(choice>=0&&choice<(int)count){strcpy(id==PRIMARY?pending.primary:pending.secondary,monitors[choice].id);dirty|=id==PRIMARY?VO_EDIT_PRIMARY:VO_EDIT_SECONDARY;}
  state(h);event(2,0);return TRUE;
 }
 if(id==IDOK){
  if(!dirty){EndDialog(h,0);return TRUE;}
  if(!discover()){event(3,2);MessageBoxW(h,L"Displays could not be checked. No changes were saved.",L"Display Settings",MB_OK|MB_ICONERROR);return TRUE;}
  if(!pending.primary[0])for(unsigned i=0;i<count;i++)if(monitors[i].primary){strcpy(pending.primary,monitors[i].id);break;}
  int error=vo_settings_validate(monitors,count,&pending,dirty);
  save_trace(0,error==VO_SETTINGS_OK,ERROR_SUCCESS);
  if(error){
   const WCHAR *messages[]={L"",L"Choose a supported display mode.",L"Choose a supported game aspect ratio.",L"Choose an available primary display.",L"Choose an available secondary display for dual mode.",L"Choose different, independently arranged displays for dual mode."};
   event(3,error);MessageBoxW(h,messages[error],L"Display Settings — not saved",MB_OK|MB_ICONWARNING);return TRUE;
  }
  if(!save_pending()){event(3,3);WCHAR message[256];swprintf(message,256,L"Display settings could not be saved (step %u, Windows error %lu). Your previous settings are unchanged. Enable diagnostics in F11 for additional details.",save_stage,(unsigned long)save_error);MessageBoxW(h,message,L"Display Settings",MB_OK|MB_ICONERROR);return TRUE;}
  event(4,1);MessageBoxW(h,L"Display settings saved. Restart required for display changes.",L"Display Settings",MB_OK|MB_ICONINFORMATION);EndDialog(h,1);return TRUE;
 }
 return FALSE;
}
__declspec(dllexport) int WINAPI VonDisplaySettings(HWND owner){
 if(busy)return 0;busy=1;
 if(!path_config()||!discover()){MessageBoxW(owner,L"Display information could not be read. No settings were changed.",L"Display Settings",MB_OK|MB_ICONERROR);busy=0;return 0;}
 read_saved();dirty=0;
 /* Native modal child, same implementation family as upstream and CE dialogs. */
 WORD words[64]={0};DLGTEMPLATE *t=(DLGTEMPLATE*)words;t->style=WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME|DS_CENTER;t->cx=270;t->cy=235;
 WCHAR *title=(WCHAR*)(words+sizeof(DLGTEMPLATE)/2+2);wcscpy(title,L"Display Settings");
 INT_PTR result=DialogBoxIndirectParamW(GetModuleHandleW(NULL),t,owner,procedure,0);busy=0;return result>0?(int)result:0;
}
__declspec(dllexport) INT_PTR WINAPI VonDisplayF5(HWND h,UINT msg,WPARAM wp,LPARAM lp,DLGPROC original){
 if(msg==WM_COMMAND&&LOWORD(wp)==DISPLAY_BUTTON){VonDisplaySettings(h);return TRUE;}
 INT_PTR result=original(h,msg,wp,lp);
 if(msg==WM_INITDIALOG){
  font=(HFONT)SendMessageW(h,WM_GETFONT,0,0);
  control(h,L"BUTTON",L"Display...",WS_TABSTOP,DISPLAY_BUTTON,15,115,44,14);
 }
 return result;
}
/* Uses effective launch state, never the pending/saved next-launch mode. */
__declspec(dllexport) int WINAPI VonDisplayCanResize(HWND owner){
 char dual[2]={0};
 if(GetEnvironmentVariableA("VO_DUAL_DISPLAY",dual,sizeof dual)!=1||dual[0]!='1')return 1;
 event(6,0);
 MessageBoxW(owner,L"Resolution switching is not yet supported in dual-display mode. The current presentation has been retained.",L"Display Settings",MB_OK|MB_ICONINFORMATION);
 return 0;
}

#include "startup_runtime.h"

#include "f11_diagnostics.h"
