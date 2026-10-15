#!/usr/bin/env python3
"""B01 artwork, UI content and unchanged game/installation contract checks."""
import ast
import base64
import hashlib
import io
from pathlib import Path
import runpy
import subprocess
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = '1ec5140c11a12dfe22e64e721bffae85a91b1b6c'
def original(name):
    return subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)
source = (ROOT / 'v-on-patcher.py').read_text()
now = runpy.run_path(str(ROOT / 'v-on-patcher.py'))
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / 'v-on-patcher.py'; p.write_bytes(original('v-on-patcher.py'))
    before = runpy.run_path(str(p))
for key in ('BLOBS', 'CREDITS', 'LABEL', 'REPO_URL', 'LOGO_CREDIT', 'ICON_PNG',
            'ESSENTIAL', 'EXTRA', 'ABOUT'):
    assert now[key] == before[key], key
assert now['BY_KEY']['padxinput'] == before['BY_KEY']['padxinput']
assert now['BY_KEY']['hires'][1].startswith(before['BY_KEY']['hires'][1] + '\n\n')
assert now['TITLE'] == 'V-On Patcher EX'
assert now['EX_VERSION'] == '0.1-dev'
assert now['PROJECT_URL'] == 'https://github.com/hyp36rmax/VO_PATCH_EX'
for name in ('assets/VONPatcherLogo1.png', 'assets/VONPatcherIcon.png', 'assets/icon.ico'):
    assert (ROOT / name).read_bytes() == original(name), name
# Restrict function changes to About, the information popup and no installation code.
def funcs(text):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))
            if isinstance(n, ast.FunctionDef) and n.name in ('apply', 'restore', 'load', 'stamp_version')}
assert funcs(source) == funcs(original('v-on-patcher.py').decode())
base = Image.open(ROOT / 'assets/VONPatcherLogo1.png').convert('RGBA')
ex = Image.open(ROOT / 'assets/EX-approved.png').convert('RGBA')
assert hashlib.sha256((ROOT / 'assets/EX-approved.png').read_bytes()).hexdigest() == '0fce2fa24e638197873819efe3ca22112c8854fa51814ea804357053ad678cfb'
assert ex.getchannel('A').getextrema() == (0, 255)
ex = ex.crop(ex.getchannel('A').getbbox())
ex = ex.resize((650, round(ex.height * 650 / ex.width)), Image.Resampling.LANCZOS)
expected = Image.new('RGBA', (2715, 716)); expected.alpha_composite(base); expected.alpha_composite(ex, (2020, 480))
actual = Image.open(ROOT / 'assets/VOPatchEXLogo.png').convert('RGBA')
assert actual.tobytes() == expected.tobytes()
# The added logo must not cover any original nontransparent artwork.
for y in range(ex.height):
    for x in range(ex.width):
        if y + 480 < base.height and ex.getpixel((x, y))[3]:
            assert not base.getpixel((x + 2020, y + 480))[3]
embedded = Image.open(io.BytesIO(base64.b64decode(now['LOGO_PNG']))).convert('RGBA')
assert embedded.size == (728, 192)
assert embedded.getchannel('A').getextrema() == (0, 255)
about = source[source.index('        def _about_body'):source.index('        def _log_body')]
assert about.index('VO PATCH EX') < about.index('Based on:') < about.index('Original logo by:')
assert 'self._patch_body(parent, ABOUT, None)' in about and 'LOGO_PNG' not in about
assert 'wraplength=380' not in about
assert 'height=min(height, limit)' in source and 'scrollregion=' in source
print('PASS exact source provenance, original artwork/icon, composition, alpha, embedded size, title/About, appended hires, unchanged XInput, blobs and installation functions')
print('NEEDS VALIDATION: physical Windows layout, DPI, popup scrolling and clickable links')
