"""Run the original six-size desktop-preservation checks against F04's opt-in gate.
The same assertions apply; only the private mode name and extraction boundary differ.
"""
from pathlib import Path
source=Path(__file__).with_name('test_desktop_mode.py')
s=source.read_text().replace("s.index('    BOOL zooming',start)","s.index('    BOOL vo_selected_desktop',start)").replace('VO_DUAL_DISPLAY','VO_PRIVATE_DISPLAY')
exec(compile(s,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
