"""Exercise production transaction rollback with file/API fault injection."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=(here/'ini_transaction.h').read_text().replace('#include <windows.h>','')
body=body.replace('(char*)(uintptr_t)(j?0x1acb7f0:0x1ad0b98)','paths[j]').replace('(char*)(uintptr_t)(j?0x1acb9c0:0x1ad0b70)','sections[j]')
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#define MAX_PATH 260
#define FALSE 0
#define INVALID_FILE_ATTRIBUTES 0xffffffffu
#define FILE_ATTRIBUTE_READONLY 1
#define FILE_ATTRIBUTE_DIRECTORY 16
#define FILE_ATTRIBUTE_NORMAL 128
#define GENERIC_WRITE 1
#define FILE_SHARE_READ 1
#define OPEN_EXISTING 3
#define MOVEFILE_REPLACE_EXISTING 1
#define MOVEFILE_WRITE_THROUGH 8
typedef unsigned DWORD;typedef int HANDLE;
#define INVALID_HANDLE_VALUE -1
static char paths[2][264],sections[2][40],original[128],staged[128];
static int failure,exists,readonly,temp,flushes;
static DWORD GetFullPathNameA(const char*p,DWORD n,char*out,char**file){(void)n;if(failure==1)return 0;strcpy(out,p);*file=strrchr(out,'\\')+1;return (DWORD)strlen(out);}
static DWORD GetFileAttributesA(const char*p){(void)p;return exists?(readonly?1:128):INVALID_FILE_ATTRIBUTES;}
static int GetTempFileNameA(const char*d,const char*prefix,unsigned zero,char*out){assert(!strcmp(prefix,"vux")&&!zero);if(failure==2)return 0;snprintf(out,260,"%stmp.ini",d);temp=1;staged[0]=0;return 1;}
static int CopyFileA(const char*a,const char*b,int f){(void)a;(void)b;assert(!f);if(failure==3)return 0;strcpy(staged,original);return 1;}
static int DeleteFileA(const char*p){(void)p;temp=0;return 1;}
static int WritePrivateProfileStringA(const char*s,const char*k,const char*v,const char*p){assert(!s&&!k&&!v&&p);return 1;}
static HANDLE CreateFileA(const char*p,int a,int share,void*sec,int disposition,int flags,void*t){(void)p;(void)a;(void)share;(void)sec;(void)disposition;(void)flags;(void)t;return failure==4?-1:1;}
static int FlushFileBuffers(HANDLE h){assert(h==1);flushes++;return failure!=5;}
static void CloseHandle(HANDLE h){assert(h==1);}
static int MoveFileExA(const char*a,const char*b,int flags){(void)a;(void)b;assert(flags==9);if(failure==6)return 0;strcpy(original,staged);exists=1;temp=0;return 1;}
'''
main=r'''
int main(void){
 for(unsigned j=0;j<2;j++)for(int fail=0;fail<=6;fail++)for(int present=0;present<2;present++){
  strcpy(paths[j],"C:\\Games With Spaces\\Virtual On\\v_on.ini");strcpy(sections[j],"Original Section");strcpy(original,"old unrelated settings");exists=present;failure=fail;readonly=temp=0;
  VoIniTransaction t;int began=vo_ini_begin(&t,j,"Device Settings");
  if(began){assert(strcmp(paths[j],t.old_path)&&!strcmp(sections[j],"Device Settings"));strcpy(staged,"new settings plus unrelated settings");int saved=vo_ini_end(&t,1);assert(saved==(fail==0||(fail==3&&!present)));}
  assert(!strcmp(paths[j],"C:\\Games With Spaces\\Virtual On\\v_on.ini")&&!strcmp(sections[j],"Original Section")&&!temp);
  if(fail&&!(fail==3&&!present))assert(!strcmp(original,"old unrelated settings"));
 }
 failure=0;exists=1;readonly=1;VoIniTransaction t;assert(!vo_ini_begin(&t,0,"Device Settings"));
 readonly=0;strcpy(original,"preserved");assert(vo_ini_begin(&t,0,"Device Settings"));strcpy(staged,"partial write");assert(!vo_ini_end(&t,0));assert(!strcmp(original,"preserved")&&!temp);
 puts("PASS original INI transaction: both editions, spaces, missing target, read-only, directory/temp/copy/open/flush/replace failure, original path/section restoration, no partial publication");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture+body+main)
 subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
