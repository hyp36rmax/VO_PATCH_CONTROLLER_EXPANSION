#include "window_model.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 VoWindow a[VO_WINDOWS]={0};unsigned n=0;
 VoWindow game={1,0,0,42,7,5,1,{0,0,2560,1440}};
 VoWindow movie={2,1,0,42,7,5,1,{0,0,1920,1080}};
 VoWindow p1={3,0,0,42,8,2,1,{0,0,2560,1440}};
 VoWindow p2={4,0,0,42,8,3,1,{2560,0,4480,1080}};
 assert(vo_append(a,&n,game)&&vo_append(a,&n,movie)&&n==2);
 assert(vo_append(a,&n,movie)&&n==2&&a[1].parent==1&&a[1].owner==0);
 assert(vo_cover_candidate(p1,movie)&&!vo_cover_candidate(p2,movie));
 p1.visible=0;assert(!vo_cover_candidate(p1,movie));p1.visible=1;
 p1.rank=6;assert(!vo_cover_candidate(p1,movie));
 assert(!vo_cover_candidate(game,movie));
 assert(vo_contains(a,n,2)&&!vo_contains(a,n,99));
 VoWindow next[VO_WINDOWS]={0};unsigned nn=0;assert(vo_append(next,&nn,game));
 assert(!vo_contains(next,nn,movie.hwnd)); /* observed disappearance */
 assert(!vo_contains(next,0,game.hwnd)); /* empty and process-exit snapshot */
 for(unsigned i=2;i<VO_WINDOWS;i++){VoWindow w={0};w.hwnd=i+100;assert(vo_append(a,&n,w));}
 VoWindow excess={0};excess.hwnd=999;assert(!vo_append(a,&n,excess)&&n==VO_WINDOWS);
 assert(vo_overlap((VoBounds){-1920,-1080,0,0},(VoBounds){-100,-100,100,100}));
 assert(!vo_overlap((VoBounds){0,0,1920,1080},(VoBounds){1920,0,3840,1080}));
 assert(!vo_overlap((VoBounds){0,0,0,0},(VoBounds){-100,-100,100,100}));
 puts("PASS bounded enumeration model, deduplication, parent/owner retention, top-level overlap candidates, hidden/below/disjoint rejection, missing windows, lifecycle and empty exit snapshot");
}
