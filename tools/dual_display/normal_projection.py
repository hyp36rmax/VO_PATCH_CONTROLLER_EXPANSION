"""Freeze normal-startup presentation choices until the next process launch."""

def apply(out):
 def replace_once(text,old,new):
  assert text.count(old)==1,(old,text.count(old))
  return text.replace(old,new)
 p=out/'inc/presentation.h';s=p.read_text()
 from pathlib import Path
 (out/'inc/diagnostics_privacy.h').write_bytes(Path(__file__).with_name('diagnostics_privacy.h').read_bytes())
 (out/'inc/diagnostics_runtime.h').write_bytes(Path(__file__).with_name('diagnostics_runtime.h').read_bytes())
 s=replace_once(s,'#include \"policy.h\"','#include \"policy.h\"\n#include \"diagnostics_runtime.h\"')
 s=replace_once(s,'    if(vo_dual.attempted) {','    if(vo_dual.attempted && vo_diagnostic_level()>=2) {')
 s=replace_once(s,'FILE *log=_wfopen(path,L\"a\");','WIN32_FILE_ATTRIBUTE_DATA info;\n            int room=!GetFileAttributesExW(path,GetFileExInfoStandard,&info)||(info.nFileSizeHigh==0&&info.nFileSizeLow<256*1024-32768);\n            FILE *log=room?_wfopen(path,L\"a\"):NULL;')
 s=replace_once(s,'player=%d id=%s source=', 'player=%d source=').replace('i+1,monitors[o.monitor].id,o.source.x','i+1,o.source.x')
 old='    vo_dual.mirror = GetPrivateProfileIntW(L"Presentation", L"Mode", 1, config) == 2;'
 new='''    char effective_mode[2]={0};
    DWORD effective_length=GetEnvironmentVariableA("VO_EX_EFFECTIVE_MODE",effective_mode,2);
    if(effective_length && (effective_length!=1 || (effective_mode[0]!='1' && effective_mode[0]!='2')))goto fail;
    vo_dual.mirror = effective_length ? effective_mode[0]=='2' : GetPrivateProfileIntW(L"Presentation", L"Mode", 1, config) == 2;'''
 assert s.count(old)==1;s=s.replace(old,new)
 old='    load_id(L"Player1", a); load_id(L"Player2", b);'
 new='''    if(effective_length){
        DWORD na=GetEnvironmentVariableA("VO_EX_PRIMARY_ID",a,sizeof a), nb=GetEnvironmentVariableA("VO_EX_SECONDARY_ID",b,sizeof b);
        if(!na||na>=sizeof a||!nb||nb>=sizeof b)goto fail;
    }else{load_id(L"Player1", a); load_id(L"Player2", b);}'''
 assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)

 # Gate optional in-memory traces; essential phase classification stays active.
 p=out/'inc/movie_window.h';text=p.read_text()
 text=replace_once(text,' ++m->total;', ' if(vo_diagnostic_level()<3)return;\n ++m->total;')
 p.write_text(text)
 p=out/'src/state_bridge.c';text=p.read_text()
 text=replace_once(text,'#include "state_bridge.h"','#include "state_bridge.h"\n#include "diagnostics_runtime.h"')
 text=replace_once(text,' ++observation.captures;if(kind==2)++observation.flips;else ++observation.unlocks;', ' unsigned diagnostic=vo_diagnostic_level();\n if(diagnostic>=3){++observation.captures;if(kind==2)++observation.flips;else ++observation.unlocks;}')
 text=replace_once(text,' if(phase==VO_POLICY_UNKNOWN){', ' if(diagnostic>=3 && phase==VO_POLICY_UNKNOWN){')
 text=replace_once(text,' if(observation.captures==1||prior_status!=observation.status||prior_phase!=(unsigned)phase){', ' if(diagnostic>=2 && (observation.captures==1||prior_status!=observation.status||prior_phase!=(unsigned)phase)){')
 p.write_text(text)
