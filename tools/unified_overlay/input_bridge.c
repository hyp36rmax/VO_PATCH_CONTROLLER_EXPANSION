/* Private input seam over the existing Controller Expansion implementation.
 * The installed game and both interfaces share one compiled ownership instance.
 * The original packaged helper remains byte-exact for independent recovery. */
#ifdef VO_OVERLAY_TEST
#include "test_platform.h"
#include <string.h>
#define ZeroMemory(p,n) memset(p,0,n)
#define ERROR_BAD_ARGUMENTS 160
#define ERROR_DEVICE_NOT_CONNECTED 1167
typedef void *FARPROC;
HMODULE LoadLibraryW(const wchar_t*);
#else
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <xinput.h>
#endif
#include "../../input/twinstick_state.h"
#ifndef VO_OVERLAY_TEST
/* Build the existing reader/ownership implementation into this module. Every
 * installed game helper reference targets this one instance; F7 and overlay
 * therefore share owners and HID reservations. */
#define VonGetState OriginalVonGetState
#define VonTwinGetState OriginalVonTwinGetState
#define VonSelectController OriginalVonSelectController
#define VonCaptureInput OriginalVonCaptureInput
#undef _WIN32_WINNT
#include "../../input/controller.c"
#undef VonGetState
#undef VonTwinGetState
#undef VonSelectController
#undef VonCaptureInput
#else
static HMODULE original;
#endif
static DWORD ready;
static DWORD sampled_kind[2],sample_known;
/* Last result from the existing owned-input path. This does not enumerate,
 * poll, or invent a physical device identity. -1 means no current sample. */
__declspec(dllexport) int WINAPI VonOverlayControllerStatus(DWORD player,DWORD kind){
 if(player>1||!(sample_known&(1u<<player))||sampled_kind[player]!=kind)return -1;
 return !!(ready&(1u<<player));
}
static FARPROC function(const char *name){
#ifdef VO_OVERLAY_TEST
 if(!original)original=LoadLibraryW(L"vontanita.dll");
 return original?GetProcAddress(original,name):NULL;
#else
 if(!strcmp(name,"VonGetState"))return (FARPROC)OriginalVonGetState;
 if(!strcmp(name,"VonTwinGetState"))return (FARPROC)OriginalVonTwinGetState;
 if(!strcmp(name,"VonSelectController"))return (FARPROC)OriginalVonSelectController;
 if(!strcmp(name,"VonCaptureInput"))return (FARPROC)OriginalVonCaptureInput;
 return NULL;
#endif
}
static void sample(DWORD player,DWORD kind,void *state,DWORD result,int native){
 (void)native;
 typedef int (WINAPI *OverlayInput)(DWORD,DWORD,void*,DWORD,DWORD);
 HMODULE overlay=GetModuleHandleW(L"vooverlay.dll");
 OverlayInput step=overlay?(OverlayInput)GetProcAddress(overlay,"VonOverlayInput"):NULL;
 if(player<2){sample_known|=1u<<player;sampled_kind[player]=kind;if(result)ready&=~(1u<<player);else ready|=1u<<player;}
 if(step)step(player,kind,state,result,ready);
}
#ifdef VO_OVERLAY_TEST
__declspec(dllexport) DWORD WINAPI TanitaGetState(DWORD index,XINPUT_STATE *state){
 typedef DWORD (WINAPI *Read)(DWORD,XINPUT_STATE*);Read read=(Read)function("TanitaGetState");
 if(!state)return ERROR_BAD_ARGUMENTS;
 ZeroMemory(state,sizeof *state);return read?read(index,state):ERROR_DEVICE_NOT_CONNECTED;
}
#endif
/* Opening an overlay page must not trigger the legacy first-use modal prompt.
 * Explicit F7 selection and normal closed-overlay game startup remain intact. */
static int suppress_implicit_prompt(DWORD player){
#ifndef VO_OVERLAY_TEST
 if(player<2&&!owners[player].attempted){
  HMODULE h=GetModuleHandleW(L"vooverlay.dll");
  int (WINAPI *visible)(void)=h?(void*)GetProcAddress(h,"VonOverlayVisible"):NULL;
  return visible&&visible();
 }
#else
 (void)player;
#endif
 return 0;
}
__declspec(dllexport) DWORD WINAPI VonGetState(DWORD player,DWORD kind,XINPUT_STATE *state){
 typedef DWORD (WINAPI *Read)(DWORD,DWORD,XINPUT_STATE*);Read read=(Read)function("VonGetState");
 if(!state)return ERROR_BAD_ARGUMENTS;
 ZeroMemory(state,sizeof *state);DWORD result=read&&!suppress_implicit_prompt(player)?read(player,kind,state):ERROR_DEVICE_NOT_CONNECTED;
 sample(player,kind,state,result,0);return result;
}
__declspec(dllexport) DWORD WINAPI VonTwinGetState(DWORD player,DWORD kind,VonTwinState *state){
 typedef DWORD (WINAPI *Read)(DWORD,DWORD,VonTwinState*);Read read=(Read)function("VonTwinGetState");
 if(!state)return ERROR_BAD_ARGUMENTS;
 state->controls=0;DWORD result=read&&!suppress_implicit_prompt(player)?read(player,kind,state):ERROR_DEVICE_NOT_CONNECTED;
 sample(player,kind,state,result,1);return result;
}
__declspec(dllexport) int WINAPI VonSelectController(HWND parent,DWORD player,DWORD kind){
 typedef int (WINAPI *Select)(HWND,DWORD,DWORD);Select select=(Select)function("VonSelectController");
 if(player<2){ready&=~(1u<<player);sample_known=0;}
 return select?select(parent,player,kind):0;
}
__declspec(dllexport) int WINAPI VonCaptureInput(HWND parent,DWORD player,DWORD kind,int threshold){
 typedef int (WINAPI *Capture)(HWND,DWORD,DWORD,int);Capture capture=(Capture)function("VonCaptureInput");
 return capture?capture(parent,player,kind,threshold):0;
}

#ifndef VO_OVERLAY_TEST
#include "direct_input.h"
#endif
