"""Execute dedicated VS split-preference hooks against both generated editions."""
import hashlib
from pathlib import Path
import struct
import sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ESP
import mode_profiles,split_preference
v=mode_profiles.engineering3840.load_private()
for folder in map(Path,sys.argv[1:]):
 raw=(folder/'v_on.exe').read_bytes();edition=v.BUILDS[hashlib.md5(raw).hexdigest()]
 baseline,_=mode_profiles.engineering_shared.build(raw);image,m=split_preference.install(baseline,edition);pe=v._PE(image)
 assert len(image)==len(baseline) and v._PE(baseline).sections==pe.sections
 port=None if edition.short=='retail' else v.PORT['%08x'%v._pe_stamp(raw)]
 addr=lambda a:a if port is None else port['va'][a]
 mu=Uc(UC_ARCH_X86,UC_MODE_32);mu.mem_map(0x400000,0x4000000);mu.mem_map(0x7000000,0x10000)
 for s in pe.sections:mu.mem_write(pe.base+s['vaddr'],image[s['raddr']:s['raddr']+s['rsize']])
 def put(a,n):mu.mem_write(a,struct.pack('<I',n))
 def get(a):return struct.unpack('<I',mu.mem_read(a,4))[0]
 def run(name,stop,eax=0):
  mu.reg_write(UC_X86_REG_ESP,0x700f000);mu.reg_write(UC_X86_REG_EAX,eax)
  mu.emu_start(m['entries'][name],stop,count=200)
  assert mu.reg_read(UC_X86_REG_ESP)==0x700f000
 for initial in (0,2):
  put(m['flags'],0x80|initial);put(m['initialized'],0);put(m['ui']+v.UI_F4MODE,0)
  run('ini_load',m['continuations']['ini_load'])
  assert get(m['preference'])==initial and get(m['flags'])==0x80
  for saved in (2,0,2):
   # F5 shows the saved orientation, regardless of effective vertical flags.
   run('dialog_init',addr(0x427ec9),get(m['flags']))
   stage=addr(0xbe4300);assert get(stage)&2==get(m['preference'])
   run('dialog_ok',addr(0x428241),0x80|saved)
   assert get(m['preference'])==saved and get(m['flags'])==0x80
   for low in (0,1):
    put(m['ui']+v.UI_F4MODE,low)
    run('ini_save',m['ini_save_return'])
    assert mu.reg_read(UC_X86_REG_EAX)==0x80|saved|low
    assert get(m['flags'])==0x80
   # Game drawing cannot overwrite the preference with forced vertical.
   for entry in ('frame','marker_a','marker_b'):
    run(entry,m['continuations'][entry]);assert get(m['preference'])==saved
  # Cold/default path before any INI hook still captures the original bit.
  for entry in ('frame','marker_a','marker_b'):
   put(m['initialized'],0);put(m['flags'],0x80|initial)
   run(entry,m['continuations'][entry]);assert get(m['preference'])==initial
 print('PASS',edition.short,'F5 display/commit, existing INI bit, high/low serialization, cold defaults, draw isolation and unchanged PE layout')
