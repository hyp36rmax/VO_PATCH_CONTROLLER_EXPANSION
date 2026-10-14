/* Private dual-output movie visibility only. No MCI calls or movie mutation. */
typedef struct {DWORD tick;HWND movie;unsigned event,reason;BOOL previous_visible;int result;} VoMovieEvent;
typedef struct {HWND active;BOOL restore_pending;unsigned used,total,last_reason;VoMovieEvent events[64];} VoMovie;
enum { MOVIE_DETECTED=1,MOVIE_HIDDEN,MOVIE_ENDED,MOVIE_RESTORED,MOVIE_FAILED,MOVIE_REJECTED,MOVIE_SHUTDOWN };
enum { MOVIE_OK=0,MOVIE_MISSING,MOVIE_IDENTITY,MOVIE_BOUNDS,MOVIE_AMBIGUOUS,MOVIE_LIMIT,MOVIE_PHASE,MOVIE_HIDE_FAILED,MOVIE_RESTORE_FAILED };
static void vo_movie_event(VoMovie *m,unsigned event,unsigned reason,HWND movie,BOOL previous,int result){
 ++m->total;if(m->used<64)m->events[m->used++]=(VoMovieEvent){GetTickCount(),movie,event,reason,previous,result};
}
static BOOL vo_movie_contains(VoRect r,RECT b){return b.right>b.left&&b.bottom>b.top&&b.left>=r.x&&b.top>=r.y&&(int64_t)b.right<=(int64_t)r.x+r.w&&(int64_t)b.bottom<=(int64_t)r.y+r.h;}
typedef struct {HWND game,found;DWORD pid;VoRect monitor;unsigned seen,matches,reason;BOOL capped;} VoMovieSearch;
static BOOL CALLBACK vo_movie_child(HWND h,LPARAM value){
 VoMovieSearch *s=(VoMovieSearch*)value;if(++s->seen>64){s->capped=TRUE;return FALSE;}
 char name[32]={0};if(!GetClassNameA(h,name,sizeof name)||strcmp(name,"AVIWnd32"))return TRUE;
 DWORD pid=0;GetWindowThreadProcessId(h,&pid);HWND owner=GetWindow(h,GW_OWNER);
 if(pid!=s->pid||GetParent(h)!=s->game||GetAncestor(h,GA_ROOT)!=s->game||(owner&&owner!=s->game)||!(real_GetWindowLongA(h,GWL_STYLE)&WS_CHILD)){s->reason=MOVIE_IDENTITY;return TRUE;}
 if(!IsWindow(h)||!IsWindowVisible(h))return TRUE;
 RECT bounds={0};if(!GetWindowRect(h,&bounds)||!vo_movie_contains(s->monitor,bounds)){s->reason=MOVIE_BOUNDS;return TRUE;}
 s->found=h;++s->matches;return TRUE;
}
static HWND vo_movie_find(HWND game,VoRect monitor,unsigned *reason){
 VoMovieSearch s={0};s.game=game;s.monitor=monitor;s.pid=GetCurrentProcessId();s.reason=MOVIE_MISSING;
 DWORD pid=0;GetWindowThreadProcessId(game,&pid);
 if(!IsWindow(game)||pid!=s.pid){*reason=MOVIE_IDENTITY;return NULL;}
 EnumChildWindows(game,vo_movie_child,(LPARAM)&s);
 *reason=s.capped?MOVIE_LIMIT:s.matches>1?MOVIE_AMBIGUOUS:s.matches==1?MOVIE_OK:s.reason;
 return *reason==MOVIE_OK?s.found:NULL;
}
static BOOL vo_movie_restore(VoMovie *m,HWND p1){
 if(!m->restore_pending)return TRUE;
 BOOL before=IsWindowVisible(p1);
 BOOL ok=real_SetWindowPos(p1,HWND_TOPMOST,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW);
 ok=ok&&IsWindowVisible(p1);vo_movie_event(m,ok?MOVIE_RESTORED:MOVIE_FAILED,ok?MOVIE_OK:MOVIE_RESTORE_FAILED,NULL,before,ok);
 m->restore_pending=FALSE;return ok;
}
/* Called on the output-owning render thread. Record transitions in memory only.
 * A completed PRIMARY_ONLY pair establishes that the second output is black.
 * Window visibility/destruction, not elapsed time, determines movie lifetime. */
static BOOL vo_movie_update(VoMovie *m,HWND game,HWND p1,VoRect monitor,BOOL eligible,BOOL may_show){
 unsigned reason=MOVIE_PHASE;HWND found=eligible?vo_movie_find(game,monitor,&reason):NULL;
 if(m->active&&m->active!=found){vo_movie_event(m,MOVIE_ENDED,reason,m->active,IsWindowVisible(p1),1);m->active=NULL;m->restore_pending=TRUE;}
 if(found&&!m->active&&may_show){
  if(!IsWindow(found)||!IsWindowVisible(found)){reason=MOVIE_MISSING;found=NULL;}
  else {BOOL before=IsWindowVisible(p1);m->active=found;m->restore_pending=FALSE;vo_movie_event(m,MOVIE_DETECTED,MOVIE_OK,found,before,1);
   ShowWindow(p1,SW_HIDE);BOOL ok=!IsWindowVisible(p1);vo_movie_event(m,ok?MOVIE_HIDDEN:MOVIE_FAILED,ok?MOVIE_OK:MOVIE_HIDE_FAILED,found,before,ok);if(!ok)return FALSE;}
 }
 if(reason!=m->last_reason){if(reason!=MOVIE_OK)vo_movie_event(m,MOVIE_REJECTED,reason,found,IsWindowVisible(p1),0);m->last_reason=reason;}
 if(may_show&&!m->active&&!vo_movie_restore(m,p1))return FALSE;
 return TRUE;
}
static void vo_movie_log(FILE *log,VoMovie *m){
 fprintf(log,"movie_events=%u recorded=%u active=%p restore_pending=%d event_codes=1:DETECTED,2:P1_HIDDEN,3:ENDED_OR_HIDDEN,4:P1_RESTORED,5:FAILED,6:REJECTED,7:SHUTDOWN reason_codes=0:OK,1:MISSING,2:IDENTITY,3:BOUNDS,4:AMBIGUOUS,5:LIMIT,6:PHASE,7:HIDE_FAILED,8:RESTORE_FAILED\n",m->total,m->used,m->active,m->restore_pending);
 for(unsigned i=0;i<m->used;i++){VoMovieEvent *e=&m->events[i];fprintf(log,"movie_event tick=%lu hwnd=%p event=%u reason=%u previous_p1_visible=%d result=%d\n",(unsigned long)e->tick,e->movie,e->event,e->reason,e->previous_visible,e->result);}
}
