/* Shared stable-identity discovery and assignment reader. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include "layout.h"
static VoMonitor monitors[VO_MAX_MONITORS];
static WCHAR names[VO_MAX_MONITORS][256],config[MAX_PATH];
static unsigned count;
static int discover(void){
 DISPLAYCONFIG_PATH_INFO *paths=NULL;DISPLAYCONFIG_MODE_INFO *modes=NULL;UINT32 np=0,nm=0;LONG result=ERROR_INSUFFICIENT_BUFFER;
 for(unsigned attempt=0;attempt<3&&result==ERROR_INSUFFICIENT_BUFFER;attempt++){
  free(paths);free(modes);paths=NULL;modes=NULL;
  result=GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS,&np,&nm);if(result!=ERROR_SUCCESS)break;
  if(np>1024||nm>4096){result=ERROR_INVALID_DATA;break;}
  paths=calloc(np?np:1,sizeof *paths);modes=calloc(nm?nm:1,sizeof *modes);
  if(!paths||!modes){result=ERROR_NOT_ENOUGH_MEMORY;break;}
  result=QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS,&np,paths,&nm,modes,NULL);
 }
 if(result!=ERROR_SUCCESS){fprintf(stderr,"display_query_error=%ld\n",result);free(paths);free(modes);return 0;}
 count=0;
 for(UINT32 i=0;i<np;i++){
  DISPLAYCONFIG_SOURCE_DEVICE_NAME src={0};src.header.type=DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME;src.header.size=sizeof src;src.header.adapterId=paths[i].sourceInfo.adapterId;src.header.id=paths[i].sourceInfo.id;
  DISPLAYCONFIG_TARGET_DEVICE_NAME dst={0};dst.header.type=DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME;dst.header.size=sizeof dst;dst.header.adapterId=paths[i].targetInfo.adapterId;dst.header.id=paths[i].targetInfo.id;
  if(DisplayConfigGetDeviceInfo(&src.header)!=ERROR_SUCCESS||DisplayConfigGetDeviceInfo(&dst.header)!=ERROR_SUCCESS||!dst.monitorDevicePath[0]){result=ERROR_INVALID_DATA;break;}
  DEVMODEW dm={0};dm.dmSize=sizeof dm;if(!EnumDisplaySettingsExW(src.viewGdiDeviceName,ENUM_CURRENT_SETTINGS,&dm,0)){result=ERROR_INVALID_DATA;break;}
  if(count==VO_MAX_MONITORS){result=ERROR_INSUFFICIENT_BUFFER;break;}
  VoMonitor *m=&monitors[count];memset(m,0,sizeof *m);
  if(!WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,dst.monitorDevicePath,-1,m->id,sizeof m->id,NULL,NULL)){result=ERROR_INVALID_DATA;break;}
  m->desktop=(VoRect){dm.dmPosition.x,dm.dmPosition.y,(int32_t)dm.dmPelsWidth,(int32_t)dm.dmPelsHeight};
  RECT rect={dm.dmPosition.x,dm.dmPosition.y,dm.dmPosition.x+(LONG)dm.dmPelsWidth,dm.dmPosition.y+(LONG)dm.dmPelsHeight};
  MONITORINFO mi={0};mi.cbSize=sizeof mi;HMONITOR hm=MonitorFromRect(&rect,MONITOR_DEFAULTTONULL);
  if(hm&&GetMonitorInfoW(hm,&mi))m->primary=(mi.dwFlags&MONITORINFOF_PRIMARY)!=0;
  m->available=paths[i].targetInfo.targetAvailable!=0;
  swprintf(names[count],256,L"%ls — %lux%lu (%ld,%ld)%ls",dst.monitorFriendlyDeviceName,dm.dmPelsWidth,dm.dmPelsHeight,dm.dmPosition.x,dm.dmPosition.y,m->primary?L" primary":L"");
  printf("monitor=%u id=%s desktop=%ld,%ld,%ld,%ld primary=%u available=%u refresh=%u/%u rotation=%u\n",count,m->id,(long)m->desktop.x,(long)m->desktop.y,(long)m->desktop.w,(long)m->desktop.h,m->primary,m->available,paths[i].targetInfo.refreshRate.Numerator,paths[i].targetInfo.refreshRate.Denominator,paths[i].targetInfo.rotation);
  count++;
 }
 free(paths);free(modes);if(result!=ERROR_SUCCESS){count=0;fprintf(stderr,"display_inventory_incomplete=%ld; fallback required\n",result);return 0;}return 1;
}
static void load_id(const WCHAR *key,char *id){
 WCHAR text[VO_ID_CHARS]={0};DWORD n=GetPrivateProfileStringW(L"Players",key,L"",text,VO_ID_CHARS,config);
 if(n>=VO_ID_CHARS-1||!WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,text,-1,id,VO_ID_CHARS,NULL,NULL))strcpy(id,"invalid-saved-id");
}
