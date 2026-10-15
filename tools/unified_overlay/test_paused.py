"""Run the production paused compositor with pixel/surface transaction doubles."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
fixture=r'''
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <wchar.h>
#define WINAPI
#define BOOL int
#define DD_OK 0
#define SRCCOPY 0
typedef struct Surface {int pixel,refs,lost;} Surface;
typedef Surface *LPDIRECTDRAWSURFACE;
typedef struct DC {int *pixel;} *HDC;
typedef int *HBITMAP;
typedef void *HMODULE;
typedef struct {unsigned dwSize,dwWidth,dwHeight;} DDSURFACEDESC;
static struct DC screen;
static int depth,fail_alloc,fail_lock,pending,uploads,last_upload;
static Surface *held;
static void upload(void){if(!depth){assert(!pending);uploads++;last_upload=screen.pixel?*screen.pixel:-1;}}
static int GdiFlush(void){pending=0;return 1;}
static int begin(LPDIRECTDRAWSURFACE s){if(fail_lock)return 0;assert(!depth);held=s;depth++;s->refs++;return 1;}
static void end(LPDIRECTDRAWSURFACE s){assert(depth==1&&held==s);GdiFlush();depth--;s->refs--;upload();}
static HMODULE GetModuleHandleW(const wchar_t*s){(void)s;return (void*)1;}
static void *GetProcAddress(HMODULE h,const char*s){(void)h;return strstr(s,"Begin")?(void*)begin:(void*)end;}
static void IDirectDrawSurface_AddRef(Surface*s){s->refs++;}
static void IDirectDrawSurface_Release(Surface*s){s->refs--;assert(s->refs>=0);}
static int IDirectDrawSurface_IsLost(Surface*s){return s->lost;}
static int IDirectDrawSurface_GetDC(Surface*s,HDC*out){screen.pixel=&s->pixel;*out=&screen;return 0;}
static int IDirectDrawSurface_ReleaseDC(Surface*s,HDC dc){(void)s;(void)dc;upload();return 0;}
static int IDirectDrawSurface_GetSurfaceDesc(Surface*s,DDSURFACEDESC*d){(void)s;d->dwWidth=640;d->dwHeight=480;return 0;}
static HDC CreateCompatibleDC(HDC dc){(void)dc;if(fail_alloc)return NULL;return calloc(1,sizeof(struct DC));}
static HBITMAP CreateCompatibleBitmap(HDC dc,unsigned w,unsigned h){(void)dc;(void)w;(void)h;return calloc(1,sizeof(int));}
static HBITMAP SelectObject(HDC dc,HBITMAP b){int *old=dc->pixel;dc->pixel=b;return old?old:(int*)1;}
static void DeleteObject(HBITMAP b){free(b);}
static void DeleteDC(HDC dc){free(dc);}
static int BitBlt(HDC dst,int x,int y,int w,int h,HDC src,int a,int b,int rop){(void)x;(void)y;(void)w;(void)h;(void)a;(void)b;(void)rop;*dst->pixel=*src->pixel;pending=1;return 1;}
'''
main=r'''
int main(void){
 Surface a={10,0,0},b={20,0,0};
 for(int i=0;i<100;i++){
  int count=uploads;assert(vo_pause_begin(&a,1));assert(a.pixel==10&&depth==1);
  a.pixel=11;pending=1;upload();assert(uploads==count); // original pause text
  a.pixel=99;GdiFlush();upload();assert(uploads==count); // complete overlay
  vo_pause_end();assert(last_upload==99&&!depth&&a.refs==1);
 }
 assert(vo_pause_begin(&a,0));assert(a.pixel==10&&!a.refs&&!depth); // dismiss/resume restores pixels
 assert(vo_pause_begin(&a,1));a.pixel=99;vo_pause_end();
 assert(vo_pause_begin(&b,1));assert(a.pixel==10&&!a.refs&&b.pixel==20);b.pixel=98;vo_pause_end();
 vo_pause_clear();assert(b.pixel==20&&!b.refs&&!depth);
 // Active frame is captured BEFORE composition; pause must not retain it.
 a.pixel=40;assert(vo_pause_capture(&a));a.pixel=99;
 b.pixel=99;assert(vo_pause_begin(&b,1));assert(b.pixel==40);b.pixel=98;vo_pause_end();vo_pause_clear();assert(b.pixel==40);
 a.pixel=50;assert(vo_pause_capture(&a));a.pixel=60;assert(vo_pause_capture(&a));vo_pause_clear();assert(a.pixel==60&&!a.refs);
 a.pixel=70;assert(vo_pause_capture(&a));b.pixel=99;vo_pause_restore_to(&b);assert(b.pixel==70&&!a.refs&&!b.refs&&!depth);
 fail_alloc=1;assert(!vo_pause_begin(&a,1));assert(!a.refs&&!depth);fail_alloc=0;
 fail_lock=1;assert(!vo_pause_begin(&a,1));assert(!a.refs&&!depth);fail_lock=0;
 assert(vo_pause_begin(&a,1));assert(!vo_pause_begin(&a,1));vo_pause_end();a.lost=1;vo_pause_clear();assert(!a.refs&&!depth);
 puts("PASS paused compositor: no intermediate upload across 100 idle cycles; original pixels restored on close/resume/surface change; balanced references/locks; allocation, lost-surface and missing synchronization recovery");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);src=p/'paused.c';src.write_text(fixture+(here/'paused.c').read_text().replace('#include "runtime.h"','')+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(src),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
