#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include "inventory.h"
static HWND boxes[2];
static int saved;
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
  CreateWindowW(L"STATIC",L"Assignments apply on the next private dual-display launch.",WS_CHILD|WS_VISIBLE,15,150,550,35,h,NULL,NULL,NULL);
  CreateWindowW(L"BUTTON",L"Save assignments",WS_CHILD|WS_VISIBLE|BS_DEFPUSHBUTTON,15,195,170,30,h,(HMENU)1,NULL,NULL);
  return 0;
 }
 if(msg==WM_COMMAND&&LOWORD(w)==1){
  LRESULT a=SendMessageW(boxes[0],CB_GETCURSEL,0,0),b=SendMessageW(boxes[1],CB_GETCURSEL,0,0);
  VoOutput plan[2];if(a<0||b<0||a>=(LRESULT)count||b>=(LRESULT)count||vo_plan(monitors,count,monitors[a].id,monitors[b].id,plan)!=VO_DUAL_READY){MessageBoxW(h,L"Choose two available, separate displays.",L"Display assignment",MB_OK);return 0;}
  WCHAR ids[2][VO_ID_CHARS];MultiByteToWideChar(CP_UTF8,0,monitors[a].id,-1,ids[0],VO_ID_CHARS);MultiByteToWideChar(CP_UTF8,0,monitors[b].id,-1,ids[1],VO_ID_CHARS);
  if(!WritePrivateProfileStringW(L"Players",L"Player1",ids[0],config)||!WritePrivateProfileStringW(L"Players",L"Player2",ids[1],config)){MessageBoxW(h,L"Assignments could not be saved.",L"Display assignment",MB_OK|MB_ICONERROR);return 0;}
  saved=1;DestroyWindow(h);return 0;
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
 printf("assignment_result=%d presentation_status=SETUP_ONLY\n",result);
 if(argc>1&&!wcscmp(argv[1],L"--list"))return 0;
 WNDCLASSW wc={0};wc.lpfnWndProc=proc;wc.hInstance=GetModuleHandleW(NULL);wc.lpszClassName=L"VoPrivateDisplaySetup";wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);
 if(!RegisterClassW(&wc))return 1;
 HWND h=CreateWindowW(wc.lpszClassName,L"Player Displays — Private Setup",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_VISIBLE,CW_USEDEFAULT,CW_USEDEFAULT,600,280,NULL,NULL,wc.hInstance,NULL);if(!h)return 1;
 MSG msg;int r;while((r=GetMessageW(&msg,NULL,0,0))>0){TranslateMessage(&msg);DispatchMessageW(&msg);}return r<0?1:(saved?0:2);
}
