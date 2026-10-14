#ifndef VO_STATE_BRIDGE_H
#define VO_STATE_BRIDGE_H
#include <stdio.h>
void vo_capture_policy(void);
void vo_capture_flip_policy(void);
void vo_policy_log(FILE *log);
unsigned vo_completed_policy(void);
unsigned vo_unknown_policy_count(void);
unsigned vo_unknown_policy_value(unsigned i);
#endif
