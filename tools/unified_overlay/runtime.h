#ifndef VO_OVERLAY_RUNTIME_H
#define VO_OVERLAY_RUNTIME_H
#ifdef VO_OVERLAY_TEST
#include "test_platform.h"
#else
#define COBJMACROS
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <windowsx.h>
#include <ddraw.h>
#include <xinput.h>
#endif
#include "model.h"
#define VO_OPEN_MESSAGE (WM_APP+0x350)
typedef struct {
 DWORD size;
 LPDIRECTDRAWSURFACE *primary,*back;
 volatile LONG *inactive,*gamemode,*mode,*submode,*movie;
 void (__cdecl *pause)(int);
 void (__cdecl *resume)(void);
 int (__cdecl *allowed)(void);
 void (__cdecl *frame)(void);
 unsigned char *custom;
 volatile LONG *threshold;
 volatile LONG *devices;
 const unsigned char *padbinds,*conditions,*twinbinds,*horibinds;
 volatile LONG *mode2;
 void (__cdecl *cdstop)(void);
} VoGame;
#ifndef VO_OVERLAY_TEST
_Static_assert(sizeof(VoGame)==84,"Overlay bridge requires the verified 32-bit ABI");
#endif
typedef struct {
 LPDIRECTDRAWSURFACE surface;HFONT title,body;
 int width,height,area_width,x,y,w,h,row,first,visible,page;
} VoPaint;
int vo_pause_begin(LPDIRECTDRAWSURFACE,int);
int vo_pause_capture(LPDIRECTDRAWSURFACE);
void vo_pause_end(void);
void vo_pause_clear(void);
void vo_pause_restore_to(LPDIRECTDRAWSURFACE);
int vo_attach(VoPaint*,LPDIRECTDRAWSURFACE);
int vo_paint(VoPaint*,const VoOverlay*);
void vo_dispose(VoPaint*);
int vo_hit_source(VoPaint*,int,int);
#endif
