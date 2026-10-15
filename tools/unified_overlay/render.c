#include "runtime.h"
static void fill(HDC dc,RECT r,COLORREF c){HBRUSH b=CreateSolidBrush(c);if(b){FillRect(dc,&r,b);DeleteObject(b);}}
static void text(HDC dc,RECT r,const char *s,COLORREF c){
 WCHAR wide[1024];
 if(!MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,wide,1024))
  lstrcpynW(wide,L"Unavailable",1024);
 SetTextColor(dc,c);
 DrawTextW(dc,wide,-1,&r,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_NOPREFIX|DT_END_ELLIPSIS);
}
void vo_dispose(VoPaint *p){if(p->title)DeleteObject(p->title);if(p->body)DeleteObject(p->body);if(p->surface)IDirectDrawSurface_Release(p->surface);*p=(VoPaint){0};}
int vo_attach(VoPaint *p,LPDIRECTDRAWSURFACE surface){
 DDSURFACEDESC d={0};d.dwSize=sizeof d;vo_dispose(p);
 if(!surface||IDirectDrawSurface_GetSurfaceDesc(surface,&d)!=DD_OK||d.dwWidth<320||d.dwHeight<240||d.dwWidth>8192||d.dwHeight>8192)return 0;
 p->surface=surface;IDirectDrawSurface_AddRef(surface);p->width=d.dwWidth;p->height=d.dwHeight;
 char mode[2]={0};GetEnvironmentVariableA("VO_EX_EFFECTIVE_MODE",mode,2);
 p->area_width=mode[0]=='1'?p->width/2:p->width;
 /* Uniform bounded panel: ultrawide changes centering, never text stretch. */
 int scale=max(1,p->height/720);p->row=36*scale;
 p->w=min(560*scale,p->area_width-32);p->h=min((112+7*36)*scale,p->height-32);
 p->x=(p->area_width-p->w)/2;p->y=(p->height-p->h)/2;
 p->visible=min(7,(p->h-112*scale)/p->row);
 if(p->visible<1){vo_dispose(p);return 0;}
 p->title=CreateFontA(-24*scale,0,0,0,FW_BOLD,0,0,0,DEFAULT_CHARSET,0,0,ANTIALIASED_QUALITY,DEFAULT_PITCH,"Segoe UI");
 p->body=CreateFontA(-18*scale,0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,0,0,ANTIALIASED_QUALITY,DEFAULT_PITCH,"Segoe UI");
 if(!p->title||!p->body){vo_dispose(p);return 0;}return 1;
}
int vo_paint(VoPaint *p,const VoOverlay *s){
 HDC dc;if(!p->surface||IDirectDrawSurface_IsLost(p->surface)!=DD_OK||IDirectDrawSurface_GetDC(p->surface,&dc)!=DD_OK)return 0;
 p->page=s->menu?3:s->confirm?2:s->unavailable;
 if(s->menu){
  int scale=max(1,p->height/720);
  p->h=min((140+min(14,(int)s->menu->count)*36)*scale,p->height-32);
  p->y=(p->height-p->h)/2;
 }
 int saved=SaveDC(dc);if(!saved){IDirectDrawSurface_ReleaseDC(p->surface,dc);return 0;}
 RECT panel={p->x,p->y,p->x+p->w,p->y+p->h};fill(dc,panel,RGB(16,24,32));SetBkMode(dc,TRANSPARENT);
 SelectObject(dc,p->title);RECT title={p->x+16,p->y+8,p->x+p->w-16,p->y+48};text(dc,title,s->menu?s->menu->title:s->confirm?"EXIT TO TITLE":"VO PATCH EX",RGB(244,247,250));SelectObject(dc,p->body);
 if(s->menu){
  p->visible=max(1,(p->h-140)/p->row);
  if(s->selected<(unsigned)p->first)p->first=(int)s->selected;
  if(s->selected>=(unsigned)(p->first+p->visible))p->first=(int)s->selected-p->visible+1;
  if(p->first<0)p->first=0;
  for(int row=0;row<p->visible&&p->first+row<(int)s->menu->count;row++){
   unsigned i=(unsigned)(p->first+row);const VoMenuRow *item=&s->menu->rows[i];
   RECT r={p->x+12,p->y+52+row*p->row,p->x+p->w-12,p->y+52+(row+1)*p->row};
   if(i==s->selected&&item->enabled)fill(dc,r,RGB(36,61,80));
   r.left+=12;RECT value=r;
   if(item->value[0]){r.right=p->x+p->w*56/100;value.left=r.right+8;}
   text(dc,r,item->label,item->enabled?RGB(244,247,250):RGB(128,160,174));
   if(item->value[0])text(dc,value,item->value,RGB(94,231,247));
  }
  RECT notice={p->x+16,p->y+p->h-66,p->x+p->w-16,p->y+p->h-48};
  text(dc,notice,s->menu->notice,RGB(244,211,140));
  RECT back={p->x+16,p->y+p->h-48,p->x+p->w/2,p->y+p->h-12};
  RECT resume={p->x+p->w/2,p->y+p->h-48,p->x+p->w-16,p->y+p->h-12};
  text(dc,back,"BACK",RGB(94,231,247));text(dc,resume,"RESUME",RGB(94,231,247));
  int flushed=GdiFlush();RestoreDC(dc,saved);
  return IDirectDrawSurface_ReleaseDC(p->surface,dc)==DD_OK&&flushed;
 }
 if(!s->unavailable && !s->confirm && s->selected<(unsigned)p->first)p->first=s->selected;
 if(!s->unavailable && !s->confirm && s->selected>=(unsigned)(p->first+p->visible))p->first=s->selected-p->visible+1;
 if(s->confirm){
  RECT r={p->x+16,p->y+56,p->x+p->w-16,p->y+p->h-60};
  SetTextColor(dc,RGB(244,247,250));DrawTextA(dc,"Return to the title screen?\n\nCurrent match progress will be lost.",-1,&r,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX);
 }else if(s->unavailable){
  RECT r={p->x+16,p->y+56,p->x+p->w-16,p->y+p->h-60};
  SetTextColor(dc,RGB(244,247,250));DrawTextA(dc,"Not available in this private build.\nUse the existing F-key menus for settings.",-1,&r,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX);
 }else for(int row=0;row<p->visible;row++){
  unsigned i=p->first+row;RECT r={p->x+12,p->y+52+row*p->row,p->x+p->w-12,p->y+52+(row+1)*p->row};
  if(i==s->selected){fill(dc,r,RGB(36,61,80));RECT edge=r;edge.right=edge.left+3;fill(dc,edge,RGB(94,231,247));}
  r.left+=12;text(dc,r,vo_overlay_labels[i],i==6&&!s->exit_allowed?RGB(128,140,148):RGB(244,247,250));
 }
 RECT back={p->x+16,p->y+p->h-48,p->x+p->w/2,p->y+p->h-12};if((s->confirm&&s->selected==0)||(s->unavailable&&s->selected==7)||s->hover==7)fill(dc,back,RGB(36,61,80));text(dc,back,s->confirm?"CANCEL":"BACK",RGB(94,231,247));
 RECT resume={p->x+p->w/2,p->y+p->h-48,p->x+p->w-16,p->y+p->h-12};if((s->confirm&&s->selected==1)||(s->unavailable&&s->selected==5)||s->hover==5)fill(dc,resume,RGB(36,61,80));text(dc,resume,s->confirm?"EXIT TO TITLE":"RESUME",RGB(94,231,247));
 /* cnc-ddraw ReleaseDC does not flush GDI's per-thread batch. Its
  * render thread reads DIB pixels at publication, so complete CPU drawing
  * before releasing this frame to DirectDraw. */
 int flushed=GdiFlush();RestoreDC(dc,saved);
 return IDirectDrawSurface_ReleaseDC(p->surface,dc)==DD_OK&&flushed;
}
int vo_hit_source(VoPaint *p,int x,int y){
 if(x<p->x||x>=p->x+p->w||y<p->y||y>=p->y+p->h)return -1;
 if(y>=p->y+p->h-48)return p->page==3?(x<p->x+p->w/2?1000:1001):p->page==2?(x<p->x+p->w/2?8:9):(x<p->x+p->w/2?7:5);
 if(p->page&&p->page!=3)return -1;
 int row=(y-p->y-52)/p->row;
 return y>=p->y+52&&row<p->visible?row+p->first:-1;
}
