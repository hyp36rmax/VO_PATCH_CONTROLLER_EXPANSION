"""Reproduce P05's missed callback using its exact committed bridge.
The event fixture follows the separately verified Retail/JPRE backbuffer/Flip path;
it is deterministic host evidence, not captured Windows state values.
"""
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
old=subprocess.check_output(['git','show','13c402c7e513bd948ff05b6a54f2470a271eeb70:tools/dual_display/state_bridge.c'],cwd=here,text=True)
api=(here/'test_bridge.c').read_text().split('#include "state_bridge.c"')[0]
main='''
int main(void){
 void *primary=(void*)1,*backbuffer=(void*)2;
 /* Game locks/unlocks backbuffer, then flips primary. P05 has no Flip callback. */
 if(backbuffer==primary)vo_capture_policy();
 assert(!checked&&!profile&&vo_completed_policy()==VO_PRIMARY_ONLY);
 puts("REPRODUCED P05: backbuffer Unlock -> primary Flip leaves bridge uncalled and falsely PRIMARY_ONLY");
}
'''
with tempfile.TemporaryDirectory() as d:
 d=Path(d);(d/'old.c').write_text(old);(d/'test.c').write_text(api+'\n#include "old.c"\n'+main)
 subprocess.run(['clang','-std=c11','-I'+str(here),'-fsanitize=address,undefined',str(d/'test.c'),'-o',str(d/'test')],check=True)
 subprocess.run([str(d/'test')],check=True)
