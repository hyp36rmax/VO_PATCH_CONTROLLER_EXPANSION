"""Execute production layout and hit tests with GDI/DirectDraw API doubles."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=(here/'render.c').read_text().replace('#include "runtime.h"','')
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "model.h"
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define RGB(r,g,b) ((r)|((g)<<8)|((b)<<16))
#define DD_OK 0
#define FW_BOLD 700
#define FW_NORMAL 400
#define DEFAULT_CHARSET 1
#define ANTIALIASED_QUALITY 4
#define DEFAULT_PITCH 0
#define TRANSPARENT 1
#define DT_LEFT 0
#define DT_VCENTER 4
#define DT_SINGLELINE 32
#define DT_NOPREFIX 2048
#define DT_WORDBREAK 16
typedef unsigned COLORREF;typedef void *HDC,*HBRUSH,*HFONT,*LPDIRECTDRAWSURFACE;
typedef struct {int left,top,right,bottom;} RECT;
typedef struct {unsigned dwSize,dwWidth,dwHeight;} DDSURFACEDESC;
typedef struct {LPDIRECTDRAWSURFACE surface;HFONT title,body;int width,height,area_width,x,y,w,h,row,first,visible;} VoPaint;
static int width,height,mode,refs,fonts,labels;
static HBRUSH CreateSolidBrush(COLORREF c){(void)c;return (void*)1;}
static void FillRect(HDC d,const RECT*r,HBRUSH b){(void)d;(void)b;assert(r->left>=0&&r->top>=0&&r->right<=width&&r->bottom<=height);}
static void DeleteObject(void*p){(void)p;}
static void SetTextColor(HDC h,COLORREF c){(void)h;(void)c;}
static void DrawTextA(HDC h,const char*s,int n,const RECT*r,int f){(void)h;(void)s;(void)n;(void)f;assert(r->right<=width&&r->bottom<=height);labels++;}
static void IDirectDrawSurface_Release(LPDIRECTDRAWSURFACE s){(void)s;refs--;}
static int IDirectDrawSurface_GetSurfaceDesc(LPDIRECTDRAWSURFACE s,DDSURFACEDESC*d){(void)s;d->dwWidth=width;d->dwHeight=height;return 0;}
static void IDirectDrawSurface_AddRef(LPDIRECTDRAWSURFACE s){(void)s;refs++;}
static int GetEnvironmentVariableA(const char*k,char*out,int n){assert(!strcmp(k,"VO_EX_EFFECTIVE_MODE")&&n==2);out[0]='0'+mode;out[1]=0;return 1;}
static HFONT CreateFontA(int h,int w,int a,int b,int c,int d,int e,int f,int g,int i,int j,int k,int l,const char*name){assert(h<=-18);(void)w;(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;(void)i;(void)j;(void)k;(void)l;(void)name;fonts++;return (void*)1;}
static int IDirectDrawSurface_IsLost(LPDIRECTDRAWSURFACE s){(void)s;return 0;}
static int IDirectDrawSurface_GetDC(LPDIRECTDRAWSURFACE s,HDC*d){(void)s;*d=(void*)1;return 0;}
static int SaveDC(HDC d){(void)d;return 1;}static void RestoreDC(HDC d,int n){(void)d;assert(n==1);}
static int IDirectDrawSurface_ReleaseDC(LPDIRECTDRAWSURFACE s,HDC d){(void)s;(void)d;return 0;}
static void SelectObject(HDC d,HFONT f){(void)d;(void)f;}static void SetBkMode(HDC d,int m){(void)d;(void)m;}
'''
main=r'''
int main(void){
 const int sizes[][2]={{320,240},{640,480},{1920,1080},{2560,1080},{3840,1080}};
 for(unsigned i=0;i<5;i++)for(mode=0;mode<3;mode++){
  if(mode==1&&i!=4)continue;
  width=sizes[i][0];height=sizes[i][1];VoPaint paint={0};assert(vo_attach(&paint,(void*)1));
  assert(paint.area_width==(mode==1?1920:width));assert(paint.visible>=1&&paint.visible<=6);assert(paint.w<=560*max(1,height/720));
  VoOverlay s;vo_overlay_init(&s);assert(vo_overlay_pause_result(&s,1,1));
  for(unsigned row=0;row<6;row++){s.selected=row;assert(vo_paint(&paint,&s));assert(vo_hit_source(&paint,paint.x+20,paint.y+53+(row-paint.first)*paint.row)==(int)row);}
  assert(vo_hit_source(&paint,paint.x+20,paint.y+paint.h-25)==6);
  assert(vo_hit_source(&paint,paint.x+paint.w-20,paint.y+paint.h-25)==5);
  assert(vo_hit_source(&paint,0,0)==-1);s.unavailable=1;assert(vo_paint(&paint,&s));
  vo_dispose(&paint);assert(!refs);
 }
 assert(fonts&&labels);puts("PASS production layout/render calls: 320/640 4:3, 16:9, 21:9, 32:9, Versus P1 bounds, bounded width, scroll visibility, Back/Resume hit tests, surface release");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture+body+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
