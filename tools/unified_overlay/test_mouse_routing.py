"""Execute emitted output-window mouse routing using Win32 API doubles."""
from pathlib import Path
import subprocess,sys,tempfile
source=(Path(sys.argv[1])/'inc/presentation.h').read_text()
body=source[source.index('static LRESULT CALLBACK vo_output_proc'):source.index('/* Caller holds')]
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <wchar.h>
#define CALLBACK
#define WINAPI
#define TRUE 1
#define WM_MOUSEACTIVATE 33
#define MA_NOACTIVATE 3
#define MA_NOACTIVATEANDEAT 4
#define WM_MOUSEFIRST 512
#define WM_MOUSEMOVE 512
#define WM_LBUTTONUP 514
#define WM_MOUSELAST 526
#define WM_MOUSEWHEEL 522
#define WM_DISPLAYCHANGE 126
#define WM_CLOSE 16
#define WM_APP 32768
#define LOWORD(x) ((unsigned)(x)&65535)
#define HIWORD(x) (((unsigned)(x)>>16)&65535)
#define MAKELPARAM(x,y) ((LPARAM)(((unsigned)(x)&65535)|((unsigned)(y)<<16)))
typedef void *HMODULE;typedef int HWND;typedef unsigned UINT;typedef uintptr_t WPARAM;typedef intptr_t LPARAM;typedef intptr_t LRESULT;
typedef struct {int x,y,w,h;} VoRect;
typedef struct {int monitor;VoRect source,destination;} VoOutput;
typedef struct {long x,y;} POINT;
static struct {HWND window[2];int mirror,disabled;VoOutput output[2];} vo_dual;
static struct {VoRect desktop;} monitors[2];
static struct {int cs;HWND hwnd;} g_ddraw={0,10};
static int active,posts,posted_x,posted_y;static WPARAM posted_w;
static int visible(void){return active;}
static HMODULE GetModuleHandleW(const wchar_t*s){(void)s;return (void*)1;}
static void *GetProcAddress(HMODULE h,const char*s){(void)h;(void)s;return (void*)visible;}
static void ScreenToClient(HWND w,POINT*p){(void)w;p->x-=100;p->y-=200;}
static void PostMessageA(HWND w,UINT msg,WPARAM wp,LPARAM lp){assert(w==10&&msg==WM_APP+0x351);posts++;posted_x=LOWORD(lp);posted_y=HIWORD(lp);posted_w=wp;}
static void EnterCriticalSection(int*p){(void)p;}static void LeaveCriticalSection(int*p){(void)p;}
static int DefWindowProcA(HWND w,UINT m,WPARAM wp,LPARAM lp){(void)w;(void)m;(void)wp;(void)lp;return 99;}
'''
main=r'''
int main(void){
 vo_dual.window[0]=20;vo_dual.window[1]=21;
 for(int i=0;i<2;i++){monitors[i].desktop=(VoRect){100+i*2560,200,2560,1440};vo_dual.output[i]=(VoOutput){i,{0,0,1920,1080},{100+i*2560,200,2560,1440}};}
 assert(vo_output_proc(20,WM_MOUSEACTIVATE,0,0)==MA_NOACTIVATEANDEAT);
 active=1;assert(vo_output_proc(20,WM_MOUSEACTIVATE,0,0)==MA_NOACTIVATE);
 vo_output_proc(20,WM_LBUTTONUP,0,MAKELPARAM(1280,720));assert(posts==1&&posted_x==960&&posted_y==540&&posted_w==WM_LBUTTONUP);
 vo_output_proc(21,WM_LBUTTONUP,0,MAKELPARAM(1280,720));assert(posts==1);
 vo_dual.mirror=1;vo_output_proc(21,WM_LBUTTONUP,0,MAKELPARAM(1280,720));assert(posts==2&&posted_x==960&&posted_y==540);
 /* Letterbox outside the fitted content is never a selectable source pixel. */
 vo_dual.output[1].destination=(VoRect){2660,560,2560,720};vo_dual.output[1].source=(VoRect){0,0,3840,1080};
 vo_output_proc(21,WM_LBUTTONUP,0,MAKELPARAM(100,100));assert(posts==2);
 vo_output_proc(21,WM_MOUSEMOVE,0,MAKELPARAM(1280,720));assert(posts==3&&posted_x==1920&&posted_y==540);
 vo_output_proc(20,WM_MOUSEWHEEL,(WPARAM)(120u<<16),MAKELPARAM(1380,920));assert(posts==4&&posted_x==960&&posted_y==540&&(posted_w>>16)==120);
 active=0;vo_output_proc(20,WM_MOUSEMOVE,0,MAKELPARAM(500,500));assert(posts==4);
 puts("PASS emitted primary/complete-Mirror mouse routing, Versus P2 exclusion, letterboxing, wheel coordinates, inactive pass-through");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture+body+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
