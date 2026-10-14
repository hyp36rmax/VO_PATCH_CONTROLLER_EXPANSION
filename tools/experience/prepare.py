"""Apply hash-checked sparse recipes to a user-owned pristine installation.
No original game files are shipped; installation source is never written.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apply_recipe(raw, recipe):
    if digest(raw) != recipe['base_sha256']:
        raise ValueError('Pristine game revision does not match')
    if not len(raw) <= recipe['size'] <= 32*1024*1024:
        raise ValueError('Invalid generated image size')
    output = bytearray(raw) + bytearray(recipe['size']-len(raw))
    for offset, hexbytes in recipe['writes']:
        block = bytes.fromhex(hexbytes)
        if not 0 <= offset <= len(output) or offset+len(block) > len(output):
            raise ValueError('Invalid patch bounds')
        output[offset:offset+len(block)] = block
    if digest(output) != recipe['sha256']:
        raise ValueError('Generated profile verification failed')
    return bytes(output)


def verify(root):
    root = Path(root)
    for name, expected in json.loads((root/'package-manifest.json').read_text())['files'].items():
        p = (root/name).resolve()
        if not p.is_relative_to(root.resolve()) or digest(p.read_bytes()) != expected:
            raise ValueError('Package integrity failed')


def choose_folder():
    command = "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description='Select your own pristine Retail or Japanese rerelease game folder'; if($f.ShowDialog() -eq 'OK'){[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Console]::Write($f.SelectedPath)}"
    selected = subprocess.check_output(['powershell.exe', '-NoProfile', '-STA', '-Command', command]).decode('utf-8-sig').strip()
    if not selected:
        raise ValueError('Installation selection cancelled')
    return Path(selected)


def prepare(root, source=None):
    root = Path(root).resolve()
    verify(root)
    if (root/'prepared.json').exists():
        record = json.loads((root/'prepared.json').read_text())
        for item in record['profiles']:
            if digest((root/'profiles'/f"{item['profile']}.exe").read_bytes()) != item['sha256']:
                raise ValueError('Prepared profile integrity failed')
        for name in ('ddraw.dll', 'ddraw.ini', 'DISPLAY-MODES.exe', 'vontanita.dll'):
            if digest((root/'game'/name).read_bytes()) != digest((root/'support'/name).read_bytes()):
                raise ValueError('Prepared helper integrity failed')
        return record
    source = (Path(source) if source else choose_folder()).resolve()
    if source.is_relative_to(root):
        raise ValueError('Choose the original installation outside this package')
    recipes = json.loads((root/'recipes.json').read_text())
    original = next((p for p in source.iterdir() if p.name.lower() == 'v_on.exe'), None)
    if original is None:
        raise ValueError('No v_on.exe in selected folder')
    raw = original.read_bytes()
    edition = next((key for key, val in recipes.items() if val['base_sha256'] == digest(raw)), None)
    if not edition:
        raise ValueError('A pristine Retail or JPRE executable is required')
    recipe = recipes[edition]
    files = {p.name.lower(): p for p in source.iterdir() if p.is_file()}
    # Hash-check all required assets before creating the working copy.
    for name, sha in recipe['assets'].items():
        if name not in files or digest(files[name].read_bytes()) != sha:
            raise ValueError('Missing or modified original game resources; use a pristine installation')
    staging = root/'preparing'
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    for name in recipe['assets']:
        shutil.copyfile(files[name], staging/name)
    (staging/'v_on.exe').write_bytes(raw)
    spec = importlib.util.spec_from_file_location('vo_patcher', root/'v-on-patcher.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    patch = module.Patcher()
    if not patch.load(str(staging/'v_on.exe'))[1]:
        raise ValueError('Game identification failed')
    log = []
    if not patch._write_credits(log):
        raise ValueError('Existing upstream credit resources could not be prepared')
    patch._write_banner(log)
    if not (staging/(patch.build.art[0]+'.bak')).is_file():
        raise ValueError('Banner resource preparation failed')
    for name in ('ddraw.dll', 'ddraw.ini', 'DISPLAY-MODES.exe', 'vontanita.dll'):
        shutil.copyfile(root/'support'/name, staging/name)
    profiles = root/'profiles'; profiles.mkdir(exist_ok=True)
    for entry in recipe['profiles']:
        (profiles/(entry['profile']+'.exe')).write_bytes(apply_recipe(raw, entry))
    # v_on.exe is selected afresh by the existing display launcher.
    (staging/'v_on.exe').rename(staging/'v_on.exe.bak')
    game = root/'game'
    if game.exists():
        raise ValueError('Unrecognized partial working copy; retain it and extract a fresh package')
    os.replace(staging, game)
    record = {'edition': edition, 'profiles': [{k: v for k, v in entry.items() if k != 'writes'} for entry in recipe['profiles']]}
    (root/'build-record.json').write_text(json.dumps(record))
    (root/'prepared.json').write_text(json.dumps(record))
    return record
