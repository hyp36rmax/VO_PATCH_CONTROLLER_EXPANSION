"""Execute installed F7 enumeration and atomic two-player profile commits.
Uses original Retail/JPRE data and writer, with fault-injected Windows file APIs.
"""
from pathlib import Path
import sys,struct,subprocess,tempfile
from test_controller_adapter import AdapterMachine,v
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 cc=here.parents[1]/'../llvm-mingw-20260908-ucrt-macos-universal/bin/i686-w64-mingw32-clang';dll=Path(td)/'profiles.dll'
 subprocess.run([str(cc.absolute()),'-shared','-O2','-Wl,--export-all-symbols','-Wl,--image-base,0x60000000',str(here/'controller_settings.c'),'-o',str(dll),'-luser32'],check=True)
 for path in sys.argv[1:]:
  m=AdapterMachine(path);m.load(dll);j=m.ed.short=='jpre';game=0x10050000;draft=0x10060000;text=0x10061000
  sym={n:v.symbol_va(n,m.ed) for n in ('MODE','CUSTOM1','DZTHR1','DEVICES','BINDS1','BLOCKS','DEV_NUM')}
  m.u.mem_write(game,struct.pack('<21I',84,0,0,0,0,sym['MODE'],0,0,0,0,0,0,sym['CUSTOM1'],sym['DZTHR1'],sym['DEVICES'],sym['BINDS1'],0,0,0,0,0))
  m.u.mem_write(0x1acb7f0 if j else 0x1ad0b98,b'C:\\Games With Spaces\\v_on.ini\0')
  count=m.ccall('vo_controller_profile_count',game);assert count==9
  ids=list(m.u.mem_read(sym['DEV_NUM'],count));labels=v.symbol_va(('RAPH','profiles'),m.ed)
  for i,id in enumerate(ids):
   assert m.ccall('vo_controller_profile_choice',game,i,text,192)==id
   expected=m.string(struct.unpack('<I',m.u.mem_read(labels+4*i,4))[0]);assert m.string(text)==expected
  config=0x64f6c0 if j else 0x6536c0
  original_config=bytes(m.u.mem_read(config,8))
  original=bytes(m.u.mem_read(sym['BLOCKS'],224));bindings=bytes(m.u.mem_read(sym['CUSTOM1'],48))
  for p in range(2):
   for id in ids:
    values=list(struct.unpack('<2I',m.u.mem_read(sym['DEVICES'],8)));values[p]=id;m.u.mem_write(draft,struct.pack('<2I',*values))
    before=bytes(m.u.mem_read(sym['DEVICES'],8));old=dict(m.files['C:\\Games With Spaces\\v_on.ini'])
    m.fail_replace=True;assert not m.ccall('vo_controller_profiles_save',game,draft);m.fail_replace=False
    assert bytes(m.u.mem_read(sym['DEVICES'],8))==before and m.files['C:\\Games With Spaces\\v_on.ini']==old
    assert m.ccall('vo_controller_profiles_save',game,draft)
    assert list(struct.unpack('<2I',m.u.mem_read(sym['DEVICES'],8)))==values
    for player,k in enumerate(values):
     saved=m.files['C:\\Games With Spaces\\v_on.ini'][('Device Settings',f'{player+1}P Device No.')]
     assert int(saved,16)>>16==k
  after=bytes(m.u.mem_read(sym['BLOCKS'],224))
  assert original[4:112]==after[4:112] and original[116:]==after[116:]
  assert bytes(m.u.mem_read(sym['CUSTOM1'],48))==bindings
  assert bytes(m.u.mem_read(config,8))==original_config
  m.u.mem_write(draft,struct.pack('<2I',999,1));assert not m.ccall('vo_controller_profiles_save',game,draft)
  print(m.ed.short,'PASS installed F7 order/labels/IDs, all P1/P2 profiles, atomic failure/retry, original saved values, binding preservation, unsupported rejection')
