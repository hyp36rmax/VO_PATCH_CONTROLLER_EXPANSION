#define OVERLAY_BUTTON 0x5e12
#define DIAGNOSTICS_LEVEL 0x5e10
#define DIAGNOSTICS_EXPORT 0x5e11
static int vo_export_diagnostics(HWND owner){
 WCHAR root[MAX_PATH],exe[MAX_PATH],command[2048];
 DWORD n=GetModuleFileNameW(NULL,root,MAX_PATH);if(!n||n>=MAX_PATH)return 0;
 WCHAR *slash=wcsrchr(root,L'\\');if(!slash)return 0;*slash=0;
 if(wcslen(root)+45>=MAX_PATH)return 0;
 swprintf(exe,MAX_PATH,L"%ls\\experience-runtime\\pythonw.exe",root);
 swprintf(command,2048,L"\"%ls\" -B \"%ls\\experience-runtime\\normal_lifecycle.py\" \"%ls\" --export",exe,root,root);
 STARTUPINFOW si={0};PROCESS_INFORMATION pi={0};si.cb=sizeof si;
 if(!CreateProcessW(exe,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,root,&si,&pi)){
  MessageBoxW(owner,L"Diagnostics export could not start. Existing logs are preserved.",L"Diagnostics",MB_OK|MB_ICONERROR);return 0;
 }
 CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 1;
}
/* Both configuration interfaces share this immediate-consent transaction. */
static int vo_save_diagnostics_level(int level){
 const WCHAR *names[]={L"OFF",L"NORMAL",L"DETAILED",L"DEVELOPMENT"};
 if(level<0||level>3||!path_config()||!WritePrivateProfileStringW(L"Diagnostics",L"Level",names[level],config))return 0;
 WritePrivateProfileStringW(NULL,NULL,NULL,config);
 InterlockedExchange(&diagnostic_level,level);return 1;
}
__declspec(dllexport) int WINAPI VonOverlayDiagnostics(HWND owner,unsigned command,int value){
 if(command==0)return (int)vo_diagnostic_level();
 if(command==1)return vo_save_diagnostics_level(value);
 if(command==2)return vo_export_diagnostics(owner);
 return 0;
}
__declspec(dllexport) INT_PTR WINAPI VonDiagnosticsF11(HWND h,UINT msg,WPARAM wp,LPARAM lp,DLGPROC original){
 if(msg==WM_COMMAND&&LOWORD(wp)==OVERLAY_BUTTON){
  HWND game=GetParent(h);original(h,WM_COMMAND,IDCANCEL,0);PostMessageW(game,WM_APP+0x350,0,0);return TRUE;
 }
 if(msg==WM_COMMAND&&LOWORD(wp)==DIAGNOSTICS_EXPORT){vo_export_diagnostics(h);return TRUE;}
 if(msg==WM_COMMAND&&LOWORD(wp)==DIAGNOSTICS_LEVEL){
  if(HIWORD(wp)!=CBN_SELCHANGE)return TRUE;
  int level=(int)SendDlgItemMessageW(h,DIAGNOSTICS_LEVEL,CB_GETCURSEL,0,0);
  unsigned prior=vo_diagnostic_level();
  if(!vo_save_diagnostics_level(level)){
   SendDlgItemMessageW(h,DIAGNOSTICS_LEVEL,CB_SETCURSEL,prior,0);
   MessageBoxW(h,L"Diagnostic preference could not be saved. The previous selection remains active.",L"Diagnostics",MB_OK|MB_ICONERROR);
  }else{
   MessageBoxW(h,level==0?L"Diagnostics are Off. Existing logs are retained.":L"Diagnostic level saved. Restart Virtual-On to start a new diagnostic session. No information is uploaded.",L"Diagnostics",MB_OK|MB_ICONINFORMATION);
  }
  return TRUE;
 }
 INT_PTR result=original(h,msg,wp,lp);
 if(msg==WM_INITDIALOG){
  RECT client,window,unit={0,0,4,8};GetClientRect(h,&client);GetWindowRect(h,&window);MapDialogRect(h,&unit);
  int y=client.bottom*8/unit.bottom;
  font=(HFONT)SendMessageW(h,WM_GETFONT,0,0);
  SetWindowPos(h,NULL,0,0,window.right-window.left,window.bottom-window.top+unit.bottom*10,SWP_NOMOVE|SWP_NOZORDER);
  control(h,L"STATIC",L"Diagnostics (saved immediately)",0,0,8,y+2,170,10);
  control(h,L"COMBOBOX",L"",WS_TABSTOP|WS_VSCROLL|CBS_DROPDOWNLIST,DIAGNOSTICS_LEVEL,8,y+14,80,70);
  for(unsigned i=0;i<4;i++)add(h,DIAGNOSTICS_LEVEL,(const WCHAR*[]){L"Off",L"Normal",L"Detailed",L"Development"}[i]);
  SendDlgItemMessageW(h,DIAGNOSTICS_LEVEL,CB_SETCURSEL,vo_diagnostic_level(),0);
  control(h,L"BUTTON",L"Export Diagnostics...",WS_TABSTOP,DIAGNOSTICS_EXPORT,94,y+14,84,14);
  control(h,L"BUTTON",L"Unified Overlay...",WS_TABSTOP,OVERLAY_BUTTON,8,y+56,170,14);
  control(h,L"STATIC",L"Enable: restart game. Off stops collection. Local only.",0,0,8,y+32,178,18);
 }
 return result;
}
