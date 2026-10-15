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
static unsigned char *used_keys(unsigned j){return (unsigned char*)(uintptr_t)(j?0xbf1598:0xbf6b20);}
static unsigned offset(unsigned kind){return kind==0?32:kind==3?56:8;}
static unsigned control(VoControllerSettings *s,unsigned slot){
 if(slot>=12)return 0;
 if(s->kind==4){static const unsigned order[]={0,1,2,3,8,10,4,5,6,7,9,11};return 100+order[slot];}
 const Addresses *a=&addresses[s->edition];
 const unsigned *ids=(const unsigned*)(s->kind==0?a->ids_real:a->ids_pad);
 if(s->kind==0){static const unsigned order[]={0,1,2,3,4,5,6,7,8,9,10,5};return ids[order[slot]];}
 static const unsigned order[]={0,1,2,3,4,5,6,7,11,8,9,10};return ids[order[slot]];
}
static int method(VoControllerSettings *s,uintptr_t address,unsigned command){
 typedef int (__thiscall *Method)(void*,HWND,unsigned,unsigned);
 return ((Method)address)(s->object,s->host,command,0);
}
static int initialize(VoControllerSettings *s){
 const Addresses *a=&addresses[s->edition];
 for(unsigned i=0;i<12;i++)SendDlgItemMessageA(s->host,control(s,i),CB_RESETCONTENT,0,0);
 if(s->kind==4){
  if(!((int(__cdecl*)(void))a->custom_resolve)())return 0;
  ((DLGPROC)a->custom_proc)(s->host,WM_INITDIALOG,0,s->player);
 }else method(s,s->kind==0?a->init_real:a->init_pad,0);
 return 1;
}
static int open_controls(VoControllerSettings *s){
 s->host=CreateWindowExA(0,"STATIC","",WS_POPUP,0,0,1,1,s->owner,NULL,GetModuleHandleA(NULL),NULL);
 if(!s->host)return 0;
 for(unsigned i=0;i<12;i++){
  unsigned id=control(s,i);if(GetDlgItem(s->host,id))continue;
  if(!CreateWindowExA(0,"COMBOBOX","",WS_CHILD|CBS_DROPDOWNLIST,0,0,1,1,s->host,(HMENU)(uintptr_t)id,GetModuleHandleA(NULL),NULL))return 0;
 }
 if(!initialize(s))return 0;
 return 1;
}
void vo_controller_end(VoControllerSettings *s){
 if(!s)return;
 if(s->active){const Addresses *a=&addresses[s->edition];memcpy((void*)a->blocks,s->blocks,224);*(unsigned*)a->player=s->previous_player;
  memcpy(used_keys(s->edition),s->used_keys,138);
  memcpy((void*)a->custom_pending,s->custom_pending,24);*(unsigned*)a->custom_player=s->custom_player;}
 if(s->host)DestroyWindow(s->host);memset(s,0,sizeof *s);
}
int vo_controller_begin(VoControllerSettings *s,const VoGame *g,HWND owner,unsigned player,unsigned kind){
 if(!s||!vo_controller_available(g)||s->active||player>1||(kind!=0&&kind!=1&&kind!=3&&kind!=4))return 0;
 int j=edition(g);if(j<0)return 0;
 s->game=g;s->owner=owner;s->player=player;s->kind=kind;s->edition=j;
 const Addresses *a=&addresses[j];memcpy(s->blocks,(void*)a->blocks,224);s->previous_player=*(unsigned*)a->player;memcpy(s->used_keys,used_keys(j),138);memset(used_keys(j),0,138);
 memcpy(s->custom_pending,(void*)a->custom_pending,24);s->custom_player=*(unsigned*)a->custom_player;s->active=1;
 *(unsigned*)a->player=player;*(unsigned*)(a->blocks+player*112)=kind;
 if(!open_controls(s))goto fail;
 return 1;
 fail:vo_controller_end(s);return 0;
}
int vo_controller_count(VoControllerSettings *s,unsigned slot){return s->active?(int)SendDlgItemMessageA(s->host,control(s,slot),CB_GETCOUNT,0,0):0;}
int vo_controller_selected(VoControllerSettings *s,unsigned slot){return s->active?(int)SendDlgItemMessageA(s->host,control(s,slot),CB_GETCURSEL,0,0):-1;}
int vo_controller_choice(VoControllerSettings *s,unsigned slot,unsigned choice,char *text,unsigned size){
 if(!text||!size||choice>=(unsigned)vo_controller_count(s,slot))return 0;
 int n=(int)SendDlgItemMessageA(s->host,control(s,slot),CB_GETLBTEXTLEN,choice,0);
 if(n<0||(unsigned)n>=size)return 0;
 return SendDlgItemMessageA(s->host,control(s,slot),CB_GETLBTEXT,choice,(LPARAM)text)==n;
}
int vo_controller_select(VoControllerSettings *s,unsigned slot,unsigned choice){
 if(choice>=(unsigned)vo_controller_count(s,slot))return 0;
 return SendDlgItemMessageA(s->host,control(s,slot),CB_SETCURSEL,choice,0)!=CB_ERR;
}
static FARPROC helper(const char *name){HMODULE h=GetModuleHandleW(L"voinputux.dll");return h?GetProcAddress(h,name):NULL;}
int vo_controller_assign(HWND owner,unsigned p,unsigned kind){
 typedef int(WINAPI *Select)(HWND,DWORD,DWORD);Select f=(Select)helper("VonSelectController");return f?f(owner,p,kind):0;
}
int vo_controller_status(unsigned p,unsigned kind){
 if(kind==0||kind==3)return 1;
 typedef int(WINAPI *Status)(DWORD,DWORD);Status f=(Status)helper("VonOverlayControllerStatus");return f?f(p,kind):-1;
}
int vo_controller_capture(VoControllerSettings *s,unsigned slot){
 if(!s->active||(s->kind!=1&&s->kind!=4))return 0;
 typedef int(WINAPI *Capture)(HWND,DWORD,DWORD,int);Capture f=(Capture)helper("VonCaptureInput");
 if(!f)return 0;
 int paused=*s->game->inactive!=0;
 if(!paused)s->game->pause(0);
 int value=f(s->owner,s->player,s->kind,s->game->threshold[s->player]);
 if(paused){if(!*s->game->inactive)s->game->pause(0);}else s->game->resume();
 if(value<0xe0||value>=0xf4)return 0;
 return vo_controller_select(s,slot,(unsigned)(value-0xe0+(s->kind==4)));
}
int vo_controller_defaults(VoControllerSettings *s){
 if(!s->active)return 0;
 const Addresses *a=&addresses[s->edition];
 if(s->kind==4){((DLGPROC)a->custom_proc)(s->host,WM_COMMAND,3,0);return 1;}
 uintptr_t defaults=s->kind==0?a->real_defaults:s->kind==1?a->pad_defaults:a->simple_defaults;
 memcpy((void*)(a->blocks+s->player*112+offset(s->kind)),(void*)(defaults+s->player*24),24);
 return initialize(s);
}
static int line(const Addresses *a,const char *key,const char *value){return ((int(__cdecl*)(const char*,const char*))a->writer)(key,value);}
static int binding_line(const Addresses *a,unsigned p,const char *name,const unsigned char *data){
 char key[40],value[49];snprintf(key,sizeof key,"%uP %s",p+1,name);
 for(unsigned i=0;i<24;i++)snprintf(value+i*2,3,"%02x",data[i]);
 return line(a,key,value);
}
/* Re-run the original keyboard validators in their normal P1 then P2 order.
 * Their used-key bitmap is modal scratch, not saved configuration. This also
 * prevents an unsuccessful file write from making a retry look like a duplicate. */
static int validate_keyboards(VoControllerSettings *s){
 const Addresses *a=&addresses[s->edition];unsigned char blocks[224];memcpy(blocks,(void*)a->blocks,224);
 memset(used_keys(s->edition),0,138);int ok=1;
 for(unsigned p=0;p<2&&ok;p++){
  unsigned kind=p==s->player?s->kind:(unsigned)s->game->devices[p];
  if(kind!=0&&kind!=3)continue;
  VoControllerSettings t={0};t.game=s->game;t.owner=s->owner;t.edition=s->edition;t.player=p;t.kind=kind;
  *(unsigned*)a->player=p;*(unsigned*)(a->blocks+p*112)=kind;
  if(!open_controls(&t))ok=0;
  else{method(&t,kind==0?a->command_real:a->command_pad,kind==0?1017:1022);ok=*(HWND*)(t.object+12)==NULL;}
  if(t.host)DestroyWindow(t.host);
 }
 memcpy((void*)a->blocks,blocks,224);*(unsigned*)a->player=s->player;
 memset(used_keys(s->edition),0,138);return ok;
}
int vo_controller_save(VoControllerSettings *s){
 if(!s->active)return 0;
 const Addresses *a=&addresses[s->edition];unsigned char values[24],live[24];
 if(s->kind!=4){
  memset(used_keys(s->edition),0,138);
  *(HWND*)(s->object+12)=s->host;
  method(s,s->kind==0?a->command_real:a->command_pad,s->kind==0?1017:1022);
  if(*(HWND*)(s->object+12))return 0; /* original validator rejected */
  memcpy(values,(void*)(a->blocks+s->player*112+offset(s->kind)),24);
  if((s->kind==0||s->kind==3)&&!validate_keyboards(s))return 0;
 }else{
  /* Native Custom OK owns its None/input conversion and serializer. Restore
   * live bindings before publishing the staged file, even on failure. */
  memcpy(live,s->game->custom+s->player*24,24);
 }
 VoIniTransaction t;if(!vo_ini_begin(&t,s->edition,"Device Settings"))return 0;
 int ok;
 if(s->kind==4){
  ((DLGPROC)a->custom_proc)(s->host,WM_COMMAND,1,0);
  memcpy(values,s->game->custom+s->player*24,24);memcpy(s->game->custom+s->player*24,live,24);
  /* Repeat through the same writer to observe its result (native Save is void). */
  ok=binding_line(a,s->player,"Custom Assign",values);
 }else{
  ok=binding_line(a,s->player,s->kind==3?"Simple Assign":"Keyboard Assign",values);
  if(ok&&s->kind==3)ok=binding_line(a,s->player,"Keyboard Assign",(void*)(a->blocks+s->player*112+8));
 }
 if(!vo_ini_end(&t,ok))return 0;
 unsigned char *destination=s->kind==4?s->game->custom+s->player*24:s->kind==0?(unsigned char*)(uintptr_t)(s->edition?0x364c140:0x3651440)+s->player*24:(unsigned char*)s->game->padbinds+s->player*24;
 memcpy(destination,values,24);
 /* Keep the original saved block coherent after releasing modal scratch. */
 if(s->kind!=4)memcpy(s->blocks+s->player*112+offset(s->kind),values,24);
 return 1;
}
int vo_controller_profile(const VoGame *g,unsigned p,unsigned kind){
 int j=edition(g);if(j<0||!vo_controller_available(g)||p>1||kind>8)return 0;
 const Addresses *a=&addresses[j];VoIniTransaction t;if(!vo_ini_begin(&t,j,"Device Settings"))return 0;
 char key[32],value[32];snprintf(key,sizeof key,"%uP Device No.",p+1);
 unsigned existing=*(unsigned*)(a->device_config+p*4);snprintf(value,sizeof value,"0x%08x",(kind<<16)|(existing&65535));
 int ok=line(a,key,value);if(!vo_ini_end(&t,ok))return 0;
 *(unsigned*)(a->blocks+p*112)=kind;g->devices[p]=kind;*(unsigned short*)a->padidx=0;
 if(kind==1||kind==3)memcpy((void*)(g->padbinds+p*24),(void*)(a->blocks+p*112+offset(kind)),24);
 return 1;
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
