#include "runtime.h"
static void fill(HDC dc,RECT r,COLORREF c){HBRUSH b=CreateSolidBrush(c);if(b){FillRect(dc,&r,b);DeleteObject(b);}}
static void text(HDC dc,RECT r,const char *s,COLORREF c){SetTextColor(dc,c);DrawTextA(dc,s,-1,&r,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_NOPREFIX);}
void vo_dispose(VoPaint *p){if(p->title)DeleteObject(p->title);if(p->body)DeleteObject(p->body);if(p->surface)IDirectDrawSurface_Release(p->surface);*p=(VoPaint){0};}
int vo_attach(VoPaint *p,LPDIRECTDRAWSURFACE surface){
 DDSURFACEDESC d={0};d.dwSize=sizeof d;vo_dispose(p);
 if(!surface||IDirectDrawSurface_GetSurfaceDesc(surface,&d)!=DD_OK||d.dwWidth<320||d.dwHeight<240||d.dwWidth>8192||d.dwHeight>8192)return 0;
 p->surface=surface;IDirectDrawSurface_AddRef(surface);p->width=d.dwWidth;p->height=d.dwHeight;
 char mode[2]={0};GetEnvironmentVariableA("VO_EX_EFFECTIVE_MODE",mode,2);
 p->area_width=mode[0]=='1'?p->width/2:p->width;
 /* Uniform bounded panel: ultrawide changes centering, never text stretch. */
 int scale=max(1,p->height/720);p->row=36*scale;
 p->w=min(560*scale,p->area_width-32);p->h=min((112+6*36)*scale,p->height-32);
 p->x=(p->area_width-p->w)/2;p->y=(p->height-p->h)/2;
 p->visible=min(6,(p->h-112*scale)/p->row);
 if(p->visible<1){vo_dispose(p);return 0;}
 p->title=CreateFontA(-24*scale,0,0,0,FW_BOLD,0,0,0,DEFAULT_CHARSET,0,0,ANTIALIASED_QUALITY,DEFAULT_PITCH,"Segoe UI");
 p->body=CreateFontA(-18*scale,0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,0,0,ANTIALIASED_QUALITY,DEFAULT_PITCH,"Segoe UI");
 if(!p->title||!p->body){vo_dispose(p);return 0;}return 1;
}
int vo_paint(VoPaint *p,const VoOverlay *s){
 HDC dc;if(!p->surface||IDirectDrawSurface_IsLost(p->surface)!=DD_OK||IDirectDrawSurface_GetDC(p->surface,&dc)!=DD_OK)return 0;
 int saved=SaveDC(dc);if(!saved){IDirectDrawSurface_ReleaseDC(p->surface,dc);return 0;}
 RECT panel={p->x,p->y,p->x+p->w,p->y+p->h};fill(dc,panel,RGB(16,24,32));SetBkMode(dc,TRANSPARENT);
 SelectObject(dc,p->title);RECT title={p->x+16,p->y+8,p->x+p->w-16,p->y+48};text(dc,title,"VO PATCH EX",RGB(244,247,250));SelectObject(dc,p->body);
 if(s->selected<(unsigned)p->first)p->first=s->selected;
 if(s->selected>=(unsigned)(p->first+p->visible))p->first=s->selected-p->visible+1;
 if(s->unavailable){
  RECT r={p->x+16,p->y+56,p->x+p->w-16,p->y+p->h-60};
  SetTextColor(dc,RGB(244,247,250));DrawTextA(dc,"Not available in this private build.\nUse the existing F-key menus for settings.",-1,&r,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX);
 }else for(int row=0;row<p->visible;row++){
  unsigned i=p->first+row;RECT r={p->x+12,p->y+52+row*p->row,p->x+p->w-12,p->y+52+(row+1)*p->row};
  if(i==s->selected){fill(dc,r,RGB(36,61,80));RECT edge=r;edge.right=edge.left+3;fill(dc,edge,RGB(94,231,247));}
  r.left+=12;text(dc,r,vo_overlay_labels[i],RGB(244,247,250));
 }
 RECT back={p->x+16,p->y+p->h-48,p->x+p->w/2,p->y+p->h-12};text(dc,back,"Back",RGB(94,231,247));
 RECT resume={p->x+p->w/2,p->y+p->h-48,p->x+p->w-16,p->y+p->h-12};text(dc,resume,"Resume",RGB(94,231,247));
 RestoreDC(dc,saved);return IDirectDrawSurface_ReleaseDC(p->surface,dc)==DD_OK;
}
int vo_hit_source(VoPaint *p,int x,int y){
 if(x<p->x||x>=p->x+p->w||y<p->y||y>=p->y+p->h)return -1;
 if(y>=p->y+p->h-48)return x<p->x+p->w/2?6:5;
 int row=(y-p->y-52)/p->row;
 return y>=p->y+52&&row<p->visible?row+p->first:-1;
}
