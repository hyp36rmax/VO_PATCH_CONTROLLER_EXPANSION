#ifndef VO_PRESENTATION_POLICY_H
#define VO_PRESENTATION_POLICY_H
#include "layout.h"
typedef enum { VO_PRIMARY_ONLY, VO_LOCAL_VS_SHARED, VO_LOCAL_VS_GAMEPLAY, VO_POLICY_UNKNOWN } VoPolicy;
/* D_SHOW is the producer's decision, not a second round-state table. */
static VoPolicy vo_policy(unsigned loop,unsigned mode,unsigned split,unsigned show) {
 if(loop>2||mode>5||split>1||show>2)return VO_POLICY_UNKNOWN;
 if(loop!=1||mode!=4)return VO_PRIMARY_ONLY;
 if(!split)return VO_POLICY_UNKNOWN;
 return show?VO_LOCAL_VS_SHARED:VO_LOCAL_VS_GAMEPLAY;
}
static int vo_route(VoPolicy phase,int mirror,unsigned player,VoRect monitor,VoOutput *o,int *black) {
 *black=phase==VO_PRIMARY_ONLY&&player==1;
 o->source=(VoRect){0,0,3840,1080};
 if(phase==VO_LOCAL_VS_GAMEPLAY)
  o->source=(VoRect){player&&!(phase==VO_LOCAL_VS_GAMEPLAY&&mirror)?1920:0,0,1920,1080};
 return vo_fit_source(monitor,o->source.w,o->source.h,&o->destination);
}
#endif
