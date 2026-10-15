#ifndef VO_F5_SETTINGS_H
#define VO_F5_SETTINGS_H
#include "mode_config.h"
/* Pending preferences are separate from the running game and parent F5 state. */
enum { VO_EDIT_MODE=1, VO_EDIT_PRIMARY=2, VO_EDIT_SECONDARY=4, VO_EDIT_ASPECT=8 };
enum { VO_SETTINGS_OK, VO_SETTINGS_MODE, VO_SETTINGS_ASPECT,
       VO_SETTINGS_PRIMARY, VO_SETTINGS_SECONDARY, VO_SETTINGS_SAME };
static int vo_settings_validate(const VoMonitor *m,unsigned n,const VoPreference *p,unsigned dirty){
 if(!dirty)return VO_SETTINGS_OK; /* Opening/closing must preserve saved fallback requests. */
 if(p->mode<VO_SINGLE||p->mode>VO_MIRROR)return VO_SETTINGS_MODE;
 if(p->aspect<VO_ORIGINAL||p->aspect>VO_SUPER)return VO_SETTINGS_ASPECT;
 /* Unrelated edits must not erase or reject a temporarily missing saved pair. */
 if(!(dirty&(VO_EDIT_MODE|VO_EDIT_PRIMARY|VO_EDIT_SECONDARY)))return VO_SETTINGS_OK;
 int a=vo_find(m,n,p->primary);
 if(a<0||!m[a].available)return VO_SETTINGS_PRIMARY;
 if(p->mode==VO_SINGLE)return VO_SETTINGS_OK;
 int b=vo_find(m,n,p->secondary);
 if(b<0||!m[b].available)return VO_SETTINGS_SECONDARY;
 if(a==b||!strcmp(p->primary,p->secondary))return VO_SETTINGS_SAME;
 /* Cloned outputs occupying the same desktop are not independent displays. */
 if(m[a].desktop.x==m[b].desktop.x&&m[a].desktop.y==m[b].desktop.y)return VO_SETTINGS_SAME;
 return VO_SETTINGS_OK;
}
#endif
