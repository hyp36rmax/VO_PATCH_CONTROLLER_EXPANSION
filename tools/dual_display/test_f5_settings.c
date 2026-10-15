#include <assert.h>
#include <stdio.h>
#include "f5_settings.h"
int main(void){
 VoMonitor m[2]={0};strcpy(m[0].id,"display-a");strcpy(m[1].id,"display-b");
 m[0].available=m[1].available=1;m[0].desktop=(VoRect){0,0,2560,1440};m[1].desktop=(VoRect){2560,0,1920,1200};
 VoPreference saved={VO_MIRROR,VO_ULTRA,"display-a","display-b"},pending=saved;
 assert(vo_settings_validate(m,2,&pending,VO_EDIT_MODE)==VO_SETTINGS_OK);
 pending.mode=VO_SINGLE;assert(vo_settings_validate(m,2,&pending,VO_EDIT_MODE)==0);
 assert(!strcmp(pending.secondary,"display-b")); /* Hidden control retains value. */
 pending=saved;strcpy(pending.secondary,"display-a");assert(vo_settings_validate(m,2,&pending,VO_EDIT_SECONDARY)==VO_SETTINGS_SAME);
 pending=saved;m[1].available=0;assert(vo_settings_validate(m,2,&pending,0)==0);
 pending.aspect=VO_SUPER;assert(vo_settings_validate(m,2,&pending,VO_EDIT_ASPECT)==0);
 assert(vo_settings_validate(m,2,&pending,VO_EDIT_MODE)==VO_SETTINGS_SECONDARY);
 pending.mode=VO_SINGLE;assert(vo_settings_validate(m,1,&pending,VO_EDIT_MODE)==0);
 assert(saved.mode==VO_MIRROR&&saved.aspect==VO_ULTRA&&!strcmp(saved.secondary,"display-b")); /* Cancel never changed saved. */
 pending=saved;pending.mode=99;assert(vo_settings_validate(m,2,&pending,VO_EDIT_MODE)==VO_SETTINGS_MODE);
 pending=saved;pending.aspect=99;assert(vo_settings_validate(m,2,&pending,VO_EDIT_ASPECT)==VO_SETTINGS_ASPECT);
 puts("PASS pending/cancel isolation, independent monitor validation, hidden secondary retention, missing-monitor preference preservation and invalid values");
 return 0;
}
