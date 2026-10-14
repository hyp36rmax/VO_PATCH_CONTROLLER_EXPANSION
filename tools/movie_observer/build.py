"""Cross-build the standalone ordinary-user external observer."""
import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--cc',required=True);p.add_argument('--windres',required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;a.output.mkdir(parents=True,exist_ok=True);obj=a.output.resolve()/'observer-res.o'
subprocess.run([a.windres,'-I',str(here),str(here/'observer.rc'),str(obj)],check=True)
subprocess.run([a.cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-municode',str(here/'observer.c'),str(obj),'-luser32','-ldwmapi','-Wl,--no-insert-timestamp','-o',str(a.output.resolve()/'MOVIE-OBSERVER.exe')],check=True)
