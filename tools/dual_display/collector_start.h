/* Child is a passive collector, not a game launcher. No inherited handles. */
static int vo_state(const char *key,int value){char text[32];snprintf(text,sizeof text,"%d",value);return SetEnvironmentVariableA(key,text)!=0;}
static int vo_collector(const VoSelection *s){
 WCHAR root[MAX_PATH],exe[MAX_PATH],script[MAX_PATH],command[2048],event_name[100];
 DWORD n=GetModuleFileNameW(NULL,root,MAX_PATH);if(!n||n>=MAX_PATH)return 0;
 WCHAR *slash=wcsrchr(root,L'\\');if(!slash)return 0;*slash=0;
 if(wcslen(root)+40>=MAX_PATH)return 0;
 swprintf(exe,MAX_PATH,L"%ls\\experience-runtime\\pythonw.exe",root);
 swprintf(script,MAX_PATH,L"%ls\\experience-runtime\\normal_lifecycle.py",root);
 swprintf(event_name,100,L"Local\\VOEX-%lu-%lu",GetCurrentProcessId(),GetTickCount());
 HANDLE ready=CreateEventW(NULL,TRUE,FALSE,event_name);if(!ready)return 0;
 if(GetLastError()==ERROR_ALREADY_EXISTS){CloseHandle(ready);return 0;}
 if(!vo_state("VO_EX_REQUESTED_MODE",saved.mode)||!vo_state("VO_EX_EFFECTIVE_MODE",s->mode)||
 !vo_state("VO_EX_PROFILE",s->profile)||!vo_state("VO_EX_PRIMARY",s->primary)||
 !vo_state("VO_EX_SECONDARY",s->secondary)||!vo_state("VO_EX_FALLBACK",s->reasons)){CloseHandle(ready);return 0;}
 swprintf(command,2048,L"\"%ls\" -B \"%ls\" \"%ls\" --pid %lu --ready \"%ls\"",exe,script,root,GetCurrentProcessId(),event_name);
 STARTUPINFOW start={0};PROCESS_INFORMATION process={0};start.cb=sizeof start;
 BOOL created=CreateProcessW(exe,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,root,&start,&process);
 int ok=0;
 if(created){
  HANDLE waits[]={ready,process.hProcess};ok=WaitForMultipleObjects(2,waits,FALSE,10000)==WAIT_OBJECT_0;
  if(!ok){TerminateProcess(process.hProcess,1);WaitForSingleObject(process.hProcess,5000);}
  CloseHandle(process.hThread);CloseHandle(process.hProcess);
 }
 CloseHandle(ready);return ok;
}
