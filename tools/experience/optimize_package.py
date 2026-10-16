"""Losslessly compress patch recipes; preserve every runtime file and recipe byte."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


def compress_recipes(catalog):
    catalog = Path(catalog)
    index = json.loads((catalog / 'catalog.json').read_text())['entries']
    source = catalog / 'recipes.zip'
    with tempfile.TemporaryDirectory(dir=catalog) as temp:
        target = Path(temp) / 'recipes.zip'
        with zipfile.ZipFile(source) as old, zipfile.ZipFile(target, 'w') as new:
            if len(old.namelist()) != len(index) or set(old.namelist()) != set(index):
                raise ValueError('Recipe archive membership differs from catalog')
            for name in sorted(index):
                data = old.read(name)
                if hashlib.sha256(data).hexdigest() != index[name]['sha256']:
                    raise ValueError('Recipe checksum mismatch: ' + name)
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_LZMA
                new.writestr(info, data)
        with zipfile.ZipFile(target) as new:
            for name in index:
                if hashlib.sha256(new.read(name)).hexdigest() != index[name]['sha256']:
                    raise ValueError('Recompressed recipe mismatch: ' + name)
        target.replace(source)


def optimize(source, output):
    source, output = Path(source), Path(output)
    manifest = json.loads((source / 'PACKAGE-SHA256.json').read_text())
    actual = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    if actual != set(manifest) | {'PACKAGE-SHA256.json'}:
        raise ValueError('Source package manifest coverage mismatch')
    for name, expected in manifest.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or (source / path).is_symlink():
            raise ValueError('Unsafe package path')
        if hashlib.sha256((source / path).read_bytes()).hexdigest() != expected:
            raise ValueError('Source package checksum mismatch: ' + name)
    shutil.copytree(source, output)
    compress_recipes(output / '_internal/experience/catalog')
    name = '_internal/experience/catalog/recipes.zip'
    manifest[name] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    (output / 'PACKAGE-SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    optimize(args.source, args.output)
