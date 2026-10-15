"""Execute direct production transactions vs original F5/F6 operations.
Original UI procedures run only as the test oracle, never in the new adapter.
"""
from pathlib import Path
import sys,struct,subprocess,tempfile
from test_controller_adapter import AdapterMachine,v
from unicorn import x86_const as r
class DirectMachine(AdapterMachine):
 def hook(self,u,a,size,data):
  hardware=(0x5ce180,0x5c8ca0,0x5c56a2,0x5c680b) if self.ed.short=='retail' else (0x5c8a10,0x5c34e6,0x5bff42,0x5c10da)
  if a in hardware:self.return_(1,0);return
  return super().hook(u,a,size,data)
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 dll=Path(td)/'direct.dll';cc=here.parents[1]/'../llvm-mingw-20260908-ucrt-macos-universal/bin/i686-w64-mingw32-clang'
 subprocess.run([str(cc.absolute()),'-shared','-O2','-Wl,--export-all-symbols','-Wl,--image-base,0x60000000',str(here/'native_settings.c'),'-o',str(dll),'-luser32'],check=True)
 for path in sys.argv[1:]:
  m=DirectMachine(path);m.load(dll);j=m.ed.short=='jpre';state=0x10040000;mode=v.symbol_va('MODE',m.ed)
  graphics=[0x6c41e8,0x3457ea8,0x3457eb4,0x3457eb8,0x67ec14,0x67ec18,0x67ec1c,0x6bb2b0,0x6bb2b4,0x67d778] if j else [0x6c84d0,0x345d248,0x345d234,0x345d25c,0x682c8c,0x682c90,0x682c94,0x6bf598,0x6bf59c,0x6817f0]
  ptr=0x1cdca64 if j else 0x1ce1dbc;snap=0x5c67a5 if j else 0x5cbf05
  globals=[0x1ad7dc0,0x1ad7dc8,0x1ad7dc4,0x1ad7db8,0x1ad7dcc,0x1ad7dbc] if j else [0x1add13c,0x1add134,0x1add138,0x1add148,0x1add144,0x1add140]
  procs=[0x427a60,0x5c5880,0x5c5db8,0x5c61fa,0x5c6569] if j else [0x427e00,0x5cafe0,0x5cb518,0x5cb95a,0x5cbcc9]
  m.word(ptr,0x10020000)
  def begin(cat):
   m.u.mem_write(state,bytes(2200));assert m.ccall('vo_native_begin',state,1,mode,cat)==1
  for cat,ids,defaults in [(1,list(range(1000,1008)),1012),(2,[1013,1014],1021),(3,[1074,1075,1076,1079,1080,1081],1041),(4,[1076,1077,1078,1079],1028)]:
   begin(cat);m.controls={};m.call(procs[cat],(1,0x110,0,0))
   for id in ids:
    if id<1020:
     for choice in range(m.ccall('vo_native_count',state,id)):
      assert m.ccall('vo_native_select',state,id,choice)
      assert m.ccall('vo_native_selected',state,id)==choice
      m.control(id)['selection']=choice;m.call(procs[cat],(1,0x111,id|(1<<16),0))
      # Snapshot encoding oracle: same byte representation, not a new format.
      m.ccall('vo_native_commit',state);m.call(snap);m.controls={};m.call(procs[cat],(1,0x110,0,0));assert m.control(id)['selection']==choice,(j,cat,id,choice)
    else:
     before=m.control(id)['checked'];fn='vo_native_radio' if cat==4 and id>=1078 else 'vo_native_click'
     args=(state,1078,1079,id) if fn=='vo_native_radio' else (state,id)
     assert m.ccall(fn,*args);expected=m.ccall('vo_native_check',state,id)
     m.ccall('vo_native_commit',state);m.call(snap);m.controls={};m.call(procs[cat],(1,0x110,0,0));assert m.control(id)['checked']==expected,(j,cat,id)
   assert m.ccall('vo_native_defaults',state);m.ccall('vo_native_commit',state)
   m.call(snap);m.controls={};m.call(procs[cat],(1,0x110,0,0));before={i:dict(c) for i,c in m.controls.items()}
   m.call(procs[cat],(1,0x111,defaults,0));m.call(0x5c6800 if j else 0x5cbf60);m.call(snap);m.controls={};m.call(procs[cat],(1,0x110,0,0))
   assert before==m.controls,(j,cat,'defaults parity')
   m.ccall('vo_native_end',state)
  for id in [1075,1077,1078,1079,1056,1057,1058,1059,1068,1069,1070,1073]:
   begin(0)
   if id in [1075,1077,1078,1079]:assert m.ccall('vo_native_click',state,id)
   else:
    first,last=(1056,1057) if id<1058 else (1058,1059) if id<1068 else (1068,1069) if id<1070 else (1070,1073)
    assert m.ccall('vo_native_radio',state,first,last,id)
   expected=m.ccall('vo_native_check',state,id);assert m.ccall('vo_native_commit',state)
   m.controls={};m.call(procs[0],(1,0x110,0,0));assert m.control(id)['checked']==expected,(j,id,expected,m.control(id),bytes(m.u.mem_read(0x36b4000+0x1ec0 if j else 0x36ba000+0x1ec0,12)).hex(),bytes(m.u.mem_read(state+2060,64)).hex())
   m.ccall('vo_native_end',state)
  # A running match updates bookkeeping after this draft was opened.
  m.ccall('vo_native_end',state);begin(1)
  live=0x1b27260 if j else 0x1caf4a0
  m.word(live+0xac-8,123456)
  assert m.ccall('vo_native_select',state,1000,3)
  assert m.ccall('vo_native_commit',state)
  assert struct.unpack('<I',m.u.mem_read(live+0xac-8,4))[0]==123456
  m.ccall('vo_native_end',state);before=bytes(m.u.mem_read(live,0x20c));begin(1)
  m.ccall('vo_native_defaults',state);m.ccall('vo_native_end',state)
  assert bytes(m.u.mem_read(live,0x20c))==before
  print(m.ed.short,'PASS direct F5/F6 current values, every combo choice, toggles, defaults parity and original commit/completion')
