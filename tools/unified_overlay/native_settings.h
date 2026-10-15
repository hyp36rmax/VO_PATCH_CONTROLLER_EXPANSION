#ifndef VO_NATIVE_SETTINGS_H
#define VO_NATIVE_SETTINGS_H
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
/* Adapts original dialog procedures; controls, value lists, defaults and
 * staged state belong to the original game. No configuration file is added. */
typedef struct {
 HWND host,page;
 DLGPROC procedure;
 void (__cdecl *snapshot)(void), (__cdecl *commit)(void), (__cdecl *finish)(void);
 void **scratch_slot,*previous_scratch;
 unsigned char scratch[2048];
 unsigned category;
} VoNativeSettings;
enum { VO_NATIVE_GRAPHICS, VO_NATIVE_1P, VO_NATIVE_2P,
 VO_NATIVE_GENERAL, VO_NATIVE_APPENDIX };
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
#endif
