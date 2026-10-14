#include "layout.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 VoMonitor m[3]={{"stable-a",{0,0,1920,1080},1,1},{"stable-b",{-2560,-1440,2560,1440},0,1},{"stable-c",{0,1080,1080,1920},0,1}};
 VoOutput o[2],sentinel[2];memset(sentinel,0xa5,sizeof sentinel);
 unsigned cases=0;
 const int sizes[][2]={{1920,1080},{2560,1440},{3840,2160},{1080,1920},{3440,1440},{1280,1024},{5120,1440},{1600,1200}};
 for(unsigned i=0;i<8;i++)for(unsigned j=0;j<8;j++){
  m[0].desktop=(VoRect){0,0,sizes[i][0],sizes[i][1]};m[1].desktop=(VoRect){-sizes[j][0],-sizes[j][1],sizes[j][0],sizes[j][1]};
  assert(vo_plan(m,2,"","",o)==VO_DUAL_READY);
  for(unsigned k=0;k<2;k++){
   VoRect d=o[k].destination,r=m[o[k].monitor].desktop;
   assert(d.x>=r.x&&d.y>=r.y&&(int64_t)d.x+d.w<=(int64_t)r.x+r.w&&(int64_t)d.y+d.h<=(int64_t)r.y+r.h);
   int64_t delta=(int64_t)d.w*9-(int64_t)d.h*16;assert(delta>-16&&delta<16);
   assert(o[k].source.x==(int)k*1920&&o[k].source.w==1920&&o[k].source.h==1080);
  }cases++;
 }
 m[0].desktop=(VoRect){0,0,1920,1080};
 assert(vo_plan(m,3,"stable-c","stable-a",o)==VO_DUAL_READY&&o[0].monitor==2&&o[1].monitor==0);
 VoMonitor swap=m[0];m[0]=m[1];m[1]=swap;
 assert(vo_plan(m,3,"stable-c","stable-a",o)==VO_DUAL_READY&&o[1].monitor==1);
 memcpy(o,sentinel,sizeof o);assert(vo_plan(m,3,"missing","stable-a",o)==VO_ASSIGNMENT_MISSING);assert(!memcmp(o,sentinel,sizeof o));
 m[2].available=0;assert(vo_plan(m,3,"stable-c","stable-a",o)==VO_ASSIGNMENT_MISSING);
 assert(vo_plan(m,1,"","",o)==VO_SINGLE_FALLBACK);
 assert(vo_plan(m,3,"stable-a","stable-a",o)==VO_CLONED_OUTPUTS);
 m[0].desktop=m[1].desktop;assert(vo_plan(m,2,"","",o)==VO_CLONED_OUTPUTS);
 VoRect r;assert(!vo_fit((VoRect){0,0,0,1080},&r));assert(!vo_fit((VoRect){INT32_MAX,0,1920,1080},&r));
 puts("PASS: 64 mixed geometry pairs; negative/vertical positions, stable reorder, disconnect, missing/duplicate identities, clone and bounds rejection; failure outputs unchanged");return cases!=64;
}
