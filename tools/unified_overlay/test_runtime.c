#define VO_OVERLAY_TEST
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "runtime.c"
static DWORD now;static HWND foreground_window=(void*)1;static unsigned keys[256];
static int pause_ok=1,attach_ok=1,paint_ok=1,pauses,resumes,posted,draws;
static LONG inactive,mode=4,submode=9,gamemode,movie,threshold=8000,devices[2]={4,4};
static LPDIRECTDRAWSURFACE primary=(void*)2,back=(void*)3;
static unsigned char binds[8]={0xf0,0,0xf1,0,0xf2,0,0xf3,0};
static void pause_game(int n){assert(!n);pauses++;if(pause_ok)inactive=1;}
static void resume_game(void){resumes++;inactive=0;}
static int allowed(void){return 1;}static void frame(void){}
static VoGame context={sizeof(VoGame),&primary,&back,&inactive,&gamemode,&mode,&submode,&movie,pause_game,resume_game,allowed,frame,binds,&threshold,devices,binds,0,binds,binds};
DWORD GetTickCount(void){return now;}int IsWindow(HWND h){return h!=0;}int IsIconic(HWND h){(void)h;return 0;}
HWND GetForegroundWindow(void){return foreground_window;}short GetAsyncKeyState(int k){return keys[k]? (short)0x8000:0;}
int PostMessageW(HWND h,UINT m,WPARAM w,LPARAM l){assert(h==(void*)1&&m==VO_OPEN_MESSAGE&&!w&&!l);posted++;return 1;}
HMODULE GetModuleHandleW(const wchar_t *s){(void)s;return 0;}void *GetProcAddress(HMODULE h,const char*s){(void)h;(void)s;return 0;}
LONG InterlockedExchange(LONG*p,LONG x){LONG old=*p;*p=x;return old;}LONG InterlockedCompareExchange(LONG*p,LONG x,LONG expected){LONG old=*p;if(old==expected)*p=x;return old;}
int vo_attach(VoPaint*p,LPDIRECTDRAWSURFACE s){p->surface=s;p->visible=6;return attach_ok;}void vo_dispose(VoPaint*p){*p=(VoPaint){0};}
int vo_paint(VoPaint*p,const VoOverlay*s){(void)p;assert(s->state==VO_OPEN);draws++;return paint_ok;}
int vo_hit(VoPaint*p,HWND h,int x,int y){(void)p;(void)h;(void)y;return x;}int vo_hit_source(VoPaint*p,int x,int y){(void)p;(void)y;return x;}
static void step(unsigned kind,unsigned msg,unsigned w,int l){VonOverlayStep((void*)1,&context,kind,msg,w,l);}
static void reset(void){clear();inactive=0;mode=4;submode=9;gamemode=0;movie=0;pauses=resumes=posted=draws=0;pause_ok=attach_ok=paint_ok=1;foreground_window=(void*)1;memset(keys,0,sizeof keys);step(2,0,0,0);}
static void sample(unsigned player,unsigned buttons,unsigned ready){XINPUT_STATE s={0};s.Gamepad.wButtons=buttons;VonOverlayInput(player,4,&s,0,ready);}
static void open_start(void){sample(0,0,3);sample(0,0x10,3);assert(posted==1);step(0,VO_OPEN_MESSAGE,0,0);}
int main(void){
 reset();sample(0,0,3);sample(1,0x10,3);assert(!posted);
 mode=1;sample(0,0,3);sample(0,0x10,3);assert(!posted);mode=4;
 gamemode=1;sample(0,0,1);sample(0,0x10,1);assert(!posted);gamemode=0;
 open_start();assert(state.state==VO_OPEN&&inactive&&pauses==1);assert(VonOverlayVisible());
 sample(0,0x10,3);assert(state.state==VO_OPEN);sample(0,0,3);sample(0,2,3);assert(state.selected==1);
 sample(1,1,3);assert(state.selected==1);step(3,0,0,0);assert(draws==1);
 sample(0,0,3);sample(0,0x10,3);assert(state.state==VO_DRAINING);step(2,0,0,0);assert(!resumes);
 sample(0,0,3);step(2,0,0,0);assert(resumes==1&&state.state==VO_CLOSED&&!VonOverlayVisible());
 reset();pause_ok=0;open_start();assert(state.state==VO_CLOSED&&!inactive&&!resumes);
 reset();attach_ok=0;open_start();assert(state.state==VO_CLOSED&&inactive&&!resumes);
 reset();open_start();foreground_window=(void*)9;step(1,0,0,0);assert(state.state==VO_CLOSED&&!resumes);
 reset();open_start();step(0,WM_KEYDOWN,VK_F11,0);assert(state.state==VO_CLOSED&&resumes==1);
 reset();gamemode=2;sample(0,0,3);sample(0,0x10,3);assert(!posted);
 reset();open_start();sample(0,0,3);step(1,0,0,0);keys[VK_DOWN]=1;step(1,0,0,0);assert(state.selected==1);
 keys[VK_DOWN]=0;step(1,0,0,0);keys[VK_RETURN]=1;step(1,0,0,0);assert(state.unavailable);
 step(0,WM_LBUTTONUP,0,6);assert(!state.unavailable);step(0,WM_MOUSEMOVE,0,3);assert(state.selected==3);
 step(0,WM_LBUTTONUP,0,3);assert(state.unavailable);step(0,WM_LBUTTONUP,0,6);assert(!state.unavailable);
 /* Approved native exception: Pause toggles, Start accepts; one lever suffices. */
 reset();VonTwinState native={0};VonOverlayInput(0,7,&native,0,3);native.controls=VON_PAUSE;VonOverlayInput(0,7,&native,0,3);assert(posted==1);step(0,VO_OPEN_MESSAGE,0,0);
 native.controls=0;VonOverlayInput(0,7,&native,0,3);native.controls=VON_LEFT_DOWN;VonOverlayInput(0,7,&native,0,3);assert(state.selected==1);
 native.controls=0;VonOverlayInput(0,7,&native,0,3);native.controls=VON_START;VonOverlayInput(0,7,&native,0,3);assert(state.unavailable&&state.state==VO_OPEN);
 reset();open_start();paint_ok=0;step(3,0,0,0);assert(state.state==VO_CLOSED&&inactive&&!resumes);
 puts("PASS production runtime with platform doubles: pause verification/failure, Start routing/edges, native exception, P1/P2, keyboard/mouse, F11 recovery, focus/render failure");
 return 0;
}
