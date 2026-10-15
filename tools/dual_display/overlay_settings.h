/* Overlay adapter for the existing F5 transaction. Included by f5_dialog.c.
 * No discovery, validation, serializer or configuration path is duplicated.
 * Commands and snapshots are synchronous on the original game UI thread. */
#include "settings_api.h"
_Static_assert(VO_MAX_MONITORS==16,"Display snapshot must hold the full F5 inventory");
static int overlay_transaction;
static void overlay_snapshot(VoDisplaySnapshot *out){
 out->mode=pending.mode;out->aspect=pending.aspect;out->dirty=dirty;
 out->count=count;out->primary=vo_find(monitors,count,pending.primary);
 out->secondary=vo_find(monitors,count,pending.secondary);
 for(unsigned i=0;i<count;i++){
  if(!WideCharToMultiByte(CP_UTF8,0,names[i],-1,out->names[i],sizeof out->names[i],NULL,NULL))out->names[i][0]=0;
 }
}
__declspec(dllexport) int WINAPI VonDisplayTransaction(unsigned command,int value,VoDisplaySnapshot *out){
 if(!out||out->size!=sizeof(*out))return 0;
 out->error=0;out->winerror=0;out->restart=0;
 if(command==VO_DISPLAY_BEGIN){
  if(busy)return 0;
  /* discover() returns a success flag, not a GetLastError contract. */
  if(!path_config()||!discover()){out->error=VO_DISPLAY_DISCOVERY;return 0;}
  busy=1;overlay_transaction=1;read_saved();dirty=0;
 }else if(!overlay_transaction)return 0;
 else if(command==VO_DISPLAY_CANCEL){pending=saved;dirty=0;overlay_transaction=0;busy=0;}
 else if(command==VO_DISPLAY_MODE){
  if(value<VO_SINGLE||value>VO_MIRROR||(count<2&&value!=VO_SINGLE)){out->error=VO_SETTINGS_MODE;return 0;}
  pending.mode=value;dirty|=VO_EDIT_MODE;
 }else if(command==VO_DISPLAY_ASPECT){
  if(value<VO_ORIGINAL||value>VO_SUPER){out->error=VO_SETTINGS_ASPECT;return 0;}
  pending.aspect=value;dirty|=VO_EDIT_ASPECT;
 }else if(command==VO_DISPLAY_PRIMARY||command==VO_DISPLAY_SECONDARY){
  if(value<0||(unsigned)value>=count){out->error=command==VO_DISPLAY_PRIMARY?VO_SETTINGS_PRIMARY:VO_SETTINGS_SECONDARY;return 0;}
  strcpy(command==VO_DISPLAY_PRIMARY?pending.primary:pending.secondary,monitors[value].id);
  dirty|=command==VO_DISPLAY_PRIMARY?VO_EDIT_PRIMARY:VO_EDIT_SECONDARY;
 }else if(command==VO_DISPLAY_APPLY&&dirty){
  /* Match F5: refresh topology, resolve automatic primary, validate, then
   * atomically commit the same saved preferences. Failure keeps the draft. */
  if(!discover()){out->error=VO_DISPLAY_DISCOVERY;return 0;}
  if(!pending.primary[0])for(unsigned i=0;i<count;i++)if(monitors[i].primary){strcpy(pending.primary,monitors[i].id);break;}
  out->error=vo_settings_validate(monitors,count,&pending,dirty);
  if(out->error){overlay_snapshot(out);return 0;}
  if(!save_pending()){out->error=VO_DISPLAY_WRITE;out->winerror=save_error;overlay_snapshot(out);return 0;}
  event(4,1);saved=pending;dirty=0;out->restart=1;
 }else if(command!=VO_DISPLAY_READ&&command!=VO_DISPLAY_APPLY)return 0;
 overlay_snapshot(out);return 1;
}
