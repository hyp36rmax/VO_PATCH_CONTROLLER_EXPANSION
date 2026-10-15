"""Exercise overlay semantics against the actual Controller Expansion table."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent));from selftest import load_patcher
conditions=load_patcher().BLOBS['PAD_COND'][0]
source='#define main existing_regressions\n#include "test_runtime.c"\n#undef main\n'
source+='static const unsigned char conditions[]={'+','.join(map(str,conditions))+'};\n'
source+=r'''
int main(void){
 existing_regressions();reset();context.conditions=conditions;
 unsigned char twin[]={0xe8,0,0xe9,0,0xea,0,0xeb,0};
 unsigned char hori[]={0xf0,0,0xf1,0,0xf2,0,0xf3,0};
 unsigned char remapped[]={0xe7,0,0xe6,0,0xe2,0,0xe3,0};
 context.twinbinds=twin;context.horibinds=hori;context.padbinds=remapped;context.custom=remapped;
 XINPUT_STATE x={0};
 x.Gamepad.sThumbLY=32767;
 assert((semantic(2,&x)&15)==VO_UP && (semantic(5,&x)&15)==VO_UP);
 assert((semantic(6,&x)&15)==0 && (semantic(4,&x)&15)==0);
 x.Gamepad.sThumbLY=-32768;assert((semantic(5,&x)&15)==VO_DOWN);
 x.Gamepad.sThumbLY=0;x.Gamepad.sThumbLX=-32768;assert((semantic(2,&x)&15)==VO_LEFT);
 x.Gamepad.sThumbLX=0;x.Gamepad.wButtons=8;assert((semantic(6,&x)&15)==VO_RIGHT);
 x.Gamepad.wButtons=0;x.Gamepad.bRightTrigger=65;
 assert((semantic(4,&x)&15)==VO_UP && (semantic(1,&x)&15)==VO_UP);
 x.Gamepad.bRightTrigger=64;assert(!(semantic(4,&x)&15));
 x.Gamepad.bRightTrigger=0;x.Gamepad.wButtons=0x1000;assert(semantic(4,&x)&VO_ACCEPT);
 x.Gamepad.wButtons=0x20;assert(!(semantic(4,&x)&VO_BACK));
 x.Gamepad.wButtons=0;x.Gamepad.sThumbLY=threshold;assert(!(semantic(2,&x)&15));
 x.Gamepad.sThumbLY=threshold+1;assert(semantic(2,&x)&VO_UP);
 puts("PASS actual CE condition table, live F7 Custom/gamepad bindings, Twin/Tanita/HORI directions, trigger/deadzone boundaries, stock accept, camera Back preserved");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(source)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
