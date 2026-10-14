#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#define VO_BRIDGE_TEST
#include "policy.h"
typedef unsigned char BYTE;typedef int32_t LONG;
typedef struct {int e_lfanew;} IMAGE_DOS_HEADER;
typedef struct {struct {unsigned TimeDateStamp;}FileHeader;struct {unsigned SizeOfImage;}OptionalHeader;} IMAGE_NT_HEADERS;
typedef struct {uintptr_t base;unsigned stamp,size;uintptr_t signature,loop,mode,split,show;unsigned char bytes[32];} VoGameProfile;
static VoGameProfile vo_profiles[1];static union {uint64_t align;BYTE data[512];} memory;
static int enabled=1;
static void *GetModuleHandleW(void *x){(void)x;return memory.data;}
static unsigned GetEnvironmentVariableA(const char*x,char*out,unsigned n){(void)x;(void)n;out[0]=enabled?'1':'0';return 1;}
static LONG InterlockedExchange(volatile LONG*p,LONG n){LONG old=*p;*p=n;return old;}
static LONG InterlockedCompareExchange(volatile LONG*p,LONG n,LONG c){LONG old=*p;if(old==c)*p=n;return old;}
static LONG InterlockedIncrement(volatile LONG*p){return ++*p;}
#include "state_bridge.c"
static void reset(void){
 checked=0;unknown_count=0;profile=NULL;completed=VO_PRIMARY_ONLY;enabled=1;memset(memory.data,0,512);
 ((IMAGE_DOS_HEADER*)memory.data)->e_lfanew=64;
 IMAGE_NT_HEADERS *nt=(void*)(memory.data+64);nt->FileHeader.TimeDateStamp=42;nt->OptionalHeader.SizeOfImage=512;
 vo_profiles[0]=(VoGameProfile){(uintptr_t)memory.data,42,512,(uintptr_t)(memory.data+100),(uintptr_t)(memory.data+200),(uintptr_t)(memory.data+204),(uintptr_t)(memory.data+208),(uintptr_t)(memory.data+212),{0}};
}
static void state(unsigned loop,unsigned mode,unsigned split,unsigned show){unsigned values[]={loop,mode,split,show};memcpy(memory.data+200,values,sizeof values);vo_capture_policy();}
int main(void){
 reset();state(0,1,0,0);assert(vo_completed_policy()==VO_PRIMARY_ONLY);
 state(1,4,1,1);assert(vo_completed_policy()==VO_LOCAL_VS_SHARED);
 state(1,4,1,0);assert(vo_completed_policy()==VO_LOCAL_VS_GAMEPLAY);
 state(1,4,1,99);assert(vo_completed_policy()==VO_LOCAL_VS_GAMEPLAY&&vo_unknown_policy_count()==1&&vo_unknown_policy_value(3)==99);
 state(1,4,1,2);assert(vo_completed_policy()==VO_LOCAL_VS_SHARED);
 state(1,1,1,1);assert(vo_completed_policy()==VO_PRIMARY_ONLY);
 reset();memory.data[100]=1;state(1,4,1,0);assert(vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();vo_profiles[0].stamp=43;state(1,4,1,0);assert(vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();enabled=0;state(1,4,1,0);assert(!profile&&vo_completed_policy()==VO_PRIMARY_ONLY);
 puts("PASS production bridge: identity/signature rejection, disabled gate, state transitions and unknown-state hold; host API doubles");
}
