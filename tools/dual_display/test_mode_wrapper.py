"""Execute F04's emitted native-pixel gate and physical rectangle adapter with API doubles."""
from pathlib import Path
import subprocess,sys,tempfile
out=Path(sys.argv[1]);s=(out/'src/winapi_hooks.c').read_text()
a=s.index('static BOOL vo_native_movie');b=s.index('BOOL WINAPI fake_StretchBlt(',a);gate=s[a:b]
dd=(out/'src/dd.c').read_text();a=dd.index('    BOOL vo_selected_desktop=FALSE;');b=dd.index('    BOOL zooming',a);desktop=dd[a:b]
head=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef int BOOL;typedef unsigned long DWORD;typedef int HWND;
#define TRUE 1
#define FALSE 0
#define GWL_STYLE 0
#define WS_CHILD 1
static char *enabled="1",*desk="320,-1080,2560,1440",*cls="AVIWnd32";
static int parent=10,pid=5,child=1;
static struct {int hwnd;struct {int dmPelsWidth,dmPelsHeight;} mode;} g_ddraw={10,{0,0}};
static struct {int windowed;struct {int left,top,right,bottom;} window_rect;} g_config={1,{0,0,0,0}};
static int GetEnvironmentVariableA(const char *name,char *out,unsigned n){const char *v=!strcmp(name,"VO_DESKTOP")?desk:enabled;if(strlen(v)>=n)return (int)strlen(v)+1;strcpy(out,v);return (int)strlen(v);}
static HWND GetParent(HWND h){(void)h;return parent;}
static int real_GetWindowLongA(HWND h,int index){(void)h;(void)index;return child;}
static void GetWindowThreadProcessId(HWND h,DWORD *p){(void)h;*p=pid;}
static DWORD GetCurrentProcessId(void){return 5;}
static int GetClassNameA(HWND h,char *b,unsigned n){(void)h;(void)n;strcpy(b,cls);return (int)strlen(cls);}
'''
body=r'''
int main(void){
 assert(vo_native_movie(22));assert(!vo_native_movie(0));
 enabled="0";assert(!vo_native_movie(22));enabled="1";
 parent=11;assert(!vo_native_movie(22));parent=10;
 pid=6;assert(!vo_native_movie(22));pid=5;
 child=0;assert(!vo_native_movie(22));child=1;
 cls="Edit";assert(!vo_native_movie(22));cls="AVIWnd32";
 placement();assert(g_ddraw.mode.dmPelsWidth==2560&&g_ddraw.mode.dmPelsHeight==1440);assert(g_config.window_rect.left==320&&g_config.window_rect.top==-1080);
 const char *bad[]={"", "0,0,0,1080","0,0,1920,-1","0,0,999999999999999,1080","0,0,1920,1080extra","999999999,0,1920,1080"};
 for(unsigned i=0;i<sizeof bad/sizeof bad[0];i++){desk=(char*)bad[i];g_ddraw.mode.dmPelsWidth=123;placement();assert(g_ddraw.mode.dmPelsWidth==123);}
 desk="0,0,1920,1080";g_config.windowed=0;placement();assert(g_ddraw.mode.dmPelsWidth==123);
 puts("PASS emitted native AVI identity gate and physical desktop placement; invalid geometry/non-windowed paths untouched");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'test.c';p.write_text(head+gate+'\nstatic void placement(void){\n'+desktop+'}\n'+body)
 subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(p),'-o',td+'/test'],check=True);subprocess.run([td+'/test'],check=True)
# Exact forwarding checks: the early return precedes all framebuffer transforms,
# and keeps every original GDI argument. The rest of each upstream path is intact.
import mode_extension
expected={
'fake_StretchBlt':'real_StretchBlt(hdcDest,xDest,yDest,wDest,hDest,hdcSrc,xSrc,ySrc,wSrc,hSrc,rop)',
'fake_BitBlt':'real_BitBlt(hdc,x,y,cx,cy,hdcSrc,x1,y1,rop)',
'fake_SetDIBitsToDevice':'real_SetDIBitsToDevice(hdc,xDest,yDest,w,h,xSrc,ySrc,StartScan,cLines,lpvBits,lpbmi,ColorUse)',
'fake_StretchDIBits':'real_StretchDIBits(hdc,xDest,yDest,DestWidth,DestHeight,xSrc,ySrc,SrcWidth,SrcHeight,lpBits,lpbmi,iUsage,rop)'}
for name,call in expected.items():
 start=s.index('WINAPI '+name+'(');end=s.index('\n}',start);block=s[start:end]
 assert block.index('if(vo_native_movie(hwnd))return '+call+';')<block.index('if (g_ddraw.ref')
 assert block.count('vo_native_movie')==1
print('PASS four movie-only GDI forwards preserve every original argument before framebuffer transforms')

assert "x = vo_selected_desktop ? vo_x : 0; y = vo_selected_desktop ? vo_y : 0;" in dd
