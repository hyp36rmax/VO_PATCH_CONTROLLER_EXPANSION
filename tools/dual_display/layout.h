#ifndef VO_DUAL_LAYOUT_H
#define VO_DUAL_LAYOUT_H
#include <stdint.h>
#include <string.h>
#include <limits.h>
#define VO_MAX_MONITORS 16
#define VO_ID_CHARS 512
typedef struct { int32_t x,y,w,h; } VoRect;
typedef struct { char id[VO_ID_CHARS]; VoRect desktop; unsigned primary,available; } VoMonitor;
typedef struct { VoRect source,destination; unsigned monitor; } VoOutput;
typedef enum { VO_DUAL_READY, VO_SINGLE_FALLBACK, VO_ASSIGNMENT_MISSING, VO_CLONED_OUTPUTS, VO_INVALID_GEOMETRY } VoResult;
/* Contain 16:9 in physical desktop pixels. No extra framebuffer allocation. */
static int vo_fit(VoRect m, VoRect *out) {
    if(m.w<=0||m.h<=0) return 0;
    int64_t w=m.w,h=m.h;
    if(w*9>h*16) w=h*16/9; else h=w*9/16;
    int64_t x=(int64_t)m.x+(m.w-w)/2,y=(int64_t)m.y+(m.h-h)/2;
    if(w<1||h<1||x<INT32_MIN||y<INT32_MIN||x+w>INT32_MAX||y+h>INT32_MAX)return 0;
    *out=(VoRect){(int32_t)x,(int32_t)y,(int32_t)w,(int32_t)h};return 1;
}
static int vo_find(const VoMonitor *m,unsigned n,const char *id) {
    for(unsigned i=0;i<n;i++)if(m[i].available&&id[0]&&!strcmp(id,m[i].id))return (int)i;
    return -1;
}
/* Saved IDs never silently bind to a different display. Missing IDs fall back. */
static VoResult vo_plan(const VoMonitor *m,unsigned n,const char *p1,const char *p2,VoOutput out[2]) {
    if(n>VO_MAX_MONITORS)return VO_INVALID_GEOMETRY;
    int a=-1,b=-1;
    if(p1[0]||p2[0]) {
        a=vo_find(m,n,p1);b=vo_find(m,n,p2);
        if(a<0||b<0)return VO_ASSIGNMENT_MISSING;
    } else {
        for(unsigned i=0;i<n;i++)if(m[i].available&&(a<0||m[i].primary))a=(int)i;
        for(unsigned i=0;i<n;i++)if(m[i].available&&(int)i!=a){b=(int)i;break;}
    }
    if(a<0||b<0)return VO_SINGLE_FALLBACK;
    if(a==b||!strcmp(m[a].id,m[b].id))return VO_CLONED_OUTPUTS;
    VoRect x=m[a].desktop,y=m[b].desktop;
    if((int64_t)x.x+x.w>y.x&&(int64_t)y.x+y.w>x.x&&(int64_t)x.y+x.h>y.y&&(int64_t)y.y+y.h>x.y)return VO_CLONED_OUTPUTS;
    VoOutput proposed[2]={{{0,0,1920,1080},{0},(unsigned)a},{{1920,0,1920,1080},{0},(unsigned)b}};
    if(!vo_fit(x,&proposed[0].destination)||!vo_fit(y,&proposed[1].destination))return VO_INVALID_GEOMETRY;
    memcpy(out,proposed,sizeof proposed);return VO_DUAL_READY;
}
#endif
