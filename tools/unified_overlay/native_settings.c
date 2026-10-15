#include "native_settings.h"
#include <stdint.h>
#include <string.h>
/* These functions and scratch ownership are exercised against both original
 * executable editions by test_native_settings.py. The overlay is installed
 * only after the patch generator verifies the executable identity. */
static const uintptr_t procedures[2][5]={
 {0x427e00,0x5cafe0,0x5cb518,0x5cb95a,0x5cbcc9},
 {0x427a60,0x5c5880,0x5c5db8,0x5c61fa,0x5c6569}
};
static int valid(const VoNativeSettings *s){
 return s&&s->host&&s->page&&IsWindow(s->host)&&IsWindow(s->page)&&
  (!s->scratch_slot||*s->scratch_slot==s->scratch);
}
void vo_native_end(VoNativeSettings *s){
 if(!s)return;
 if(s->page)DestroyWindow(s->page);
 if(s->host)DestroyWindow(s->host);
 if(s->scratch_slot&&*s->scratch_slot==s->scratch)*s->scratch_slot=s->previous_scratch;
 memset(s,0,sizeof *s);
}
int vo_native_begin(VoNativeSettings *s,HWND owner,const volatile LONG *mode,unsigned category){
 if(!s||s->host||category>VO_NATIVE_APPENDIX)return 0;
 int edition=(uintptr_t)mode==0x1ae3594?0:(uintptr_t)mode==0x1adcdf0?1:-1;
 if(edition<0)return 0;
 s->category=category;s->procedure=(DLGPROC)procedures[edition][category];
 if(category==VO_NATIVE_GRAPHICS){
  /* The original caller applies staged resolution after the dialog returns.
   * Follow its installed call, including the existing resize safety guard. */
  const unsigned char *site=(const unsigned char*)(uintptr_t)(edition?0x5c1d63:0x5c7494);
  if(*site!=0xe8)goto failed;
  int32_t displacement;memcpy(&displacement,site+1,4);
  s->finish=(void(__cdecl*)(void))(site+5+displacement);
 }
 /* An invisible parent keeps native child controls off-screen without
  * changing focus, desktop geometry, or the original game window. */
 s->host=CreateWindowExA(0,"STATIC","",WS_POPUP,0,0,1,1,owner,NULL,GetModuleHandleA(NULL),NULL);
 if(!s->host)goto failed;
 if(category){
  s->scratch_slot=(void**)(uintptr_t)(edition?0x1cdca64:0x1ce1dbc);
  s->previous_scratch=*s->scratch_slot;*s->scratch_slot=s->scratch;
  s->snapshot=(void(__cdecl*)(void))(uintptr_t)(edition?0x5c67a5:0x5cbf05);
  s->commit=(void(__cdecl*)(void))(uintptr_t)(edition?0x5c6800:0x5cbf60);
  s->snapshot();
 }
 /* Remove only the template's top-level visibility. This is a private copy;
  * the original resource and F-key menu are unchanged. */
 HMODULE module=GetModuleHandleA(NULL);
 HRSRC resource=FindResourceA(module,MAKEINTRESOURCEA(category?117+category:127),RT_DIALOG);
 DWORD length=resource?SizeofResource(module,resource):0;
 if(length<sizeof(DLGTEMPLATE)||length>65536)goto failed;
 const void *raw=LockResource(LoadResource(module,resource));
 if(!raw)goto failed;
 void *copy=HeapAlloc(GetProcessHeap(),0,length);if(!copy)goto failed;
 memcpy(copy,raw,length);
 /* Both verified editions use standard templates for these five pages. */
 DLGTEMPLATE *template=(DLGTEMPLATE*)copy;
 template->style&=~(WS_VISIBLE|WS_POPUP|WS_CAPTION|WS_SYSMENU);
 template->style|=WS_CHILD;
 s->page=CreateDialogIndirectParamA(module,template,s->host,s->procedure,0);
 HeapFree(GetProcessHeap(),0,copy);
 if(!valid(s))goto failed;
 return 1;
 failed:vo_native_end(s);return 0;
}
int vo_native_count(VoNativeSettings *s,unsigned id){
 if(!valid(s)||!GetDlgItem(s->page,(int)id))return 0;
 LRESULT count=SendDlgItemMessageA(s->page,(int)id,CB_GETCOUNT,0,0);
 return count>0&&count<=256?(int)count:0;
}
int vo_native_selected(VoNativeSettings *s,unsigned id){
 return valid(s)?(int)SendDlgItemMessageA(s->page,(int)id,CB_GETCURSEL,0,0):-1;
}
int vo_native_choice(VoNativeSettings *s,unsigned id,unsigned choice,char *text,unsigned size){
 if(!text||!size||choice>=(unsigned)vo_native_count(s,id))return 0;
 LRESULT n=SendDlgItemMessageA(s->page,(int)id,CB_GETLBTEXTLEN,choice,0);
 if(n<0||(unsigned)n>=size)return 0;
 return SendDlgItemMessageA(s->page,(int)id,CB_GETLBTEXT,choice,(LPARAM)text)==n;
}
int vo_native_select(VoNativeSettings *s,unsigned id,unsigned choice){
 if(choice>=(unsigned)vo_native_count(s,id))return 0;
 if(SendDlgItemMessageA(s->page,(int)id,CB_SETCURSEL,choice,0)==CB_ERR)return 0;
 s->procedure(s->page,WM_COMMAND,MAKEWPARAM(id,CBN_SELCHANGE),(LPARAM)GetDlgItem(s->page,(int)id));
 return 1;
}
int vo_native_check(VoNativeSettings *s,unsigned id){return valid(s)&&IsDlgButtonChecked(s->page,(int)id)==BST_CHECKED;}
int vo_native_click(VoNativeSettings *s,unsigned id){
 if(!valid(s))return 0;
 HWND control=GetDlgItem(s->page,(int)id);if(!control)return 0;
 unsigned type=(unsigned)GetWindowLongA(control,GWL_STYLE)&BS_TYPEMASK;
 if(type==BS_AUTORADIOBUTTON||type==BS_RADIOBUTTON)return 0;
 /* BM_CLICK is unreliable on inactive dialogs. Deliver the same control
  * notification without bringing the private native controls into focus. */
 if(type==BS_AUTOCHECKBOX||type==BS_CHECKBOX)
  CheckDlgButton(s->page,(int)id,vo_native_check(s,id)?BST_UNCHECKED:BST_CHECKED);
 s->procedure(s->page,WM_COMMAND,MAKEWPARAM(id,BN_CLICKED),(LPARAM)control);
 return 1;
}
int vo_native_radio(VoNativeSettings *s,unsigned first,unsigned last,unsigned id){
 if(!valid(s)||id<first||id>last||!GetDlgItem(s->page,(int)id))return 0;
 if(!CheckRadioButton(s->page,(int)first,(int)last,(int)id))return 0;
 s->procedure(s->page,WM_COMMAND,MAKEWPARAM(id,BN_CLICKED),(LPARAM)GetDlgItem(s->page,(int)id));
 return 1;
}
int vo_native_defaults(VoNativeSettings *s){
 static const unsigned defaults[]={0,1012,1021,1041,1028};
 return s&&s->category&&s->category<=VO_NATIVE_APPENDIX&&vo_native_click(s,defaults[s->category]);
}
int vo_native_commit(VoNativeSettings *s){
 if(!valid(s))return 0;
 if(s->category)s->commit();
 else {s->procedure(s->page,WM_COMMAND,1072,0);s->finish();}
 return 1;
}
