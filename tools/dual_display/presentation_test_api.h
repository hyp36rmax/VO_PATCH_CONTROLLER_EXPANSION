#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
#include "layout.h"
typedef int BOOL;typedef int32_t HRESULT;typedef unsigned UINT;typedef uint32_t DWORD;
typedef wchar_t WCHAR;typedef void *HWND;typedef void *HANDLE;typedef uintptr_t WPARAM;typedef intptr_t LPARAM;typedef intptr_t LRESULT;
typedef void IDirect3DSwapChain9;typedef void IDirect3DSurface9;typedef void IDirect3DStateBlock9;typedef void IDirect3DBaseTexture9;
typedef struct {float x,y,z,rhw,u,v;} CUSTOMVERTEX;
typedef struct {int Windowed,SwapEffect,BackBufferCount,BackBufferWidth,BackBufferHeight,BackBufferFormat,PresentationInterval;HWND hDeviceWindow;} D3DPRESENT_PARAMETERS;
typedef struct {DWORD x,y,w,h;float minz,maxz;} D3DVIEWPORT9;
typedef struct {LRESULT (*lpfnWndProc)(HWND,UINT,WPARAM,LPARAM);void *hInstance;const char *lpszClassName;} WNDCLASSA;
typedef struct {int unused;} MSG;
#define CALLBACK
#define TRUE 1
#define FALSE 0
#define FAILED(x) ((x)<0)
#define SUCCEEDED(x) ((x)>=0)
#define E_FAIL ((HRESULT)-1)
#define MAX_PATH 260
#define INFINITE UINT32_MAX
#define WAIT_TIMEOUT 258
#define WM_CLOSE 16
#define WM_DISPLAYCHANGE 126
#define WM_MOUSEACTIVATE 33
#define MA_NOACTIVATEANDEAT 4
#define HWND_TOP ((HWND)0)
#define HWND_TOPMOST ((HWND)(intptr_t)-1)
#define SWP_NOMOVE 1
#define SWP_NOSIZE 2
#define SWP_NOACTIVATE 4
#define SWP_SHOWWINDOW 8
#define SW_HIDE 0
#define PM_REMOVE 1
#define WS_EX_NOACTIVATE 1
#define WS_EX_TOOLWINDOW 2
#define WS_POPUP 1
#define ERROR_CLASS_ALREADY_EXISTS 1410
#define D3DSWAPEFFECT_DISCARD 1
#define D3DFMT_UNKNOWN 0
#define D3DPRESENT_INTERVAL_IMMEDIATE 0
#define D3DBACKBUFFER_TYPE_MONO 0
#define D3DSBT_ALL 0
#define D3DSAMP_MINFILTER 0
#define D3DSAMP_MAGFILTER 1
#define D3DTEXF_POINT 1
#define D3DCLEAR_TARGET 1
#define D3DPT_TRIANGLESTRIP 1
#define min(a,b) ((a)<(b)?(a):(b))
static struct {int cs,width,height,bpp;HWND hwnd;struct {int run;}render;} g_ddraw;
static struct {D3DPRESENT_PARAMETERS params;int tex_width,tex_height;void *device,*surface_tex[2],*vertex_buf;} g_d3d9;
static VoMonitor monitors[VO_MAX_MONITORS];static WCHAR config[MAX_PATH];static unsigned count;
static struct {int calls,fail_at,live,draws,presents,restores,streams,destroyed,foreground,enabled,closed;int minimized,p1_topmost,p1_above,position_calls[2],original_moves;HWND windows[2];void *bound,*texture[16];CUSTOMVERTEX vertices[16][4];} fake;
static HRESULT api(void){return ++fake.calls==fake.fail_at?E_FAIL:0;}
static HRESULT acquire(void **out){HRESULT h=api();if(SUCCEEDED(h)){*out=(void*)(uintptr_t)(100+ ++fake.live);}return h;}
static int release(void *p){(void)p;--fake.live;return 0;}
static int discover(void){return 1;}
static void load_id(const WCHAR *key,char *id){(void)key;id[0]=0;}
#define DefWindowProcA(...) 0
#define EnterCriticalSection(...) ((void)0)
#define LeaveCriticalSection(...) ((void)0)
#define IDirect3DStateBlock9_Release(p) release(p)
#define IDirect3DSurface9_Release(p) release(p)
#define IDirect3DSwapChain9_Release(p) release(p)
static BOOL real_SetWindowPos(HWND h,HWND after,int x,int y,int w,int height,int flags){
    (void)x;(void)y;(void)w;(void)height;
    if(h==g_ddraw.hwnd){++fake.original_moves;return FALSE;}
    int i=h==fake.windows[0]?0:1;
    ++fake.position_calls[i];
    if(!(flags&SWP_NOACTIVATE))fake.foreground=(int)(uintptr_t)h;
    if(i==0 && after==HWND_TOPMOST){fake.p1_topmost=1;fake.p1_above=1;}
    return TRUE;
}
static BOOL EnumWindows(BOOL (*callback)(HWND,LPARAM),LPARAM value){
    HWND first=fake.p1_above?fake.windows[0]:g_ddraw.hwnd;
    HWND second=fake.p1_above?g_ddraw.hwnd:fake.windows[0];
    if(callback(first,value))callback(second,value);
    return TRUE;
}
#define ShowWindow(...) ((void)0)
#define PeekMessageA(...) 0
#define DispatchMessageA(...) ((void)0)
#define GetForegroundWindow() ((HWND)(uintptr_t)fake.foreground)
#define IsIconic(...) fake.minimized
static DWORD GetTickCount(void){static DWORD t;return ++t;}
static DWORD WaitForSingleObject(HANDLE h,DWORD timeout){(void)h;(void)timeout;return 0;}
static DWORD GetEnvironmentVariableA(const char *key,char *out,DWORD size){(void)key;(void)size;out[0]=fake.enabled?'1':'0';return 1;}
static DWORD GetModuleFileNameW(void *module,WCHAR *out,DWORD size){(void)module;(void)size;wcscpy(out,L"C:\\game.exe");return 11;}
#define GetModuleHandleA(...) NULL
#define RegisterClassA(...) 1
#define UnregisterClassA(...) ((void)0)
#define GetLastError() 0
static HWND real_CreateWindowExA(int a,const char*b,const char*c,int d,int x,int y,int w,int h,void *i,void*j,void*k,void*l){(void)a;(void)b;(void)c;(void)d;(void)x;(void)y;(void)w;(void)h;(void)i;(void)j;(void)k;(void)l;static uintptr_t id=5;HWND window=(HWND)++id;if(!fake.windows[0])fake.windows[0]=window;else fake.windows[1]=window;return window;}
#define IDirect3DDevice9_CreateAdditionalSwapChain(d,p,out) acquire((void**)out)
#define IDirect3DSwapChain9_GetBackBuffer(d,i,t,out) acquire((void**)out)
#define IDirect3DDevice9_CreateStateBlock(d,t,out) acquire((void**)out)
#define IDirect3DDevice9_GetRenderTarget(d,i,out) acquire((void**)out)
#define IDirect3DStateBlock9_Capture(...) api()
#define IDirect3DDevice9_SetPixelShader(...) api()
static HRESULT set_texture(void *tex){fake.bound=tex;return api();}
#define IDirect3DDevice9_SetTexture(d,i,t) set_texture(t)
#define IDirect3DDevice9_SetSamplerState(...) api()
#define IDirect3DDevice9_SetRenderTarget(...) api()
#define IDirect3DDevice9_SetViewport(...) api()
#define IDirect3DDevice9_Clear(...) api()
#define IDirect3DDevice9_BeginScene(...) api()
static HRESULT draw(const CUSTOMVERTEX *v){HRESULT h=api();if(SUCCEEDED(h)){memcpy(fake.vertices[fake.draws],v,4*sizeof *v);fake.texture[fake.draws++]=fake.bound;}return h;}
#define IDirect3DDevice9_DrawPrimitiveUP(d,t,n,v,s) draw(v)
#define IDirect3DDevice9_EndScene(...) api()
static HRESULT restore(void){++fake.restores;return api();}
#define IDirect3DStateBlock9_Apply(...) restore()
static HRESULT fake_stream(void){++fake.streams;return api();}
#define IDirect3DDevice9_SetStreamSource(...) fake_stream()
static HRESULT present(void){HRESULT h=api();if(SUCCEEDED(h))++fake.presents;return h;}
#define IDirect3DSwapChain9_Present(...) present()
#define PostMessageA(...) (++fake.closed)
#define DestroyWindow(...) (++fake.destroyed)
static FILE *_wfopen(const WCHAR *path,const WCHAR *mode){(void)path;(void)mode;return NULL;}
