#ifndef VO_OVERLAY_TEST_PLATFORM_H
#define VO_OVERLAY_TEST_PLATFORM_H
#include <stdint.h>
#include <stdlib.h>
#include <wchar.h>
#define __declspec(x)
#define __cdecl
#define WINAPI
typedef uint32_t DWORD,UINT;typedef int32_t LONG;typedef uintptr_t WPARAM;typedef intptr_t LPARAM;
typedef void *HWND,*HFONT,*HMODULE,*LPDIRECTDRAWSURFACE;
typedef struct {uint16_t wButtons;uint8_t bLeftTrigger,bRightTrigger;int16_t sThumbLX,sThumbLY,sThumbRX,sThumbRY;} XINPUT_GAMEPAD;
typedef struct {DWORD dwPacketNumber;XINPUT_GAMEPAD Gamepad;} XINPUT_STATE;
enum {VK_LBUTTON=1,VK_RETURN=13,VK_ESCAPE=27,VK_LEFT=37,VK_UP=38,VK_RIGHT=39,VK_DOWN=40,VK_F1=112,VK_F3=114,VK_F4=115,VK_F9=120,VK_F11=122,
WM_DESTROY=2,WM_SIZE=5,WM_ACTIVATE=6,WM_CLOSE=16,WM_ACTIVATEAPP=28,WM_KEYDOWN=256,WM_KEYUP=257,WM_CHAR=258,WM_SYSCOMMAND=274,
WM_MOUSEFIRST=512,WM_MOUSEMOVE=512,WM_LBUTTONDOWN=513,WM_LBUTTONUP=514,WM_MOUSEWHEEL=522,WM_MOUSELAST=526,WM_APP=32768};
#define GET_X_LPARAM(l) ((short)(l))
#define GET_Y_LPARAM(l) ((short)((l)>>16))
#define GET_WHEEL_DELTA_WPARAM(w) ((short)((w)>>16))
typedef struct {DWORD cbSize,flags;} CURSORINFO;
#define CURSOR_SHOWING 1
int ShowCursor(int);int GetCursorInfo(CURSORINFO*);
DWORD GetTickCount(void);int IsWindow(HWND);int IsIconic(HWND);HWND GetForegroundWindow(void);short GetAsyncKeyState(int);
int PostMessageW(HWND,UINT,WPARAM,LPARAM);HMODULE GetModuleHandleW(const wchar_t*);void *GetProcAddress(HMODULE,const char*);
LONG InterlockedExchange(LONG*,LONG);LONG InterlockedCompareExchange(LONG*,LONG,LONG);
#endif
