"""Link production runtime and pages; drive their real message/input boundary."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
component=runpy.run_path(str(here/'test_pages.py'))
fixture=component['fixture'].replace('return !strcmp(s,"VonDisplayTransaction")?(void*)display_double:(void*)diagnostics_double;','return !strcmp(s,"VonDisplayTransaction")?(void*)display_double:!strcmp(s,"VonOverlayDiagnostics")?(void*)diagnostics_double:NULL;')
fixture=fixture.replace('int PostMessageW(HWND h,UINT m,WPARAM w,LPARAM l){(void)h;(void)m;(void)w;(void)l;return 1;}','static unsigned posted_command;\nint PostMessageW(HWND h,UINT m,WPARAM w,LPARAM l){assert(h==(void*)1&&m==WM_COMMAND&&!l);posted_command=(unsigned)w;return 1;}')
body=component['body'].replace('void vo_pages_begin(VoOverlay *s,const VoGame *g,HWND h){','static VoOverlay *observed;\nvoid vo_pages_begin(VoOverlay *s,const VoGame *g,HWND h){observed=s;')
platform=r'''
static unsigned keys[256],clock_ms;static int cursor=-1,painted;static HWND foreground_window=(void*)1;
int ShowCursor(int show){cursor+=show?1:-1;return cursor;}
int GetCursorInfo(CURSORINFO *i){i->flags=cursor>=0?CURSOR_SHOWING:0;return 1;}
DWORD GetTickCount(void){return clock_ms;}
int IsWindow(HWND h){return !!h;}int IsIconic(HWND h){(void)h;return 0;}
HWND GetForegroundWindow(void){return foreground_window;}
short GetAsyncKeyState(int k){return keys[k]?(short)0x8000:0;}
LONG InterlockedExchange(LONG*p,LONG v){LONG old=*p;*p=v;return old;}
LONG InterlockedCompareExchange(LONG*p,LONG v,LONG match){LONG old=*p;if(old==match)*p=v;return old;}
int vo_pause_begin(LPDIRECTDRAWSURFACE s,int on){(void)s;(void)on;return 1;}
int vo_pause_capture(LPDIRECTDRAWSURFACE s){(void)s;return 1;}
void vo_pause_end(void){}void vo_pause_clear(void){}
void vo_pause_restore_to(LPDIRECTDRAWSURFACE s){(void)s;}
int vo_attach(VoPaint*p,LPDIRECTDRAWSURFACE s){p->surface=s;p->visible=7;return 1;}
void vo_dispose(VoPaint*p){memset(p,0,sizeof *p);}
int vo_paint(VoPaint*p,const VoOverlay*s){(void)p;assert(s->state==VO_OPEN&&s->menu);painted++;return 1;}
int vo_hit_source(VoPaint*p,int x,int y){(void)p;(void)y;return x;}
int WINAPI VonOverlayStep(HWND,const VoGame*,UINT,UINT,WPARAM,LPARAM);
int WINAPI VonOverlayInput(DWORD,DWORD,void*,DWORD,DWORD);
static VoGame context;static LPDIRECTDRAWSURFACE primary=(void*)2,back=(void*)3;
static LONG devices[2]={4,5},movie,threshold=13080,mode2;
static unsigned char bindings[48];static int stops;
static void cdstop(void){stops++;}
static void event(unsigned m,unsigned w,int l){VonOverlayStep((void*)1,&context,0,m,w,l);}
static void tick(void){VonOverlayStep((void*)1,&context,2,0,0,0);}
static void esc(void){event(WM_KEYDOWN,VK_ESCAPE,0);event(WM_KEYUP,VK_ESCAPE,0);}
static void click(unsigned id){int found=-1;for(unsigned i=0;i<menu.count;i++)if(menu.rows[i].id==id&&menu.rows[i].enabled){found=(int)i;break;}assert(found>=0);event(WM_LBUTTONDOWN,0,found);event(WM_LBUTTONUP,0,found);tick();}
static void key(unsigned vk){tick();keys[vk]=1;tick();event(WM_KEYDOWN,vk,0);tick();keys[vk]=0;tick();event(WM_KEYUP,vk,0);tick();}
int main(void){
 context=(VoGame){0};context.size=sizeof context;context.primary=&primary;context.back=&back;context.inactive=&inactive;context.mode=&mode;context.submode=&submode;context.gamemode=&gamemode;context.movie=&movie;context.pause=pause_game;context.resume=resume_game;context.devices=devices;context.custom=bindings;context.padbinds=bindings;context.twinbinds=bindings;context.horibinds=bindings;context.threshold=&threshold;context.mode2=&mode2;context.cdstop=cdstop;
 for(int paused=0;paused<2;paused++){
  inactive=paused;esc();assert(observed->state==VO_OPEN&&observed->selected==6&&!strcmp(menu.title,"Virtual On EX"));
  click(10+CONTROLLERS);assert(page==CONTROLLERS);
  /* A complete queued tap between async polls was discarded by F03. */
  for(unsigned i=0;i<menu.count;i++)if(menu.rows[i].id==6000)observed->selected=i;
  unsigned original_profile=pending_profiles[0];
  keys[VK_RIGHT]=1;tick();keys[VK_RIGHT]=0;tick();assert(pending_profiles[0]==original_profile);
  event(WM_KEYDOWN,VK_RIGHT,0);event(WM_KEYUP,VK_RIGHT,0);
  assert(pending_profiles[0]!=original_profile&&devices[0]==(LONG)original_profile);
  event(WM_KEYDOWN,VK_LEFT,0);event(WM_KEYUP,VK_LEFT,0);assert(pending_profiles[0]==original_profile);
  /* Real runtime semantic boundary: P1 directions, P2 isolation, confirm list. */
  for(unsigned k=1;k<=8;k++)if(k!=3){
   XINPUT_STATE raw={0};unsigned native_bits=0;void *sample=k>=7?(void*)&native_bits:(void*)&raw;
   VonOverlayInput(0,k,sample,0,3);
   if(k>=7)native_bits=8;else raw.Gamepad.wButtons=8;
   VonOverlayInput(1,k,sample,0,3);assert(pending_profiles[0]==original_profile);
   VonOverlayInput(0,k,sample,0,3);assert(pending_profiles[0]!=original_profile);
   memset(&raw,0,sizeof raw);native_bits=0;VonOverlayInput(0,k,sample,0,3);
   if(k>=7)native_bits=4;else raw.Gamepad.wButtons=4;
   VonOverlayInput(0,k,sample,0,3);assert(pending_profiles[0]==original_profile);
   memset(&raw,0,sizeof raw);native_bits=0;VonOverlayInput(0,k,sample,0,3);
   if(k>=7)native_bits=1u<<12;else raw.Gamepad.wButtons=0x1000;
   VonOverlayInput(0,k,sample,0,3);assert(page==PROFILE_LIST);
   memset(&raw,0,sizeof raw);native_bits=0;VonOverlayInput(0,k,sample,0,3);click(CANCEL);
   for(unsigned i=0;i<menu.count;i++)if(menu.rows[i].id==6000)observed->selected=i;
  }
  click(6000);assert(page==PROFILE_LIST);click(9003);assert(pending_profiles[0]==5&&devices[0]==4);
  click(CANCEL);assert(page==ROOT&&devices[0]==4);click(10+CONTROLLERS);assert(pending_profiles[0]==4);
  click(6000);click(9003);click(SAVE);assert(devices[0]==5);click(10+CONTROLLERS);
  click(6000);click(9002);click(SAVE);assert(devices[0]==4);click(10+CONTROLLERS);
  capture_pending=1;
  for(unsigned i=0;i<menu.count;i++)if(menu.rows[i].id==6001)observed->selected=i;
  event(WM_KEYDOWN,VK_RETURN,0);event(WM_KEYUP,VK_RETURN,0);
  assert(page==ASSIGN&&vo_pages_capture_active());
  XINPUT_STATE held={0};held.Gamepad.wButtons=0x1011;unsigned selected=observed->selected;
  assert(VonOverlayInput(0,4,&held,0,3)==1);assert(page==ASSIGN&&observed->selected==selected);
  assert(VonOverlayInput(1,4,&held,0,3)==0);assert(page==ASSIGN);
  esc();assert(page==CONTROLLERS&&!capturing&&!vo_pages_capture_active());capture_pending=0;
  click(6011);assert(page==CONTROLLERS&&!capturing);
  capture_pending=1;click(6001);assert(page==ASSIGN);capture_pending=0;
  VonOverlayStep((void*)1,&context,1,0,0,0);assert(page==CONTROLLERS&&!capturing);

  click(6002);click(7000);assert(page==EDITOR&&dirty);esc();assert(page==CONFIRM);click(CANCEL);assert(page==EDITOR&&dirty);click(SAVE);assert(page==CONTROLLERS);esc();assert(page==ROOT);
  click(10+GAME);click(10+SOLO);click(2000);click(DEFAULTS);click(CANCEL);assert(page==GAME);esc();
  click(10+DISPLAY);click(DISPLAY_MODE);apply_fail=1;click(SAVE);assert(page==DISPLAY&&dirty);apply_fail=0;click(SAVE);assert(page==ROOT&&inactive==paused);
  click(10+GRAPHICS);click(GRAPH_RES);click(CANCEL);assert(page==ROOT&&inactive==paused);
  click(10+EXTRAS);click(10+DIAGNOSTICS);click(EXPORT);esc();esc();
  VonOverlayStep((void*)1,&context,paused?1:3,0,0,0);if(paused)VonOverlayStep((void*)1,&context,5,0,0,0);assert(painted);
  esc();assert(observed->state==VO_CLOSED&&inactive==paused);esc();assert(observed->state==VO_OPEN&&inactive==paused);
  key(VK_UP);assert(observed->selected==4); // skips nonselectable SESSION
  esc();assert(observed->state==VO_CLOSED&&inactive==paused);
 }
 inactive=1;esc();click(QUIT);assert(observed->confirm);event(WM_LBUTTONUP,0,1);assert(!posted_command);click(CONFIRM_YES);assert(posted_command==0x9c41&&observed->state==VO_CLOSED&&inactive==1);
 esc();click(10+GRAPHICS);click(GRAPH_RES);event(WM_KEYDOWN,0x74,0);assert(observed->state==VO_CLOSED&&!native.host&&!dirty);
 esc();click(10+DISPLAY);click(DISPLAY_MODE);foreground_window=(void*)9;tick();assert(observed->state==VO_CLOSED&&!display_open&&!dirty);foreground_window=(void*)1;
 esc();assert(observed->state==VO_OPEN);esc();assert(observed->state==VO_CLOSED);
 assert(begins==ends);puts("PASS linked production runtime/pages: default Resume, controller edits, F6 defaults, Display failure/retry, Graphics cancel, Diagnostics export, active/paused close/reopen, keyboard navigation, fresh Quit confirmation, F5/focus cleanup");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture+body+platform)
 subprocess.run(['clang','-DVO_OVERLAY_TEST','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(here),str(p/'test.c'),str(here/'runtime.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
