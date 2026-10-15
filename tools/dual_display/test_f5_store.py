"""Exercise the production transaction with documented Win32 flush semantics.
API doubles cover ordinary writable and denied paths; physical Windows remains UAT.
"""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'f5_dialog.c').read_text()
def body(text):return text[text.index('static int save_pending(void)'):text.index('static HWND control(')]
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include "f5_settings.h"
typedef wchar_t WCHAR;typedef unsigned DWORD;typedef int HANDLE;
#define MAX_PATH 260
#define FALSE 0
#define INVALID_FILE_ATTRIBUTES (~0u)
#define ERROR_SUCCESS 0
#define ERROR_FILE_NOT_FOUND 2
#define ERROR_PATH_NOT_FOUND 3
#define CP_UTF8 65001
#define MB_ERR_INVALID_CHARS 8
#define FILE_ATTRIBUTE_NORMAL 128
#define MOVEFILE_REPLACE_EXISTING 1
#define MOVEFILE_WRITE_THROUGH 8
#define GENERIC_READ 1
#define GENERIC_WRITE 2
#define FILE_SHARE_READ 1
#define OPEN_EXISTING 3
#define INVALID_HANDLE_VALUE (-1)
static WCHAR config[MAX_PATH];
static VoPreference pending={VO_MIRROR,VO_SUPER,"monitor-a","monitor-b"};
static VoPreference committed;
static unsigned original,temporary,last_error,last_stage,last_failure;
static int step,fail,exists,deleted,moved,dir_missing,dir_denied,readonly,flush_zero;
static void SetLastError(DWORD n){last_error=n;}
static DWORD GetLastError(void){return last_error;}
static int allow(void){if(++step==fail){last_error=29;return 0;}return 1;}
static void save_trace(unsigned stage,int result,DWORD error){last_stage=stage;if(!result&&stage!=8)last_failure=stage;last_error=error;}
static int save_step(unsigned stage,int ok){save_trace(stage,ok,ok?0:GetLastError());return ok;}
static int GetTempFileNameW(const WCHAR *dir,const WCHAR *prefix,unsigned n,WCHAR *out){
 (void)prefix;(void)n;assert(!wcsncmp(dir,config,wcslen(dir)));assert(dir[wcslen(dir)-1]==L'\\');
 if(dir_missing||dir_denied){last_error=dir_missing?3:5;return 0;}
 if(!allow())return 0;wcscpy(out,L"temp");temporary=0;return 1;
}
static DWORD GetFileAttributesW(const WCHAR *path){assert(!wcscmp(path,config));last_error=exists?0:2;return exists?(readonly?1:0):INVALID_FILE_ATTRIBUTES;}
static int CopyFileW(const WCHAR *a,const WCHAR *b,int flag){assert(!wcscmp(a,config)&&!wcscmp(b,L"temp")&&!flag);if(!allow())return 0;temporary=original;return 1;}
static int WritePrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *value,const WCHAR *path){
 if(!section&&!key&&!value){flush_zero++;return 0;} /* documented successful cache flush */
 assert(!wcscmp(path,L"temp"));if(readonly){last_error=5;return 0;}if(!allow())return 0;
 if(!wcscmp(key,L"Mode")){assert(wcstol(value,NULL,10)==pending.mode);temporary|=1;}
 else if(!wcscmp(key,L"GameAspect")){assert(wcstol(value,NULL,10)==pending.aspect);temporary|=2;}
 else if(!wcscmp(key,L"Player1")){assert(!wcscmp(value,L"monitor-a"));temporary|=4;}
 else if(!wcscmp(key,L"Player2")){assert(!wcscmp(value,L"monitor-b"));temporary|=8;}
 else assert(0);return 1;
}
static int MultiByteToWideChar(unsigned cp,unsigned flags,const char *in,int len,WCHAR *out,int size){(void)cp;(void)flags;(void)len;if(!allow())return 0;return (int)mbstowcs(out,in,size)+1;}
static HANDLE CreateFileW(const WCHAR *p,unsigned access,unsigned share,void *security,unsigned create,unsigned attr,void *template){
 assert(!wcscmp(p,L"temp")&&access==3&&share==1&&!security&&create==3&&attr==128&&!template);return allow()?1:-1;
}
static int FlushFileBuffers(HANDLE h){assert(h==1);return allow();}
static int CloseHandle(HANDLE h){assert(h==1);return allow();}
static int MoveFileExW(const WCHAR *a,const WCHAR *b,unsigned flags){assert(!wcscmp(a,L"temp")&&!wcscmp(b,config)&&flags==9);if(!allow())return 0;original=temporary;committed=pending;moved=1;return 1;}
static int DeleteFileW(const WCHAR *path){assert(!wcscmp(path,L"temp"));deleted=1;return 1;}
static int SetFileAttributesW(const WCHAR *path,unsigned flags){(void)path;(void)flags;return 1;}
static void reset(void){original=64;temporary=0;step=fail=deleted=moved=flush_zero=dir_missing=dir_denied=readonly=last_error=last_stage=last_failure=0;}
'''
reader=r'''
static VoPreference saved;
static void load_id(const WCHAR *key,char *out){strcpy(out,!wcscmp(key,L"Player1")?committed.primary:committed.secondary);}
static unsigned GetPrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *fallback,WCHAR *out,unsigned size,const WCHAR *path){(void)section;(void)fallback;(void)path;assert(!wcscmp(key,L"Mode"));swprintf(out,size,L"%d",committed.mode);return (unsigned)wcslen(out);}
static unsigned GetPrivateProfileIntW(const WCHAR *section,const WCHAR *key,int fallback,const WCHAR *path){(void)section;(void)fallback;(void)path;return !wcscmp(key,L"Mode")?(unsigned)committed.mode:(unsigned)committed.aspect;}
static unsigned GetEnvironmentVariableA(const char *key,char *value,unsigned size){(void)key;(void)value;(void)size;return 0;}
'''+source[source.index('static void read_saved(void)'):source.index('/* Local path-bearing')]
main=r'''
int main(void){
 const WCHAR *paths[]={L"C:\\game\\player-displays.ini",L"C:\\Games With Spaces\\Virtual On\\player-displays.ini",L"C:\\Games\\\u65e5\u672c\\player-displays.ini"};
 for(unsigned path=0;path<3;path++)for(int mode=0;mode<3;mode++)for(int aspect=0;aspect<4;aspect++)for(int present=0;present<2;present++){
  wcscpy(config,paths[path]);pending.mode=mode;pending.aspect=aspect;exists=present;reset();
  assert(save_pending()&&moved&&!deleted&&flush_zero==2);assert(original==(unsigned)(15+(present?64:0)));
  int steps=step;
  memset(&saved,0,sizeof saved);read_saved();assert(saved.mode==mode&&saved.aspect==aspect&&!strcmp(saved.primary,"monitor-a")&&!strcmp(saved.secondary,"monitor-b"));
  VoMonitor monitors[2]={0};strcpy(monitors[0].id,"monitor-a");strcpy(monitors[1].id,"monitor-b");
  monitors[0].available=monitors[1].available=1;monitors[0].primary=1;
  monitors[0].desktop=(VoRect){0,0,1920,1080};monitors[1].desktop=(VoRect){1920,0,1920,1080};
  VoSelection selection;assert(vo_select(monitors,2,&saved,31,&selection)&&selection.mode==mode&&selection.profile==(mode==VO_VERSUS?VO_DUAL_PROFILE:aspect));
  for(int failure=1;failure<=steps;failure++){
   reset();fail=failure;assert(!save_pending()&&!moved&&original==64);assert(last_failure&&last_error==29);
   assert(deleted==(failure!=1));
  }
 }
 for(int type=0;type<3;type++){
  reset();exists=1;dir_missing=type==0;dir_denied=type==1;readonly=type==2;
  assert(!save_pending()&&!moved&&original==64);assert(last_error==(type==0?3u:5u));
 }
 puts("PASS production save: Single/Versus/Mirror x four aspects x new/existing files x space/Unicode paths; successful zero-return flush; every operation failure; missing/denied directory, read-only file; original preservation, next-launch production reader/selection and cleanup");
}
'''
old=subprocess.check_output(['git','show','bf91aef44368fa3d7c36c9a8c51f9baaff9706dc:tools/dual_display/f5_dialog.c'],cwd=here,text=True)
reproduce=r'''int main(void){wcscpy(config,L"C:\\game\\player-displays.ini");exists=1;reset();assert(!save_pending()&&!moved&&deleted&&original==64&&flush_zero==2);puts("REPRODUCED original failure: successful zero-return INI cache flush prevents commit");}'''
with tempfile.TemporaryDirectory() as td:
 for name,text,entry in [('original',old,reproduce),('corrected',source,main)]:
  p=Path(td);(p/(name+'.c')).write_text(fixture+(reader if name=="corrected" else "")+body(text)+entry)
  subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-I',str(here),str(p/(name+'.c')),'-o',str(p/name)],check=True)
  subprocess.run([str(p/name)],check=True)
