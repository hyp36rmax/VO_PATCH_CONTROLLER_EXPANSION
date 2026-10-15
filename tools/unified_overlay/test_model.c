#include <assert.h>
#include <stdio.h>
#include "model.h"
static void neutral(VoOverlay *s){vo_overlay_controller(s,0,0,1,0,0,1);}
static void opened(VoOverlay *s){vo_overlay_init(s);assert(vo_overlay_pause_result(s,1,1));}
int main(void){
 VoOverlay s;vo_overlay_init(&s);
 /* Held Start cannot open on attach. Assignment Start never also pauses. */
 assert(!vo_overlay_controller(&s,0,VO_START,1,0,0,1));
 neutral(&s);assert(!vo_overlay_controller(&s,0,VO_START,1,1,0,1));
 assert(!vo_overlay_controller(&s,0,VO_START,1,0,0,1));
 neutral(&s);assert(!vo_overlay_controller(&s,0,VO_START,1,0,1,1));
 neutral(&s);assert(!vo_overlay_controller(&s,1,VO_START,1,0,0,1));
 assert(!vo_overlay_controller(&s,0,VO_START,1,0,0,1));
 assert(!vo_overlay_controller(&s,0,VO_START,1,0,0,1));
 assert(vo_overlay_pause_result(&s,0,1));assert(s.state==VO_OPEN);vo_overlay_init(&s);
 assert(!vo_overlay_pause_result(&s,1,0));assert(s.state==VO_CLOSED);
 assert(vo_overlay_pause_result(&s,1,1));
 vo_overlay_controller(&s,0,VO_DOWN|VO_ACCEPT|VO_START,1,0,0,1);
 assert(s.state==VO_OPEN && s.selected==0 && !s.unavailable);
 neutral(&s);vo_overlay_controller(&s,1,VO_DOWN,1,0,0,1);assert(s.selected==0);
 vo_overlay_controller(&s,0,VO_DOWN,1,0,0,1);assert(s.selected==1);
 vo_overlay_controller(&s,0,VO_DOWN,1,0,0,1);assert(s.selected==1);
 neutral(&s);vo_overlay_controller(&s,0,VO_ACCEPT,1,0,0,1);assert(s.unavailable);
 neutral(&s);vo_overlay_controller(&s,0,VO_START,1,0,0,1);assert(s.state==VO_OPEN);
 vo_overlay_event(&s,VO_BACK);vo_overlay_event(&s,VO_BACK);assert(s.state==VO_DRAINING);
 assert(!vo_overlay_release(&s,0));assert(!vo_overlay_release(&s,1));
 assert(s.state==VO_CLOSED && !vo_overlay_release(&s,1));
 opened(&s);vo_overlay_keyboard(&s,VO_ACCEPT);assert(!s.unavailable);
 vo_overlay_keyboard(&s,0);vo_overlay_keyboard(&s,VO_DOWN);assert(s.selected==1);
 vo_overlay_keyboard(&s,0);vo_overlay_keyboard(&s,VO_ACCEPT);assert(s.unavailable);
 vo_overlay_click(&s,6);assert(!s.unavailable);
 vo_overlay_hover(&s,4);assert(s.selected==4);vo_overlay_click(&s,4);assert(s.unavailable);
 vo_overlay_click(&s,6);vo_overlay_wheel(&s,1,0);assert(s.selected==0);
 vo_overlay_wheel(&s,1,1);assert(s.selected==5);
 vo_overlay_click(&s,5);assert(s.state==VO_DRAINING);
 opened(&s);vo_overlay_controller(&s,0,0,0,0,0,1);
 vo_overlay_keyboard(&s,0);vo_overlay_keyboard(&s,VO_BACK);assert(s.state==VO_DRAINING);
 opened(&s);s.unavailable=1;vo_overlay_click(&s,5);assert(s.state==VO_DRAINING);
 opened(&s);vo_overlay_focus_lost(&s);assert(s.state==VO_CLOSED && !s.owns_pause);
 for(unsigned m=0;m<3;m++)for(unsigned o=0;o<3;o++)
  assert(vo_overlay_output(m,o)==(o==0||(m==VO_MIRROR&&o==1)));
 puts("PASS overlay model: assignment/menu priority, release edges, pause transaction, P1 ownership, keyboard, semantic controller, mouse, focus, output routing");
}
