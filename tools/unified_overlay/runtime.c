#include "runtime.h"
#include <string.h>
#include "../../input/twinstick_state.h"
static VoOverlay state;
static VoPaint paint;
static const VoGame *game;
static HWND owner;
static unsigned controller_held;
static int busy,redraw,escape_down;
static DWORD last_sample;
static LONG published_open;
static int mouse_ready,cursor_increments;
static void cursor_release(void){while(cursor_increments>0){ShowCursor(0);--cursor_increments;}}
static void cursor_acquire(void){
 CURSORINFO info={0};info.cbSize=sizeof info;
 if(GetCursorInfo(&info)&&(info.flags&CURSOR_SHOWING))return;
 /* Balance only our own increments; never reset another component count. */
 for(unsigned i=0;i<32;i++){++cursor_increments;if(ShowCursor(1)>=0)break;}
}
__declspec(dllexport) int WINAPI VonOverlayVisible(void){return (int)InterlockedCompareExchange(&published_open,0,0);}
static void lifecycle(unsigned code){
 typedef void (WINAPI *Event)(unsigned);
 HMODULE h=GetModuleHandleW(L"vodisplay.dll");
 Event event=h?(Event)GetProcAddress(h,"VonOverlayLifecycle"):NULL;
 if(event)event(code);
}
static int foreground(void){return owner&&IsWindow(owner)&&GetForegroundWindow()==owner&&!IsIconic(owner);}
static int supported(void){
 if(!game||!foreground()||*game->gamemode==2||(*game->movie&1))return 0;
 /* Original attract dispatcher: logo 6/23, menu 17, demo 7.
  * Match input-state predicate is the unchanged upstream range. */
 return (*game->mode==1&&(*game->submode==6||*game->submode==23||*game->submode==17||*game->submode==7)) ||
  (*game->mode==4&&*game->submode>=8&&*game->submode<=12);
}
static unsigned keyboard(void){
 unsigned held=0;const int keys[]={VK_UP,VK_DOWN,VK_LEFT,VK_RIGHT,VK_RETURN};
 for(unsigned i=0;i<5;i++)if(GetAsyncKeyState(keys[i])&0x8000)held|=1u<<i;
 return held;
}
static void clear(void){escape_down=0;cursor_release();vo_dispose(&paint);vo_overlay_focus_lost(&state);controller_held=0;redraw=1;InterlockedExchange(&published_open,0);}
static void release_if_ready(void){
 if(GetTickCount()-last_sample>500)controller_held=0;
 if(state.state==VO_DRAINING&&!controller_held&&!keyboard()&&!escape_down&&!(GetAsyncKeyState(VK_LBUTTON)&0x8000)){
  vo_overlay_init(&state);cursor_release();vo_dispose(&paint);redraw=1;InterlockedExchange(&published_open,0);lifecycle(2);
 }
}
static int open_menu(void){
 if(!supported()||!vo_attach(&paint,*game->back)){return 0;}
 vo_overlay_pause_result(&state,0,1);cursor_acquire();
 redraw=1;mouse_ready=!(GetAsyncKeyState(VK_LBUTTON)&0x8000);InterlockedExchange(&published_open,1);lifecycle(1);return 1;
}
static unsigned semantic(DWORD kind,const void *raw){
 if(kind==7||kind==8){unsigned c=((const VonTwinState*)raw)->controls;
  return (c&15)|((c&VON_START)?VO_ACCEPT:0)|((c&0xff0)?128:0);
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
 if(b&0x1000)held|=VO_ACCEPT;
 if((b&~0x101f)||p->bLeftTrigger>64||p->bRightTrigger>64||abs(p->sThumbLX)>threshold||abs(p->sThumbLY)>threshold||abs(p->sThumbRX)>threshold||abs(p->sThumbRY)>threshold)held|=128;
 return held;
}
/* Remove only controls used by this menu, preserving unrelated buttons,
 * P2, and original Start/Pause. Bind conditions come from the live profile. */
static void isolate(DWORD kind,void *raw){
 if(kind==7||kind==8){((VonTwinState*)raw)->controls&=~(15u|VON_START);return;}
 XINPUT_GAMEPAD *p=&((XINPUT_STATE*)raw)->Gamepad;
 unsigned start=p->wButtons&0x10;
 p->wButtons&=~0x100f;
 const unsigned char *binds=kind==4?game->custom:kind==1?game->padbinds:kind==6?game->horibinds:game->twinbinds;
 for(unsigned i=0;binds&&game->conditions&&i<4;i++){
  unsigned id=binds[i*2];if(id<0xe0||id>=0xf4)continue;
  const unsigned char *c=game->conditions+(id-0xe0)*8;
  unsigned offset=0,value;memcpy(&offset,c+2,2);memcpy(&value,c+4,4);
  if(c[0]<=1&&offset<=10){short neutral=0;memcpy((char*)p+offset,&neutral,2);}
  else if(c[0]==2)p->wButtons&=~value;
  else if(c[0]==3&&offset<sizeof *p)((unsigned char*)p)[offset]=0;
 }
 p->wButtons|=start;
}
__declspec(dllexport) int WINAPI VonOverlayInput(DWORD player,DWORD kind,void *raw,DWORD result,DWORD ready){
 /* Closed, ineligible and P2 inputs are byte-for-byte pass-through. */
 if(!game||busy||player!=0||state.state==VO_CLOSED)return 0;
 if(!supported()){clear();return 0;}
 if(!result&&(kind==1||kind==2||kind==4||kind==6)){
  const XINPUT_GAMEPAD *p=&((XINPUT_STATE*)raw)->Gamepad;
  if((p->wButtons&0x310)==0x310&&p->bLeftTrigger>=30&&p->bRightTrigger>=30){clear();return 0;}
 }
 unsigned held=result?0:semantic(kind,raw);controller_held=held;last_sample=GetTickCount();
 vo_overlay_controller(&state,0,held,!result,!(ready&1),0,1);
 if(!result)isolate(kind,raw);
 return state.state!=VO_CLOSED;
}
/* ABI kinds: window message, idle render request, pump initialization, present. */
__declspec(dllexport) int WINAPI VonOverlayStep(HWND hwnd,const VoGame *g,UINT kind,UINT msg,WPARAM wp,LPARAM lp){
 if(!g||g->size!=sizeof(*g)||kind>4||busy)return 0;
 busy=1;game=g;if(!owner)owner=hwnd;int consumed=0;
 if(state.state!=VO_CLOSED&&!supported()){
  clear();lifecycle(4);
 }
 if(kind==4){
  if(state.state!=VO_CLOSED&&wp){
   /* Verified P1 DirectInput buffer; preserve P2 and all unrelated keys. */
   unsigned char *keys=(unsigned char*)wp;
   const unsigned scan[]={0xc8,0xd0,0xcb,0xcd,0x1c,0x01};
   for(unsigned i=0;i<sizeof(scan)/sizeof(*scan);i++)keys[scan[i]]=0;
  }
  goto done;
 }
 if(kind==2){if(state.state!=VO_CLOSED)vo_overlay_keyboard(&state,keyboard());release_if_ready();goto done;}
 if(kind==1){
  if(state.state!=VO_CLOSED){vo_overlay_keyboard(&state,keyboard());release_if_ready();}
  consumed=(state.state!=VO_CLOSED||redraw)&&supported()&&*g->inactive&&*g->back;redraw=0;goto done;
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
 if(msg==VO_OPEN_MESSAGE){if(state.state==VO_OPEN)vo_overlay_close(&state);else if(state.state==VO_CLOSED)open_menu();consumed=1;goto done;}
 /* Consume only eligible ESC edges before TranslateAccelerator/Dispatch.
  * Movie ESC remains entirely original and is never queued. */
 if((msg==WM_KEYDOWN||msg==WM_KEYUP)&&wp==VK_ESCAPE){
  if(!supported()){escape_down=msg==WM_KEYDOWN;goto done;}
  consumed=1;
  if(msg==WM_KEYUP){escape_down=0;release_if_ready();goto done;}
  if(!escape_down && !(lp&((LPARAM)1<<30))){
   escape_down=1;
   if(state.state==VO_CLOSED)consumed=open_menu();else if(state.state==VO_OPEN)vo_overlay_event(&state,VO_BACK);
  }
  goto done;
 }
 if(state.state==VO_CLOSED)goto done;
 if(msg==WM_CLOSE||msg==WM_DESTROY||msg==WM_ACTIVATEAPP||msg==WM_ACTIVATE||msg==WM_SIZE||msg==WM_SYSCOMMAND){clear();lifecycle(4);goto done;}
 if(msg==WM_KEYDOWN&&(wp==VK_F1||wp==VK_F3||(wp>=VK_F4&&wp<=VK_F9)||wp==VK_F11)){
  /* Original F-key handler alone owns pause and configuration. */
  clear();lifecycle(2);goto done;
 }
 if((msg==WM_KEYDOWN||msg==WM_KEYUP)&&(wp==VK_UP||wp==VK_DOWN||wp==VK_LEFT||wp==VK_RIGHT||wp==VK_RETURN)){consumed=1;goto done;}
 if(msg==WM_CHAR&&(wp==VK_RETURN||wp==VK_ESCAPE)){consumed=1;goto done;}
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
