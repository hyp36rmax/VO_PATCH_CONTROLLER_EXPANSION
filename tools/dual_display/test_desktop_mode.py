"""Execute the actual patched desktop-query block with API doubles.
No claim of executing the Windows display driver.
"""
import subprocess,sys,tempfile
from pathlib import Path
wrapper=Path(sys.argv[1]);s=(wrapper/'src/dd.c').read_text()
start=s.index('    if (!g_ddraw.mode.dmPelsWidth)',s.index('HRESULT dd_SetDisplayMode('))
block=s[start:s.index('    BOOL zooming',start)]
source=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#define FALSE 0
#define DEVMODE Mode
#define ENUM_CURRENT_SETTINGS -1
#define DM_PELSWIDTH 1
#define DM_PELSHEIGHT 2
#define DM_BITSPERPEL 4
#define DM_DISPLAYFREQUENCY 8
#define SM_CXSCREEN 0
#define SM_CYSCREEN 1
typedef struct {unsigned dmSize,dmDriverExtra,dmFields,dmPelsWidth,dmPelsHeight,dmDisplayFrequency,dmBitsPerPel;} Mode;
static struct { Mode mode; } g_ddraw;
static struct {int windowed,fullscreen;} g_config;
static int resets,enabled,query_ok,width,height;
static void ChangeDisplaySettings(void *p,int flags){assert(!p&&!flags);resets++;}
static unsigned GetEnvironmentVariableA(const char *n,char *b,unsigned z){assert(!strcmp(n,"VO_DUAL_DISPLAY")&&z==2);b[0]=enabled?'1':'0';return enabled?1:0;}
static int real_EnumDisplaySettingsA(void *n,int mode,Mode *m){assert(!n&&mode==ENUM_CURRENT_SETTINGS);m->dmPelsWidth=width;m->dmPelsHeight=height;m->dmDisplayFrequency=144;return query_ok;}
static int real_GetSystemMetrics(int n){return n==SM_CXSCREEN?width:height;}
static void query(void){
'''+block+r'''
}
int main(void){
 const int dimensions[][2]={{2560,1440},{1920,1080},{1600,1200},{3440,1440},{5120,1440},{1080,1920}};
 for(unsigned i=0;i<6;i++)for(int ok=0;ok<2;ok++){
  memset(&g_ddraw,0,sizeof g_ddraw);g_config.windowed=1;g_config.fullscreen=1;
  enabled=1;query_ok=ok;width=dimensions[i][0];height=dimensions[i][1];resets=0;
  query();assert(!resets&&g_ddraw.mode.dmPelsWidth==width&&g_ddraw.mode.dmPelsHeight==height);
  query();assert(!resets);
 }
 for(int win=0;win<2;win++)for(int env=0;env<2;env++){
  memset(&g_ddraw,0,sizeof g_ddraw);g_config.windowed=win;enabled=env;query_ok=1;resets=0;
  query();assert(resets==!(win&&env));
 }
 puts("PASS actual desktop-query block: 6 desktop dimensions, query fallback, cached mode, current-mode preservation and unchanged non-private/exclusive path; API doubles");
}
'''
with tempfile.TemporaryDirectory() as td:
 td=Path(td);(td/'mode.c').write_text(source)
 subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(td/'mode.c'),'-o',str(td/'mode')],check=True)
 subprocess.run([str(td/'mode')],check=True)
# F01 focus/close/reset paths remain exclusive-only; no new global API hook.
for file in ('src/wndproc.c','src/utils.c'):
 assert (wrapper/file).read_bytes()==subprocess.check_output(['git','show','279a057ee7e1e4d584b56141c014ab01f3c6ee6d:'+file],cwd=sys.argv[2])
here=Path(__file__).resolve().parent
for name in ('presentation.h','inventory.h','displays.c'):
 text=(here/name).read_text();assert 'ChangeDisplaySettings' not in text and 'SetDisplayConfig(' not in text
text=(here/'presentation.h').read_text()
assert 'params.Windowed = TRUE' in text and 'params.BackBufferWidth = r.w; params.BackBufferHeight = r.h;' in text
print('PASS native-sized windowed swapchains; unchanged pinned focus/utility code; no physical mode-setting calls in private presentation/discovery')
