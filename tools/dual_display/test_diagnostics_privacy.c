#include <assert.h>
#include <wchar.h>
#include <string.h>
#include <stdio.h>
typedef wchar_t WCHAR;typedef unsigned DWORD;
#define MAX_PATH 260
static const WCHAR *setting=L"";
static DWORD GetModuleFileNameW(void *m,WCHAR *out,DWORD n){(void)m;(void)n;wcscpy(out,L"C:\\My Game\\v_on.exe");return wcslen(out);}
static DWORD GetPrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *fallback,WCHAR *out,DWORD n,const WCHAR *path){
 assert(!wcscmp(section,L"Diagnostics")&&!wcscmp(key,L"Level"));
 assert(!wcscmp(path,L"C:\\My Game\\player-displays.ini"));
 wcsncpy(out,setting[0]?setting:fallback,n-1);out[n-1]=0;return wcslen(out);
}
#include "diagnostics_privacy.h"
int main(void){
 const WCHAR *names[]={L"",L"OFF",L"NORMAL",L"DETAILED",L"DEVELOPMENT",L"invalid",L"4",L"normal"};
 unsigned levels[]={0,0,1,2,3,0,0,0};
 for(unsigned i=0;i<8;i++){setting=names[i];assert(vo_diagnostic_level()==levels[i]);}
 puts("PASS production native privacy gate: missing, Off, all levels, invalid and spaced path");return 0;
}
