"""Exercise emitted production classification with diagnostic consent at each level."""
from pathlib import Path
import sys,tempfile,subprocess,shutil
here=Path(__file__).resolve().parent;wrapper=Path(sys.argv[1])
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for name in ('policy.h','layout.h','state_bridge.h'):shutil.copy2(wrapper/'inc'/name,t/name)
 source=(wrapper/'src/state_bridge.c').read_text().replace('#include "diagnostics_runtime.h"','static unsigned diagnostic_level=3;\nstatic unsigned vo_diagnostic_level(void){return diagnostic_level;}')
 (t/'state_bridge.c').write_text(source)
 test=(here/'test_bridge.c').read_text();end=test.rfind('}')
 test=test[:end]+'''
 for(unsigned level=0;level<4;level++){
  reset();diagnostic_level=level;
  state(1,4,1,0);assert(vo_completed_policy()==VO_LOCAL_VS_GAMEPLAY);
  state(1,4,1,1);assert(vo_completed_policy()==VO_LOCAL_VS_SHARED);
  state(0,1,0,0);assert(vo_completed_policy()==VO_PRIMARY_ONLY);
  assert((observation.used>0)==(level>=2));
  assert((observation.captures>0)==(level>=3));
 }
 reset();diagnostic_level=3;state(1,4,1,0);
 unsigned used=observation.used,captures=observation.captures;
 diagnostic_level=0;state(1,4,1,1);
 assert(vo_completed_policy()==VO_LOCAL_VS_SHARED&&observation.used==used&&observation.captures==captures);
 puts("PASS emitted bridge: functional classification all levels, Off no traces/counters, immediate Off retains prior evidence");
'''+test[end:]
 (t/'test.c').write_text(test)
 subprocess.run(['clang','-std=c11','-fsanitize=address,undefined',str(t/'test.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test')],check=True)
