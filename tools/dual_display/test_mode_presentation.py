"""Run existing presentation tests against the emitted F04 header, plus Mode integration."""
from pathlib import Path
import shutil,subprocess,sys,tempfile
here=Path(__file__).resolve().parent;wrapper=Path(sys.argv[1])
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for name in ('presentation.h','movie_window.h','policy.h','layout.h'):shutil.copy2(wrapper/'inc'/name,t/name)
 api='#include <assert.h>\n'+(here/'presentation_test_api.h').read_text().replace('#define GetPrivateProfileIntW(...) 0', 'static int selected_mode=1, session_config_test=0;\nstatic int mode_read(const WCHAR *section,const WCHAR *key,int fallback,const WCHAR *path){(void)section;(void)fallback;if(session_config_test)assert(!wcscmp(path,L"session.ini"));assert(!wcscmp(key,L"Mode"));return selected_mode;}\n#define GetPrivateProfileIntW mode_read')
 api=api.replace('static DWORD GetEnvironmentVariableA(', 'static DWORD base_environment(')
 api+='\nstatic int strict_test=0;\nstatic DWORD GetEnvironmentVariableA(const char *key,char *out,DWORD size){if(!strcmp(key,"VO_STRICT_MODE")){out[0]=strict_test?49:48;return 1;}return base_environment(key,out,size); }\nstatic DWORD GetEnvironmentVariableW(const WCHAR *key,WCHAR *out,DWORD size){(void)size;assert(!wcscmp(key,L"VO_SESSION_CONFIG"));if(!session_config_test)return 0;wcscpy(out,L"session.ini");return 11;}\n'
 (t/'presentation_test_api.h').write_text(api)
 for test in ('movie','presentation','phases'):
  source=(here/f'test_{test}.c').read_text()
  if test=='phases':
   source=source.replace('int main(void)','int phase_main(void)')
   end=source.rfind('}');source=source[:end]+'return 0;\n'+source[end:]
   source+='''\nint main(void){phase_main();for(int mode=1;mode<=2;mode++){setup();session_config_test=1;selected_mode=mode;test_policy=2;vo_dual_uploaded(0);vo_dual_present(0);assert(!vo_dual.disabled);assert(vo_dual.mirror==(mode==2));assert(vo_dual.output[1].source.x==(mode==2?0:1920));vo_dual_end();assert(!fake.live);}session_config_test=0;setup();selected_mode=1;strict_test=1;test_policy=2;vo_dual_uploaded(0);fake.fail_at=1;vo_dual_present(0);assert(vo_dual.disabled&&vo_dual.strict_stopped&&fake.closed==1);vo_dual_pump();assert(fake.closed==1);vo_dual_end();strict_test=0;puts("PASS saved Versus/Mirror Mode and strict session failure closure in emitted wrapper");return 0;}\n'''
  p=t/f'{test}.c';p.write_text(source)
  subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(p),'-o',str(t/test)],check=True);subprocess.run([str(t/test)],check=True)
