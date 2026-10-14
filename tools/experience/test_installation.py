#!/usr/bin/env python3
"""Exercise normal patcher Apply/Restore on disposable Retail/JPRE copies.

Pass pristine game directories; does not run the Windows GUI or Display modes.
"""
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from selftest import load_patcher


def verify(source):
    vp = load_patcher()
    with tempfile.TemporaryDirectory() as td:
        game = Path(td) / 'game'
        shutil.copytree(source, game)
        originals = {p.relative_to(game): hashlib.sha256(p.read_bytes()).digest()
                     for p in game.rglob('*') if p.is_file()}
        exe = game / 'v_on.exe'
        patcher = vp.Patcher()
        assert patcher.load(str(exe))[1]
        wanted = vp.default_state()
        wanted.update({key: True for key in vp.ESSENTIAL})
        wanted['hires'] = (1920, 1080)  # Existing GUI Apply conversion.
        for cycle in range(2):
            ok, log = patcher.apply(wanted)
            assert ok, log
            assert not patcher.load(str(exe))[1], 'accepted patched executable'
            assert patcher.can_restore()
            before = exe.read_bytes()
            ok, log = patcher.apply(wanted)
            assert not ok, 'patch-over accepted'
            assert exe.read_bytes() == before
            patcher.restore()
            for name, digest in originals.items():
                assert hashlib.sha256((game / name).read_bytes()).digest() == digest, name
            patcher.restore()
            assert patcher.load(str(exe))[1]
        damaged = bytearray(exe.read_bytes())
        damaged[-1] ^= 1
        exe.write_bytes(damaged)
        assert not patcher.load(str(exe))[1], 'accepted modified executable'
    print(f'PASS {source.name}: default 1920 Apply, patch-over refusal, exact restore, '
          'repeat restore/reapply, modified-file refusal')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for source in map(Path, sys.argv[1:]):
        verify(source)
