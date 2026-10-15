"""Offline profile equality and loader-write exclusion; not Windows acceptance."""
from pathlib import Path
import sys
import startup_image as s
for folder in map(Path,sys.argv[1:]):
 raw=(folder/'v_on.exe').read_bytes();base,plans,meta=s.plan(raw)
 for name,writes in plans.items():
  expected=s.mapped(meta['images'][name]);expected+=bytes(len(base)-len(expected))
  actual=bytearray(base);s.activate(actual,writes);assert actual==expected
  # Model imports/loader directories already modified before PE entry.
  loaded=bytearray(base);wanted=bytearray(expected)
  for lo,hi in meta['protected']:
   loaded[lo:hi]=bytes([0xa5])*(hi-lo);wanted[lo:hi]=bytes([0xa5])*(hi-lo)
  s.activate(loaded,writes);assert loaded==wanted
  if writes:
   bad=bytearray(base);offset=writes[-1][0];bad[offset]^=1;before=bytes(bad)
   try:s.activate(bad,writes)
   except ValueError:pass
   else:raise AssertionError('corruption accepted')
   assert bytes(bad)==before
  print('PASS',meta['edition'],name,'exact mapped profile equality;',len(writes),'writes; protected loader state excluded',flush=True)
