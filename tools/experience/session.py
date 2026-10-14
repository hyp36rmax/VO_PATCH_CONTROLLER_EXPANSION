"""Private G03 coordinator. All diagnostics I/O is outside the game process."""
import argparse
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import time
import diagnostics as d
import discovery
import prepare


def capture(root, prior):
    current = discovery.snapshot()
    if current != prior:
        d.event(root, 'controller_discovery', {'count': len(current['controllers'])})
        for item in current['controllers']:
            d.event(root, 'controller_discovery', item)
        d.event(root, 'display_discovery', {'count': len(current['displays'])})
        for item in current['displays']:
            d.event(root, 'display_discovery', item)
        if not current['displays']:
            d.event(root, 'recovery', {'code': 1})
    return current


def collect(root, level):
    failed = False
    for kind, name in d.LOGS.items():
        path = root/name
        if path.is_file():
            d.event(root, 'module_init', {'module': {'selection':2, 'presentation':3, 'movie':4}[kind], 'ok': True})
            for row in d.project(d.read_bounded(path), {'NORMAL':64, 'DETAILED':256, 'DEVELOPMENT':1024}[level]):
                d.event(root, kind, row)
                if row.get('exit_code', 0) or row.get('hr', 0) & 0x80000000 or row.get('strict_test_stopped', 0):
                    failed = True
                    d.event(root, 'error', {'code': row.get('exit_code') or row.get('hr') or 4})
                if row.get('fallback', 0):
                    d.event(root, 'recovery', {'fallback': row['fallback']})
    for values in d.configurations(root).values():
        for key, value in values.items():
            if key in ('1p device no.', '2p device no.'):
                d.event(root, 'configuration', {'player': int(key[0]), 'device': value})
    # Legacy module logs remain local for recovery. Shared exports contain only
    # numeric projections, never free-form text or identities.
    return failed


def run_session(root, mode, level):
    marker = root/'diagnostics/session-active'
    if marker.exists():
        d.event(root, 'previous_session_incomplete')
        collect(root, level)
    d.event(root, 'startup', {'level': d.LEVELS.index(level)})
    marker.write_text('active\n')
    prepare.prepare(root)
    d.event(root, 'module_init', {'module': 1, 'ok': True})
    for name in ('movie-windows.log', 'launch-status.txt', 'launch-error.txt', 'selection.txt', 'selection-errors.txt', 'game/D04-P02B-presentation.log'):
        d.rotate(root/name)
    prior = None
    try:
        prior = capture(root, prior)
    except OSError:
        d.event(root, 'error', {'code': 2})
    env = dict(os.environ, VO_EX_DIAGNOSTICS=level)
    # Existing launch policy owns mode selection, fallback and game lifetime.
    child = subprocess.Popen(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                              '-File', str(root/'LaunchModes.ps1'), '-Entry', mode], cwd=root, env=env)
    next_discovery = time.monotonic()+10
    while child.poll() is None:
        time.sleep(1)
        if time.monotonic() >= next_discovery:
            try:
                prior = capture(root, prior)
            except OSError:
                pass  # bounded initial warning; do not flood on device races
            next_discovery = time.monotonic()+10
    failed = collect(root, level)
    result = child.returncode or int(failed)
    if (root/'launch-error.txt').exists():
        result = result or 1
    if result:
        d.event(root, 'error', {'code': result})
    d.event(root, 'shutdown', {'code': result})
    marker.unlink(missing_ok=True)
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=('single', 'versus', 'mirror', 'export'))
    p.add_argument('--level', choices=d.LEVELS, default='NORMAL')
    args = p.parse_args(); root = Path(__file__).resolve().parent
    if os.name != 'nt':
        raise SystemExit('This private launcher requires Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    lock = kernel.CreateMutexW(None, False, 'Local\\VOPatchExperienceG03')
    if not lock or ctypes.get_last_error() == 183:
        if lock:
            kernel.CloseHandle(lock)
        raise SystemExit('An Experience launch/export is already active')
    result = 0
    try:
        if args.mode != 'export':
            result = run_session(root, args.mode, args.level)
    except Exception as error:
        result = 1
        try:
            d.event(root, 'error', {'code': getattr(error, 'winerror', None) or 3})
        except OSError:
            pass
        print('Launch could not finish. Check that you selected a pristine Retail/JPRE game folder and extracted this package to a writable folder.')
    finally:
        try:
            d.export(root)
            print('Return RETURN-THIS-VO-PATCH-EX-G03.zip from this folder.')
            try:
                subprocess.Popen(['explorer.exe', '/select,' + str(root/'RETURN-THIS-VO-PATCH-EX-G03.zip')])
            except OSError:
                pass
        except Exception:
            print('Export could not finish. Original local logs are retained; EXPORT-DIAGNOSTICS.cmd can retry.')
            result = 1
        kernel.CloseHandle(lock)
    return result


if __name__ == '__main__':
    sys.exit(main())
