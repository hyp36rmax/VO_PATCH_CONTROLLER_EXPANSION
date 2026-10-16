# Experience prerelease publication

Experience releases promote an approved Windows ZIP. The application commit and
publication-workflow commit are separate identities. The release tag points to the
application commit; publication never rebuilds, stamps, signs or repackages the ZIP.

## Authorization

The sole authorized version is `v0.18.0-experience.1`. Its
[authorization record](../../.github/release-authorizations/v0.18.0-experience.1.json)
binds the application commit, CI run and attempt, artifact ID, ZIP checksum,
release-note checksum and maintainer-confirmed physical Windows acceptance.
Acceptance does not extend the hardware coverage documented in the release.

Run **Publish approved Experience prerelease** manually from the current
`Experience` default branch. It accepts no version, commit, artifact or authorization
inputs. Pull requests and other branches cannot authorize this workflow. The trusted
checkout must match remote Experience and descend from the approved application
commit with only the listed publication-infrastructure and release-note changes.
Another release requires a reviewed record and implementation change; there is no
wildcard approval.

The read-only job runs rejection tests and verifies live GitHub CI metadata, all
three required jobs and the original artifact. The publication job repeats the
guard, creates the exact source tag and a draft prerelease, uploads the ZIP,
downloads the draft asset to verify its checksum, checks the tag again, and
publishes with `prerelease=true` and `make_latest=false`.

Only the publication job has `contents: write`; both jobs have `actions: read`.
Authentication uses the ephemeral Actions token, without stored Git credentials,
a PAT or signing secrets. Redirected downloads do not receive that token.
Repository protections remain unchanged. Denied writes fail the workflow.
Existing tags/releases are never rewritten. A partial failure can leave a source
tag or draft for review; rerunning does not silently replace it.

## Original tag workflow

The application commit unconditionally rejects Experience tags in `build.yml`.
Its native/package jobs also select integrated packaging by branch name. Removing
that rejection would neither preserve the ZIP nor select proper tag packaging.
The legacy path stays closed. The dedicated promotion workflow provides the
explicit guarded authorization path; manually pushed Experience tags still fail.

The Actions token creates the tag after authorization. GitHub does not trigger a
new push workflow from this token, avoiding a legacy tag rebuild. The
infrastructure-only commit uses `[skip ci]` to avoid the ordinary push build;
the manual publication workflow still runs guard tests and checks the successful
exact-source Windows build.

## Verification

```sh
python3 tools/release/test_experience.py
```

Hosted verification checks the original artifact and ZIP CRC. Its cryptographic
identity preserves the prior full-manifest, Retail/JPRE, controller, display,
license, privacy and overlay-exclusion validation. After publication, independently
inspect the public release and compare the downloaded ZIP's SHA-256.
