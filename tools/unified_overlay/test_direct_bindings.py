"""Original F7 option tables remain authoritative for direct editor labels."""
from pathlib import Path
import sys,struct,subprocess,tempfile
from test_controller_adapter import AdapterMachine,v
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 dll=Path(td)/'controller.dll';cc=here.parents[1]/'../llvm-mingw-20260908-ucrt-macos-universal/bin/i686-w64-mingw32-clang'
 subprocess.run([str(cc.absolute()),'-shared','-O2','-Wl,--export-all-symbols','-Wl,--image-base,0x60000000',str(here/'controller_settings.c'),'-o',str(dll),'-luser32'],check=True)
 for path in sys.argv[1:]:
  m=AdapterMachine(path);m.load(dll);j=m.ed.short=='jpre';game=0x10050000;state=0x10040000
  names=('MODE','CUSTOM1','DZTHR1','DEVICES','BINDS1','BLOCKS','CURPLAYER');sym={n:v.symbol_va(n,m.ed) for n in names}
  m.u.mem_write(game,struct.pack('<21I',84,0,0,0,0,sym['MODE'],0,0,0,0,0,0,sym['CUSTOM1'],sym['DZTHR1'],sym['DEVICES'],sym['BINDS1'],0,0,0,0,0))
  for player in range(2):
   for kind in (0,1,3):
    m.word(sym['CURPLAYER'],player);m.word(sym['BLOCKS']+112*player,kind)
    assert m.ccall('vo_controller_begin',state,game,1,player,kind)
    m.controls={};m.windows[1]=m.controls;m.u.mem_write(0x10030000,bytes(32))
    m.method((0x4960bf if j else 0x497560) if kind==0 else (0x496705 if j else 0x497ba8),(1,0,0))
    id=struct.unpack('<I',m.u.mem_read((0x669558 if j else 0x66d5d0) if kind==0 else (0x6695b8 if j else 0x66d630),4))[0]
    items=m.control(id)['items'];assert len(items)==m.ccall('vo_controller_count',state,0)
    for i,label in enumerate(items):
     assert m.ccall('vo_controller_choice',state,0,i,0x10060000,192)
     assert m.string(0x10060000)==label,(j,kind,i,m.string(0x10060000),label)
     assert m.ccall('vo_controller_select',state,0,i)
     assert m.ccall('vo_controller_selected',state,0)==i
    m.ccall('vo_controller_end',state)
  m.u.mem_write(sym['CUSTOM1'],bytes(48));assert m.ccall('vo_controller_has_axes',game,0,4)==0
  m.u.mem_write(sym['CUSTOM1']+24,b'\xe8');assert m.ccall('vo_controller_has_axes',game,0,4)==0 and m.ccall('vo_controller_has_axes',game,1,4)==1
  assert m.ccall('vo_controller_has_axes',game,1,5)==0
  print(m.ed.short,'PASS both players: all original F7 labels and binding encodings round-trip without native controls')
