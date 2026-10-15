/* Private forwarding seam. Original Controller Expansion helper remains exact.
 * No enumeration, input polling loop, configuration or ownership is added. */
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
static HMODULE original;
static DWORD ready;
static FARPROC function(const char *name){
 if(!original)original=LoadLibraryW(L"vontanita.dll");
 return original?GetProcAddress(original,name):NULL;
}
static void sample(DWORD player,DWORD kind,void *state,DWORD result,int native){
 typedef int (WINAPI *OverlayInput)(DWORD,DWORD,const void*,DWORD,DWORD);
 HMODULE overlay=GetModuleHandleW(L"vooverlay.dll");
 OverlayInput step=overlay?(OverlayInput)GetProcAddress(overlay,"VonOverlayInput"):NULL;
 if(player<2){if(result)ready&=~(1u<<player);else ready|=1u<<player;}
 if(step&&step(player,kind,state,result,ready))ZeroMemory(state,native?sizeof(VonTwinState):sizeof(XINPUT_STATE));
}
__declspec(dllexport) DWORD WINAPI TanitaGetState(DWORD index,XINPUT_STATE *state){
 typedef DWORD (WINAPI *Read)(DWORD,XINPUT_STATE*);Read read=(Read)function("TanitaGetState");
 if(!state)return ERROR_BAD_ARGUMENTS;
 ZeroMemory(state,sizeof *state);return read?read(index,state):ERROR_DEVICE_NOT_CONNECTED;
}
__declspec(dllexport) DWORD WINAPI VonGetState(DWORD player,DWORD kind,XINPUT_STATE *state){
 typedef DWORD (WINAPI *Read)(DWORD,DWORD,XINPUT_STATE*);Read read=(Read)function("VonGetState");
 if(!state)return ERROR_BAD_ARGUMENTS;
 ZeroMemory(state,sizeof *state);DWORD result=read?read(player,kind,state):ERROR_DEVICE_NOT_CONNECTED;
 sample(player,kind,state,result,0);return result;
}
__declspec(dllexport) DWORD WINAPI VonTwinGetState(DWORD player,DWORD kind,VonTwinState *state){
 typedef DWORD (WINAPI *Read)(DWORD,DWORD,VonTwinState*);Read read=(Read)function("VonTwinGetState");
 if(!state)return ERROR_BAD_ARGUMENTS;
 state->controls=0;DWORD result=read?read(player,kind,state):ERROR_DEVICE_NOT_CONNECTED;
 sample(player,kind,state,result,1);return result;
}
__declspec(dllexport) int WINAPI VonSelectController(HWND parent,DWORD player,DWORD kind){
 typedef int (WINAPI *Select)(HWND,DWORD,DWORD);Select select=(Select)function("VonSelectController");
 if(player<2)ready&=~(1u<<player);
 return select?select(parent,player,kind):0;
}
__declspec(dllexport) int WINAPI VonCaptureInput(HWND parent,DWORD player,DWORD kind,int threshold){
 typedef int (WINAPI *Capture)(HWND,DWORD,DWORD,int);Capture capture=(Capture)function("VonCaptureInput");
 return capture?capture(parent,player,kind,threshold):0;
}
