"""Execute production preference reads/writes against a Win32-profile API double."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent;s=(here/'mode_select.c').read_text()
read=s[s.index('static void read_preferences'):s.index('static HWND combo')]
save=s[s.index('static int save_int'):s.index('static LRESULT CALLBACK')]
fixture=r'''
#include <assert.h>
#include <wchar.h>
#include <stdlib.h>
#include <stdio.h>
#include "mode_config.h"
typedef wchar_t WCHAR;static WCHAR config[32]=L"one-authority";
static VoPreference pref;static wchar_t mode[32],aspect[32];static int legacy,writes;
static char id1[512],id2[512];
static void load_id(const WCHAR *key,char *out){strcpy(out,!wcscmp(key,L"Player1")?id1:id2);}
static int GetPrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *fallback,WCHAR *out,unsigned n,const WCHAR *file){assert(!wcscmp(section,L"Presentation")&&!wcscmp(file,config)&&n==32);const WCHAR *v=!wcscmp(key,L"Mode")?mode:aspect;wcscpy(out,v[0]?v:fallback);return (int)wcslen(out);}
static unsigned GetPrivateProfileIntW(const WCHAR *section,const WCHAR *key,int fallback,const WCHAR *file){assert(!wcscmp(section,L"Presentation")&&!wcscmp(file,config));if(!wcscmp(key,L"MirrorPlayer1"))return legacy;const WCHAR *v=!wcscmp(key,L"Mode")?mode:aspect;return v[0]?(unsigned)wcstol(v,NULL,10):(unsigned)fallback;}
static int WritePrivateProfileStringW(const WCHAR *section,const WCHAR *key,const WCHAR *value,const WCHAR *file){assert(!wcscmp(section,L"Presentation")&&!wcscmp(file,config));wcscpy(!wcscmp(key,L"Mode")?mode:aspect,value);writes++;return 1;}
'''
body=r'''
int main(void){
 read_preferences();assert(pref.mode==VO_SINGLE&&pref.aspect==VO_WIDE&&!writes);
 strcpy(id1,"A");strcpy(id2,"B");legacy=1;read_preferences();assert(pref.mode==VO_MIRROR&&!writes);
 assert(save_int(L"Mode",VO_SINGLE)&&save_int(L"GameAspect",VO_ULTRA));read_preferences();assert(pref.mode==VO_SINGLE&&pref.aspect==VO_ULTRA&&writes==2);
 save_int(L"Mode",VO_VERSUS);read_preferences();VoPreference saved=pref;
 VoMonitor m[2]={{{0},{0,0,2560,1440},1,1},{{0},{2560,0,1920,1080},0,1}};strcpy(m[0].id,"A");strcpy(m[1].id,"B");VoSelection selection;
 assert(vo_select(m,1,&pref,31,&selection)&&selection.mode==VO_SINGLE);assert(!memcmp(&pref,&saved,sizeof pref)&&writes==3);
 read_preferences();assert(vo_select(m,2,&pref,31,&selection)&&selection.mode==VO_VERSUS&&pref.aspect==VO_ULTRA&&writes==3);
 puts("PASS production preference persistence, fresh defaults, legacy migration, explicit override and disconnect/reconnect without preference writes; Win32 API double");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'prefs.c';p.write_text(fixture+read+save+body)
 subprocess.run(['clang','-std=c11','-fsanitize=address,undefined','-I'+str(here),str(p),'-o',td+'/prefs'],check=True);subprocess.run([td+'/prefs'],check=True)
