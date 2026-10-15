#include "runtime.h"
#include <string.h>
#include "../../input/twinstick_state.h"
static VoOverlay state;
static VoPaint paint;
static const VoGame *game;
static HWND owner;
static unsigned controller_held;
static int queued,busy,redraw;
static DWORD last_sample;
static LONG published_open;
static int mouse_ready;
__declspec(dllexport) int WINAPI VonOverlayVisible(void){return (int)InterlockedCompareExchange(&published_open,0,0);}
static void lifecycle(unsigned code){
 typedef void (WINAPI *Event)(unsigned);
 HMODULE h=GetModuleHandleW(L"vodisplay.dll");
 Event event=h?(Event)GetProcAddress(h,"VonOverlayLifecycle"):NULL;
 if(event)event(code);
}
static int foreground(void){return owner&&IsWindow(owner)&&GetForegroundWindow()==owner&&!IsIconic(owner);}
static int supported(void){
 return game&&foreground()&&*game->gamemode!=2&&!(*game->movie&1)&&
  *game->mode==4&&*game->submode>=8&&*game->submode<=12&&game->allowed();
}
static unsigned keyboard(void){
 unsigned held=0;const int keys[]={VK_UP,VK_DOWN,VK_LEFT,VK_RIGHT,VK_RETURN,VK_ESCAPE};
 for(unsigned i=0;i<6;i++)if(GetAsyncKeyState(keys[i])&0x8000)held|=1u<<i;
 return held;
}
static void clear(void){vo_dispose(&paint);vo_overlay_focus_lost(&state);queued=0;controller_held=0;redraw=1;InterlockedExchange(&published_open,0);}
static void release_if_ready(void){
 if(GetTickCount()-last_sample>500)controller_held=0;
 if(vo_overlay_release(&state,!controller_held&&!keyboard()&&!(GetAsyncKeyState(VK_LBUTTON)&0x8000))==VO_REQUEST_RESUME){
  vo_dispose(&paint);redraw=1;InterlockedExchange(&published_open,0);if(foreground()&&game&&*game->inactive)game->resume();lifecycle(2);
 }
}
static int open_menu(void){
 if(!supported()||*game->inactive)return 0;
 game->pause(0);
 /* Pause failure and unavailable surfaces preserve stock pause authority. */
 if(!*game->inactive||!vo_attach(&paint,*game->back)){lifecycle(3);return 0;}
 if(!vo_overlay_pause_result(&state,*game->inactive,1)){vo_dispose(&paint);return 0;}
 redraw=1;mouse_ready=!(GetAsyncKeyState(VK_LBUTTON)&0x8000);InterlockedExchange(&published_open,1);lifecycle(1);return 1;
}
static unsigned semantic(DWORD kind,const void *raw){
 if(kind==7||kind==8){unsigned c=((const VonTwinState*)raw)->controls;
  return (c&15)|((c&VON_START)?VO_ACCEPT:0)|((c&VON_PAUSE)?VO_START:0)|((c&0xff0)?128:0);
 }
 const XINPUT_GAMEPAD *p=&((const XINPUT_STATE*)raw)->Gamepad;
 unsigned b=p->wButtons,held=b&15;int threshold=game&&game->threshold?*game->threshold:8000;
 if(threshold<0||threshold>32767)threshold=8000;
 const unsigned char *binds=kind==4?game->custom:kind==1?game->padbinds:kind==6?game->horibinds:game->twinbinds;
 /* Evaluate the actual F7 condition rows with the game's live deadzone.
  * No hardware mapping table is invented for the overlay. */
 for(unsigned i=0;binds&&game->conditions&&i<4;i++){
  unsigned id=binds[i*2];if(id<0xe0||id>=0xf4)continue;
  const unsigned char *condition=game->conditions+(id-0xe0)*8;
  unsigned type=condition[0],offset=0;unsigned value;
  memcpy(&offset,condition+2,2);offset&=65535;memcpy(&value,condition+4,4);
  int active=0;
  if(type<=1&&offset<=10){short axis;memcpy(&axis,(const char*)p+offset,2);active=type==0?-(int)axis>threshold:(int)axis>threshold;}
  else if(type==2)active=!!(b&value);
  else if(type==3&&offset<sizeof(*p))active=((const unsigned char*)p)[offset]>value;
  if(active)held|=1u<<i;
 }
 /* Stock A is menu accept. Back is a camera function, not invented UI Back. */
 if(b&0x1000)held|=VO_ACCEPT;if(b&0x10)held|=VO_START;
 if((b&~0x101f)||p->bLeftTrigger>64||p->bRightTrigger>64||abs(p->sThumbLX)>threshold||abs(p->sThumbLY)>threshold||abs(p->sThumbRX)>threshold||abs(p->sThumbRY)>threshold)held|=128;
 return held;
}
__declspec(dllexport) int WINAPI VonOverlayInput(DWORD player,DWORD kind,const void *raw,DWORD result,DWORD ready){
 if(!game||busy)return 0;
 if(player==0){
  unsigned held=result?0:semantic(kind,raw);controller_held=held;last_sample=GetTickCount();
  unsigned needed=1;
  if(*game->gamemode==1 && game->devices[1]!=0 && game->devices[1]!=3)needed|=2;
  unsigned action=vo_overlay_controller(&state,0,held,!result,(ready&needed)!=needed,!supported()||(state.state==VO_CLOSED&&*game->inactive),supported());
  if(action==VO_REQUEST_PAUSE&&!queued){queued=PostMessageW(owner,VO_OPEN_MESSAGE,0,0)!=0;}
 }
 return queued||state.state!=VO_CLOSED;
}
/* ABI kinds: window message, idle render request, pump initialization, present. */
__declspec(dllexport) int WINAPI VonOverlayStep(HWND hwnd,const VoGame *g,UINT kind,UINT msg,WPARAM wp,LPARAM lp){
 if(!g||g->size!=sizeof(*g)||kind>3||busy)return 0;
 busy=1;game=g;if(!owner)owner=hwnd;int consumed=0;
 if(state.state!=VO_CLOSED&&(!foreground()||!*g->inactive)){
  clear();lifecycle(4);
 }
 if(kind==2){release_if_ready();goto done;}
 if(kind==1){
  if(state.state!=VO_CLOSED){vo_overlay_keyboard(&state,keyboard());release_if_ready();}
  consumed=(state.state!=VO_CLOSED||redraw)&&foreground()&&*g->back;redraw=0;goto done;
 }
 if(kind==3){
  if(state.state==VO_OPEN){
   if(paint.surface!=*g->back && !vo_attach(&paint,*g->back)){clear();lifecycle(3);goto done;}
   if(!vo_paint(&paint,&state)){clear();lifecycle(3);}
  }goto done;
 }
 if(msg==WM_APP+0x351){
  if(state.state==VO_OPEN){
   unsigned mouse=(unsigned)wp&0xffff;int item=vo_hit_source(&paint,GET_X_LPARAM(lp),GET_Y_LPARAM(lp));
   if(mouse==WM_MOUSEMOVE)vo_overlay_hover(&state,item);
   if(mouse==WM_LBUTTONDOWN)mouse_ready=1;
   if(mouse==WM_LBUTTONUP){if(mouse_ready)vo_overlay_click(&state,item);mouse_ready=1;}
   if(mouse==WM_MOUSEWHEEL)vo_overlay_wheel(&state,(short)(wp>>16),paint.visible<6);
  }consumed=1;goto done;
 }
 if(msg==VO_OPEN_MESSAGE){queued=0;if(state.state==VO_OPEN)vo_overlay_close(&state);else open_menu();consumed=1;goto done;}
 if(state.state==VO_CLOSED)goto done;
 if(msg==WM_CLOSE||msg==WM_DESTROY||msg==WM_ACTIVATEAPP||msg==WM_ACTIVATE||msg==WM_SIZE||msg==WM_SYSCOMMAND){clear();lifecycle(4);goto done;}
 if(msg==WM_KEYDOWN&&(wp==VK_F1||wp==VK_F3||(wp>=VK_F4&&wp<=VK_F9)||wp==VK_F11)){
  /* Hand the key to its original handler after relinquishing only our pause. */
  clear();if(wp!=VK_F3&&foreground()&&*g->inactive)g->resume();lifecycle(2);goto done;
 }
 if(msg==WM_KEYDOWN||msg==WM_KEYUP||msg==WM_CHAR){consumed=1;goto done;}
 if(msg>=WM_MOUSEFIRST&&msg<=WM_MOUSELAST){
  consumed=1;
  if(state.state==VO_OPEN){
   int item=vo_hit_source(&paint,GET_X_LPARAM(lp),GET_Y_LPARAM(lp));
   if(msg==WM_MOUSEMOVE)vo_overlay_hover(&state,item);
   if(msg==WM_LBUTTONDOWN)mouse_ready=1;
   if(msg==WM_LBUTTONUP){if(mouse_ready)vo_overlay_click(&state,item);mouse_ready=1;}
   if(msg==WM_MOUSEWHEEL)vo_overlay_wheel(&state,GET_WHEEL_DELTA_WPARAM(wp),paint.visible<6);
  }
 }
 done:busy=0;return consumed;
}
