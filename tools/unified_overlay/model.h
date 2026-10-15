#ifndef VO_OVERLAY_MODEL_H
#define VO_OVERLAY_MODEL_H
/* UI state only. The adapter must use the game's pause/resume and established
 * profile semantics; this module never polls hardware or owns configuration. */
enum { VO_UP=1, VO_DOWN=2, VO_LEFT=4, VO_RIGHT=8, VO_ACCEPT=16,
       VO_BACK=32, VO_START=64 };
enum { VO_CLOSED, VO_OPEN, VO_DRAINING };
enum { VO_SINGLE, VO_VERSUS, VO_MIRROR };
enum { VO_NO_ACTION, VO_REQUEST_PAUSE, VO_REQUEST_RESUME, VO_REQUEST_EXIT };
typedef struct {
 unsigned state, selected, unavailable, controller_ready, previous;
 unsigned keyboard_ready, previous_keyboard, owns_pause;
 unsigned confirm, exit_allowed, exit_requested;
 int hover;
} VoOverlay;
static const char *const vo_overlay_labels[]={
 "CONTROLLERS", "DISPLAY", "GRAPHICS", "GAME SETTINGS", "EXTRAS", "RESUME", "EXIT TO TITLE"
};
static inline void vo_overlay_init(VoOverlay *s) { *s=(VoOverlay){0}; s->hover=-1; }
/* UI ownership is independent of the original game pause flag. */
static inline int vo_overlay_pause_result(VoOverlay *s, int paused,
                                         int presentation_ready) {
 (void)paused;
 if (!presentation_ready) return 0;
 s->state=VO_OPEN; s->selected=0; s->unavailable=0; s->owns_pause=0; s->hover=-1;
 s->controller_ready=0; s->keyboard_ready=0;
 s->previous=0; s->previous_keyboard=0; return 1;
}
static inline unsigned vo_overlay_close(VoOverlay *s) {
 if(s->state!=VO_OPEN) return VO_NO_ACTION;
 s->state=VO_DRAINING; s->unavailable=0; return VO_NO_ACTION;
}
static inline unsigned vo_overlay_release(VoOverlay *s, int all_released) {
 if(s->state!=VO_DRAINING || !all_released) return VO_NO_ACTION;
 unsigned resume=s->owns_pause; vo_overlay_init(s);
 return resume?VO_REQUEST_RESUME:VO_NO_ACTION;
}
/* Losing focus relinquishes UI ownership, without resuming an unfocused
 * game. The game's existing activation handler retains pause authority. */
static inline void vo_overlay_focus_lost(VoOverlay *s) { vo_overlay_init(s); }
static inline unsigned vo_overlay_event(VoOverlay *s, unsigned edge) {
 if(s->state!=VO_OPEN) return VO_NO_ACTION;
 s->hover=-1;
 /* Start is never an overlay toggle. */
 if(s->confirm) {
  if(edge&VO_BACK){s->confirm=0;s->selected=6;return VO_NO_ACTION;}
  if(edge&(VO_UP|VO_DOWN|VO_LEFT|VO_RIGHT))s->selected^=1;
  if(edge&VO_ACCEPT){if(s->selected==1&&s->exit_allowed){s->exit_requested=1;return VO_REQUEST_EXIT;}s->confirm=0;s->selected=6;}
  return VO_NO_ACTION;
 }
 if(edge & VO_BACK) {
  if(s->unavailable) { s->unavailable=0; s->selected=0; } else vo_overlay_close(s);
  return VO_NO_ACTION;
 }
 if(s->unavailable) {
  if(edge&(VO_UP|VO_DOWN|VO_LEFT|VO_RIGHT))s->selected=s->selected==7?5:7;
  if(edge&VO_ACCEPT){
   if(s->selected==5)return vo_overlay_close(s);
   s->unavailable=0;s->selected=0;
  }
  return VO_NO_ACTION;
 }
 if((edge&(VO_UP|VO_DOWN))==VO_UP) s->selected=(s->selected+6)%7;
 if((edge&(VO_UP|VO_DOWN))==VO_DOWN) s->selected=(s->selected+1)%7;
 if(edge&VO_ACCEPT) {
  if(s->selected==5) return vo_overlay_close(s);
  if(s->selected==6){if(s->exit_allowed){s->confirm=1;s->selected=0;s->controller_ready=0;s->keyboard_ready=0;}return VO_NO_ACTION;}
  s->unavailable=1; s->selected=7;
 }
 return VO_NO_ACTION;
}
/* Inputs are semantic snapshots from the existing P1 owner, never raw
 * device indices. Assignment and stock menus win before gameplay activation. */
static inline unsigned vo_overlay_controller(VoOverlay *s, unsigned player,
 unsigned held, int connected, int assignment_pending, int stock_menu,
 int supported_gameplay) {
 (void)stock_menu;(void)supported_gameplay;
 if(player!=0) return VO_NO_ACTION;
 if(!connected || assignment_pending) {
  s->controller_ready=0; s->previous=held; return VO_NO_ACTION;
 }
 unsigned edge=held & ~s->previous; s->previous=held;
 if(!held) { s->controller_ready=1; return VO_NO_ACTION; }
 if(!s->controller_ready) return VO_NO_ACTION;
 if(s->state==VO_OPEN) return vo_overlay_event(s,edge);
 return VO_NO_ACTION;
}
static inline unsigned vo_overlay_keyboard(VoOverlay *s,unsigned held) {
 unsigned edge=held & ~s->previous_keyboard; s->previous_keyboard=held;
 if(!held) { s->keyboard_ready=1; return VO_NO_ACTION; }
 if(!s->keyboard_ready) return VO_NO_ACTION;
 return vo_overlay_event(s,edge);
}
static inline void vo_overlay_hover(VoOverlay *s,int item) {
 if(s->confirm){s->hover=item;if(item==8||item==9)s->selected=(unsigned)(item-8);return;}
 s->hover=item;
 if(s->state==VO_OPEN && ((s->unavailable && (item==5||item==7)) || (!s->unavailable && item>=0 && item<7))) s->selected=(unsigned)item;
}
static inline unsigned vo_overlay_click(VoOverlay *s,int item) {
 if(s->state!=VO_OPEN) return VO_NO_ACTION;
 if(s->confirm){if(item==8||item==9){s->selected=(unsigned)(item-8);return vo_overlay_event(s,VO_ACCEPT);}return VO_NO_ACTION;}
 if(item==5) return vo_overlay_close(s); /* Resume also works on unavailable pages. */
 if(item==7) return vo_overlay_event(s,VO_BACK); /* visible Back */
 if(item<0 || item>=7 || s->unavailable) return VO_NO_ACTION;
 s->selected=(unsigned)item; return vo_overlay_event(s,VO_ACCEPT);
}
static inline void vo_overlay_wheel(VoOverlay *s,int direction,int scrollable) {
 if(scrollable && direction) vo_overlay_event(s,direction>0?VO_UP:VO_DOWN);
}
/* Complete Mirror uses the SAME state on both targets. Versus draws only
 * on P1; no state mutation or second configuration session on output 2. */
static inline int vo_overlay_output(unsigned mode,unsigned output) {
 return output==0 || (mode==VO_MIRROR && output==1);
}
#endif
