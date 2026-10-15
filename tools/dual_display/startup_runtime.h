/* Invoked at PE entry, after loader imports and before the retained game entry.
 * Not DllMain: monitor queries, allocation and protection changes are outside
 * loader-lock initialization. The existing F5 helpers own configuration reads.
 */
#include "startup_plan.h"
#include "collector_start.h"
static int vo_activate(unsigned char *base,const unsigned char *plan,unsigned n,unsigned mapped){
 if(!vo_startup_matches(base,plan,n))return 0;
 unsigned pages=(mapped+4095)/4096;
 DWORD *old=calloc(pages,sizeof *old);if(!old)return 0;
 const unsigned char *cursor=plan;int ok=1;
 for(unsigned i=0;i<n&&ok;i++){
  VoStartupWrite w=vo_startup_write(&cursor);
  for(unsigned p=w.offset/4096;p<=(w.offset+w.size-1)/4096;p++)
   if(!old[p]){DWORD prior=0;if(!VirtualProtect(base+p*4096,4096,PAGE_EXECUTE_READWRITE,&prior)){ok=0;break;}old[p]=prior;}
 }
 if(ok){cursor=plan;for(unsigned i=0;i<n;i++){VoStartupWrite w=vo_startup_write(&cursor);memcpy(base+w.offset,w.after,w.size);}
  if(!FlushInstructionCache(GetCurrentProcess(),base,mapped))ok=0;
 }
 for(unsigned p=0;p<pages;p++)if(old[p]){DWORD unused;if(!VirtualProtect(base+p*4096,4096,old[p],&unused))ok=0;}
 free(old);return ok;
}
__declspec(dllexport) int WINAPI VonDisplayStartup(unsigned char *base,const unsigned char *table,unsigned bytes,unsigned crc){
 static LONG entered;
 if(InterlockedCompareExchange(&entered,1,0))return 0;
 if(base!=(unsigned char*)GetModuleHandleW(NULL)||!path_config()||!discover())goto fail;
 if(bytes<20||vo_word(table+16)>1)goto fail;
 if(!SetEnvironmentVariableA("VO_EX_DEFAULT_ASPECT",vo_word(table+16)?"1":"0"))goto fail;
 read_saved();VoSelection selection;
 if(!vo_select(monitors,count,&saved,31,&selection))goto fail;
 const unsigned char *plan=NULL;unsigned n=0;
 unsigned mapped=bytes>=16?vo_word(table+8):0;
 IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)base;
 IMAGE_NT_HEADERS *nt=(IMAGE_NT_HEADERS*)(base+dos->e_lfanew);
 if(mapped>nt->OptionalHeader.SizeOfImage||!vo_startup_plan(table,bytes,crc,selection.profile,mapped,&plan,&n))goto fail;
 /* Set only process-local effective state; saved preferences remain untouched. */
 char desktop[128],size[64];VoRect d=monitors[selection.primary].desktop;
 const unsigned width[]={640,1920,2560,3840,3840},height[]={480,1080,1080,1080,1080};
 snprintf(desktop,sizeof desktop,"%d,%d,%d,%d",d.x,d.y,d.w,d.h);
 snprintf(size,sizeof size,"%u,%u",width[selection.profile],height[selection.profile]);
 if(!SetEnvironmentVariableA("VO_PRIVATE_DISPLAY","1")||
 !SetEnvironmentVariableA("VO_DUAL_DISPLAY",selection.mode==VO_SINGLE?"0":"1")||
 !SetEnvironmentVariableA("VO_COMPLETE_MIRROR",selection.mode==VO_MIRROR?"1":"0")||
 !SetEnvironmentVariableA("VO_SOURCE_SIZE",size)||!SetEnvironmentVariableA("VO_DESKTOP",desktop)||
 !SetEnvironmentVariableA("VO_SESSION_CONFIG",NULL)||!SetEnvironmentVariableA("VO_STRICT_MODE","0"))goto fail;
 if(!SetEnvironmentVariableA("VO_EX_PRIMARY_ID",monitors[selection.primary].id)||
 !SetEnvironmentVariableA("VO_EX_SECONDARY_ID",selection.secondary>=0?monitors[selection.secondary].id:NULL))goto fail;
 if(!vo_activate(base,plan,n,mapped)||!vo_collector(&selection))goto fail;
 return 1;
fail:
 MessageBoxW(NULL,L"Display initialization could not complete safely. The game has not started.",L"VO PATCH EX",MB_OK|MB_ICONERROR);
 return 0;
}
