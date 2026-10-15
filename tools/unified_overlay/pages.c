#include "pages.h"
#include "native_settings.h"
#include "controller_settings.h"
#include "../dual_display/settings_api.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
enum { ROOT,CONTROLLERS,DISPLAY,DISPLAY_ADV,GRAPHICS,GRAPHICS_ADV,GAME,SOLO,VS,GENERAL,APPENDIX,EXTRAS,DEBUG,DIAGNOSTICS,CONFIRM,EDITOR };
enum { BACK=100,SAVE,CANCEL,DEFAULTS,ADVANCED,RESUME,EXIT_TITLE,QUIT,DISCARD,CONFIRM_YES,
 DISPLAY_MODE=200,DISPLAY_PRIMARY,DISPLAY_SECONDARY,DISPLAY_ASPECT,
 GRAPH_RES=300,GRAPH_SKY,GRAPH_FIELD,GRAPH_MOTION,GRAPH_TEX1,GRAPH_TEX2,GRAPH_TEX3,SPLIT,
 CREDITS=400,SCORES,NO_SHOT,SE,CD,KILL1,KILL2,LOG_LEVEL,EXPORT };
static VoMenu menu;
static VoNativeSettings native;
static VoControllerSettings controller;
static VoDisplaySnapshot display;
static const VoGame *game;
static HWND owner;
static unsigned page,parent,dirty,confirm_action,command;
static int display_open;
static char notice[256];
static int (WINAPI *display_api)(unsigned,int,VoDisplaySnapshot*);
static int (WINAPI *diagnostic_api)(HWND,unsigned,int);
static void refresh(VoOverlay*);
static void row(const char *label,const char *value,unsigned id,int enabled){
 if(menu.count>=48)return;
 VoMenuRow *r=&menu.rows[menu.count++];snprintf(r->label,sizeof r->label,"%s",label);
 snprintf(r->value,sizeof r->value,"%s",value?value:"");r->id=id;r->enabled=enabled;
}
static void title(const char *text){memset(&menu,0,sizeof menu);snprintf(menu.title,sizeof menu.title,"%s",text);}
static void error(const char *text){snprintf(notice,sizeof notice,"%s",text);}
static void native_combo(const char *label,unsigned id){
 char value[192]="Unavailable";int selected=vo_native_selected(&native,id);
 if(selected>=0)vo_native_choice(&native,id,(unsigned)selected,value,sizeof value);
 row(label,value,1000+id,vo_native_count(&native,id)>0);
}
static void toggle(const char *label,unsigned id,unsigned control){row(label,vo_native_check(&native,control)?"On":"Off",id,1);}
static void actions(int defaults){if(defaults)row("RESTORE DEFAULTS",NULL,DEFAULTS,1);row("SAVE",NULL,SAVE,1);row("CANCEL",NULL,CANCEL,1);row("BACK",NULL,BACK,1);}
static void close_transaction(void){
 if(display_open&&display_api){display_api(VO_DISPLAY_CANCEL,0,&display);display_open=0;}
 vo_native_end(&native);vo_controller_end(&controller);dirty=0;
}
void vo_pages_end(void){close_transaction();game=NULL;owner=NULL;}
unsigned vo_pages_command(void){unsigned result=command;command=0;return result;}
static void show(VoOverlay *s,unsigned destination){page=destination;s->selected=0;refresh(s);}
static void confirm(VoOverlay *s,unsigned action){parent=page;confirm_action=action;page=CONFIRM;s->selected=0;s->controller_ready=s->keyboard_ready=0;s->confirm=1;refresh(s);}
static void leave(VoOverlay *s){
 if(page==DISPLAY_ADV){show(s,DISPLAY);return;}
 if(page==GRAPHICS_ADV){show(s,GRAPHICS);return;}
 if(page==CONFIRM){s->confirm=0;show(s,parent);return;}
 if(dirty){confirm(s,DISCARD);return;}
 if(page==EDITOR){close_transaction();show(s,CONTROLLERS);return;}
 close_transaction();show(s,page>=SOLO&&page<=APPENDIX?GAME:page==DEBUG||page==DIAGNOSTICS?EXTRAS:ROOT);
}
static int open_native(unsigned category){
 if(vo_native_begin(&native,owner,game->mode,category))return 1;
 error("Original settings could not be opened. No changes saved.");return 0;
}
static int save_native(void){
 int was_paused=*game->inactive!=0;
 if(native.category==VO_NATIVE_GRAPHICS&&!was_paused)game->pause(0);
 int result=vo_native_commit(&native);
 if(native.category==VO_NATIVE_GRAPHICS){
  if(was_paused&&!*game->inactive)game->pause(0);
  else if(!result&&!was_paused)game->resume();
 }
 return result;
}
static unsigned navigate(VoOverlay *s,unsigned edge){
 if(edge&VO_BACK){if(page==ROOT)vo_overlay_close(s);else leave(s);return VO_NO_ACTION;}
 if(edge&(VO_UP|VO_DOWN)){
  int delta=edge&VO_UP?-1:1;
  for(unsigned tries=0;tries<menu.count;tries++){
   s->selected=(s->selected+menu.count+delta)%menu.count;
   if(menu.rows[s->selected].enabled)break;
  }
  return VO_NO_ACTION;
 }
 if(!(edge&(VO_ACCEPT|VO_LEFT|VO_RIGHT))||s->selected>=menu.count)return VO_NO_ACTION;
 VoMenuRow selected=menu.rows[s->selected];if(!selected.enabled)return VO_NO_ACTION;
 unsigned id=selected.id;int delta=edge&VO_LEFT?-1:1;
 /* Horizontal input adjusts settings; it must never activate Save, a page,
  * or a destructive confirmation. Confirmation always needs fresh Accept. */
 if(!(edge&VO_ACCEPT)){
  if(page==CONFIRM){s->selected=s->selected==0?1:0;return VO_NO_ACTION;}
  int adjustable=(id>=DISPLAY_MODE&&id<=DISPLAY_ASPECT)||
   (id>=GRAPH_RES&&id<=SPLIT)||(id>=2000&&id<4000)||id==5000||id==LOG_LEVEL||(id>=6000&&id<6020&&((id-6000)%10==0||(id-6000)%10==3))||(id>=7000&&id<7012);
  if(!adjustable)return VO_NO_ACTION;
 }
 if(id==BACK){leave(s);return VO_NO_ACTION;}
 if(page==CONFIRM){
  unsigned action=confirm_action;s->confirm=0;
  if(id!=CONFIRM_YES){show(s,parent);return VO_NO_ACTION;}
  if(action==DISCARD){close_transaction();show(s,parent==EDITOR?CONTROLLERS:parent>=SOLO&&parent<=APPENDIX?GAME:ROOT);return VO_NO_ACTION;}
  if(action==EXIT_TITLE){if(s->exit_allowed)s->exit_requested=1;else show(s,ROOT);return VO_NO_ACTION;}
  command=action==QUIT?0x9c41:action==CREDITS?0x51:action==KILL1?0x9c61:0x9c62;
  vo_overlay_close(s);return VO_NO_ACTION;
 }
 if(id==RESUME){vo_overlay_close(s);return VO_NO_ACTION;}
 if(id==EXIT_TITLE||id==QUIT||id==KILL1||id==KILL2||id==CREDITS){confirm(s,id);return VO_NO_ACTION;}
 if(id==CANCEL){close_transaction();show(s,page==EDITOR?CONTROLLERS:page>=SOLO&&page<=APPENDIX?GAME:ROOT);return VO_NO_ACTION;}
 if(id==SAVE){
  if(page==EDITOR){
   if(!vo_controller_save(&controller)){error("Bindings not saved. Check assignments and file access.");refresh(s);return VO_NO_ACTION;}
   error("Bindings saved.");
  }else if(page==DISPLAY){
   if(!display_api||!display_api(VO_DISPLAY_APPLY,0,&display)){error("Display settings not saved. Check display selections and access.");refresh(s);return VO_NO_ACTION;}
   if(native.host&&!save_native()){error("Local VS split could not be applied.");refresh(s);return VO_NO_ACTION;}
   error("Display settings saved. Restart Virtual-On to apply.");
  }else if(!save_native()){error("Settings could not be applied. Draft retained.");refresh(s);return VO_NO_ACTION;}
  else error("Settings saved.");
  unsigned next=page==EDITOR?CONTROLLERS:page>=SOLO&&page<=APPENDIX?GAME:ROOT;
  close_transaction();show(s,next);return VO_NO_ACTION;
 }
 if(id==DEFAULTS){if(page==EDITOR?vo_controller_defaults(&controller):vo_native_defaults(&native))dirty=1;refresh(s);return VO_NO_ACTION;}
 if(id==ADVANCED){show(s,page==DISPLAY?DISPLAY_ADV:GRAPHICS_ADV);return VO_NO_ACTION;}
 if(id>=7000&&id<7012){
  unsigned slot=id-7000;int changed=0;
  if((edge&VO_ACCEPT)&&(controller.kind==1||controller.kind==4))changed=vo_controller_capture(&controller,slot);
  else {int count=vo_controller_count(&controller,slot),current=vo_controller_selected(&controller,slot);if(count>0)changed=vo_controller_select(&controller,slot,(current+count+delta)%count);}
  if(changed)dirty=1;
  s->keyboard_ready=s->controller_ready=0;
 }else if(id>=6000&&id<6100){
  unsigned player=(id-6000)/10,action=(id-6000)%10;unsigned kind=(unsigned)game->devices[player];
  if(action==0){static const unsigned order[]={1,2,4,5,6,7,8,3,0};unsigned i=0;while(i<9&&order[i]!=kind)i++;unsigned next=order[(i+9+delta)%9];if(!vo_controller_profile(game,player,next))error("Profile could not be saved. Previous settings retained.");}
  else if(action==1){int paused=*game->inactive!=0;if(!paused)game->pause(0);
   int assigned=vo_controller_assign(owner,player,kind);
   if(paused){if(!*game->inactive)game->pause(0);}else game->resume();
   if(!assigned)error("Controller selection cancelled or unavailable.");s->keyboard_ready=s->controller_ready=0;}
  else if(action==2){if(vo_controller_begin(&controller,game,owner,player,kind)){show(s,EDITOR);return VO_NO_ACTION;}error("Original controller settings could not be opened.");}
  else if(action==3){int value=vo_controller_deadzone(game,player,-1);value+=delta*5;if(value<5)value=95;if(value>95)value=5;if(vo_controller_deadzone(game,player,value)<0)error("Deadzone could not be saved.");}
 }else if(id==5000){
  if(vo_native_radio(&native,1078,1079,vo_native_check(&native,1078)?1079:1078))dirty=1;
 }else if(id>=3000&&id<4000){
  if(vo_native_click(&native,id-2000))dirty=1;
 }else if(id>=1000&&id<3000){
  unsigned control=id-1000;int count=vo_native_count(&native,control),current=vo_native_selected(&native,control);
  if(count&&vo_native_select(&native,control,(unsigned)((current+count+delta)%count)))dirty=1;
 }else if(id>=DISPLAY_MODE&&id<=DISPLAY_ASPECT){
  int value;unsigned operation;
  if(id==DISPLAY_MODE){int n=display.count>1?3:1;value=(display.mode+n+delta)%n;operation=VO_DISPLAY_MODE;}
  else if(id==DISPLAY_ASPECT){value=(display.aspect+4+delta)%4;operation=VO_DISPLAY_ASPECT;}
  else{int current=id==DISPLAY_PRIMARY?display.primary:display.secondary;
   if(!display.count)return VO_NO_ACTION;
   value=(current+(int)display.count+delta)%(int)display.count;
   operation=id==DISPLAY_PRIMARY?VO_DISPLAY_PRIMARY:VO_DISPLAY_SECONDARY;
  }
  if(display_api(operation,value,&display))dirty|=!!display.dirty;
 }else if(id>=GRAPH_RES&&id<=SPLIT){
  int ok=0;
  switch(id){
   case GRAPH_RES:ok=vo_native_radio(&native,1056,1057,vo_native_check(&native,1056)?1057:1056);break;
   case GRAPH_FIELD:ok=vo_native_radio(&native,1058,1059,vo_native_check(&native,1058)?1059:1058);break;
   case GRAPH_MOTION:ok=vo_native_radio(&native,1068,1069,vo_native_check(&native,1068)?1069:1068);break;
   case SPLIT:ok=vo_native_radio(&native,1070,1073,vo_native_check(&native,1073)?1070:1073);break;
   default:ok=vo_native_click(&native,id==GRAPH_SKY?1075:id==GRAPH_TEX1?1077:id==GRAPH_TEX2?1079:1078);break;
  }
  if(ok)dirty=1;
 }else if(id==NO_SHOT||id==SE||id==CD||id==SCORES){
  PostMessageW(owner,WM_COMMAND,id==NO_SHOT?0x9c47:id==SE?0x9c5b:id==CD?0x9c5c:0x9c67,0);
 }else if(id==LOG_LEVEL){
  int current=diagnostic_api(owner,0,0),next=(current+4+delta)%4;
  if(diagnostic_api(owner,1,next))error(next?"Saved. Restart Virtual-On to enable logging.":"Logging Off. Existing logs retained.");
  else error("Logging preference could not be saved.");
 }else if(id==EXPORT){diagnostic_api(owner,2,0);}
 else if(id>=10&&id<10+CONFIRM){
  unsigned destination=id-10;
  if(destination==DISPLAY){
   display=(VoDisplaySnapshot){0};display.size=sizeof display;
   if(!display_api||!display_api(VO_DISPLAY_BEGIN,0,&display)){error("Display settings unavailable. No changes saved.");refresh(s);return VO_NO_ACTION;}
   display_open=1;
   if(!open_native(VO_NATIVE_GRAPHICS)){close_transaction();refresh(s);return VO_NO_ACTION;}
  }else if(destination==GRAPHICS){if(!open_native(VO_NATIVE_GRAPHICS)){refresh(s);return VO_NO_ACTION;}}
  else if(destination>=SOLO&&destination<=APPENDIX){if(!open_native(destination-SOLO+VO_NATIVE_1P)){refresh(s);return VO_NO_ACTION;}}
  show(s,destination);return VO_NO_ACTION;
 }
 refresh(s);return VO_NO_ACTION;
}
static void refresh(VoOverlay *s){
 unsigned selected=s->selected;
 switch(page){
 case ROOT:
  title("Virtual On EX");row("CONTROLLERS",NULL,10+CONTROLLERS,1);row("DISPLAY",NULL,10+DISPLAY,1);row("GRAPHICS",NULL,10+GRAPHICS,1);row("GAME SETTINGS",NULL,10+GAME,1);row("EXTRAS",NULL,10+EXTRAS,1);
  row("SESSION",NULL,0,0);row("RESUME",NULL,RESUME,1);if(s->exit_allowed)row("EXIT TO TITLE",NULL,EXIT_TITLE,1);row("QUIT GAME",NULL,QUIT,1);break;
 case CONTROLLERS:
  title("CONTROLLERS");
  if(!vo_controller_available(game)){row("Controller Expansion is not enabled.",NULL,0,0);row("Original controls remain available in F7.",NULL,0,0);row("BACK",NULL,BACK,1);break;}
  for(unsigned p=0;p<2;p++){
   static const char *profiles[]={"Keyboard (Real)","Gamepad (XInput)","Twin-Stick (XInput)","Keyboard (Simple)","Twin-Stick (Custom)","Twin-Stick (Tanita)","Twin-Stick (HORI EX)","Twin-Stick (Raphnet DC)","Twin-Stick (Raphnet Saturn)"};
   unsigned kind=(unsigned)game->devices[p],base=6000+p*10;int keyboard=kind==0||kind==3;
   row(p?"PLAYER 2":"PLAYER 1",NULL,0,0);row("Profile",kind<9?profiles[kind]:"Unknown",base,1);
   row("Controller",keyboard?"Keyboard":"Select physical controller >",base+1,!keyboard);
   int status=vo_controller_status(p,kind);row("Status",status<0?"Awaiting input":status?"Connected":"Disconnected",0,0);
   if(kind==0||kind==1||kind==3||kind==4)row(keyboard?"Configure Keys":"Configure Buttons",">",base+2,1);
   if(kind==1||kind==2||kind==4||kind==6){char value[24];snprintf(value,sizeof value,"%d%%",vo_controller_deadzone(game,p,-1));row("Stick Deadzone",value,base+3,1);}
  }
  row("BACK",NULL,BACK,1);break;
 case EDITOR:{
  static const char *action_labels[]={"Move Forward","Move Backward","Move Left","Move Right","Turn Left","Turn Right","Left Weapon","Right Weapon","Center Weapon","Dash","Jump","Guard"};
  static const char *lever[]={"Up","Down","Left","Right","Trigger","Dash"};
  char heading[96];snprintf(heading,sizeof heading,"PLAYER %u : %s",controller.player+1,controller.kind==4?"CUSTOM TWIN-STICK":controller.kind==0?"KEYBOARD (REAL)":controller.kind==3?"KEYBOARD (SIMPLE)":"GAMEPAD CONTROLS");title(heading);
  for(unsigned i=0;i<12;i++){
   int twin=controller.kind==0||controller.kind==4;
   if(twin&&(i==0||i==6))row(i?"RIGHT STICK":"LEFT STICK",NULL,0,0);
   char value[192]="Unavailable";int choice=vo_controller_selected(&controller,i);
   if(choice>=0)vo_controller_choice(&controller,i,choice,value,sizeof value);
   row(twin?lever[i%6]:action_labels[i],value,7000+i,choice>=0);
  }
  actions(1);break;
 }
 case DISPLAY:{
  static const char *modes[]={"Single Display","Dual Display Versus","Dual Display Mirror"};static const char *aspects[]={"4:3","16:9","21:9","32:9"};
  title("DISPLAY");row("Display Mode",display.mode>=0&&display.mode<3?modes[display.mode]:"Saved mode unavailable",DISPLAY_MODE,1);
  row("Primary Display",display.primary>=0&&display.primary<(int)display.count?display.names[display.primary]:"Automatic / saved display unavailable",DISPLAY_PRIMARY,display.count>0);
  if(display.mode)row("Secondary Display",display.secondary>=0&&display.secondary<(int)display.count?display.names[display.secondary]:"Saved display unavailable",DISPLAY_SECONDARY,display.count>0);
  row("Game Aspect Ratio",display.aspect>=0&&display.aspect<4?aspects[display.aspect]:"Saved aspect unavailable",DISPLAY_ASPECT,display.mode!=1);
  row("Advanced Settings",">",ADVANCED,1);row("APPLY CHANGES",NULL,SAVE,1);row("CANCEL",NULL,CANCEL,1);row("BACK",NULL,BACK,1);break;
 }
 case DISPLAY_ADV:title("ADVANCED DISPLAY");row("Local VS Split",vo_native_check(&native,1073)?"Horizontal":"Vertical",SPLIT,1);row("BACK",NULL,BACK,1);break;
 case GRAPHICS:
  title("GRAPHICS");row("Resolution",vo_native_check(&native,1056)?"720p":"1080p",GRAPH_RES,1);toggle("Sky",GRAPH_SKY,1075);row("Field Graphic",vo_native_check(&native,1058)?"Rich":"Normal",GRAPH_FIELD,1);row("Motion",vo_native_check(&native,1068)?"30 FPS":"60 FPS",GRAPH_MOTION,1);
  row("Advanced Settings",">",ADVANCED,1);row("APPLY CHANGES",NULL,SAVE,1);row("CANCEL",NULL,CANCEL,1);row("BACK",NULL,BACK,1);break;
 case GRAPHICS_ADV:title("ADVANCED GRAPHICS");toggle("Machine(1P)",GRAPH_TEX1,1077);toggle("Machine(2P)",GRAPH_TEX2,1079);toggle("Effects",GRAPH_TEX3,1078);row("BACK",NULL,BACK,1);break;
 case GAME:title("GAME SETTINGS");row("1P MODE",">",10+SOLO,1);row("2P VS",">",10+VS,1);row("GENERAL",">",10+GENERAL,1);row("APPENDIX",">",10+APPENDIX,1);row("BACK",NULL,BACK,1);break;
 case SOLO:
  title("1P MODE");row("PLAY TIME",NULL,0,0);native_combo("Stage 1-5",1000);native_combo("Penalty Stage",1001);native_combo("Stage 6-8",1002);native_combo("Last Stage",1003);
  row("MATCH COUNT",NULL,0,0);native_combo("Stage 1-5",1004);native_combo("Penalty Stage",1005);native_combo("Stage 6-8",1006);native_combo("Difficulty",1007);actions(1);break;
 case VS:title("2P VS");native_combo("Play Time",1013);native_combo("Match Count",1014);actions(1);break;
 case GENERAL:title("GENERAL");
  row("View Replay",vo_native_check(&native,1074)?"On":"Off",2000+1074,1);row("View Posing",vo_native_check(&native,1075)?"On":"Off",2000+1075,1);row("Display Ranking",vo_native_check(&native,1076)?"On":"Off",2000+1076,1);row("Quick VR Select 1P",vo_native_check(&native,1079)?"On":"Off",2000+1079,1);row("Quick VR Select 2P / Network VS",vo_native_check(&native,1080)?"On":"Off",2000+1080,1);row("Demo Movie",vo_native_check(&native,1081)?"On":"Off",2000+1081,1);actions(1);break;
 case APPENDIX:title("APPENDIX");row("Machine Color Select",vo_native_check(&native,1076)?"On":"Off",2000+1076,1);row("Enemy Color Random",vo_native_check(&native,1077)?"On":"Off",2000+1077,1);row("Color Format",vo_native_check(&native,1078)?"32000 color":"64000 color",5000,1);actions(1);break;
 case EXTRAS:title("EXTRAS");row("GAME UTILITIES",NULL,0,0);row("Credits",">",CREDITS,*game->mode==4);row("Scorekeeping",">",SCORES,1);row("DEBUG SETTINGS",">",10+DEBUG,1);row("DIAGNOSTICS",">",10+DIAGNOSTICS,diagnostic_api!=NULL);row("BACK",NULL,BACK,1);break;
 case DEBUG:{
  int j=(uintptr_t)game->mode==0x1adcdf0;
  title("DEBUG SETTINGS");row("No Shot",*(LONG*)(uintptr_t)(j?0x64efd8:0x652fd8)?"On":"Off",NO_SHOT,1);row("SE",*(LONG*)(uintptr_t)(j?0x6b89ac:0x6bcc4c)?"Off":"On",SE,1);row("CD",*(LONG*)(uintptr_t)(j?0x63b430:0x63f430)?"Off":"On",CD,1);row("Kill Player 1",">",KILL1,1);row("Kill Player 2",">",KILL2,1);row("BACK",NULL,BACK,1);break;
 }
 case DIAGNOSTICS:{
  static const char *levels[]={"Off","Normal","Detailed","Development"};int level=diagnostic_api?diagnostic_api(owner,0,0):0;
  title("DIAGNOSTICS");row("Help identify controller, display,",NULL,0,0);row("startup and configuration issues.",NULL,0,0);row("Logging is disabled by default.",NULL,0,0);row("Logging Level",levels[level>=0&&level<4?level:0],LOG_LEVEL,diagnostic_api!=NULL);row("Export Diagnostics",">",EXPORT,diagnostic_api!=NULL);row("Local logs. No automatic uploads.",NULL,0,0);row("BACK",NULL,BACK,1);break;
 }
 case CONFIRM:
  title(confirm_action==DISCARD?"UNSAVED CHANGES":confirm_action==QUIT?"QUIT GAME":confirm_action==EXIT_TITLE?"EXIT TO TITLE":"CONFIRM ACTION");
  row("CANCEL",NULL,CANCEL,1);row(confirm_action==DISCARD?"DISCARD CHANGES":confirm_action==QUIT?"QUIT GAME":confirm_action==EXIT_TITLE?"EXIT TO TITLE":"CONTINUE",NULL,CONFIRM_YES,1);
  row(confirm_action==DISCARD?"Pending changes will be discarded.":"Current match progress may be lost.",NULL,0,0);break;
 }
 snprintf(menu.notice,sizeof menu.notice,"%s",notice);
 s->menu=&menu;s->selected=selected<menu.count?selected:0;
 if(menu.count&&!menu.rows[s->selected].enabled){for(unsigned i=0;i<menu.count;i++)if(menu.rows[i].enabled){s->selected=i;break;}}
}
void vo_pages_refresh(VoOverlay *s){if(game&&(page==ROOT||page==CONTROLLERS||page==DEBUG))refresh(s);}
void vo_pages_begin(VoOverlay *s,const VoGame *g,HWND h){
 close_transaction();game=g;owner=h;page=ROOT;command=0;notice[0]=0;
 HMODULE module=GetModuleHandleW(L"vodisplay.dll");
 display_api=module?(void*)GetProcAddress(module,"VonDisplayTransaction"):NULL;
 diagnostic_api=module?(void*)GetProcAddress(module,"VonOverlayDiagnostics"):NULL;
 s->navigate=navigate;s->selected=6;refresh(s);
}
