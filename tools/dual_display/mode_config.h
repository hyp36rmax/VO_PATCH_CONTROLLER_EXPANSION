#ifndef VO_MODE_CONFIG_H
#define VO_MODE_CONFIG_H
#include "layout.h"
enum {VO_SINGLE,VO_VERSUS,VO_MIRROR};
enum {VO_ORIGINAL,VO_WIDE,VO_ULTRA,VO_SUPER,VO_DUAL_PROFILE};
enum {VO_MODE_OK,VO_MODE_MISSING_PRIMARY,VO_MODE_DUAL_UNAVAILABLE,VO_MODE_PROFILE_UNAVAILABLE,VO_MODE_INVALID};
typedef struct {int mode,aspect;char primary[VO_ID_CHARS],secondary[VO_ID_CHARS];} VoPreference;
typedef struct {int mode,profile,primary,secondary;unsigned reasons;} VoSelection;
/* Resolve without mutating preferences. A disconnected display never erases IDs. */
static int vo_select(const VoMonitor *m,unsigned n,const VoPreference *p,unsigned profiles,VoSelection *s){
 if(!n||n>VO_MAX_MONITORS)return 0;
 *s=(VoSelection){VO_SINGLE,VO_WIDE,-1,-1,0};
 s->primary=vo_find(m,n,p->primary);
 if(s->primary<0){
  if(p->primary[0])s->reasons|=1u<<VO_MODE_MISSING_PRIMARY;
  for(unsigned i=0;i<n;i++)if(m[i].available&&(s->primary<0||m[i].primary))s->primary=(int)i;
 }
 if(s->primary<0)return 0;
 VoRect fitted;if(!vo_fit(m[s->primary].desktop,&fitted))return 0;
 if(p->mode<VO_SINGLE||p->mode>VO_MIRROR)s->reasons|=1u<<VO_MODE_INVALID;
 else if(p->mode!=VO_SINGLE){
  VoOutput outputs[2];VoResult r=vo_plan(m,n,p->primary,p->secondary,outputs);
  if(r==VO_DUAL_READY&&(profiles&(1u<<VO_DUAL_PROFILE))){s->mode=p->mode;s->profile=VO_DUAL_PROFILE;s->primary=outputs[0].monitor;s->secondary=outputs[1].monitor;return 1;}
  s->reasons|=1u<<VO_MODE_DUAL_UNAVAILABLE;
 }
 if(p->aspect>=VO_ORIGINAL&&p->aspect<=VO_SUPER&&(profiles&(1u<<p->aspect)))s->profile=p->aspect;
 else {s->reasons|=1u<<VO_MODE_PROFILE_UNAVAILABLE;if(!(profiles&(1u<<VO_WIDE)))return 0;}
 /* Explicit aspect preference is contained on the monitor, never inferred from width. */
 return 1;
}
/* An explicit UAT mode may fail; it must never resolve as another mode. */
static int vo_select_session(const VoMonitor *m,unsigned n,const VoPreference *saved,int mode,unsigned profiles,VoSelection *s){
 if(mode<VO_SINGLE||mode>VO_MIRROR)return 0;
 VoPreference effective=*saved;effective.mode=mode;
 return vo_select(m,n,&effective,profiles,s)&&s->mode==mode;
}
#endif
