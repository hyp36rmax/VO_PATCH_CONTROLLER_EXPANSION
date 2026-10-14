/* Fault-injection tests of production lifecycle code with a host API double.
 * This is NOT Windows/GPU or real-game-frame acceptance evidence. */
#define VO_DUAL_TEST
#include "presentation_test_api.h"
#include "presentation.h"
#include <assert.h>
static void reset_test(void) {
    memset(&vo_dual,0,sizeof vo_dual); memset(&fake,0,sizeof fake);
    fake.foreground=1; fake.enabled=1;
    g_ddraw.width=3840;g_ddraw.height=1080;g_ddraw.bpp=16;g_ddraw.hwnd=(HWND)1;
    g_d3d9.params.Windowed=1;g_d3d9.tex_width=4096;g_d3d9.tex_height=2048;
    g_d3d9.surface_tex[0]=(void*)10;g_d3d9.surface_tex[1]=(void*)11;
    count=2;monitors[0]=(VoMonitor){"a",{0,0,1920,1080},1,1};
    monitors[1]=(VoMonitor){"b",{-2560,-1440,2560,1440},0,1};
}
int main(void) {
    reset_test();vo_dual_present(0);assert(!vo_dual.attempted&&fake.draws==0);
    vo_dual_uploaded(1);vo_dual_present(1);
    assert(vo_dual.pairs==1&&fake.draws==2&&fake.presents==2);
    assert(fake.texture[0]==(void*)11&&fake.texture[1]==(void*)11);
    assert(fake.vertices[0][0].u==0&&fake.vertices[0][2].u==1920.0f/4096);
    assert(fake.vertices[1][0].u==1920.0f/4096&&fake.vertices[1][2].u==3840.0f/4096);
    assert(fake.vertices[0][0].v==1080.0f/2048);
    assert(fake.vertices[1][2].x==2559.5f&&fake.vertices[1][0].y==1439.5f);
    assert(fake.restores==1&&fake.streams==1&&fake.live==5&&vo_dual.visible);
    fake.foreground=0;vo_dual_present(1);assert(fake.draws==2&&!vo_dual.visible);
    fake.foreground=1;vo_dual_present(1);assert(vo_dual.pairs==2&&vo_dual.visible);
    vo_output_proc(vo_dual.window[0],WM_DISPLAYCHANGE,0,0);vo_dual_present(1);
    assert(fake.live==0&&vo_dual.disabled&&!vo_dual.visible);
    vo_dual_end();assert(fake.destroyed==2);
    reset_test();vo_dual_uploaded(0);fake.enabled=0;vo_dual_present(0);assert(!vo_dual.attempted&&!fake.draws);
    reset_test();vo_dual_uploaded(0);count=1;vo_dual_present(0);assert(vo_dual.disabled&&!fake.draws&&!fake.live);
    reset_test();vo_dual_uploaded(0);vo_dual_present(0);vo_dual_before_reset();assert(!fake.live&&vo_dual.disabled);vo_dual_end();
    /* Fail every graphics call once: no leaks, paired draws precede presents,
       failed draw/capture cannot publish stale outputs, restoration attempted. */
    reset_test();vo_dual_uploaded(0);vo_dual_present(0);int calls=fake.calls;vo_dual_end();
    for(int n=1;n<=calls;++n) {
        reset_test();vo_dual_uploaded(0);fake.fail_at=n;vo_dual_present(0);
        assert(vo_dual.disabled);assert(!vo_dual.visible);assert(fake.live==0);
        assert(fake.presents==0||fake.draws==2);
        vo_dual_end();assert(fake.live==0);
    }
    printf("PASS: production presentation lifecycle; %d graphics failure points, texture ownership, UV halves, state restore, focus, disconnect, reset and teardown (API doubles)\n",calls);
    return 0;
}
