"""Execute emitted wrapper synchronization exports; pin the matching upload lock."""
from pathlib import Path
import subprocess,sys,tempfile
wrapper=Path(sys.argv[1]);source=(wrapper/'src/ddsurface.c').read_text()
body=source[source.index('BOOL WINAPI VonOverlaySurfaceBegin'):]
render=(wrapper/'src/render_d3d9.c').read_text()
assert 'g_config.lock_surfaces && !TryEnterCriticalSection(&g_ddraw.primary->cs)' in render
assert 'LeaveCriticalSection(&g_ddraw.primary->cs)' in render
assert all(name in (wrapper/'exports.def').read_text() for name in ('VonOverlaySurfaceBegin','VonOverlaySurfaceEnd'))
fixture=r'''
#include <assert.h>
#include <stdio.h>
#define WINAPI
#define BOOL int
#define FALSE 0
#define TRUE 1
typedef struct {int cs,refs;} IDirectDrawSurfaceImpl;
static struct {int lock_surfaces;} g_config;
static struct {IDirectDrawSurfaceImpl *primary;struct {int run,surface_updated,screen_updated,sem;} render;} g_ddraw;
static int flushes,wakes;
static void IDirectDrawSurface_AddRef(IDirectDrawSurfaceImpl*s){s->refs++;}
static void IDirectDrawSurface_Release(IDirectDrawSurfaceImpl*s){assert(!s->cs);s->refs--;}
static void EnterCriticalSection(int*p){assert(!*p);*p=1;}
static void LeaveCriticalSection(int*p){assert(*p);*p=0;}
static void GdiFlush(void){flushes++;}
static void InterlockedExchange(int*p,int n){assert(flushes);*p=n;}
static void ReleaseSemaphore(int sem,int n,void*p){(void)sem;assert(n==1&&!p&&flushes&&g_ddraw.primary->cs);wakes++;}
'''
main=r'''
int main(void){IDirectDrawSurfaceImpl a={0},b={0};g_ddraw.primary=&a;g_ddraw.render.run=1;
 assert(!VonOverlaySurfaceBegin(&a)&&!a.refs&&!a.cs);g_config.lock_surfaces=1;
 assert(!VonOverlaySurfaceBegin(NULL));
 for(int i=0;i<10;i++){assert(VonOverlaySurfaceBegin(&a)&&a.refs==1&&a.cs);VonOverlaySurfaceEnd(&a);assert(!a.refs&&!a.cs&&wakes==i+1);}
 assert(VonOverlaySurfaceBegin(&b));VonOverlaySurfaceEnd(&b);assert(!b.refs&&!b.cs&&wakes==10);
 assert(g_ddraw.render.surface_updated&&g_ddraw.render.screen_updated);
 puts("PASS emitted wrapper transaction: renderer's existing surface lock, balanced lifetime, flush before publication, immediate primary wake only, disabled-lock refusal");}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'sync.c').write_text(fixture+body+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p/'sync.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
