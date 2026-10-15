"""Exercise production asynchronous capture with existing ownership rules."""
from pathlib import Path
import tempfile,subprocess
here=Path(__file__).resolve().parent
source=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#define __declspec(x)
#define WINAPI
#define ZeroMemory(p,n) memset(p,0,n)
typedef unsigned DWORD;
#include "../../input/controller_logic.h"
typedef struct {struct {uint16_t wButtons;unsigned char bLeftTrigger,bRightTrigger;short sThumbLX,sThumbLY,sThumbRX,sThumbRY;} Gamepad;} XINPUT_STATE;
typedef struct {unsigned player;int kind,capture,threshold;DWORD started;unsigned ready;VonCapture edge;} Prompt;
static VonOwner owners[2]={{-1,0},{-1,0}};
static int owner_kind[2],suppress_start[2],busy;
static unsigned sample_known,clock_ms,connected,starts;
static XINPUT_STATE pad;
static DWORD GetTickCount(void){return clock_ms;}
static DWORD source_start(int i,int *start){*start=!!(starts&(1u<<i));return connected&(1u<<i)?0:1;}
static DWORD raw_state(int i,XINPUT_STATE *s){*s=pad;return i>=0&&(connected&(1u<<i))?0:1;}
#include "direct_input.h"
static void neutral(void){starts=0;assert(VonInputPoll()==0);}
int main(void){
 connected=1023;
 for(unsigned kind=1;kind<=8;kind++){
  if(von_kind_family(kind)<0)continue;
  owners[0]=(VonOwner){-1,0};owners[1]=(VonOwner){-1,0};
  int a=von_source_first(kind),b=a+1;
  starts=1u<<a;assert(VonInputBegin(0,kind,0,0));assert(busy);assert(VonInputPoll()==0);
  neutral();starts=1u<<a;assert(VonInputPoll()==1&&!busy&&owners[0].source==a&&suppress_start[0]);
  assert(VonInputBegin(1,kind,0,0));neutral();starts=1u<<b;assert(VonInputPoll()==1&&owners[1].source==b);
  assert(VonInputBegin(0,kind,0,0));neutral();starts=1u<<b;assert(VonInputPoll()==1&&owners[0].source==b&&owners[1].source==a);
  assert(VonInputIdentity(0,kind)==b);
  assert(VonInputBegin(0,kind,0,0));VonInputCancel();assert(!busy&&owners[0].source==b);
  assert(VonInputBegin(0,kind,0,0));neutral();starts=(1u<<a)|(1u<<b);assert(VonInputPoll()==-2&&owners[0].source==b);VonInputCancel();
 }
 owners[0]=(VonOwner){0,1};connected=1;pad.Gamepad.wButtons=0x1000;
 assert(VonInputBegin(0,1,1,13080));assert(VonInputPoll()==0);pad.Gamepad.wButtons=0;assert(VonInputPoll()==0);pad.Gamepad.wButtons=0x3000;assert(VonInputPoll()==0);pad.Gamepad.wButtons=0;assert(VonInputPoll()==0);pad.Gamepad.wButtons=0x1000;assert(VonInputPoll()==0xe0&&!busy);
 assert(VonInputBegin(0,4,1,13080));connected=0;assert(VonInputPoll()==-1&&owners[0].source==-1&&!busy);
 owners[0]=(VonOwner){0,1};assert(VonInputBegin(0,1,0,0));clock_ms+=30001;assert(VonInputPoll()==-1&&owners[0].source==0&&!busy);
 assert(!VonInputBegin(2,1,0,0));assert(!VonInputBegin(0,0,0,0));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(source)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS production direct input: all families/P1/P2/swap/Cancel/neutral/fresh Start/multiple/disconnect/timeout/binding single-input/ownership identity')
