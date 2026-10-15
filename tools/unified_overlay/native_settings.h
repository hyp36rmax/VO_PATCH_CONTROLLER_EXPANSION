#ifndef VO_NATIVE_SETTINGS_H
#define VO_NATIVE_SETTINGS_H
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
/* Direct draft over original live settings and original F6 snapshot/apply.
 * host is an active token retained for the page API, never a Windows HWND. */
typedef struct {
 HWND host; unsigned category,edition;
 unsigned char scratch[2048];
 unsigned values[16];
 unsigned char changed[2048];
 unsigned value_mask;
 uintptr_t ui;
 void (__cdecl *finish)(void);
} VoNativeSettings;
enum { VO_NATIVE_GRAPHICS, VO_NATIVE_1P, VO_NATIVE_2P,
 VO_NATIVE_GENERAL, VO_NATIVE_APPENDIX, VO_NATIVE_SCORES };
int vo_native_begin(VoNativeSettings*,HWND,const volatile LONG*,unsigned);
void vo_native_end(VoNativeSettings*);
int vo_native_choice(VoNativeSettings*,unsigned,unsigned,char*,unsigned);
int vo_native_count(VoNativeSettings*,unsigned);
int vo_native_selected(VoNativeSettings*,unsigned);
int vo_native_select(VoNativeSettings*,unsigned,unsigned);
int vo_native_check(VoNativeSettings*,unsigned);
int vo_native_click(VoNativeSettings*,unsigned);
int vo_native_radio(VoNativeSettings*,unsigned,unsigned,unsigned);
int vo_native_defaults(VoNativeSettings*);
int vo_native_commit(VoNativeSettings*);
int vo_native_score(VoNativeSettings*,unsigned,unsigned,char*,unsigned);
#endif
