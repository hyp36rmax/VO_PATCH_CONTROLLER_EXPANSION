"""Pin all controller adapter pointers to the patcher's authoritative symbols."""
from pathlib import Path
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from selftest import load_patcher
v=load_patcher();source=Path(__file__).with_name('controller_settings.c').read_text()
body=source.split('addresses[2]={',1)[1].split('\n};',1)[0]
rows=[[int(x,16) for x in re.findall(r'0x[0-9a-f]+',row)] for row in body.splitlines() if '0x' in row]
keys={0:'BLOCKS',1:'CURPLAYER',9:'GAMEPADDEF',10:'SIMPLEDEF',11:('TWIN','custombinds'),12:('CUSTOM','resolve'),13:('CUSTOM','procedure'),14:('CUSTOM','pending'),15:('CUSTOM','player'),16:'PADIDX',17:'DZSTR1',18:'DZSEED',19:'WRITELINE'}
for j,name in enumerate(('retail','jpre')):
 b=next(b for b in v.BUILDS.values() if b.short==name)
 for index,key in keys.items():assert rows[j][index]==v.symbol_va(key,b),(name,key,hex(rows[j][index]),hex(v.symbol_va(key,b)))
 assert len(rows[j])==21
 print(name,'PASS controller adapter linked-symbol identities')

 # The overlay reads the existing F7 enumeration, not a parallel ID table.
 order=0x36aff59 if j else 0x36b5f59
 labels=0x36b14e0 if j else 0x36b74e0
 assert v.symbol_va('DEV_NUM',b)==order and hex(order) in source
 assert v.symbol_va(('RAPH','profiles'),b)==labels and hex(labels) in source
