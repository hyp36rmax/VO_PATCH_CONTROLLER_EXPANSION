#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include "layout.h"
static VoMonitor monitors[VO_MAX_MONITORS];
static WCHAR names[VO_MAX_MONITORS][256],config[MAX_PATH];
static unsigned count;
static HWND boxes[2];
static int discover(void){
 DISPLAYCONFIG_PATH_INFO *paths=NULL;DISPLAYCONFIG_MODE_INFO *modes=NULL;UINT32 np=0,nm=0;LONG result=ERROR_INSUFFICIENT_BUFFER;
 for(unsigned attempt=0;attempt<3&&result==ERROR_INSUFFICIENT_BUFFER;attempt++){
  free(paths);free(modes);paths=NULL;modes=NULL;
  result=GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS,&np,&nm);if(result!=ERROR_SUCCESS)break;
  if(np>1024||nm>4096){result=ERROR_INVALID_DATA;break;}
  paths=calloc(np?np:1,sizeof *paths);modes=calloc(nm?nm:1,sizeof *modes);
  if(!paths||!modes){result=ERROR_NOT_ENOUGH_MEMORY;break;}
  result=QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS,&np,paths,&nm,modes,NULL);
 }
 if(result!=ERROR_SUCCESS){fprintf(stderr,"display_query_error=%ld\n",result);free(paths);free(modes);return 0;}
 count=0;
 for(UINT32 i=0;i<np;i++){
  DISPLAYCONFIG_SOURCE_DEVICE_NAME src={0};src.header.type=DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME;src.header.size=sizeof src;src.header.adapterId=paths[i].sourceInfo.adapterId;src.header.id=paths[i].sourceInfo.id;
  DISPLAYCONFIG_TARGET_DEVICE_NAME dst={0};dst.header.type=DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME;dst.header.size=sizeof dst;dst.header.adapterId=paths[i].targetInfo.adapterId;dst.header.id=paths[i].targetInfo.id;
  if(DisplayConfigGetDeviceInfo(&src.header)!=ERROR_SUCCESS||DisplayConfigGetDeviceInfo(&dst.header)!=ERROR_SUCCESS||!dst.monitorDevicePath[0]){result=ERROR_INVALID_DATA;break;}
  DEVMODEW dm={0};dm.dmSize=sizeof dm;if(!EnumDisplaySettingsExW(src.viewGdiDeviceName,ENUM_CURRENT_SETTINGS,&dm,0)){result=ERROR_INVALID_DATA;break;}
  if(count==VO_MAX_MONITORS){result=ERROR_INSUFFICIENT_BUFFER;break;}
  VoMonitor *m=&monitors[count];memset(m,0,sizeof *m);
  if(!WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,dst.monitorDevicePath,-1,m->id,sizeof m->id,NULL,NULL)){result=ERROR_INVALID_DATA;break;}
  m->desktop=(VoRect){dm.dmPosition.x,dm.dmPosition.y,(int32_t)dm.dmPelsWidth,(int32_t)dm.dmPelsHeight};
  RECT rect={dm.dmPosition.x,dm.dmPosition.y,dm.dmPosition.x+(LONG)dm.dmPelsWidth,dm.dmPosition.y+(LONG)dm.dmPelsHeight};
  MONITORINFO mi={0};mi.cbSize=sizeof mi;HMONITOR hm=MonitorFromRect(&rect,MONITOR_DEFAULTTONULL);
  if(hm&&GetMonitorInfoW(hm,&mi))m->primary=(mi.dwFlags&MONITORINFOF_PRIMARY)!=0;
  m->available=paths[i].targetInfo.targetAvailable!=0;
  swprintf(names[count],256,L"%ls — %lux%lu (%ld,%ld)%ls",dst.monitorFriendlyDeviceName,dm.dmPelsWidth,dm.dmPelsHeight,dm.dmPosition.x,dm.dmPosition.y,m->primary?L" primary":L"");
  printf("monitor=%u id=%s desktop=%ld,%ld,%ld,%ld primary=%u available=%u refresh=%u/%u rotation=%u\n",count,m->id,(long)m->desktop.x,(long)m->desktop.y,(long)m->desktop.w,(long)m->desktop.h,m->primary,m->available,paths[i].targetInfo.refreshRate.Numerator,paths[i].targetInfo.refreshRate.Denominator,paths[i].targetInfo.rotation);
  count++;
 }
 free(paths);free(modes);if(result!=ERROR_SUCCESS){count=0;fprintf(stderr,"display_inventory_incomplete=%ld; fallback required\n",result);return 0;}return 1;
}
static void load_id(const WCHAR *key,char *id){
 WCHAR text[VO_ID_CHARS]={0};DWORD n=GetPrivateProfileStringW(L"Players",key,L"",text,VO_ID_CHARS,config);
 if(n>=VO_ID_CHARS-1||!WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,text,-1,id,VO_ID_CHARS,NULL,NULL))strcpy(id,"invalid-saved-id");
}
static LRESULT CALLBACK proc(HWND h,UINT msg,WPARAM w,LPARAM l){
 if(msg==WM_CREATE){
  char a[VO_ID_CHARS],b[VO_ID_CHARS];VoOutput plan[2];load_id(L"Player1",a);load_id(L"Player2",b);
  VoResult result=vo_plan(monitors,count,a,b,plan);
  for(unsigned k=0;k<2;k++){
   CreateWindowW(L"STATIC",k?L"Player 2 Display":L"Player 1 Display",WS_CHILD|WS_VISIBLE,15,15+(int)k*65,180,20,h,NULL,NULL,NULL);
   boxes[k]=CreateWindowW(L"COMBOBOX",L"",WS_CHILD|WS_VISIBLE|WS_VSCROLL|CBS_DROPDOWNLIST,15,38+(int)k*65,550,180,h,NULL,NULL,NULL);
   for(unsigned i=0;i<count;i++)SendMessageW(boxes[k],CB_ADDSTRING,0,(LPARAM)names[i]);
   SendMessageW(boxes[k],CB_SETCURSEL,result==VO_DUAL_READY?plan[k].monitor:(WPARAM)-1,0);
  }
  CreateWindowW(L"STATIC",L"Assignment setup only. Dual-display presentation is not enabled.",WS_CHILD|WS_VISIBLE,15,150,550,35,h,NULL,NULL,NULL);
  CreateWindowW(L"BUTTON",L"Save assignments",WS_CHILD|WS_VISIBLE|BS_DEFPUSHBUTTON,15,195,170,30,h,(HMENU)1,NULL,NULL);
  return 0;
 }
 if(msg==WM_COMMAND&&LOWORD(w)==1){
  LRESULT a=SendMessageW(boxes[0],CB_GETCURSEL,0,0),b=SendMessageW(boxes[1],CB_GETCURSEL,0,0);
  VoOutput plan[2];if(a<0||b<0||a>=(LRESULT)count||b>=(LRESULT)count||vo_plan(monitors,count,monitors[a].id,monitors[b].id,plan)!=VO_DUAL_READY){MessageBoxW(h,L"Choose two available, separate displays.",L"Display assignment",MB_OK);return 0;}
  WCHAR ids[2][VO_ID_CHARS];MultiByteToWideChar(CP_UTF8,0,monitors[a].id,-1,ids[0],VO_ID_CHARS);MultiByteToWideChar(CP_UTF8,0,monitors[b].id,-1,ids[1],VO_ID_CHARS);
  if(!WritePrivateProfileStringW(L"Players",L"Player1",ids[0],config)||!WritePrivateProfileStringW(L"Players",L"Player2",ids[1],config)){MessageBoxW(h,L"Assignments could not be saved.",L"Display assignment",MB_OK|MB_ICONERROR);return 0;}
  DestroyWindow(h);return 0;
 }
 if(msg==WM_DISPLAYCHANGE){MessageBoxW(h,L"Displays changed. Close and reopen setup before saving.",L"Display assignment",MB_OK);DestroyWindow(h);return 0;}
 if(msg==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProcW(h,msg,w,l);
}
int wmain(int argc,WCHAR **argv){
 /* Physical coordinates rather than virtualized logical pixels. */
 SetProcessDPIAware();
 DWORD n=GetModuleFileNameW(NULL,config,MAX_PATH);if(!n||n>=MAX_PATH)return 1;
 WCHAR *slash=wcsrchr(config,L'\\');if(!slash||slash-config+22>=MAX_PATH)return 1;wcscpy(slash+1,L"player-displays.ini");
 if(!discover())return 1;
 char a[VO_ID_CHARS],b[VO_ID_CHARS];VoOutput plan[2];load_id(L"Player1",a);load_id(L"Player2",b);VoResult result=vo_plan(monitors,count,a,b,plan);
 printf("assignment_result=%d presentation_enabled=NO\n",result);
 if(argc>1&&!wcscmp(argv[1],L"--list"))return 0;
 WNDCLASSW wc={0};wc.lpfnWndProc=proc;wc.hInstance=GetModuleHandleW(NULL);wc.lpszClassName=L"VoPrivateDisplaySetup";wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
 if(!RegisterClassW(&wc))return 1;
 HWND h=CreateWindowW(wc.lpszClassName,L"Player Displays — Private Setup",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_VISIBLE,CW_USEDEFAULT,CW_USEDEFAULT,600,280,NULL,NULL,wc.hInstance,NULL);if(!h)return 1;
 MSG msg;int r;while((r=GetMessageW(&msg,NULL,0,0))>0){TranslateMessage(&msg);DispatchMessageW(&msg);}return r<0?1:0;
}
