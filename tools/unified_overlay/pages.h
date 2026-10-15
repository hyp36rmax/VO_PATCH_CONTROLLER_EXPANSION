#ifndef VO_OVERLAY_PAGES_H
#define VO_OVERLAY_PAGES_H
#include "runtime.h"
void vo_pages_begin(VoOverlay*,const VoGame*,HWND);
void vo_pages_end(void);
void vo_pages_refresh(VoOverlay*);
unsigned vo_pages_command(void);
#endif
