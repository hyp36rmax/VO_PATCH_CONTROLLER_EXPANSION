#define VO_OVERLAY_TEST
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "runtime.c"
void vo_pages_begin(VoOverlay*s,const VoGame*g,HWND h){(void)s;(void)g;(void)h;}
void vo_pages_end(void){}
int vo_pages_capture_active(void){return 0;}
void vo_pages_refresh(VoOverlay*s){(void)s;}
unsigned vo_pages_command(void){return 0;}
static int cursor_count=-1;
int ShowCursor(int show){cursor_count+=show?1:-1;return cursor_count;}
int GetCursorInfo(CURSORINFO *info){info->flags=cursor_count>=0?CURSOR_SHOWING:0;return 1;}
static DWORD now;static HWND foreground_window=(void*)1;static unsigned keys[256];
static int pause_ok=1,attach_ok=1,paint_ok=1,pauses,resumes,posted,draws;
static LONG mode2;static int stops;static void cdstop(void){stops++;}
static LONG inactive,mode=4,submode=9,gamemode,movie,threshold=8000,devices[2]={4,4};
static LPDIRECTDRAWSURFACE primary=(void*)2,back=(void*)3;
static unsigned char binds[8]={0xf0,0,0xf1,0,0xf2,0,0xf3,0};
static void pause_game(int n){assert(!n);pauses++;if(pause_ok)inactive=1;}
static void resume_game(void){resumes++;inactive=0;}
static int allowed(void){return 1;}static void frame(void){}
static VoGame context={sizeof(VoGame),&primary,&back,&inactive,&gamemode,&mode,&submode,&movie,pause_game,resume_game,allowed,frame,binds,&threshold,devices,binds,0,binds,binds,&mode2,cdstop};
int vo_pause_begin(LPDIRECTDRAWSURFACE s,int enabled){(void)s;(void)enabled;return 1;}
int vo_pause_capture(LPDIRECTDRAWSURFACE s){(void)s;return 1;}
void vo_pause_end(void){}
void vo_pause_restore_to(LPDIRECTDRAWSURFACE s){(void)s;}
DWORD GetTickCount(void){return now;}int IsWindow(HWND h){return h!=0;}int IsIconic(HWND h){(void)h;return 0;}
HWND GetForegroundWindow(void){return foreground_window;}short GetAsyncKeyState(int k){return keys[k]? (short)0x8000:0;}
int PostMessageW(HWND h,UINT m,WPARAM w,LPARAM l){assert(h==(void*)1&&m==VO_OPEN_MESSAGE&&!w&&!l);posted++;return 1;}
HMODULE GetModuleHandleW(const wchar_t *s){(void)s;return 0;}void *GetProcAddress(HMODULE h,const char*s){(void)h;(void)s;return 0;}
LONG InterlockedExchange(LONG*p,LONG x){LONG old=*p;*p=x;return old;}LONG InterlockedCompareExchange(LONG*p,LONG x,LONG expected){LONG old=*p;if(old==expected)*p=x;return old;}
int vo_attach(VoPaint*p,LPDIRECTDRAWSURFACE s){p->surface=s;p->visible=6;return attach_ok;}void vo_dispose(VoPaint*p){*p=(VoPaint){0};}
int vo_paint(VoPaint*p,const VoOverlay*s){(void)p;assert(s->state==VO_OPEN);draws++;return paint_ok;}
int vo_hit(VoPaint*p,HWND h,int x,int y){(void)p;(void)h;(void)y;return x;}int vo_hit_source(VoPaint*p,int x,int y){(void)p;(void)y;return x;}
static void step(unsigned kind,unsigned msg,unsigned w,int l){VonOverlayStep((void*)1,&context,kind,msg,w,l);}
static void reset(void){clear();escape_down=0;inactive=0;mode=4;submode=9;gamemode=0;movie=0;pauses=resumes=posted=draws=0;pause_ok=attach_ok=paint_ok=1;foreground_window=(void*)1;memset(keys,0,sizeof keys);step(2,0,0,0);}
static void sample(unsigned player,unsigned buttons,unsigned ready){XINPUT_STATE s={0};s.Gamepad.wButtons=buttons;VonOverlayInput(player,4,&s,0,ready);}

static void esc(void){step(0,WM_KEYDOWN,VK_ESCAPE,0);step(0,WM_KEYUP,VK_ESCAPE,0);}
static void open_start(void){esc();assert(state.state==VO_OPEN);}
int main(void){
 for(int m=0;m<6;m++)for(int sub=0;sub<36;sub++)for(int video=0;video<2;video++){
  reset();mode=m;submode=sub;movie=video;
  for(unsigned kind=1;kind<=8;kind++)for(unsigned player=0;player<2;player++){
   XINPUT_STATE x={0};VonTwinState n={VON_START|VON_PAUSE};x.Gamepad.wButtons=0x1010;
   assert(!VonOverlayInput(player,kind,kind>=7?(void*)&n:(void*)&x,0,3));
  }
  assert(!posted&&!pauses&&!resumes&&state.state==VO_CLOSED);
  int eligible=!video&&((m==1&&(sub==6||sub==7||sub==17||sub==23))||(m==4&&sub>=8&&sub<=12));
  esc();assert((state.state==VO_OPEN)==eligible);assert(!pauses&&!resumes);
 }
 reset();open_start();assert(!inactive&&VonOverlayVisible()&&cursor_count==0);
 sample(0,2,3);assert(state.selected==0);sample(0,0,3);sample(0,2,3);assert(state.selected==1);
 XINPUT_STATE p2={0};p2.Gamepad.wButtons=0xffff;p2.Gamepad.sThumbLX=12345;XINPUT_STATE original_p2=p2;
 assert(!VonOverlayInput(1,4,&p2,0,3)&&!memcmp(&p2,&original_p2,sizeof p2));assert(state.selected==1);
 sample(0,0,3);sample(0,0x1000,3);assert(state.unavailable&&state.selected==7);
 sample(0,0,3);sample(0,0x1000,3);assert(!state.unavailable); // controller BACK
 sample(0,0,3);sample(0,1,3);sample(0,0,3);sample(0,1,3);assert(state.selected==5);
 sample(0,0,3);sample(0,0x1000,3);assert(state.state==VO_DRAINING);
 sample(0,0,3);step(2,0,0,0);assert(state.state==VO_CLOSED&&!resumes&&!pauses&&cursor_count==-1);
 // Never change original pause, whether initially paused or running.
 for(int paused=0;paused<2;paused++){
  reset();inactive=paused;open_start();step(paused?1:3,0,0,0);if(paused)step(5,0,0,0);assert(draws==1);
  mode=1;submode=7;step(2,0,0,0);assert(state.state==VO_OPEN); // eligible transition
  esc();assert(state.state==VO_CLOSED&&inactive==paused&&!pauses&&!resumes);
 }
 reset();step(0,WM_KEYDOWN,VK_ESCAPE,0);assert(state.state==VO_OPEN);
 step(0,WM_KEYDOWN,VK_ESCAPE,1<<30);assert(state.state==VO_OPEN);
 step(2,0,0,0);assert(state.state==VO_OPEN); // asynchronous poll cannot double ESC
 step(0,WM_KEYUP,VK_ESCAPE,0);step(0,WM_KEYDOWN,VK_ESCAPE,0);assert(state.state==VO_DRAINING);
 step(0,WM_KEYUP,VK_ESCAPE,0);assert(state.state==VO_CLOSED);
 reset();movie=1;assert(!VonOverlayStep((void*)1,&context,0,WM_KEYDOWN,VK_ESCAPE,0));
 movie=0;step(2,0,0,0);assert(state.state==VO_CLOSED); // no deferred activation
 step(0,WM_KEYUP,VK_ESCAPE,0);open_start();movie=1;step(3,0,0,0);assert(state.state==VO_CLOSED&&!draws);
 reset();open_start();sample(0,0,3);step(2,0,0,0);keys[VK_DOWN]=1;step(2,0,0,0);assert(state.selected==1);
 keys[VK_DOWN]=0;step(2,0,0,0);keys[VK_RETURN]=1;step(2,0,0,0);assert(state.unavailable);
 keys[VK_RETURN]=0;step(2,0,0,0);esc();assert(!state.unavailable&&state.state==VO_OPEN);
 step(0,WM_MOUSEMOVE,0,3);assert(state.selected==3);step(0,WM_LBUTTONDOWN,0,3);step(0,WM_LBUTTONUP,0,3);assert(state.unavailable);
 step(0,WM_MOUSEMOVE,0,7);assert(state.selected==7);step(0,WM_LBUTTONDOWN,0,7);step(0,WM_LBUTTONUP,0,7);assert(!state.unavailable);
 for(unsigned kind=7;kind<=8;kind++){
  reset();open_start();VonTwinState native={0};VonOverlayInput(0,kind,&native,0,1);
  native.controls=VON_LEFT_DOWN;VonOverlayInput(0,kind,&native,0,1);assert(state.selected==1);
  native.controls=0;VonOverlayInput(0,kind,&native,0,1);native.controls=VON_START;
  VonOverlayInput(0,kind,&native,0,1);assert(state.unavailable);
 }
 for(unsigned key=VK_F1;key<=VK_F11;key++){
  if(key!=VK_F1&&key!=VK_F3&&!(key>=VK_F4&&key<=VK_F9)&&key!=VK_F11)continue;
  reset();inactive=1;open_start();assert(!VonOverlayStep((void*)1,&context,0,WM_KEYDOWN,key,0));
  assert(state.state==VO_CLOSED&&inactive&&!resumes);
 }
 reset();open_start();foreground_window=(void*)9;step(2,0,0,0);assert(state.state==VO_CLOSED&&!resumes);
 reset();attach_ok=0;esc();assert(state.state==VO_CLOSED&&!inactive&&!resumes);
 reset();open_start();paint_ok=0;step(3,0,0,0);assert(state.state==VO_CLOSED&&!inactive&&!resumes);
 reset();unsigned char keybuffer[256];memset(keybuffer,0x80,sizeof keybuffer);
 VonOverlayStep((void*)1,&context,4,0,(WPARAM)keybuffer,0);assert(keybuffer[0xc8]==0x80);
 open_start();VonOverlayStep((void*)1,&context,4,0,(WPARAM)keybuffer,0);
 for(unsigned i=0;i<256;i++)assert(keybuffer[i]==((i==0xc8||i==0xd0||i==0xcb||i==0xcd||i==0x1c||i==1)?0:0x80));
 reset();gamemode=2;esc();assert(state.state==VO_CLOSED);
 reset();open_start();step(0,WM_LBUTTONDOWN,0,6);step(0,WM_LBUTTONUP,0,6);assert(state.confirm&&!state.selected);
 for(int i=0;i<3;i++)step(0,WM_LBUTTONUP,0,9);assert(state.state==VO_OPEN&&!reset_pending);
 step(0,WM_LBUTTONDOWN,0,8);step(0,WM_LBUTTONUP,0,8);assert(!state.confirm&&state.state==VO_OPEN);
 // Confirmed exits use original reset words/audio and only resume paused cases.
 for(int paused=0;paused<2;paused++)for(int versus=0;versus<2;versus++){
  reset();inactive=paused;gamemode=versus;mode2=4;stops=0;open_start();
  state.selected=6;vo_overlay_event(&state,VO_ACCEPT);confirmation();
  assert(state.confirm&&state.selected==0&&!state.exit_requested);
  // Held activation cannot confirm; a fresh directional/accept pair is needed.
  vo_overlay_keyboard(&state,VO_ACCEPT);assert(!state.exit_requested);
  vo_overlay_keyboard(&state,0);vo_overlay_keyboard(&state,VO_RIGHT);vo_overlay_keyboard(&state,0);vo_overlay_keyboard(&state,VO_ACCEPT);
  confirmation();assert(state.state==VO_DRAINING&&mode==4);
  step(2,0,0,0);assert(state.state==VO_CLOSED&&mode==-1&&mode2==(versus?-1:4)&&stops==1&&resumes==paused&&!inactive);
  mode=1;submode=6;step(2,0,0,0);assert(!reset_waiting);
 }
 reset();open_start();state.selected=6;vo_overlay_event(&state,VO_ACCEPT);vo_overlay_event(&state,VO_ACCEPT);assert(!state.confirm&&!state.exit_requested&&state.state==VO_OPEN); // Cancel
 for(int sub=6;sub<=23;sub++){reset();mode=1;submode=sub;esc();if(state.state==VO_OPEN){assert(!state.exit_allowed);state.selected=6;vo_overlay_event(&state,VO_ACCEPT);assert(!state.confirm);}}
 reset();open_start();state.selected=6;vo_overlay_event(&state,VO_ACCEPT);gamemode=2;state.selected=1;vo_overlay_event(&state,VO_ACCEPT);step(2,0,0,0);assert(mode==4&&!reset_pending&&!resumes);
 puts("PASS F03 production runtime: 432 state/movie combinations, Start pass-through, ESC edges, pause independence, P1/P2, native confirm, Back/Resume, keyboard/mouse, movie/focus/failure/F-key recovery");
 return 0;
}
