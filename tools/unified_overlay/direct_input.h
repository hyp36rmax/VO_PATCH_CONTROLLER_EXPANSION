/* Non-modal operations over controller.c's existing owners, readers and rules.
 * No independent device enumeration or alternate ownership table. */
static Prompt direct_prompt;
static int direct_active;
/* Begin: assignment=0, binding=1. Poll returns pending=0, assigned=1,
 * input=e0..f3, cancelled/error=-1, multiple Start=-2. */
__declspec(dllexport) int WINAPI VonInputBegin(DWORD player,DWORD kind,int capture,int threshold){
 if(player>1||busy||direct_active||von_kind_family(kind)<0)return 0;
 if(capture&&(!von_owned_source(owners,player,kind)||kind==7||kind==8))return 0;
 ZeroMemory(&direct_prompt,sizeof direct_prompt);
 direct_prompt.player=player;direct_prompt.kind=kind;direct_prompt.capture=capture;
 direct_prompt.threshold=threshold;direct_prompt.started=GetTickCount();
 direct_active=busy=1;return 1;
}
__declspec(dllexport) void WINAPI VonInputCancel(void){if(direct_active){direct_active=0;busy=0;}}
__declspec(dllexport) int WINAPI VonInputPoll(void){
 Prompt *p=&direct_prompt;if(!direct_active)return -1;
 if(GetTickCount()-p->started>30000){VonInputCancel();return -1;}
 if(p->capture){
  XINPUT_STATE state;
  if(raw_state(owners[p->player].source,&state)){owners[p->player].source=-1;VonInputCancel();return -1;}
  int input=von_capture(&p->edge,von_inputs(state.Gamepad.wButtons,state.Gamepad.bLeftTrigger,state.Gamepad.bRightTrigger,state.Gamepad.sThumbLX,state.Gamepad.sThumbLY,state.Gamepad.sThumbRX,state.Gamepad.sThumbRY,p->threshold));
  if(input){suppress_start[0]=suppress_start[1]=1;VonInputCancel();}return input;
 }
 unsigned connected=0,held=0;
 for(int i=von_source_first(p->kind);i<von_source_end(p->kind);i++){
  int start;if(source_start(i,&start))continue;connected|=1u<<i;if(start)held|=1u<<i;
 }
 int candidate=von_start_edge(&p->ready,connected,held);
 if(candidate==-2)return -2;
 if(candidate>=0&&von_claim(owners,p->player,candidate)){
  owner_kind[p->player]=p->kind;suppress_start[0]=suppress_start[1]=1;
  sample_known=0;VonInputCancel();return 1;
 }
 return 0;
}
/* Identity is session-scoped source identity, never a fabricated product ID. */
__declspec(dllexport) int WINAPI VonInputIdentity(DWORD player,DWORD kind){
 if(!von_owned_source(owners,player,kind))return -1;
 return owners[player].source;
}
