#ifndef VO_BRIDGE_TEST
#include <windows.h>
#endif
#include <string.h>
#include "policy.h"
#include "state_bridge.h"
#ifndef VO_BRIDGE_TEST
#include "game_profiles.h"
#endif
static volatile LONG completed=VO_PRIMARY_ONLY;
static volatile LONG unknown_count;
static volatile LONG unknown_state[4];
static int checked;
static const VoGameProfile *profile;
void vo_capture_policy(void) {
 if(!checked){
  char enabled[2];checked=1;
  if(GetEnvironmentVariableA("VO_DUAL_DISPLAY",enabled,2)!=1||enabled[0]!='1')return;
  BYTE *base=(BYTE*)GetModuleHandleW(NULL);
  IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)base;
  IMAGE_NT_HEADERS *nt=(IMAGE_NT_HEADERS*)(base+dos->e_lfanew);
  for(unsigned i=0;i<sizeof(vo_profiles)/sizeof(vo_profiles[0]);i++){
   const VoGameProfile *p=&vo_profiles[i];
   if((uintptr_t)base==p->base && nt->FileHeader.TimeDateStamp==p->stamp && nt->OptionalHeader.SizeOfImage==p->size && !memcmp((void*)p->signature,p->bytes,sizeof(p->bytes))){profile=p;break;}
  }
  if(!profile){InterlockedExchange(&completed,VO_POLICY_UNKNOWN);return;}
 }
 if(!profile)return;
 unsigned state[4]={*(volatile unsigned*)profile->loop,*(volatile unsigned*)profile->mode,*(volatile unsigned*)profile->split,*(volatile unsigned*)profile->show};
 VoPolicy phase=vo_policy(state[0],state[1],state[2],state[3]);
 /* Unrecognized producer states keep the last verified routing decision. */
 if(phase!=VO_POLICY_UNKNOWN)InterlockedExchange(&completed,phase);
 else {
  for(unsigned i=0;i<4;i++)InterlockedExchange(&unknown_state[i],state[i]);
  InterlockedIncrement(&unknown_count);
 }
}
unsigned vo_completed_policy(void){return (unsigned)InterlockedCompareExchange(&completed,0,0);}

unsigned vo_unknown_policy_count(void){return (unsigned)InterlockedCompareExchange(&unknown_count,0,0);}

unsigned vo_unknown_policy_value(unsigned i){return i<4?(unsigned)InterlockedCompareExchange(&unknown_state[i],0,0):0;}
