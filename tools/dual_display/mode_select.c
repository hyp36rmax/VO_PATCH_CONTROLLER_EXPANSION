#ifndef UNICODE
#define UNICODE
#define _UNICODE
#endif
#include "inventory.h"
#include "mode_config.h"
static HWND modebox,aspectbox,displaybox[2];static VoPreference pref;static VoSelection selected;static unsigned changed;static int accepted;
static unsigned available;
static void read_preferences(void){
 load_id(L"Player1",pref.primary);load_id(L"Player2",pref.secondary);
 WCHAR stored[32];GetPrivateProfileStringW(L"Presentation",L"Mode",L"",stored,32,config);
 /* Legacy explicit assignments are an existing dual preference, not discovery. */
 int legacy=pref.primary[0]&&pref.secondary[0] ? (GetPrivateProfileIntW(L"Presentation",L"MirrorPlayer1",0,config)==1?VO_MIRROR:VO_VERSUS):VO_SINGLE;
 pref.mode=stored[0]?(int)GetPrivateProfileIntW(L"Presentation",L"Mode",0,config):legacy;
 pref.aspect=GetPrivateProfileIntW(L"Presentation",L"GameAspect",VO_WIDE,config);
}
static HWND combo(HWND h,int id,int y,const WCHAR *label){
 CreateWindowW(L"STATIC",label,WS_CHILD|WS_VISIBLE,15,y,560,20,h,NULL,NULL,NULL);
 return CreateWindowW(L"COMBOBOX",L"",WS_CHILD|WS_VISIBLE|WS_VSCROLL|CBS_DROPDOWNLIST,15,y+22,560,200,h,(HMENU)(INT_PTR)id,NULL,NULL);
}
static int save_int(const WCHAR *key,int v){WCHAR b[24];swprintf(b,24,L"%d",v);return WritePrivateProfileStringW(L"Presentation",key,b,config);}
static LRESULT CALLBACK proc(HWND h,UINT msg,WPARAM w,LPARAM l){
 if(msg==WM_CREATE){
  modebox=combo(h,10,10,L"Display Mode");
  SendMessageW(modebox,CB_ADDSTRING,0,(LPARAM)L"Single Display");
  if(count>1){SendMessageW(modebox,CB_ADDSTRING,0,(LPARAM)L"Dual Display — Versus");SendMessageW(modebox,CB_ADDSTRING,0,(LPARAM)L"Dual Display — Mirror");}
  SendMessageW(modebox,CB_SETCURSEL,selected.mode,0);
  for(int k=0;k<2;k++){
   displaybox[k]=combo(h,12+k,70+k*60,k?L"Secondary Display":L"Primary Display");
   for(unsigned i=0;i<count;i++)SendMessageW(displaybox[k],CB_ADDSTRING,0,(LPARAM)names[i]);
   int index=k?vo_find(monitors,count,pref.secondary):selected.primary;
   if(k&&index<0)for(unsigned i=0;i<count;i++)if((int)i!=selected.primary){index=(int)i;break;}
   SendMessageW(displaybox[k],CB_SETCURSEL,index,0);EnableWindow(displaybox[k],count>1);
  }
  aspectbox=combo(h,11,190,L"Single Display — Game Aspect Ratio");
  const WCHAR *labels[]={L"Original (4:3) — original rendering",L"Widescreen (16:9)",L"Ultrawide (21:9) — single-player",L"Super-ultrawide (32:9) — single-player"};
  for(int i=0;i<4;i++)SendMessageW(aspectbox,CB_ADDSTRING,0,(LPARAM)labels[i]);
  SendMessageW(aspectbox,CB_SETCURSEL,pref.aspect>=0&&pref.aspect<4?pref.aspect:VO_WIDE,0);
  CreateWindowW(L"STATIC",selected.reasons?L"Temporary fallback active. Saved preferences are retained unless changed.":L"Changes apply to this launch. For ordinary Local VS, use Original or Widescreen.",WS_CHILD|WS_VISIBLE,15,255,560,45,h,NULL,NULL,NULL);
  CreateWindowW(L"BUTTON",L"Launch",WS_CHILD|WS_VISIBLE|BS_DEFPUSHBUTTON,15,310,150,30,h,(HMENU)1,NULL,NULL);
  return 0;
 }
 if(msg==WM_COMMAND&&HIWORD(w)==CBN_SELCHANGE){changed|=1u<<(LOWORD(w)-10);return 0;}
 if(msg==WM_COMMAND&&LOWORD(w)==1){
  VoPreference next=pref;
  if(changed&1)next.mode=(int)SendMessageW(modebox,CB_GETCURSEL,0,0);
  if(changed&2)next.aspect=(int)SendMessageW(aspectbox,CB_GETCURSEL,0,0);
  for(int k=0;k<2;k++)if((changed&(4u<<k))||!(k?pref.secondary:pref.primary)[0]){
   int index=(int)SendMessageW(displaybox[k],CB_GETCURSEL,0,0);
   if(index>=0&&index<(int)count)strcpy(k?next.secondary:next.primary,monitors[index].id);
  }
  if(!vo_select(monitors,count,&next,available,&selected)){MessageBoxW(h,L"No compatible display/profile is available.",L"Display setup",MB_OK|MB_ICONERROR);return 0;}
  WCHAR ids[2][VO_ID_CHARS];MultiByteToWideChar(CP_UTF8,0,next.primary,-1,ids[0],VO_ID_CHARS);MultiByteToWideChar(CP_UTF8,0,next.secondary,-1,ids[1],VO_ID_CHARS);
  if(!save_int(L"Mode",next.mode)||!save_int(L"GameAspect",next.aspect)||!WritePrivateProfileStringW(L"Players",L"Player1",ids[0],config)||!WritePrivateProfileStringW(L"Players",L"Player2",ids[1],config)){MessageBoxW(h,L"Settings could not be saved.",L"Display setup",MB_OK|MB_ICONERROR);return 0;}
  pref=next;accepted=1;DestroyWindow(h);return 0;
 }
 if(msg==WM_DISPLAYCHANGE){MessageBoxW(h,L"Displays changed. Reopen setup before launching.",L"Display setup",MB_OK);DestroyWindow(h);return 0;}
 if(msg==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProcW(h,msg,w,l);
}
int wmain(int argc,WCHAR **argv){
 SetProcessDPIAware();DWORD n=GetModuleFileNameW(NULL,config,MAX_PATH);if(!n||n>=MAX_PATH)return 1;
 WCHAR *slash=wcsrchr(config,L'\\');if(!slash||slash-config+22>=MAX_PATH)return 1;wcscpy(slash+1,L"player-displays.ini");
 const WCHAR *profiles[]={L"original",L"wide",L"ultrawide",L"superwide",L"dual"};
 WCHAR path[MAX_PATH],base[MAX_PATH];wcscpy(base,config);WCHAR *end=wcsrchr(base,L'\\');if(!end)return 1;*end=0;
 for(int i=0;i<5;i++){if(swprintf(path,MAX_PATH,L"%ls\\..\\profiles\\%ls.exe",base,profiles[i])<0)return 1;DWORD attr=GetFileAttributesW(path);if(attr!=INVALID_FILE_ATTRIBUTES&&!(attr&FILE_ATTRIBUTE_DIRECTORY))available|=1u<<i;}
 if(!discover())return 1;read_preferences();
 if(!vo_select(monitors,count,&pref,available,&selected))return 1;
 if(argc>1&&!wcscmp(argv[1],L"--resolve"))accepted=1;
 else{
  WNDCLASSW wc={0};wc.lpfnWndProc=proc;wc.hInstance=GetModuleHandleW(NULL);wc.lpszClassName=L"VoDisplayModes";wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
  if(!RegisterClassW(&wc))return 1;
  if(!CreateWindowW(wc.lpszClassName,L"Virtual-On Display Settings",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_VISIBLE,CW_USEDEFAULT,CW_USEDEFAULT,610,395,NULL,NULL,wc.hInstance,NULL))return 1;
  MSG m;while(GetMessageW(&m,NULL,0,0)>0){TranslateMessage(&m);DispatchMessageW(&m);}
 }
 if(!accepted)return 2;
 VoRect d=monitors[selected.primary].desktop;
 printf("SELECT mode=%d profile=%d desktop=%d,%d,%d,%d fallback=%u requested_mode=%d requested_aspect=%d\n",selected.mode,selected.profile,d.x,d.y,d.w,d.h,selected.reasons,pref.mode,pref.aspect);
 return 0;
}
