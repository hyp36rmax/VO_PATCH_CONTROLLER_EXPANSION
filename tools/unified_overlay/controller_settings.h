#ifndef VO_CONTROLLER_SETTINGS_H
#define VO_CONTROLLER_SETTINGS_H
#include "runtime.h"
typedef struct {
 const VoGame *game; HWND owner,host; unsigned edition,player,kind,active;
 unsigned char object[32],blocks[224]; unsigned previous_player;
 unsigned char used_keys[138];
 unsigned char custom_pending[24]; unsigned custom_player;
} VoControllerSettings;
int vo_controller_available(const VoGame*);
int vo_controller_begin(VoControllerSettings*,const VoGame*,HWND,unsigned,unsigned);
void vo_controller_end(VoControllerSettings*);
int vo_controller_count(VoControllerSettings*,unsigned);
int vo_controller_selected(VoControllerSettings*,unsigned);
int vo_controller_choice(VoControllerSettings*,unsigned,unsigned,char*,unsigned);
int vo_controller_select(VoControllerSettings*,unsigned,unsigned);
int vo_controller_capture(VoControllerSettings*,unsigned);
int vo_controller_defaults(VoControllerSettings*);
int vo_controller_save(VoControllerSettings*);
int vo_controller_profile(const VoGame*,unsigned,unsigned);
int vo_controller_assign(HWND,unsigned,unsigned);
int vo_controller_status(unsigned,unsigned);
int vo_controller_deadzone(const VoGame*,unsigned,int);
#endif
