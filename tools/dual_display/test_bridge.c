#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#define VO_BRIDGE_TEST
#include "policy.h"
typedef unsigned char BYTE;typedef int32_t LONG;
typedef size_t SIZE_T;
#define IMAGE_DOS_SIGNATURE 0x5a4d
#define IMAGE_NT_SIGNATURE 0x4550
#define IMAGE_NT_OPTIONAL_HDR32_MAGIC 0x10b
typedef struct {unsigned e_magic;int e_lfanew;} IMAGE_DOS_HEADER;
typedef struct {unsigned Signature;struct {unsigned TimeDateStamp;}FileHeader;struct {unsigned Magic,SizeOfImage;}OptionalHeader;} IMAGE_NT_HEADERS;
typedef struct {uintptr_t base;unsigned stamp,size;uintptr_t signature,loop,mode,split,show;unsigned char bytes[32];} VoGameProfile;
static VoGameProfile vo_profiles[1];static union {uint64_t align;BYTE data[512];} memory;
static int enabled=1;static uintptr_t fail_address;
static void *GetCurrentProcess(void){return NULL;}
static int ReadProcessMemory(void *process,const void *address,void *out,size_t size,SIZE_T *got){(void)process;uintptr_t a=(uintptr_t)address,base=(uintptr_t)memory.data;if(a==fail_address||a<base||a+size>base+512){*got=0;return 0;}memcpy(out,address,size);*got=size;return 1;}
static void *GetModuleHandleW(void *x){(void)x;return memory.data;}
static unsigned GetEnvironmentVariableA(const char*x,char*out,unsigned n){(void)x;(void)n;out[0]=enabled?'1':'0';return 1;}
static LONG InterlockedExchange(volatile LONG*p,LONG n){LONG old=*p;*p=n;return old;}
static LONG InterlockedCompareExchange(volatile LONG*p,LONG n,LONG c){LONG old=*p;if(old==c)*p=n;return old;}
static LONG InterlockedIncrement(volatile LONG*p){return ++*p;}
#include "state_bridge.c"
static void reset(void){
 checked=0;unknown_count=0;profile=NULL;completed=VO_POLICY_UNKNOWN;fail_address=0;memset(&observation,0,sizeof observation);enabled=1;memset(memory.data,0,512);
 ((IMAGE_DOS_HEADER*)memory.data)->e_lfanew=64;((IMAGE_DOS_HEADER*)memory.data)->e_magic=IMAGE_DOS_SIGNATURE;
 IMAGE_NT_HEADERS *nt=(void*)(memory.data+64);nt->Signature=IMAGE_NT_SIGNATURE;nt->OptionalHeader.Magic=IMAGE_NT_OPTIONAL_HDR32_MAGIC;nt->FileHeader.TimeDateStamp=42;nt->OptionalHeader.SizeOfImage=512;
 vo_profiles[0]=(VoGameProfile){(uintptr_t)memory.data,42,512,(uintptr_t)(memory.data+100),(uintptr_t)(memory.data+200),(uintptr_t)(memory.data+204),(uintptr_t)(memory.data+208),(uintptr_t)(memory.data+212),{0}};
}
static void state(unsigned loop,unsigned mode,unsigned split,unsigned show){unsigned values[]={loop,mode,split,show};memcpy(memory.data+200,values,sizeof values);vo_capture_policy();}
int main(void){
 reset();state(0,1,0,0);assert(vo_completed_policy()==VO_PRIMARY_ONLY);
 state(1,4,1,1);assert(vo_completed_policy()==VO_LOCAL_VS_SHARED);
 state(1,4,1,0);assert(vo_completed_policy()==VO_LOCAL_VS_GAMEPLAY);
 state(1,4,1,99);assert(vo_completed_policy()==VO_POLICY_UNKNOWN&&vo_unknown_policy_count()==1&&vo_unknown_policy_value(3)==99);
 state(1,4,1,2);assert(vo_completed_policy()==VO_LOCAL_VS_SHARED);
 state(1,1,1,1);assert(vo_completed_policy()==VO_PRIMARY_ONLY);
 reset();memory.data[100]=1;state(1,4,1,0);assert(vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();vo_profiles[0].stamp=43;state(1,4,1,0);assert(vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();enabled=0;state(1,4,1,0);assert(!profile&&vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();assert(vo_completed_policy()==VO_POLICY_UNKNOWN&&observation.captures==0);
 state(0,0,0,0);assert(observation.status==SOURCE_UNINITIALIZED&&vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();fail_address=vo_profiles[0].mode;state(1,4,1,0);assert(observation.status==SOURCE_INVALID_READ&&observation.valid_mask==13&&vo_completed_policy()==VO_POLICY_UNKNOWN);
 fail_address=0;vo_capture_flip_policy();assert(vo_completed_policy()==VO_LOCAL_VS_GAMEPLAY&&observation.flips==1&&observation.status==SOURCE_VALID&&observation.valid_mask==15);
 for(unsigned i=0;i<100;i++)state(1,4,1,i%2);assert(observation.used==64&&observation.transitions>64);
 reset();fail_address=(uintptr_t)memory.data+64;vo_capture_flip_policy();assert(observation.status==SOURCE_INVALID_READ&&vo_completed_policy()==VO_POLICY_UNKNOWN);
 reset();vo_profiles[0].size=513;vo_capture_flip_policy();assert(observation.status==SOURCE_UNSUPPORTED);
 puts("PASS production bridge: identity/signature rejection, disabled gate, state transitions and unknown-state full-shared fallback, invalid reads, zero initialization, flip capture and bounded trace; host API doubles");
}
