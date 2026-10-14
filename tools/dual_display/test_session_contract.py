"""Session launch/storage wiring checks; not native PowerShell or Win32 execution."""
from pathlib import Path
h=Path(__file__).resolve().parent
s=(h/'mode_select.c').read_text();launch=(h/'LaunchModes.ps1').read_text();ext=(h/'mode_extension.py').read_text()
assert 'session_mode>=0?session_path:config' in s
assert 'session_mode>=0?WritePrivateProfileStringW' in s
assert 'else if(changed&1)next.mode=' in s and 'EnableWindow(modebox,session_mode<0)' in s
assert 'vo_select_session(monitors,count,&next,session_mode' in s
assert 'SESSION-ONLY TEST' in s and 'preferences_written=%d' in s
assert 'GetEnvironmentVariableW(L"VO_SESSION_CONFIG"' in ext
assert 'if(session_len)wcscpy(config,session_config)' in ext
assert '@{single=0;versus=1;mirror=2}' in launch
assert launch.index('Session mode mismatch')<launch.index('Copy-Item')
assert launch.index("'Collect-Modes.ps1'")<launch.index('Remove-Item -LiteralPath $sessionFile')
assert 'fallback=1|strict_test_stopped=1' in launch
assert "'VO_STRICT_MODE'" not in launch # property syntax sets environment directly
assert '$env:VO_STRICT_MODE' in launch and '$env:VO_SESSION_CONFIG' in launch
assert 'beforePreferenceHash' in launch and 'afterPreferenceHash' in launch
# Temporary session projection is collected, not promoted to saved preferences.
assert 'Copy-Item' not in s and 'MoveFile' not in s
print('PASS session-only configuration destination, locked mode UI, exact launcher labels, wrapper handoff, strict failure reporting, preference hashes and post-collection cleanup; source contracts')
