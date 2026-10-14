#include <assert.h>
#include <stdio.h>
#include "mode_config.h"
#include "policy.h"
int main(void){
 VoMonitor m[2]={{{"A"},{0,0,2560,1440},1,1},{{"B"},{2560,0,1920,1200},0,1}};
 for(int mode=0;mode<3;mode++)for(int aspect=0;aspect<4;aspect++)for(unsigned n=1;n<=2;n++){
  VoPreference p={mode,aspect,"A","B"},saved=p;VoSelection s;
  assert(vo_select_launch(m,n,&p,mode,31,&s));
  assert(!memcmp(&p,&saved,sizeof p));
  if(mode==0||n==1){
   assert(s.mode==VO_SINGLE&&s.profile==aspect);
   /* The launcher disables dual routing and selects the unchanged upstream
    * image. Never send a single framebuffer through the dual crop policy. */
   assert(s.profile!=VO_DUAL_PROFILE);
   if(mode>0)assert(s.reasons&(1u<<VO_MODE_DUAL_UNAVAILABLE));
  }else{
   assert(s.mode==mode&&s.profile==(mode==VO_MIRROR?aspect:VO_DUAL_PROFILE));
   /* Complete Mirror texture coverage is exercised against emitted code in
    * test_mode_presentation.py; the legacy crop policy belongs only to Versus. */
   if(mode==VO_MIRROR)continue;
   const VoPolicy phases[]={VO_PRIMARY_ONLY,VO_LOCAL_VS_SHARED,VO_LOCAL_VS_GAMEPLAY,VO_PRIMARY_ONLY};
   for(unsigned phase=0;phase<4;phase++)for(unsigned player=0;player<2;player++){
    VoOutput out={0};int black;
    assert(vo_route(phases[phase],s.mode==VO_MIRROR,player,m[player].desktop,&out,&black));
    assert(black==(phases[phase]==VO_PRIMARY_ONLY&&player==1));
    assert(out.source.x==((phases[phase]==VO_LOCAL_VS_GAMEPLAY&&mode==VO_VERSUS&&player==1)?1920:0));
    assert(out.source.w==1920&&out.source.h==1080);
    assert(s.mode==mode&&!memcmp(&p,&saved,sizeof p));
   }
  }
 }
 VoPreference p={VO_MIRROR,VO_WIDE,"A","B"};VoSelection s;
 assert(vo_select_launch(m,2,&p,VO_MIRROR,15,&s)&&s.mode==VO_MIRROR&&s.profile==VO_WIDE);
 assert(!vo_select_launch(m,0,&p,VO_MIRROR,31,&s));
 assert(!vo_select_launch(m,2,&p,99,31,&s));
 assert(vo_policy(1,4,1,0)==VO_LOCAL_VS_GAMEPLAY);
 assert(vo_policy(1,4,1,1)==VO_LOCAL_VS_SHARED);
 puts("PASS mode/aspect/monitor matrix, immutable preferences, prelaunch recovery, mixed aspects, phase transitions, P1/P2 source ownership; physical duplication not reproduced");
}
