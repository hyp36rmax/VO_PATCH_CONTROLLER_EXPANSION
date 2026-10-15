"""Fault-inject the production save routine through Win32 API doubles.

Verifies transaction sequencing; real filesystem/INI-cache behavior needs Windows.
"""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
source=(here/'f5_dialog.c').read_text()
body=source[source.index('static int save_pending(void)'):source.index('static HWND control(')]
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
#include "f5_settings.h"
typedef wchar_t WCHAR;typedef unsigned DWORD;
#define MAX_PATH 260
#define FALSE 0
#define NULL ((void*)0)
#define INVALID_FILE_ATTRIBUTES (~0u)
#define ERROR_FILE_NOT_FOUND 2
#define CP_UTF8 65001
#define MB_ERR_INVALID_CHARS 8
#define FILE_ATTRIBUTE_NORMAL 128
#define MOVEFILE_REPLACE_EXISTING 1
#define MOVEFILE_WRITE_THROUGH 8
static WCHAR config[MAX_PATH]=L"C:\\game\\player-displays.ini";
static VoPreference pending={VO_MIRROR,VO_SUPER,"monitor-a","monitor-b"};
static unsigned original,temporary;static int step,fail,exists,deleted,moved;
static int allow(void){return ++step!=fail;}
static int GetTempFileNameW(const WCHAR *dir,const WCHAR *prefix,unsigned n,WCHAR *out){(void)prefix;(void)n;assert(!wcscmp(dir,L"C:\\game\\"));wcscpy(out,L"temp");temporary=0;return 1;}
static DWORD GetFileAttributesW(const WCHAR *path){assert(!wcscmp(path,config));return exists?0:INVALID_FILE_ATTRIBUTES;}
static DWORD GetLastError(void){return ERROR_FILE_NOT_FOUND;}
static int CopyFileW(const WCHAR *a,const WCHAR *b,int flag){assert(!wcscmp(a,config)&&!wcscmp(b,L"temp")&&!flag);if(!allow())return 0;temporary=original;return 1;}
static int WritePrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *value,const WCHAR *path){
 if(!wcscmp(path,config)){assert(!section&&!key&&!value);return 1;}
 assert(!wcscmp(path,L"temp"));if(!allow())return 0;
 if(!key)return 1;
 if(!wcscmp(key,L"Mode")){assert(!wcscmp(value,L"2"));temporary|=1;}
 else if(!wcscmp(key,L"GameAspect")){assert(!wcscmp(value,L"3"));temporary|=2;}
 else if(!wcscmp(key,L"Player1")){assert(!wcscmp(value,L"monitor-a"));temporary|=4;}
 else if(!wcscmp(key,L"Player2")){assert(!wcscmp(value,L"monitor-b"));temporary|=8;}
 else assert(0);return 1;
}
static int MultiByteToWideChar(unsigned cp,unsigned flags,const char *in,int len,WCHAR *out,int size){(void)cp;(void)flags;(void)len;return (int)mbstowcs(out,in,size)+1;}
static int MoveFileExW(const WCHAR *a,const WCHAR *b,unsigned flags){assert(!wcscmp(a,L"temp")&&!wcscmp(b,config)&&flags==9);if(!allow())return 0;original=temporary;moved=1;return 1;}
static int DeleteFileW(const WCHAR *path){assert(!wcscmp(path,L"temp"));deleted=1;return 1;}
static int SetFileAttributesW(const WCHAR *path,unsigned flags){(void)path;(void)flags;return 1;}
'''
fixture=fixture.replace('#define NULL ((void*)0)\n','').replace('#include <string.h>','#include <string.h>\n#include <stdlib.h>')
fixture+=body+r'''
int main(void){
 for(int present=0;present<=1;present++)for(int failure=0;failure<=6+present;failure++){
  exists=present;original=64;temporary=0;step=0;fail=failure;deleted=moved=0;
  int ok=save_pending();
  if(failure){assert(!ok&&!moved&&deleted&&original==64);}
  else{assert(ok&&moved&&!deleted&&original==(unsigned)(15+(present?64:0)));}
 }
 puts("PASS production save: new/existing files, preservation of unrelated data, copy/write/flush/replace failure atomicity and temporary cleanup (API doubles)");return 0;
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture)
 subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
