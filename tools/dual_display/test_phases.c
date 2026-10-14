/* Actual presentation code with host API doubles; no Windows acceptance claim. */
#define VO_DUAL_TEST
#include "presentation_test_api.h"
#include "presentation.h"
#include <assert.h>
static void setup(void){
 memset(&vo_dual,0,sizeof vo_dual);memset(&fake,0,sizeof fake);
 fake.foreground=1;fake.enabled=1;
 g_ddraw.width=3840;g_ddraw.height=1080;g_ddraw.bpp=16;g_ddraw.hwnd=(HWND)1;
 g_d3d9.params.Windowed=1;g_d3d9.tex_width=4096;g_d3d9.tex_height=2048;
 g_d3d9.surface_tex[0]=(void*)10;g_d3d9.surface_tex[1]=(void*)11;
 count=2;monitors[0]=(VoMonitor){"a",{0,0,1920,1080},1,1};monitors[1]=(VoMonitor){"b",{-1600,0,1600,1200},0,1};
}
int main(void){
 assert(vo_policy(0,4,0,0)==VO_PRIMARY_ONLY);
 assert(vo_policy(1,1,1,1)==VO_PRIMARY_ONLY);
 assert(vo_policy(1,4,1,1)==VO_LOCAL_VS_SHARED);
 assert(vo_policy(1,4,1,2)==VO_LOCAL_VS_SHARED);
 assert(vo_policy(1,4,1,0)==VO_LOCAL_VS_GAMEPLAY);
 assert(vo_policy(2,4,1,0)==VO_PRIMARY_ONLY);
 assert(vo_policy(1,4,0,0)==VO_POLICY_UNKNOWN);
 assert(vo_policy(1,4,1,3)==VO_POLICY_UNKNOWN);
 VoOutput fallback={0};int black;
 assert(vo_route(VO_POLICY_UNKNOWN,1,1,(VoRect){0,0,1920,1080},&fallback,&black)&&fallback.source.x==1920);
 setup();
 unsigned sequence[]={0,1,2,1,0};
 for(unsigned j=0;j<5;j++){
  test_policy=sequence[j];vo_dual_uploaded(j%2);
  /* A later producer state cannot change an already uploaded frame. */
  test_policy=(sequence[j]+1)%3;
  int draws=fake.draws,clears=fake.clears;vo_dual_present(j%2);
  assert(fake.clears-clears==2&&fake.clear_color==0);
  assert(fake.vertices[draws][0].u==0);
  assert(fake.vertices[draws][2].u==(sequence[j]==2?1920.0f:3840.0f)/4096);
  assert(vo_dual.pairs==j+1&&vo_dual.presented_generation[0]==j+1&&vo_dual.presented_generation[1]==j+1);
  assert(fake.draws-draws==(sequence[j]==0?1:2));
  assert(vo_dual.output[0].source.w==(sequence[j]==2?1920:3840));
  if(sequence[j]==1)assert(!memcmp(&vo_dual.output[0].source,&vo_dual.output[1].source,sizeof(VoRect)));
  if(sequence[j]==2)assert(vo_dual.output[1].source.x==1920);
  assert(fake.foreground==1&&!fake.original_moves);
 }
 vo_dual.mirror=1;test_policy=2;vo_dual_uploaded(1);vo_dual_present(1);
 assert(vo_dual.output[0].source.x==0&&vo_dual.output[1].source.x==0);
 assert(fake.texture[fake.draws-1]==fake.texture[fake.draws-2]);
 vo_dual_end();assert(!fake.live&&fake.destroyed==2);
 for(unsigned phase=0;phase<3;phase++){
  setup();test_policy=phase;vo_dual_uploaded(0);vo_dual_present(0);int calls=fake.calls;vo_dual_end();
  for(int n=1;n<=calls;n++){
   setup();test_policy=phase;vo_dual_uploaded(0);fake.fail_at=n;vo_dual_present(0);
   assert(vo_dual.disabled&&!vo_dual.visible&&!fake.live);vo_dual_end();assert(!fake.live);
  }
 }
 const int sizes[][2]={{1920,1080},{2560,1440},{3440,1440},{5120,1440},{1600,1200}};
 for(unsigned n=0;n<5;n++)for(unsigned phase=0;phase<3;phase++)for(unsigned player=0;player<2;player++){
  VoRect m={-sizes[n][0],-sizes[n][1],sizes[n][0],sizes[n][1]};VoOutput out={0};int black;
  assert(vo_route(phase,0,player,m,&out,&black));
  assert(out.destination.x>=m.x&&out.destination.y>=m.y&&out.destination.x+out.destination.w<=0&&out.destination.y+out.destination.h<=0);
  long long error=(long long)out.destination.w*out.source.h-(long long)out.destination.h*out.source.w;
  assert(error>-out.source.w&&error<out.source.w);
 }
 puts("PASS three-phase transitions, full shared source, black secondary, mirror P1, latched generations, mixed aspects and all graphics failure points per phase; API doubles only");
}
