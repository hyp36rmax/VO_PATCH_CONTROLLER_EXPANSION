#include <assert.h>
#include <stdio.h>
#include "mode_config.h"
int main(void){
 VoMonitor m[3]={{{0},{0,0,2560,1440},1,1},{{0},{2560,0,1920,1080},0,1},{{0},{-1920,0,1920,1200},0,1}};
 strcpy(m[0].id,"A");strcpy(m[1].id,"B");strcpy(m[2].id,"C");
 VoPreference p={0,VO_WIDE,"",""};VoSelection s;
 assert(vo_select(m,3,&p,31,&s)&&s.mode==0&&s.profile==VO_WIDE&&s.primary==0);
 for(int aspect=0;aspect<4;aspect++)for(unsigned n=1;n<=3;n++){
  p.aspect=aspect;VoPreference saved=p;assert(vo_select(m,n,&p,31,&s));assert(s.profile==aspect&&s.mode==0);assert(!memcmp(&p,&saved,sizeof p));
 }
 p.aspect=VO_SUPER;p.mode=VO_VERSUS;strcpy(p.primary,"A");strcpy(p.secondary,"B");VoPreference saved=p;
 assert(vo_select(m,2,&p,31,&s)&&s.mode==VO_VERSUS&&s.profile==VO_DUAL_PROFILE);
 assert(vo_select(m,1,&p,31,&s)&&s.mode==VO_SINGLE&&s.profile==VO_SUPER&&s.reasons);assert(!memcmp(&p,&saved,sizeof p));
 assert(vo_select(m,2,&p,31,&s)&&s.mode==VO_VERSUS);
 p.mode=VO_MIRROR;assert(vo_select(m,2,&p,31,&s)&&s.mode==VO_MIRROR);
 strcpy(p.primary,"MISSING");saved=p;assert(vo_select(m,2,&p,31,&s)&&s.mode==VO_SINGLE&&s.primary==0&&s.reasons);assert(!memcmp(&p,&saved,sizeof p));
 p.mode=VO_SINGLE;assert(vo_select(m,2,&p,1u<<VO_WIDE,&s)&&s.profile==VO_WIDE);assert(p.aspect==VO_SUPER);
 assert(!vo_select(m,0,&p,31,&s));assert(!vo_select(m,2,&p,0,&s));
 p.mode=VO_VERSUS;strcpy(p.primary,"A");strcpy(p.secondary,"A");assert(vo_select(m,2,&p,31,&s)&&s.mode==VO_SINGLE);
 p.mode=99;p.aspect=99;assert(vo_select(m,2,&p,31,&s)&&s.mode==VO_SINGLE&&s.profile==VO_WIDE&&s.reasons);
 VoRect target;assert(vo_fit_source(m[0].desktop,320,240,&target));assert(target.x==320&&target.y==0&&target.w==1920&&target.h==1440);
 for(int w=640;w<=7680;w+=640)for(int h=480;h<=2160;h+=240){assert(vo_fit_source((VoRect){-w,-h,w,h},320,240,&target));assert(target.w*3==target.h*4);assert(target.x>=-w&&target.y>=-h&&target.x+target.w<=0&&target.y+target.h<=0);}
 saved=p;
 p.mode=VO_MIRROR;p.aspect=VO_WIDE;strcpy(p.primary,"A");strcpy(p.secondary,"B");saved=p;
 for(int mode=0;mode<=2;mode++){
  assert(vo_select_session(m,2,&p,mode,31,&s)&&s.mode==mode);assert(!memcmp(&p,&saved,sizeof p));
 }
 assert(!vo_select_session(m,1,&p,VO_VERSUS,31,&s));
 assert(!vo_select_session(m,1,&p,VO_MIRROR,31,&s));
 assert(!vo_select_session(m,2,&p,VO_MIRROR,15,&s));
 assert(!vo_select_session(m,2,&p,99,31,&s));assert(!memcmp(&p,&saved,sizeof p));
 puts("PASS explicit session overrides, no differently labeled fallback, immutable saved mode and monitor preferences");
 puts("PASS mode/profile defaults, explicit aspect, missing monitor recovery, preference immutability, versus/mirror, unavailable profile fallback, geometry and negative positions");
}
