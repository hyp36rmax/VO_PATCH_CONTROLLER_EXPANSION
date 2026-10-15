/* The existing player-displays.ini is the sole runtime preference authority. */
static unsigned vo_diagnostic_level(void){
 WCHAR path[MAX_PATH],value[32];DWORD n=GetModuleFileNameW(NULL,path,MAX_PATH);
 if(!n||n>=MAX_PATH)return 0;
 WCHAR *slash=wcsrchr(path,L'\\');if(!slash||slash-path+22>=MAX_PATH)return 0;
 wcscpy(slash+1,L"player-displays.ini");
 GetPrivateProfileStringW(L"Diagnostics",L"Level",L"OFF",value,32,path);
 if(!wcscmp(value,L"NORMAL"))return 1;
 if(!wcscmp(value,L"DETAILED"))return 2;
 if(!wcscmp(value,L"DEVELOPMENT"))return 3;
 return 0;
}
