#include "controller_settings.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "ini_transaction.h"
/* Original addresses are checked against both executable editions and the
 * patcher's linked symbols by the controller adapter regression. */
typedef struct {uintptr_t blocks,player,init_real,init_pad,command_real,command_pad,ids_real,ids_pad,real_defaults,pad_defaults,simple_defaults,custom_defaults,custom_resolve,custom_proc,custom_pending,custom_player,padidx,digits,seed,writer,device_config;} Addresses;
static const Addresses addresses[2]={
 {0xbf6838,0xbf6bac,0x497560,0x497ba8,0x4976dd,0x497d28,0x66d5d0,0x66d630,0x66d5a0,0x66d600,0x36b66e0,0x36b5920,0x36b6992,0x36b6a05,0x36b6d18,0x36b6d30,0x365cb64,0x365cb94,0x36b5e71,0x5b1833,0x6536c0},
 {0xbf1730,0xbf1590,0x4960bf,0x496705,0x49623c,0x496885,0x669558,0x6695b8,0x669528,0x669588,0x36b06e0,0x36af920,0x36b0992,0x36b0a05,0x36b0d18,0x36b0d30,0x36577c4,0x36577f4,0x36afe71,0x5ac4f3,0x64f6c0}
};
static int edition(const VoGame *g){return (uintptr_t)g->mode==0x1ae3594?0:(uintptr_t)g->mode==0x1adcdf0?1:-1;}
int vo_controller_available(const VoGame *g){
 int j=edition(g);if(j<0)return 0;
 const Addresses *a=&addresses[j];MEMORY_BASIC_INFORMATION m;
 if(!VirtualQuery((void*)a->custom_proc,&m,sizeof m)||m.State!=MEM_COMMIT||(m.Protect&(PAGE_NOACCESS|PAGE_GUARD)))return 0;
 if(a->custom_player+4>(uintptr_t)m.BaseAddress+m.RegionSize)return 0;
 static const unsigned char prefix[]={0x55,0x89,0xe5,0x53,0x56,0x57,0x8b,0x5d,0x08};
 return !memcmp((void*)a->custom_proc,prefix,sizeof prefix);
}
static unsigned offset(unsigned kind){return kind==0?32:kind==3?56:8;}
static unsigned slot_index(unsigned kind,unsigned slot){
 static const unsigned custom[]={0,1,2,3,8,10,4,5,6,7,9,11};
 static const unsigned real[]={0,1,2,3,4,5,6,7,8,9,10,5};
 static const unsigned pad[]={0,1,2,3,4,5,6,7,11,8,9,10};
 return kind==4?custom[slot]:kind==0?real[slot]:pad[slot];
}
/* The original tables define both labels and encoded bindings. */
static unsigned key_code(unsigned j,unsigned choice){
 uintptr_t letters=j?0x6694c8:0x66d540,numbers=j?0x6694e8:0x66d560,keys=j?0x6693c4:0x66d43c;
 return *(unsigned char*)(choice<26?letters+choice:choice<36?numbers+choice-26:keys+(choice-36)*8);
}
static unsigned code(VoControllerSettings *s,unsigned choice){return s->kind==4?(choice?0xdf+choice:0):s->kind==1?0xe0+choice:key_code(s->edition,choice);}
void vo_controller_end(VoControllerSettings *s){if(s)memset(s,0,sizeof *s);}
int vo_controller_begin(VoControllerSettings *s,const VoGame *g,HWND owner,unsigned player,unsigned kind){
 if(!s||s->active||!vo_controller_available(g)||player>1||(kind!=0&&kind!=1&&kind!=3&&kind!=4))return 0;
 s->game=g;s->owner=owner;s->player=player;s->kind=kind;s->edition=edition(g);s->active=1;
 const Addresses *a=&addresses[s->edition];
 memcpy(s->pending,kind==4?g->custom+player*24:(void*)(a->blocks+player*112+offset(kind)),24);return 1;
}
int vo_controller_count(VoControllerSettings *s,unsigned slot){return s->active&&slot<12?(s->kind==4?21:s->kind==1?20:69):0;}
int vo_controller_selected(VoControllerSettings *s,unsigned slot){
 unsigned count=vo_controller_count(s,slot);if(!count)return -1;
 unsigned c=s->pending[slot_index(s->kind,slot)*2];
 for(unsigned i=0;i<count;i++)if(code(s,i)==c)return i;return -1;
}
int vo_controller_choice(VoControllerSettings *s,unsigned slot,unsigned choice,char *text,unsigned size){
 if(!text||!size||choice>=(unsigned)vo_controller_count(s,slot))return 0;
 if(s->kind==4&&!choice){snprintf(text,size,"None");return 1;}
 if(s->kind==1||s->kind==4){uintptr_t list=s->edition?0x36b04e0:0x36b64e0;snprintf(text,size,"%s",*(const char**)(list+8*(choice-(s->kind==4))));}
 else if(choice<36)snprintf(text,size,"%c",choice<26?'A'+choice:'0'+choice-26);
 else {uintptr_t list=s->edition?0x6693c0:0x66d438;snprintf(text,size,"%s",*(const char**)(list+8*(choice-36)));}
 return 1;
}
int vo_controller_select(VoControllerSettings *s,unsigned slot,unsigned choice){
 if(choice>=(unsigned)vo_controller_count(s,slot))return 0;
 unsigned i=slot_index(s->kind,slot)*2;s->pending[i]=code(s,choice);s->pending[i+1]=0;return 1;
}
static FARPROC helper(const char *name){HMODULE h=GetModuleHandleW(L"voinputux.dll");return h?GetProcAddress(h,name):NULL;}
int vo_controller_status(unsigned p,unsigned kind){
 if(kind==0||kind==3)return 1;
 typedef int(WINAPI *Status)(DWORD,DWORD);Status f=(Status)helper("VonOverlayControllerStatus");return f?f(p,kind):-1;
}
int vo_controller_defaults(VoControllerSettings *s){
 if(!s->active)return 0;const Addresses *a=&addresses[s->edition];
 uintptr_t defaults=s->kind==4?a->custom_defaults:s->kind==0?a->real_defaults:s->kind==1?a->pad_defaults:a->simple_defaults;
 memcpy(s->pending,(void*)(defaults+(s->kind==4?0:s->player*24)),24);return 1;
}
static int line(const Addresses *a,const char *key,const char *value){return ((int(__cdecl*)(const char*,const char*))a->writer)(key,value);}
static int binding_line(const Addresses *a,unsigned p,const char *name,const unsigned char *data){
 char key[40],value[49];snprintf(key,sizeof key,"%uP %s",p+1,name);
 for(unsigned i=0;i<24;i++)snprintf(value+i*2,3,"%02x",data[i]);
 return line(a,key,value);
}
/* Same original slot uniqueness rule, using the original encoded key table.
 * Real has eleven logical slots; its two Dash rows address one slot. Custom
 * intentionally permits repeated inputs and None. Original Simple does not
 * cross-check the other keyboard; Real P2 does (kbpage.asm). */
static int validate(VoControllerSettings *s){
 if(s->kind==4)return 1;
 unsigned n=s->kind==0?11:12;unsigned char used[256]={0};
 for(unsigned i=0;i<n;i++){unsigned k=s->pending[2*i];if(used[k])return 0;used[k]=1;}
 if(s->kind==0&&s->player==1&&(s->game->devices[0]==0||s->game->devices[0]==3)){
  const Addresses *a=&addresses[s->edition];const unsigned char *other=(void*)(a->blocks+offset(s->game->devices[0]));
  for(unsigned i=0;i<(s->game->devices[0]==0?11u:12u);i++)if(used[other[2*i]])return 0;
 }
 return 1;
}
int vo_controller_save(VoControllerSettings *s){
 if(!s->active||!validate(s))return 0;
 const Addresses *a=&addresses[s->edition];VoIniTransaction t;if(!vo_ini_begin(&t,s->edition,"Device Settings"))return 0;
 int ok=binding_line(a,s->player,s->kind==4?"Custom Assign":s->kind==3?"Simple Assign":"Keyboard Assign",s->pending);
 if(ok&&s->kind==3)ok=binding_line(a,s->player,"Keyboard Assign",(void*)(a->blocks+s->player*112+8));
 if(!vo_ini_end(&t,ok))return 0;
 unsigned char *destination=s->kind==4?s->game->custom+s->player*24:s->kind==0?(unsigned char*)(uintptr_t)(s->edition?0x364c140:0x3651440)+s->player*24:(unsigned char*)s->game->padbinds+s->player*24;
 memcpy(destination,s->pending,24);
 if(s->kind!=4)memcpy((void*)(a->blocks+s->player*112+offset(s->kind)),s->pending,24);
 return 1;
}
/* Read the installed F7 display list and its position-to-device mapping.
 * These linked addresses are pinned against both patcher editions by tests. */
int vo_controller_profile_count(const VoGame *g){
 int j=edition(g);if(j<0||!vo_controller_available(g))return 0;
 const char *const *names=(void*)(uintptr_t)(j?0x36b14e0:0x36b74e0);
 unsigned n=0;while(n<16&&names[n])n++;return n<16?(int)n:0;
}
int vo_controller_profile_choice(const VoGame *g,unsigned index,char *text,unsigned size){
 int n=vo_controller_profile_count(g);if(index>=(unsigned)n)return -1;
 int j=edition(g);const char *const *names=(void*)(uintptr_t)(j?0x36b14e0:0x36b74e0);
 const unsigned char *ids=(void*)(uintptr_t)(j?0x36aff59:0x36b5f59);
 if(text&&size)snprintf(text,size,"%s",names[index]);return ids[index];
}
int vo_controller_profiles_save(const VoGame *g,const unsigned *kinds){
 int j=edition(g),n=vo_controller_profile_count(g);if(j<0||!kinds||!n)return 0;
 for(unsigned p=0;p<2;p++){int valid=0;for(int i=0;i<n;i++)if(vo_controller_profile_choice(g,i,NULL,0)==(int)kinds[p])valid=1;if(!valid)return 0;}
 const Addresses *a=&addresses[j];VoIniTransaction t;if(!vo_ini_begin(&t,j,"Device Settings"))return 0;
 int ok=1;for(unsigned p=0;p<2;p++){
  char key[32],value[32];snprintf(key,sizeof key,"%uP Device No.",p+1);
  unsigned existing=*(unsigned*)(a->device_config+p*4);snprintf(value,sizeof value,"0x%08x",(kinds[p]<<16)|(existing&65535));
  if(!line(a,key,value))ok=0;
 }
 if(!vo_ini_end(&t,ok))return 0;
 for(unsigned p=0;p<2;p++){
  unsigned kind=kinds[p];*(unsigned*)(a->blocks+p*112)=kind;g->devices[p]=kind;
  if(kind==1||kind==3)memcpy((void*)(g->padbinds+p*24),(void*)(a->blocks+p*112+offset(kind)),24);
 }
 *(unsigned short*)a->padidx=0;return 1;
}
int vo_controller_profile(const VoGame *g,unsigned p,unsigned kind){
 if(p>1)return 0;unsigned kinds[2]={g->devices[0],g->devices[1]};kinds[p]=kind;
 return vo_controller_profiles_save(g,kinds);
}
int vo_controller_deadzone(const VoGame *g,unsigned p,int value){
 int j=edition(g);if(j<0||!vo_controller_available(g)||p>1)return -1;
 const Addresses *a=&addresses[j];unsigned char *digits=(unsigned char*)(a->digits+p*4);
 if(value<0)return digits[3];if(value<5||value>95)return -1;
 VoIniTransaction t;if(!vo_ini_begin(&t,j,"Device Settings"))return -1;
 char key[32],text[3];snprintf(key,sizeof key,"%uP Deadzone",p+1);snprintf(text,sizeof text,"%02d",value);
 int ok=line(a,key,text);if(!vo_ini_end(&t,ok))return -1;
 /* Invoke the original F11 seed: ECX percent, EBX player. */
 __asm__ volatile("push %%ebx\n\tmov %1,%%ebx\n\tcall *%2\n\tpop %%ebx" : : "c"(value),"S"(p),"d"(a->seed) : "eax","memory","cc");
 return value;
}

/* Only real XInput axes use DZTHR. Native HID profiles are already digital.
 * A configurable profile with no axis bindings has no adjustable stick range. */
int vo_controller_has_axes(const VoGame *g,unsigned p,unsigned kind){
 if(!g||p>1||(kind!=1&&kind!=2&&kind!=4&&kind!=6))return 0;
 const unsigned char *binds=kind==1?g->padbinds:kind==4?g->custom:kind==2?g->twinbinds:g->horibinds;
 if(!binds)return 0;
 if(kind==1&&(unsigned)g->devices[p]!=kind){int j=edition(g);if(j<0)return 0;binds=(void*)(addresses[j].blocks+p*112+offset(kind));}
 else if(kind==1||kind==4)binds+=p*24;
 for(unsigned i=0;i<12;i++)if(binds[i*2]>=0xe8&&binds[i*2]<=0xef)return 1;
 return 0;
}
