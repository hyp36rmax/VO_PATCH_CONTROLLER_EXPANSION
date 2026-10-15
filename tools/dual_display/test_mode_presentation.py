"""Run existing presentation tests against the emitted F04 header, plus Mode integration."""
from pathlib import Path
import shutil,subprocess,sys,tempfile
here=Path(__file__).resolve().parent;wrapper=Path(sys.argv[1])
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for name in ('presentation.h','movie_window.h','policy.h','layout.h'):shutil.copy2(wrapper/'inc'/name,t/name)
 api='#include <assert.h>\n'+(here/'presentation_test_api.h').read_text().replace('#define GetPrivateProfileIntW(...) 0', 'static int selected_mode=1, session_config_test=0;\nstatic int mode_read(const WCHAR *section,const WCHAR *key,int fallback,const WCHAR *path){(void)section;(void)fallback;if(session_config_test)assert(!wcscmp(path,L"session.ini"));assert(!wcscmp(key,L"Mode"));return selected_mode;}\n#define GetPrivateProfileIntW mode_read')
 api=api.replace('static DWORD GetEnvironmentVariableA(', 'static DWORD base_environment(')
 api+='\nstatic int strict_test=0, complete_test=0, normal_mode=0;\nstatic DWORD GetEnvironmentVariableA(const char *key,char *out,DWORD size){if(!strncmp(key,"VO_EX_",6)){if(!normal_mode)return 0;if(!strcmp(key,"VO_EX_EFFECTIVE_MODE")){out[0]=(char)(48+normal_mode);out[1]=0;return 1;}if(!strcmp(key,"VO_EX_PRIMARY_ID")){strcpy(out,"a");return 1;}if(!strcmp(key,"VO_EX_SECONDARY_ID")){strcpy(out,"b");return 1;}return 0;}if(!strcmp(key,"VO_COMPLETE_MIRROR")){out[0]=complete_test?49:48;return 1;}if(!strcmp(key,"VO_SOURCE_SIZE")){return snprintf(out,size,"%d,%d",g_ddraw.width,g_ddraw.height);}if(!strcmp(key,"VO_STRICT_MODE")){out[0]=strict_test?49:48;return 1;}return base_environment(key,out,size); }\nstatic DWORD GetEnvironmentVariableW(const WCHAR *key,WCHAR *out,DWORD size){(void)size;assert(!wcscmp(key,L"VO_SESSION_CONFIG"));if(!session_config_test)return 0;wcscpy(out,L"session.ini");return 11;}\n'
 (t/'presentation_test_api.h').write_text(api)
 for test in ('movie','presentation','phases'):
  source=(here/f'test_{test}.c').read_text()
  if test=='phases':
   source=source.replace('mirror P1, latched generations','legacy mirror flag ignored, latched generations').replace('int main(void)','int phase_main(void)').replace('vo_dual.output[1].source.x==0);','vo_dual.output[1].source.x==1920);')
   end=source.rfind('}');source=source[:end]+'return 0;\n'+source[end:]
   source+='''\nint main(void){phase_main();for(int mode=1;mode<=2;mode++){setup();session_config_test=1;selected_mode=mode;complete_test=mode==2;test_policy=2;vo_dual_uploaded(0);vo_dual_present(0);assert(!vo_dual.disabled);assert(vo_dual.mirror==(mode==2));assert(vo_dual.output[1].source.x==(mode==2?0:1920));vo_dual_end();assert(!fake.live);}complete_test=0;session_config_test=0;setup();selected_mode=1;strict_test=1;test_policy=2;vo_dual_uploaded(0);fake.fail_at=1;vo_dual_present(0);assert(vo_dual.disabled&&vo_dual.strict_stopped&&fake.closed==1);vo_dual_pump();assert(fake.closed==1);vo_dual_end();strict_test=0;const int sizes[][2]={{640,480},{1920,1080},{2560,1080},{3840,1080}};
for(unsigned sz=0;sz<4;sz++)for(unsigned phase=0;phase<4;phase++){
 setup();selected_mode=2;complete_test=1;test_policy=phase;
 g_ddraw.width=sizes[sz][0];g_ddraw.height=sizes[sz][1];
 vo_dual_uploaded(0);vo_dual_present(0);assert(!vo_dual.disabled&&fake.draws==2);
 for(int player=0;player<2;player++){
  VoRect r=vo_dual.output[player].source;assert(r.x==0&&r.y==0&&r.w==g_ddraw.width&&r.h==g_ddraw.height);
  assert(fake.vertices[player][0].u==0&&fake.vertices[player][2].u==(float)g_ddraw.width/g_d3d9.tex_width);
  assert(fake.vertices[player][0].v==(float)g_ddraw.height/g_d3d9.tex_height);
 }
 assert(fake.texture[0]==fake.texture[1]);
 fake.movie_present=fake.movie_visible=1;vo_dual_pump();assert(vo_dual.movie.active);
 int draws=fake.draws;vo_dual_uploaded(0);vo_dual_present(0);assert(fake.draws==draws);
 fake.movie_visible=0;vo_dual_pump();assert(!vo_dual.movie.active);vo_dual_uploaded(0);vo_dual_present(0);assert(fake.draws==draws+2);
 vo_dual_end();assert(!fake.live);
}
for(int fail=1;fail<=28;fail++){
 setup();selected_mode=2;complete_test=1;g_ddraw.width=1920;g_ddraw.height=1080;test_policy=2;
 vo_dual_uploaded(0);fake.fail_at=fail;vo_dual_present(0);
 assert(vo_dual.disabled&&!vo_dual.visible&&!fake.live);vo_dual_end();assert(!fake.live);
}
for(int mode=1;mode<=2;mode++){
 setup();selected_mode=mode;complete_test=mode==1;test_policy=2;vo_dual_uploaded(0);vo_dual_present(0);
 assert(vo_dual.disabled&&fake.draws==0);vo_dual_end();assert(!fake.live);
}
complete_test=0;selected_mode=1;
puts("PASS complete-frame coverage (all P1/P2/HUD pixels), four profiles, all phases, identical texture/UV endpoints, mixed outputs and movie hide/restore");puts("PASS saved Versus/Mirror Mode and strict session failure closure in emitted wrapper");return 0;}\n'''
  if test=='phases' and 'VO_EX_EFFECTIVE_MODE' in (t/'presentation.h').read_text():
   source=source.replace('complete_test=0;selected_mode=1;\nputs(','''for(int mode=1;mode<=2;mode++){
 setup();normal_mode=mode;selected_mode=3-mode;complete_test=mode==2;test_policy=2;
 vo_dual_uploaded(0);vo_dual_present(0);assert(!vo_dual.disabled&&vo_dual.mirror==(mode==2));
 vo_dual_end();assert(!fake.live);
}
normal_mode=0;complete_test=0;selected_mode=1;
puts(''')
  p=t/f'{test}.c';p.write_text(source)
  subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(p),'-o',str(t/test)],check=True);subprocess.run([str(t/test)],check=True)
