"""Distribution integrity and game-asset exclusion, no Windows execution claim."""
from pathlib import Path
import hashlib,json,sys,zipfile
root=Path(sys.argv[1]).resolve();internal=root/'_internal';ex=internal/'experience'
manifest=json.loads((root/'PACKAGE-SHA256.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
allowed={'v-on-patcher.exe','python.exe','pythonw.exe'}
for path in root.rglob('*'):
 if not path.is_file():continue
 assert path.name.lower() not in ('v_on.exe','von.bin','von.cue'),path
 assert path.suffix.lower() not in ('.iso','.avi','.wav','.img'),path
 if path.suffix.lower()=='.exe':assert path.name in allowed,path
assert (root/'v-on-patcher.exe').read_bytes()[:2]==b'MZ'
assert (ex/'payload/vodisplay.dll').read_bytes()[:2]==b'MZ'
index=json.loads((ex/'catalog/catalog.json').read_text())
assert len(index['entries'])==512
with zipfile.ZipFile(ex/'catalog/recipes.zip') as z:
 assert z.testzip() is None and set(z.namelist())==set(index['entries'])
 for name,entry in index['entries'].items():
  data=z.read(name);assert hashlib.sha256(data).hexdigest()==entry['sha256']
  recipe=json.loads(data);assert recipe['final']==entry['final']
  # Recipes are sparse changes requiring a verified original, never full files.
  assert sum(len(bytes.fromhex(x[1])) for x in recipe['writes'])<recipe['size']
for name in ['normal_lifecycle.py','diagnostics.py','discovery.py','movie_geometry.py','pythonw.exe','python312.dll','python312.zip']:
 assert (ex/'payload/experience-runtime'/name).is_file()
print('PASS manifest hashes, 512 sparse option recipes, upstream Windows launcher, runtime completeness, game-asset exclusion')
