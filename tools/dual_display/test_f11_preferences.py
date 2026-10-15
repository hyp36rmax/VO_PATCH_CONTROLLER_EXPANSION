"""Execute production F11 command handling with Win32 profile/control doubles."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
s=(here/'f11_diagnostics.h').read_text();start=s.index('__declspec(dllexport) INT_PTR WINAPI VonDiagnosticsF11');end=s.index(' INT_PTR result=original',start)
body=s[start:end]+' return original(h,msg,wp,lp);\n}\n'
fixture=r'''
#include <assert.h>
#include <wchar.h>
#include <stdio.h>
#define __declspec(x)
#define WINAPI
#define WM_COMMAND 273
#define CBN_SELCHANGE 1
#define CB_GETCURSEL 1
#define CB_SETCURSEL 2
#define MB_OK 0
#define MB_ICONERROR 1
#define MB_ICONINFORMATION 2
#define LOWORD(x) ((x)&65535)
#define HIWORD(x) (((x)>>16)&65535)
#define TRUE 1
#define NULLHWND 0
#define DIAGNOSTICS_LEVEL 0x5e10
#define DIAGNOSTICS_EXPORT 0x5e11
typedef wchar_t WCHAR;typedef int HWND;typedef unsigned UINT;typedef unsigned long WPARAM;typedef long LPARAM;typedef long INT_PTR;typedef INT_PTR (*DLGPROC)(HWND,UINT,WPARAM,LPARAM);
static WCHAR config[]=L"C:\\Games With Spaces\\player-displays.ini",stored[32];
static int selected,prior,denied,restored=-1,messages,exports,forwarded,diagnostic_level;
static unsigned vo_diagnostic_level(void){return prior;}
static int path_config(void){return 1;}
static int WritePrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *value,const WCHAR *path){assert(path==config);if(!section)return 0;assert(!wcscmp(section,L"Diagnostics")&&!wcscmp(key,L"Level"));if(denied)return 0;wcscpy(stored,value);return 1;}
static int SendDlgItemMessageW(HWND h,int id,int msg,int w,int l){(void)h;(void)id;(void)l;if(msg==CB_GETCURSEL)return selected;restored=w;return 0;}
static void MessageBoxW(HWND h,const WCHAR *text,const WCHAR *title,int flags){(void)h;(void)text;(void)title;(void)flags;messages++;}
static void InterlockedExchange(int *where,int value){*where=value;}
static int vo_export_diagnostics(HWND h){(void)h;exports++;return 1;}
static INT_PTR original(HWND h,UINT m,WPARAM w,LPARAM l){assert(h==7&&m==55&&w==8&&l==9);forwarded++;return 42;}
'''
main=r'''
int main(void){
 const WCHAR *names[]={L"OFF",L"NORMAL",L"DETAILED",L"DEVELOPMENT"};
 for(int level=0;level<4;level++){
  selected=level;prior=0;denied=0;messages=0;diagnostic_level=0;
  assert(VonDiagnosticsF11(7,WM_COMMAND,DIAGNOSTICS_LEVEL|(CBN_SELCHANGE<<16),0,original)==1);
  assert(!wcscmp(stored,names[level])&&diagnostic_level==level&&messages==1);
 }
 wcscpy(stored,L"DETAILED");prior=2;selected=0;denied=1;diagnostic_level=2;
 VonDiagnosticsF11(7,WM_COMMAND,DIAGNOSTICS_LEVEL|(CBN_SELCHANGE<<16),0,original);
 assert(!wcscmp(stored,L"DETAILED")&&diagnostic_level==2&&restored==2);
 assert(VonDiagnosticsF11(7,55,8,9,original)==42&&forwarded==1);
 VonDiagnosticsF11(7,WM_COMMAND,DIAGNOSTICS_EXPORT,0,original);assert(exports==1);
 puts("PASS production F11 choices, same INI authority, saved level/atomic consent, failed-write retention, upstream command forwarding and explicit export dispatch");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture+body+main)
 subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
