"""Exercise the actual overlay adapter and F5 serializer with Win32 API doubles."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'test_f5_store.py'))
fixture=base['fixture']+base['reader']+base['body'](base['source'])
fixture+=r'''
#define __declspec(x)
#define WINAPI
static unsigned count=2,dirty,save_error;
static int busy,discovery_ok=1,discoveries;
static VoMonitor monitors[VO_MAX_MONITORS];
static WCHAR names[VO_MAX_MONITORS][256];
static int path_config(void){return 1;}
static int discover(void){discoveries++;return discovery_ok;}
static void event(unsigned code,int result){assert(code==4&&result==1);}
static int WideCharToMultiByte(unsigned cp,unsigned flags,const WCHAR *in,int len,char *out,int size,void *a,void *b){(void)cp;(void)flags;(void)len;(void)a;(void)b;return (int)wcstombs(out,in,size)+1;}
#include "overlay_settings.h"
int main(void){
 wcscpy(config,L"C:\\Games With Spaces\\player-displays.ini");
 strcpy(monitors[0].id,"monitor-a");strcpy(monitors[1].id,"monitor-b");
 monitors[0].available=monitors[1].available=1;monitors[0].primary=1;monitors[1].desktop.x=1920;
 wcscpy(names[0],L"Primary display");wcscpy(names[1],L"Secondary display");
 VoDisplaySnapshot s={0};s.size=sizeof s;
 for(int mode=0;mode<3;mode++){
  committed=(VoPreference){VO_SINGLE,VO_WIDE,"monitor-a","monitor-b"};reset();exists=1;
  assert(VonDisplayTransaction(VO_DISPLAY_BEGIN,0,&s)&&busy);
  assert(!VonDisplayTransaction(VO_DISPLAY_BEGIN,0,&s));
  assert(VonDisplayTransaction(VO_DISPLAY_MODE,mode,&s)&&!moved);
  assert(VonDisplayTransaction(VO_DISPLAY_ASPECT,VO_SUPER,&s)&&!moved);
  assert(VonDisplayTransaction(VO_DISPLAY_APPLY,0,&s)&&moved&&s.restart&&!s.dirty);
  assert(committed.mode==mode&&committed.aspect==VO_SUPER);
  assert(VonDisplayTransaction(VO_DISPLAY_CANCEL,0,&s)&&!busy);
 }
 reset();assert(VonDisplayTransaction(VO_DISPLAY_BEGIN,0,&s));
 VoPreference before=committed;
 assert(VonDisplayTransaction(VO_DISPLAY_MODE,VO_SINGLE,&s));
 assert(VonDisplayTransaction(VO_DISPLAY_CANCEL,0,&s)&&!moved&&!memcmp(&before,&committed,sizeof before));
 assert(!VonDisplayTransaction(VO_DISPLAY_APPLY,0,&s));
 assert(VonDisplayTransaction(VO_DISPLAY_BEGIN,0,&s));
 assert(VonDisplayTransaction(VO_DISPLAY_MODE,VO_VERSUS,&s));
 discovery_ok=0;assert(!VonDisplayTransaction(VO_DISPLAY_APPLY,0,&s)&&s.error==VO_DISPLAY_DISCOVERY&&!moved);
 discovery_ok=1;readonly=1;assert(!VonDisplayTransaction(VO_DISPLAY_APPLY,0,&s)&&s.error==VO_DISPLAY_WRITE&&s.dirty&&!moved);
 readonly=0;assert(VonDisplayTransaction(VO_DISPLAY_APPLY,0,&s)&&moved);
 assert(VonDisplayTransaction(VO_DISPLAY_CANCEL,0,&s));
 count=1;assert(VonDisplayTransaction(VO_DISPLAY_BEGIN,0,&s));
 assert(s.mode==VO_VERSUS); /* saved dual preference survives temporary fallback */
 assert(!VonDisplayTransaction(VO_DISPLAY_MODE,VO_MIRROR,&s)&&s.error==VO_SETTINGS_MODE);
 assert(VonDisplayTransaction(VO_DISPLAY_CANCEL,0,&s));
 assert(!busy&&discoveries>0);
 puts("PASS overlay/F5 shared transaction: all modes, atomic Apply, discarded Cancel, failure retention/retry, exclusive ownership, missing-display preference preservation");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text(fixture)
 subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
