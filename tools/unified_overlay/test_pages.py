"""Execute production page routing with configuration-authority doubles.
Original executable procedures are tested separately in test_native_settings.py.
"""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=(here/'pages.c').read_text()
for header in ('pages.h','native_settings.h','controller_settings.h','../dual_display/settings_api.h'):
 body=body.replace(f'#include "{header}"','')
fixture=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "runtime.h"
#include "../dual_display/settings_api.h"
#define WM_COMMAND 273
#include <stdint.h>
typedef struct {void *host;unsigned category;int values[1200];} VoNativeSettings;
enum {VO_NATIVE_GRAPHICS,VO_NATIVE_1P,VO_NATIVE_2P,VO_NATIVE_GENERAL,VO_NATIVE_APPENDIX,VO_NATIVE_SCORES};
static int vo_controller_has_axes(const VoGame*g,unsigned p,unsigned k){(void)g;(void)p;return k==1||k==2||k==4||k==6;}
static int vo_controller_available(const VoGame*g){(void)g;return 1;}
typedef struct {unsigned player,kind,active;int values[12];} VoControllerSettings;
static int vo_controller_begin(VoControllerSettings*c,const VoGame*g,HWND h,unsigned p,unsigned k){(void)g;(void)h;c->active=1;c->player=p;c->kind=k;return 1;}
static void vo_controller_end(VoControllerSettings*c){memset(c,0,sizeof *c);}
static int vo_controller_count(VoControllerSettings*c,unsigned i){(void)c;(void)i;return 20;}
static int vo_controller_selected(VoControllerSettings*c,unsigned i){return c->values[i];}
static int vo_controller_choice(VoControllerSettings*c,unsigned i,unsigned v,char*b,unsigned n){(void)c;(void)i;snprintf(b,n,"Input %u",v);return 1;}
static int vo_controller_select(VoControllerSettings*c,unsigned i,unsigned v){c->values[i]=v;return 1;}
static int vo_controller_defaults(VoControllerSettings*c){memset(c->values,0,sizeof c->values);return 1;}
static int vo_controller_save(VoControllerSettings*c){(void)c;return 1;}
static int vo_controller_profile(const VoGame*g,unsigned p,unsigned k){g->devices[p]=k;return 1;}
static int vo_controller_status(unsigned p,unsigned k){(void)p;(void)k;return 1;}
static int vo_controller_deadzone(const VoGame*g,unsigned p,int v){(void)g;(void)p;return v<0?40:v;}
static int begins,commits,ends,clicks,radios,selections,apply_fail,applies,cancels;
static int saved[1200],level,exported;
static LONG inactive,mode=4,gamemode,submode=8;
static void pause_game(int x){(void)x;inactive=1;}
static void resume_game(void){inactive=0;}
static void vo_native_end(VoNativeSettings *n){if(n->host)ends++;memset(n,0,sizeof *n);}
static int vo_native_begin(VoNativeSettings *n,HWND h,const volatile LONG *m,unsigned c){(void)h;(void)m;begins++;n->host=(void*)1;n->category=c;memcpy(n->values,saved,sizeof saved);return 1;}
static int vo_native_check(VoNativeSettings *n,unsigned c){assert(c<1200);return n->values[c];}
static int vo_native_count(VoNativeSettings *n,unsigned c){(void)n;assert(c<1200);return 15;}
static int vo_native_selected(VoNativeSettings *n,unsigned c){assert(c<1200);return n->values[c];}
static int vo_native_choice(VoNativeSettings *n,unsigned c,unsigned choice,char *b,unsigned size){(void)n;(void)c;snprintf(b,size,"Choice %u",choice);return 1;}
static int vo_native_select(VoNativeSettings *n,unsigned c,unsigned choice){assert(c<1200);selections++;n->values[c]=choice;return 1;}
static int vo_native_click(VoNativeSettings *n,unsigned c){assert(c<1200);clicks++;n->values[c]^=1;return 1;}
static int vo_native_radio(VoNativeSettings *n,unsigned first,unsigned last,unsigned c){radios++;assert(first<=c&&c<=last&&last<1200);for(unsigned i=first;i<=last;i++)n->values[i]=i==c;return 1;}
static int vo_native_defaults(VoNativeSettings *n){memset(n->values,0,sizeof n->values);return 1;}
static int vo_native_score(VoNativeSettings*n,unsigned g,unsigned r,char*b,unsigned z){(void)n;snprintf(b,z,"Score %u %u",g,r);return 1;}
static int vo_native_commit(VoNativeSettings *n){commits++;memcpy(saved,n->values,sizeof saved);if(n->category==VO_NATIVE_GRAPHICS)resume_game();return 1;}
static int display_double(unsigned op,int value,VoDisplaySnapshot *d){
 if(op==VO_DISPLAY_BEGIN){d->count=2;d->mode=0;d->aspect=1;d->primary=0;d->secondary=1;strcpy(d->names[0],"Monitor A");strcpy(d->names[1],"Monitor B");return 1;}
 if(op==VO_DISPLAY_CANCEL){cancels++;return 1;}
 if(op==VO_DISPLAY_APPLY){if(apply_fail)return 0;applies++;d->dirty=0;return 1;}
 if(op==VO_DISPLAY_MODE)d->mode=value;
 if(op==VO_DISPLAY_ASPECT)d->aspect=value;
 if(op==VO_DISPLAY_PRIMARY)d->primary=value;
 if(op==VO_DISPLAY_SECONDARY)d->secondary=value;
 d->dirty=1;return 1;
}
static int diagnostics_double(HWND h,unsigned op,int value){(void)h;if(op==0)return level;if(op==1){level=value;return 1;}if(op==2){exported++;return 1;}return 0;}
static int capture_result,capturing,capture_pending;
static int input_begin_double(DWORD p,DWORD k,int capture,int threshold){(void)p;(void)k;(void)threshold;capturing=1;capture_result=capture?0xe3:1;return 1;}
static int input_poll_double(void){if(capture_pending)return 0;if(capturing){capturing=0;return capture_result;}return -1;}
static void input_cancel_double(void){capturing=0;}
static int input_identity_double(DWORD p,DWORD k){(void)k;return p;}
static int input_loaded,input_loads;
HMODULE GetModuleHandleW(const wchar_t *s){if(!wcscmp(s,L"voinputux.dll"))return input_loaded?(void*)1:NULL;return (void*)1;}
HMODULE LoadLibraryW(const wchar_t *s){assert(!wcscmp(s,L"voinputux.dll"));input_loaded=1;input_loads++;return (void*)1;}
void *GetProcAddress(HMODULE h,const char *s){(void)h;return !strcmp(s,"VonDisplayTransaction")?(void*)display_double:!strcmp(s,"VonOverlayDiagnostics")?(void*)diagnostics_double:!strcmp(s,"VonInputBegin")?(void*)input_begin_double:!strcmp(s,"VonInputPoll")?(void*)input_poll_double:!strcmp(s,"VonInputCancel")?(void*)input_cancel_double:!strcmp(s,"VonInputIdentity")?(void*)input_identity_double:NULL;}
int PostMessageW(HWND h,UINT m,WPARAM w,LPARAM l){(void)h;(void)m;(void)w;(void)l;return 1;}
'''
main=r'''
static void activate(VoOverlay *s,unsigned id){for(unsigned i=0;i<menu.count;i++)if(menu.rows[i].id==id&&menu.rows[i].enabled){s->selected=i;vo_overlay_event(s,VO_ACCEPT);return;}assert(!"missing selectable row");}
static void begin(VoOverlay *s,VoGame *g){vo_overlay_init(s);vo_overlay_pause_result(s,0,1);s->exit_allowed=1;vo_pages_begin(s,g,(void*)1);assert(s->selected==6&&input_loaded&&input_loads==1);}
int main(void){
 LONG devices[2]={4,5};VoGame g={0};g.devices=devices;g.inactive=&inactive;g.mode=&mode;g.gamemode=&gamemode;g.submode=&submode;LONG threshold[2]={13080,13080};g.threshold=threshold;g.pause=pause_game;g.resume=resume_game;
 VoOverlay s;begin(&s,&g);
 activate(&s,10+CONTROLLERS);assert(menu.count>10);
 activate(&s,6001);assert(page==ASSIGN&&capturing);activate(&s,CANCEL);assert(page==CONTROLLERS&&!capturing);
 activate(&s,6011);assert(page==ASSIGN);vo_pages_refresh(&s);assert(page==CONTROLLERS&&!capturing);
 activate(&s,6002);assert(page==EDITOR&&controller.player==0&&controller.kind==4);
 activate(&s,7000);assert(page==CAPTURE&&capturing);vo_pages_refresh(&s);assert(dirty&&controller.values[0]==4);
 activate(&s,BACK);assert(page==CONFIRM);activate(&s,CANCEL);assert(page==EDITOR&&dirty);
 activate(&s,DEFAULTS);assert(!controller.values[0]&&dirty);activate(&s,SAVE);assert(page==CONTROLLERS&&!controller.active);
 activate(&s,6002);activate(&s,7006);vo_pages_refresh(&s);activate(&s,CANCEL);assert(page==CONTROLLERS&&!dirty);
 activate(&s,BACK);
 activate(&s,10+GAME);activate(&s,10+GENERAL);
 activate(&s,2000+1074);assert(clicks==1&&selections==0&&dirty&&native.values[1074]==1&&!saved[1074]);
 activate(&s,BACK);assert(page==CONFIRM&&s.selected==0&&s.confirm&&!s.keyboard_ready&&!s.controller_ready);
 activate(&s,CANCEL);assert(page==GENERAL&&dirty);
 activate(&s,SAVE);assert(page==GAME&&saved[1074]==1&&commits==1);
 activate(&s,10+APPENDIX);activate(&s,5000);assert(radios==1&&native.values[1078]&&!saved[1078]);
 activate(&s,CANCEL);assert(page==GAME&&!saved[1078]);
 activate(&s,10+SOLO);activate(&s,2000);assert(selections==1&&dirty);activate(&s,DEFAULTS);assert(dirty);activate(&s,BACK);activate(&s,CONFIRM_YES);assert(page==GAME&&!dirty);
 activate(&s,BACK);activate(&s,10+DISPLAY);activate(&s,ADVANCED);activate(&s,SPLIT);assert(dirty);activate(&s,BACK);assert(page==DISPLAY&&dirty);
 activate(&s,DISPLAY_MODE);display.dirty=0;assert(dirty);
 apply_fail=1;int before=commits;activate(&s,SAVE);assert(page==DISPLAY&&dirty&&commits==before&&!applies&&display_open);
 apply_fail=0;activate(&s,SAVE);assert(page==ROOT&&applies==1&&commits==before+1&&!inactive&&!display_open);
 activate(&s,10+GRAPHICS);activate(&s,GRAPH_RES);activate(&s,ADVANCED);activate(&s,GRAPH_TEX1);assert(dirty);activate(&s,BACK);activate(&s,CANCEL);assert(page==ROOT);
 activate(&s,10+EXTRAS);activate(&s,SCORES);assert(page==SCORE_PAGE&&s.selected==1);vo_overlay_event(&s,VO_DOWN);assert(s.selected==2);activate(&s,CLEAR_SCORES);assert(page==CONFIRM);activate(&s,CONFIRM_YES);assert(page==SCORE_PAGE&&dirty);activate(&s,CANCEL);assert(page==EXTRAS);activate(&s,10+DIAGNOSTICS);activate(&s,LOG_LEVEL);assert(level==1&&!exported);activate(&s,EXPORT);assert(exported==1);activate(&s,BACK);activate(&s,BACK);
 unsigned root_selection=s.selected;s.selected=menu.count-1;
 vo_overlay_event(&s,VO_RIGHT);assert(page==ROOT&&!command);s.selected=root_selection;
 activate(&s,QUIT);assert(page==CONFIRM&&!command);
 vo_overlay_event(&s,VO_RIGHT);assert(page==CONFIRM&&s.selected==1&&!command);
 vo_overlay_event(&s,VO_LEFT);assert(page==CONFIRM&&s.selected==0&&!command);activate(&s,CANCEL);assert(!command&&page==ROOT);activate(&s,QUIT);activate(&s,CONFIRM_YES);assert(s.state==VO_DRAINING&&vo_pages_command()==0x9c41&&!vo_pages_command());
 vo_pages_end();assert(begins==ends);
 puts("PASS production pages: General/Appendix dispatch, combo edits, defaults, Back confirmation, Cancel discard, Display failed Apply retention, split dirty preservation, Graphics staging, explicit diagnostics export, confirmed original Quit command");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'pages-test.c').write_text(fixture+body+main)
 subprocess.run(['clang','-DVO_OVERLAY_TEST','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(here),str(p/'pages-test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
