"""Build game-data-free G03 UAT tools and sparse profile recipes locally."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent/'dual_display'))
import mode_profiles
from prepare import apply_recipe


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recipe(raw, data):
    base = raw + bytes(len(data)-len(raw)); writes = []; start = None
    for i, (left, right) in enumerate(zip(base, data)):
        if left != right and start is None:
            start = i
        if left == right and start is not None:
            writes.append([start, data[start:i].hex()]); start = None
    if start is not None:
        writes.append([start, data[start:].hex()])
    return {'base_sha256': hashlib.sha256(raw).hexdigest(), 'size': len(data), 'writes': writes}


def main():
    p = argparse.ArgumentParser()
    for name in ('retail', 'jpre', 'baseline', 'runtime', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--cc', required=True); p.add_argument('--windres', required=True)
    a = p.parse_args(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    recipes = {}; generation = []
    for edition in ('retail', 'jpre'):
        folder = getattr(a, edition); raw = (folder/'v_on.exe').read_bytes()
        entries = []
        for profile in mode_profiles.PROFILES:
            data, meta = mode_profiles.build(raw, profile)
            entry = {**meta, **recipe(raw, data)}
            assert apply_recipe(raw, entry) == data
            entries.append(entry); generation.append(meta)
        assets = {f.name.lower(): sha(f) for f in folder.iterdir() if f.is_file() and
                  (f.suffix.lower() in ('.bin', '.img', '.avi', '.hlp', '.cnt', '.ini') or f.name.lower() in ('cpuid32.dll', 'dpctrl.dll'))}
        recipes[edition] = {'base_sha256': hashlib.sha256(raw).hexdigest(), 'assets': assets, 'profiles': entries}
    (out/'recipes.json').write_text(json.dumps(recipes, separators=(',', ':')))
    (out/'support').mkdir()
    for name in ('ddraw.dll', 'ddraw.ini', 'DISPLAY-MODES.exe', 'vontanita.dll'):
        shutil.copy2(a.baseline/'game'/name, out/'support'/name)
    # Current Controller helper must be exactly the included validated helper.
    assert sha(out/'support/vontanita.dll') == sha(ROOT/'input/vontanita.dll')
    for name in ('diagnostics.py', 'discovery.py', 'prepare.py', 'session.py'):
        shutil.copy2(HERE/name, out/name)
    shutil.copy2(ROOT/'v-on-patcher.py', out/'v-on-patcher.py')
    # Keep the existing launch/mode/strict-failure implementation; delegate export
    # to shared diagnostics and bound legacy per-session backups in the coordinator.
    launch = (HERE.parent/'dual_display/LaunchModes.ps1').read_text()
    launch = launch.replace("try { & (Join-Path $root 'Collect-Modes.ps1') } finally {", "try { # Shared diagnostics collects after this launcher exits\n        } finally {")
    launch = launch.replace("($presentationLog + '.' + [Guid]::NewGuid().ToString('N') + '.previous')", "($presentationLog + '.1') -Force")
    launch = launch.replace('if ($launchFailed) { Read-Host "Diagnostics collected. Test failed or could not start; press Enter to close" | Out-Null }', 'if ($launchFailed) { exit 1 }')
    # Verify immutable distribution once in prepare.py; generated local profiles
    # are separately verified against the exact build record by this launcher.
    begin = launch.index('    $manifest ='); end = launch.index("    $game =", begin)
    launch = launch[:begin] + launch[end:]
    (out/'LaunchModes.ps1').write_text(launch)
    # Privacy variant of the existing external observer. Never log window text,
    # executable paths or monitor IDs. NORMAL drops periodic metadata; events
    # and final process status remain. No game API/call semantics are changed.
    observer = HERE.parent/'movie_observer'
    source = (observer/'observer.c').read_text()
    forced = 'SetEnvironmentVariableW(L"VO_DUAL_DISPLAY",L"1");'
    assert source.count(forced) == 1
    source = source.replace(forced, '')  # inherit the selector's exact mode

    begin = source.index('static void text('); end = source.index('static VoWindow read_window', begin)
    source = source[:begin] + 'static void text(const WCHAR *w){(void)w;}\n' + source[end:]
    needle = 'static void logline(const char *fmt,...){'
    replacement = '''static void logline(const char *fmt,...){
 char level[16]={0};GetEnvironmentVariableA("VO_EX_DIAGNOSTICS",level,sizeof level);
 if(strcmp(level,"DETAILED") && strcmp(level,"DEVELOPMENT") &&
    (!strncmp(fmt,"WINDOW",6)||!strncmp(fmt,"SAMPLE",6)||!strncmp(fmt,"ENUM_RESULT",11)||
     !strncmp(fmt,"POSSIBLE_COVER",14)||!strncmp(fmt,"\\\"",1)))return;
'''
    assert source.count(needle) == 1; source = source.replace(needle, replacement)
    # Continue observing all window changes, but never write partial describe tails.
    begin = source.index('static void describe('); body = source.index('{', begin)+1
    source = source[:body] + '''
 WCHAR vo_class[128]={0}; GetClassNameW(h,vo_class,128);
 if(!_wcsicmp(vo_class,L"MCIAVI")||!_wcsicmp(vo_class,L"AVIWnd32")||!_wcsicmp(vo_class,L"AVI Window")||!_wcsicmp(vo_class,L"MCIWndClass")||!_wcsicmp(vo_class,L"VideoRenderer")){
  if(vo_movie_seen!=h||vo_movie_visible!=w.visible){logline("movie_event event=1 visible=%d\\n",w.visible);vo_movie_seen=h;vo_movie_visible=w.visible;}
 }
 WCHAR vo_level[16]={0};GetEnvironmentVariableW(L"VO_EX_DIAGNOSTICS",vo_level,16);if(wcscmp(vo_level,L"DETAILED")&&wcscmp(vo_level,L"DEVELOPMENT"))return;
''' + source[body:]
    source = source.replace('static FILE *logfile;', 'static FILE *logfile; static HWND vo_movie_seen; static int vo_movie_visible;')

    source = source.replace('text(exe);logline("\\\"\\n");', 'text(exe);logline("\\n");')
    source = source.replace('logline("ENUM_RESULT sample=', 'if(vo_movie_seen&&!vo_contains(windows_,count,(uintptr_t)vo_movie_seen)&&ok&&!overflow){logline("movie_event event=3 visible=0\\n");vo_movie_seen=NULL;} logline("ENUM_RESULT sample=')
    build = out.parent/'observer-build'; build.mkdir(exist_ok=True)
    src = build/'observer.c'; src.write_text(source)
    obj = build/'res.o'
    subprocess.run([a.windres, '-I', str(observer), str(observer/'observer.rc'), str(obj)], check=True)
    subprocess.run([a.cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-municode', '-I'+str(observer), str(src), str(obj), '-luser32', '-ldwmapi', '-Wl,--no-insert-timestamp', '-o', str(out/'MOVIE-OBSERVER.exe')], check=True)
    runtime = out/'runtime'; runtime.mkdir()
    for name in ('python.exe', 'python3.dll', 'python312.dll', 'python312.zip', 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt'):
        shutil.copy2(a.runtime/name, runtime/name)
    shutil.copytree(a.runtime/'DLLs', runtime/'DLLs')
    (runtime/'python312._pth').write_text('python312.zip\n.\nDLLs\n..\n')
    for mode, label in (('single', 'START-SINGLE-DISPLAY'), ('versus', 'START-DUAL-VERSUS'), ('mirror', 'START-DUAL-MIRROR'), ('export', 'EXPORT-DIAGNOSTICS')):
        (out/(label+'.cmd')).write_bytes(('@echo off\r\nsetlocal\r\n"%~dp0runtime\\python.exe" "%~dp0session.py" '+mode+' %*\r\nif errorlevel 1 pause\r\n').encode())
    notices = out/'Licenses'; notices.mkdir(); shutil.copy2(ROOT/'LICENSE', notices/'Pairomaniac-MIT.txt')
    wrapper_license = a.baseline.parent/'wrapper-final/LICENSE'
    shutil.copy2(wrapper_license, notices/'cnc-ddraw-MIT.txt')
    (out/'experience-version.json').write_text(json.dumps({'experience': '0.1-dev', 'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'wrapper_sha256': sha(out/'support/ddraw.dll'), 'helper_sha256': sha(out/'support/vontanita.dll')}, indent=2))
    shutil.copy2(HERE/'UAT.txt', out/'READ-ME.txt')
    files = {str(f.relative_to(out)): sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
    (out/'package-manifest.json').write_text(json.dumps({'files': files}, indent=2))
    with zipfile.ZipFile(out.with_suffix('.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for f in sorted(out.rglob('*')):
            if f.is_file():
                archive.write(f, str(Path(out.name)/f.relative_to(out)))
    (out.parent/'generation.json').write_text(json.dumps(generation, indent=2))
    print(out.with_suffix('.zip'))


if __name__ == '__main__':
    main()
