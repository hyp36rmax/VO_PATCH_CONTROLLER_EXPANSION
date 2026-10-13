#!/usr/bin/env python3
"""Prepare a private diagnostic UAT copy; preserve the supplied normal package."""
import argparse
import json
from pathlib import Path
import shutil

import selftest
from visualprobe import static_report


def prepare(source, destination, diagnostic=False):
    if not diagnostic:
        raise ValueError('probe is disabled; explicit diagnostic opt-in required')
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or source in destination.parents or destination.exists():
        raise ValueError('use a new independent destination')
    collector=(source/'Collect-Results.ps1').read_text()
    anchor="    $files = @('Provenance\\build.json', 'build-record.json', 'FEEDBACK.txt')"
    if collector.count(anchor)!=1:
        raise ValueError('unrecognized UAT collector; review before integration')
    vp=selftest.load_patcher()
    reports={f'{edition}/{width}/VISUAL-INTEGRITY.json':static_report(vp,width,1080)
             for edition in ('JPRE','RETAIL') for width in (1920,2560)}
    shutil.copytree(source,destination)
    for name,report in reports.items():
        (destination/name).write_text(json.dumps(report,indent=2)+'\n')
    extra='\n    # Static geometry evidence only; no live clipping capture.\n'
    extra+='    $files += @('+', '.join("'"+n.replace('/','\\')+"'" for n in reports)+')'
    (destination/'Collect-Results.ps1').write_text(collector.replace(anchor,anchor+extra))
    # The original manifest no longer describes the diagnostic copy. Rebuild it.
    import hashlib
    hashes={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in destination.rglob('*') if p.is_file() and p.name!='package-manifest.json'}
    (destination/'package-manifest.json').write_text(json.dumps({
        'diagnostic':True,'runtime_renderer_observation':'NOT IMPLEMENTED',
        'files':hashes},indent=2)+'\n')
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    p.add_argument('--diagnostic',action='store_true')
    a=p.parse_args();prepare(a.source,a.destination,a.diagnostic)
