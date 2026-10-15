#ifndef VO_DISPLAY_SETTINGS_API_H
#define VO_DISPLAY_SETTINGS_API_H
#include <stdint.h>
/* Fixed-width private ABI; no HWND, pointers, paths or renderer internals in
 * the display snapshot. Names are UTF-8 and identities stay in F5 authority. */
enum { VO_DISPLAY_BEGIN,VO_DISPLAY_READ,VO_DISPLAY_MODE,VO_DISPLAY_PRIMARY,
 VO_DISPLAY_SECONDARY,VO_DISPLAY_ASPECT,VO_DISPLAY_APPLY,VO_DISPLAY_CANCEL };
enum { VO_DISPLAY_DISCOVERY=100,VO_DISPLAY_WRITE=101 };
typedef struct {
 uint32_t size,count,dirty,error,winerror,restart;
 int32_t mode,aspect,primary,secondary;
 char names[16][1024];
} VoDisplaySnapshot;
#endif
