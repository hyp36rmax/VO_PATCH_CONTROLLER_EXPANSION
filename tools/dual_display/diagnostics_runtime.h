/* Renderer-side consent read: no file I/O, no polling or additional thread. */
#ifndef VO_DUAL_TEST
static unsigned vo_diagnostic_level(void){
 typedef unsigned (WINAPI *ReadLevel)(void);
 static ReadLevel read_level;
 if(!read_level){HMODULE h=GetModuleHandleW(L"vodisplay.dll");if(h)read_level=(ReadLevel)GetProcAddress(h,"VonDiagnosticsLevel");}
 return read_level?read_level():0;
}
#else
#include "diagnostics_privacy.h"
#endif
