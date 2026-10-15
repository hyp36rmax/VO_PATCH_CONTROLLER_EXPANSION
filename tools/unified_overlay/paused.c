#include "runtime.h"
/* The paused game draws on PRIMARY. Preserve its pixels and serialize the
 * restore/original pause text/overlay transaction with the existing upload.
 * No FRAME, Flip, window, timer, or pause-state mutation is involved. */
typedef BOOL (WINAPI *Begin)(LPDIRECTDRAWSURFACE);
typedef void (WINAPI *End)(LPDIRECTDRAWSURFACE);
static LPDIRECTDRAWSURFACE snapshot,locked;
static HDC memory;
static HBITMAP bitmap,previous;
static int width,height,cached;
static End finish;
static int lock_surface(LPDIRECTDRAWSURFACE s){
 HMODULE h=GetModuleHandleW(L"ddraw.dll");
 Begin begin=h?(Begin)GetProcAddress(h,"VonOverlaySurfaceBegin"):NULL;
 End end=h?(End)GetProcAddress(h,"VonOverlaySurfaceEnd"):NULL;
 if(!begin||!end||!begin(s))return 0;
 locked=s;finish=end;return 1;
}
static void discard(void){
 if(memory){if(previous)SelectObject(memory,previous);if(bitmap)DeleteObject(bitmap);DeleteDC(memory);}
 if(snapshot)IDirectDrawSurface_Release(snapshot);
 memory=NULL;bitmap=previous=NULL;snapshot=NULL;width=height=cached=0;
}
static int copy_pixels(int restore){
 HDC dc;if(!snapshot||IDirectDrawSurface_IsLost(snapshot)!=DD_OK||IDirectDrawSurface_GetDC(snapshot,&dc)!=DD_OK)return 0;
 int ok=restore?BitBlt(dc,0,0,width,height,memory,0,0,SRCCOPY):BitBlt(memory,0,0,width,height,dc,0,0,SRCCOPY);
 ok=GdiFlush()&&ok;
 return IDirectDrawSurface_ReleaseDC(snapshot,dc)==DD_OK&&ok;
}
void vo_pause_end(void){if(locked){LPDIRECTDRAWSURFACE s=locked;locked=NULL;finish(s);}}
void vo_pause_clear(void){
 if(snapshot){
  int owned=locked==NULL;
  if(!cached&&(!owned||lock_surface(snapshot))){copy_pixels(1);if(owned)vo_pause_end();}
  discard();
 }
}
int vo_pause_begin(LPDIRECTDRAWSURFACE surface,int enabled){
 if(locked)return 0;
 if(enabled&&cached&&surface){
  DDSURFACEDESC d={0};d.dwSize=sizeof d;
  if(IDirectDrawSurface_GetSurfaceDesc(surface,&d)==DD_OK&&(int)d.dwWidth==width&&(int)d.dwHeight==height){
   IDirectDrawSurface_AddRef(surface);IDirectDrawSurface_Release(snapshot);snapshot=surface;cached=0;
  }
 }
 if(!enabled||snapshot!=surface||cached)vo_pause_clear();
 if(!enabled)return 1;
 if(!surface||!lock_surface(surface))return 0;
 if(snapshot){if(copy_pixels(1))return 1;discard();vo_pause_end();return 0;}
 DDSURFACEDESC d={0};d.dwSize=sizeof d;HDC dc;
 if(IDirectDrawSurface_GetSurfaceDesc(surface,&d)!=DD_OK||!d.dwWidth||!d.dwHeight||d.dwWidth>8192||d.dwHeight>8192||IDirectDrawSurface_GetDC(surface,&dc)!=DD_OK){vo_pause_end();return 0;}
 memory=CreateCompatibleDC(dc);bitmap=memory?CreateCompatibleBitmap(dc,d.dwWidth,d.dwHeight):NULL;
 previous=bitmap?SelectObject(memory,bitmap):NULL;
 int ok=memory&&bitmap&&previous;
 if(IDirectDrawSurface_ReleaseDC(surface,dc)!=DD_OK)ok=0;
 snapshot=surface;IDirectDrawSurface_AddRef(snapshot);width=d.dwWidth;height=d.dwHeight;
 if(!ok||!copy_pixels(0)){discard();vo_pause_end();return 0;}
 return 1;
}

/* Preserve the clean pre-overlay frame for a subsequent original pause.
 * Reuse the bitmap; never capture the already composited primary as clean. */
int vo_pause_capture(LPDIRECTDRAWSURFACE surface){
 if(cached&&snapshot==surface){
  if(!lock_surface(surface))return 0;
  int ok=copy_pixels(0);vo_pause_end();return ok;
 }
 vo_pause_clear();
 if(!vo_pause_begin(surface,1))return 0;
 cached=1;vo_pause_end();return 1;
}

void vo_pause_restore_to(LPDIRECTDRAWSURFACE surface){
 if(cached&&surface){if(vo_pause_begin(surface,1))vo_pause_end();}
 vo_pause_clear();
}
