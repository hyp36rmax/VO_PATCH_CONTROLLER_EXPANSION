#ifndef VO_BRIDGE_TEST
#include <windows.h>
#endif
#include <string.h>
#include <stdio.h>
#include "policy.h"
#include "state_bridge.h"
#ifndef VO_BRIDGE_TEST
#include "game_profiles.h"
#endif
/* Called only at producer publication boundaries under g_ddraw.cs. */
typedef enum { SOURCE_UNINITIALIZED, SOURCE_VALID, SOURCE_DISABLED,
 SOURCE_UNSUPPORTED, SOURCE_INVALID_READ, SOURCE_UNKNOWN } VoSourceStatus;
static const char *source_names[]={"UNINITIALIZED","VALID","DISABLED","UNSUPPORTED_EXECUTABLE","INVALID_READ","UNKNOWN_STATE"};
static volatile LONG completed=VO_POLICY_UNKNOWN;
static volatile LONG unknown_count,unknown_state[4];
static int checked;
static const VoGameProfile *profile;
static struct {
 unsigned captures,flips,unlocks,raw[4],valid_mask,stamp,size,status;
 uintptr_t base;
 unsigned transitions,used;
 struct {unsigned capture,status,phase,raw[4],valid_mask,kind;} trace[64];
} observation;
static int vo_read(uintptr_t address,void *out,size_t size){
 SIZE_T got=0;
 return ReadProcessMemory(GetCurrentProcess(),(const void*)address,out,size,&got)&&got==size;
}
static unsigned vo_identify(void){
 char enabled[2];
 if(GetEnvironmentVariableA("VO_DUAL_DISPLAY",enabled,2)!=1||enabled[0]!='1')return SOURCE_DISABLED;
 uintptr_t base=(uintptr_t)GetModuleHandleW(NULL);observation.base=base;
 IMAGE_DOS_HEADER dos;IMAGE_NT_HEADERS nt;
 if(!vo_read(base,&dos,sizeof dos))return SOURCE_INVALID_READ;
 if(dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<0||dos.e_lfanew>0x100000)return SOURCE_UNSUPPORTED;
 if(!vo_read(base+dos.e_lfanew,&nt,sizeof nt))return SOURCE_INVALID_READ;
 observation.stamp=nt.FileHeader.TimeDateStamp;observation.size=nt.OptionalHeader.SizeOfImage;
 if(nt.Signature!=IMAGE_NT_SIGNATURE||nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC)return SOURCE_UNSUPPORTED;
 for(unsigned i=0;i<sizeof(vo_profiles)/sizeof(vo_profiles[0]);i++){
  const VoGameProfile *p=&vo_profiles[i];unsigned char bytes[32];
  if(base!=p->base||observation.stamp!=p->stamp||observation.size!=p->size)continue;
  if(!vo_read(p->signature,bytes,sizeof bytes))return SOURCE_INVALID_READ;
  if(memcmp(bytes,p->bytes,sizeof bytes))return SOURCE_UNSUPPORTED;
  profile=p;return SOURCE_VALID;
 }
 return SOURCE_UNSUPPORTED;
}
static void vo_capture(unsigned kind){
 unsigned prior_status=observation.status,prior_phase=(unsigned)completed;
 ++observation.captures;if(kind==2)++observation.flips;else ++observation.unlocks;
 if(!checked){observation.status=vo_identify();checked=1;}
 observation.valid_mask=0;
 memset(observation.raw,0,sizeof observation.raw);
 VoPolicy phase=VO_POLICY_UNKNOWN;
 if(profile){
  uintptr_t addresses[]={profile->loop,profile->mode,profile->split,profile->show};
  for(unsigned i=0;i<4;i++)if(vo_read(addresses[i],&observation.raw[i],sizeof(unsigned)))observation.valid_mask|=1u<<i;
  if(observation.valid_mask!=15)observation.status=SOURCE_INVALID_READ;
  else if(!(observation.raw[0]|observation.raw[1]|observation.raw[2]|observation.raw[3]))observation.status=SOURCE_UNINITIALIZED;
  else {
   phase=vo_policy(observation.raw[0],observation.raw[1],observation.raw[2],observation.raw[3]);
   observation.status=phase==VO_POLICY_UNKNOWN?SOURCE_UNKNOWN:SOURCE_VALID;
  }
 }
 /* Invalid observations never masquerade as PRIMARY_ONLY or force gameplay. */
 InterlockedExchange(&completed,phase);
 if(phase==VO_POLICY_UNKNOWN){
  for(unsigned i=0;i<4;i++)InterlockedExchange(&unknown_state[i],observation.raw[i]);
  InterlockedIncrement(&unknown_count);
 }
 if(observation.captures==1||prior_status!=observation.status||prior_phase!=(unsigned)phase){
  unsigned n=observation.used;
  ++observation.transitions;
  if(n<64){
   observation.trace[n].capture=observation.captures;observation.trace[n].status=observation.status;
   observation.trace[n].phase=phase;observation.trace[n].valid_mask=observation.valid_mask;observation.trace[n].kind=kind;
   memcpy(observation.trace[n].raw,observation.raw,sizeof observation.raw);++observation.used;
  }
 }
}
void vo_capture_policy(void){vo_capture(1);}
void vo_capture_flip_policy(void){vo_capture(2);}
unsigned vo_completed_policy(void){return (unsigned)InterlockedCompareExchange(&completed,0,0);}
unsigned vo_unknown_policy_count(void){return (unsigned)InterlockedCompareExchange(&unknown_count,0,0);}
unsigned vo_unknown_policy_value(unsigned i){return i<4?(unsigned)InterlockedCompareExchange(&unknown_state[i],0,0):0;}
void vo_policy_log(FILE *log){
 fprintf(log,"state_identity_base=0x%lx timestamp=0x%x image_size=0x%x source=%s captures=%u primary_unlocks=%u primary_flips=%u read_mask=0x%x\n",(unsigned long)observation.base,observation.stamp,observation.size,source_names[observation.status],observation.captures,observation.unlocks,observation.flips,observation.valid_mask);
 if(profile)fprintf(log,"state_rvas loop=0x%lx mode=0x%lx split=0x%lx show=0x%lx\n",(unsigned long)(profile->loop-profile->base),(unsigned long)(profile->mode-profile->base),(unsigned long)(profile->split-profile->base),(unsigned long)(profile->show-profile->base));
 fprintf(log,"last_observed_loop=%u mode=%u split=%u show=%u classified=%u fallback=%s transitions=%u recorded=%u\n",observation.raw[0],observation.raw[1],observation.raw[2],observation.raw[3],vo_completed_policy(),completed==VO_POLICY_UNKNOWN?"FULL_SHARED_NO_GAMEPLAY_ASSUMPTION":"NONE",observation.transitions,observation.used);
 for(unsigned i=0;i<observation.used;i++)fprintf(log,"transition capture=%u boundary=%s reason=%s classified=%u read_mask=0x%x raw=%u,%u,%u,%u\n",observation.trace[i].capture,observation.trace[i].kind==2?"FLIP":"UNLOCK",source_names[observation.trace[i].status],observation.trace[i].phase,observation.trace[i].valid_mask,observation.trace[i].raw[0],observation.trace[i].raw[1],observation.trace[i].raw[2],observation.trace[i].raw[3]);
}
