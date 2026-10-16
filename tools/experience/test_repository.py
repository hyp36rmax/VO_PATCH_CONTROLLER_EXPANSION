"""Preserve the frozen controller record and the prepared CI package contract."""
from pathlib import Path
import re
import subprocess
import tempfile
import json
import lzma
import sys
import catalog_input

root = Path(__file__).resolve().parents[2]
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

before = git('show', '73639a4d369dba02c97842906828f588ee4602f5:README.md').decode()
after = (root / 'README.md').read_text()
# Distribution and identity edits are outside the frozen controller record.
start = '## Controller Profiles'
assert start in before and start in after
assert before[before.index(start):before.index('## Project Status')] == after[after.index(start):after.index('## Project Status')]
assert not git('diff', '73639a4d369dba02c97842906828f588ee4602f5', '--', 'docs/controllers')
assert not git('diff', '441921828611fa0d159525939c50d6ad4ab00d43', '--', 'LICENSE', 'assets/VONPatcherLogo1.png', 'assets/VONPatcherIcon.png', 'assets/icon.ico')
for path in [root/'README.md', *(root/'docs').rglob('*.md')]:
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        target = link.split('#')[0]
        if target and '://' not in target and not target.startswith(('mailto:', '<')):
            assert (path.parent/target).exists(), (path, link)
workflow = (root/'.github/workflows/build.yml').read_text()
for value in ('Controller-Expansion, Experience', 'tools/experience/package_normal.py',
              'tools/experience/test_normal_package.py', 'Experience publication guard',
              'tools/experience/catalog_input.py', 'PYTHONUTF8', '--prerelease'):
    assert value in workflow, value
# Catalog hashes cover exact bytes, including headers on Windows checkouts.
locked_sources = catalog_input.sources()
for name in locked_sources:
    attribute = git('check-attr', 'eol', '--', name).decode().strip()
    assert attribute == name + ': eol: lf', (name, attribute)

source = root/'tools/experience/ci/catalog.json.xz'
with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    catalog_input.unpack(source, folder/'valid')
    data = json.loads(lzma.decompress(source.read_bytes()))
    data['sources']['v-on-patcher.py'] = 'invalid'
    bad = folder/'bad.xz';bad.write_bytes(lzma.compress(json.dumps(data).encode()))
    try:
        catalog_input.unpack(bad, folder/'rejected')
    except AssertionError:
        pass
    else:
        sys.exit('FAIL source-drift catalog accepted')
print('PASS frozen controller content, hardware records, original artwork/license, local links, CI contract, catalog drift rejection')
