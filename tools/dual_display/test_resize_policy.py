"""Execute the production effective-mode gate using Win32 API doubles."""
from pathlib import Path
import subprocess, tempfile
source=Path(__file__).with_name('f5_dialog.c').read_text()
body=source[source.index('__declspec(dllexport) int WINAPI VonDisplayCanResize'):].split('#include "startup_runtime.h"')[0]
fixture=r"""
#include <assert.h>
#include <stddef.h>
#include <string.h>
#include <wchar.h>
#define __declspec(x)
#define WINAPI
#define MB_OK 0
#define MB_ICONINFORMATION 0
 typedef int HWND;
static const char *value;
static unsigned events, messages;
static unsigned GetEnvironmentVariableA(const char *key,char *out,unsigned size){
 assert(!strcmp(key,"VO_DUAL_DISPLAY") && size==2);
 if(!value)return 0;
 unsigned n=(unsigned)strlen(value);
 if(n>=size)return n+1;
 memcpy(out,value,n+1);return n;
}
static void event(unsigned code,int result){assert(code==6&&result==0);events++;}
static int MessageBoxW(HWND owner,const wchar_t *text,const wchar_t *title,unsigned flags){
 (void)text;(void)title;(void)flags;assert(owner==42);messages++;return 0;
}
"""
test=r"""
int main(void){
 const char *cases[]={NULL,"","0","1","invalid"};
 for(unsigned i=0;i<5;i++){
  value=cases[i];events=messages=0;
  assert(VonDisplayCanResize(42)==(i!=3));
  assert(events==(i==3)&&messages==(i==3));
 }
}
"""
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'test.c';p.write_text(fixture+body+test)
 subprocess.run(['clang','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p),'-o',td+'/test'],check=True)
 subprocess.run([td+'/test'],check=True)
print('PASS production gate: effective dual holds; single/unset retain legacy path; one limitation message')
