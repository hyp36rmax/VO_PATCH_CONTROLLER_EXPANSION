"""Freeze normal-startup presentation choices until the next process launch."""

def apply(out):
 p=out/'inc/presentation.h';s=p.read_text()
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
