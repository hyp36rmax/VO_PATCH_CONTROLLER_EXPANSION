#ifndef VO_WINDOW_MODEL_H
#define VO_WINDOW_MODEL_H
#include <stdint.h>
#include <string.h>
#define VO_WINDOWS 256
#define VO_SAMPLES 14400
#define VO_LOG_LIMIT (16u*1024u*1024u)
typedef struct {int32_t left,top,right,bottom;} VoBounds;
typedef struct {uintptr_t hwnd,parent,owner;unsigned pid,tid,rank;int visible;VoBounds bounds;int bounds_ok;} VoWindow;
static int vo_overlap(VoBounds a,VoBounds b){return a.left<a.right&&a.top<a.bottom&&b.left<b.right&&b.top<b.bottom&&a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom;}
/* Metadata candidate only: no claim about opaque regions or decoded pixels. */
static int vo_cover_candidate(VoWindow above,VoWindow target){return above.hwnd!=target.hwnd&&above.visible&&target.visible&&above.rank<target.rank&&vo_overlap(above.bounds,target.bounds);}
static int vo_append(VoWindow *a,unsigned *n,VoWindow w){if(*n==VO_WINDOWS)return 0;for(unsigned i=0;i<*n;i++)if(a[i].hwnd==w.hwnd)return 1;a[(*n)++]=w;return 1;}
static int vo_contains(const VoWindow *a,unsigned n,uintptr_t h){for(unsigned i=0;i<n;i++)if(a[i].hwnd==h)return 1;return 0;}
#endif
