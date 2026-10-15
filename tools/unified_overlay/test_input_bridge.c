#define VO_OVERLAY_TEST
#include <assert.h>
#include <stdio.h>
#include "input_bridge.c"
static int calls,consumed,selection,captures,connected=1,overlay_enabled=1;
static unsigned observed_ready,observed_buttons;
static DWORD original_read(DWORD player,DWORD kind,XINPUT_STATE *s){assert(player<2&&kind==4);calls++;s->Gamepad.wButtons=0x1010;return connected?0:1167;}
static DWORD original_native(DWORD player,DWORD kind,VonTwinState*s){assert(player==0&&kind==7);calls++;s->controls=VON_START|VON_PAUSE;return 0;}
static int original_select(HWND h,DWORD p,DWORD k){assert(h==(void*)7&&p==1&&k==4);selection++;return 1;}
static int original_capture(HWND h,DWORD p,DWORD k,int t){assert(h==(void*)7&&p==0&&k==4&&t==9000);captures++;return 0xe8;}
static int observe(DWORD player,DWORD kind,void*raw,DWORD result,DWORD owners){assert(player<2);observed_ready=owners;observed_buttons=kind==7?((const VonTwinState*)raw)->controls:((const XINPUT_STATE*)raw)->Gamepad.wButtons;(void)result;if(consumed){if(kind==7)((VonTwinState*)raw)->controls&=~VON_START;else ((XINPUT_STATE*)raw)->Gamepad.wButtons&=~0x1000;}return consumed;}
HMODULE LoadLibraryW(const wchar_t*s){assert(!wcscmp(s,L"vontanita.dll"));return (void*)1;}
HMODULE GetModuleHandleW(const wchar_t*s){assert(!wcscmp(s,L"vooverlay.dll"));return overlay_enabled?(void*)2:0;}
void *GetProcAddress(HMODULE h,const char*n){
 if(h==(void*)2){assert(!strcmp(n,"VonOverlayInput"));return (void*)observe;}
 if(!strcmp(n,"VonGetState"))return (void*)original_read;
 if(!strcmp(n,"VonTwinGetState"))return (void*)original_native;
 if(!strcmp(n,"VonSelectController"))return (void*)original_select;
 if(!strcmp(n,"VonCaptureInput"))return (void*)original_capture;
 return 0;
}
int main(void){
 XINPUT_STATE x;VonTwinState t;
 assert(VonOverlayControllerStatus(0,4)==-1&&VonOverlayControllerStatus(2,4)==-1);
 overlay_enabled=0;assert(!VonGetState(0,4,&x)&&x.Gamepad.wButtons==0x1010&&calls==1);
 overlay_enabled=1;assert(!VonGetState(1,4,&x)&&x.Gamepad.wButtons==0x1010&&observed_ready==3&&calls==2);
 int before=calls;
 assert(VonOverlayControllerStatus(0,4)==1&&VonOverlayControllerStatus(1,4)==1&&VonOverlayControllerStatus(0,7)==-1&&calls==before);
 consumed=1;assert(!VonGetState(0,4,&x)&&x.Gamepad.wButtons==0x10&&observed_buttons==0x1010&&calls==3);
 assert(!VonTwinGetState(0,7,&t)&&t.controls==VON_PAUSE&&observed_buttons==(VON_START|VON_PAUSE)&&calls==4);
 assert(VonSelectController((void*)7,1,4)==1&&selection==1&&!(ready&2));
 assert(VonOverlayControllerStatus(0,4)==-1&&VonOverlayControllerStatus(1,4)==-1);
 assert(VonCaptureInput((void*)7,0,4,9000)==0xe8&&captures==1);
 connected=0;assert(VonGetState(0,4,&x)==1167&&observed_ready==0);
 assert(VonOverlayControllerStatus(0,4)==0);
 assert(VonGetState(0,4,0)==160&&calls==5);
 puts("PASS private input forwarding: original call count, unchanged samples when closed, ownership status, capture/selection forwarding, native semantics and failure result");
}
