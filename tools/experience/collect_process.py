"""Passive process-exit collector for an installed game; no launch/config authority.

The normal-startup bridge must invoke this once with the actual game PID. Until
that bridge is integrated this module is not installed or started automatically.
"""
import argparse
import ctypes
import os
from pathlib import Path
import diagnostics

RETURN = 'RETURN-THIS-VO-PATCH-EX-F01-P02.zip'


def wait_process(pid):
    if os.name != 'nt':
        raise OSError('Windows process handles are required')
    if type(pid) is not int or pid <= 0:
        raise ValueError('Invalid game process')
    from ctypes import wintypes
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.WaitForSingleObject.restype = wintypes.DWORD
    k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k.GetExitCodeProcess.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = k.OpenProcess(0x100000 | 0x1000, False, pid)  # wait + limited query; no input/memory access
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if k.WaitForSingleObject(handle, 0xffffffff) != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        code = wintypes.DWORD()
        if not k.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value
    finally:
        k.CloseHandle(handle)


def collect(root, pid, *, wait=wait_process):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('Game directory is missing')
    diagnostics.event(root, 'module_init', {'module': 5, 'stage': 0})
    try:
        code = wait(pid)
    except (OSError, ValueError):
        diagnostics.event(root, 'error', {'module': 5, 'code': 1, 'exit_known': False})
    else:
        diagnostics.event(root, 'shutdown', {'exit_known': True, 'exit_code': code})
    try:
        return diagnostics.export(root, game_directory=root, return_name=RETURN)
    except Exception:
        # Existing exporter retains raw logs and the prior stable archive.
        diagnostics.event(root, 'error', {'module': 5, 'code': 2, 'io_error': True})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('pid', type=int)
    args = parser.parse_args()
    collect(args.game, args.pid)
