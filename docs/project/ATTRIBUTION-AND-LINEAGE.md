# Attribution and lineage

VO PATCH EX is an independent community integration maintained by hyp36rmax.
It does not imply endorsement by SEGA, Pairomaniac or earlier patch authors.

| Layer | Ownership and status |
|---|---|
| Cyber Troopers Virtual-On PC | Original game and game assets belong to their respective owners, including SEGA. Original copyright and staff credits remain unchanged |
| Earlier VO_Patch lineage | Existing upstream attribution is retained; no new authorship or licensing claim is inferred from the historical name |
| V-On Patcher | Pairomaniac foundation, MIT copyright 2026 pairo; original source history, in-game version label, upstream repository link and artwork credits retained |
| Controllers Expansion | hyp36rmax controller work and measured hardware records, inherited intact from Controller-Expansion |
| Display Expansion | Private rendering/presentation work through F04B; automated validation is distinct from pending Windows acceptance |
| Unified Overlay Menu Expansion | Not included in Experience. Developed separately on Unified-Overlay-Menu-Expansion; the older Unified-Overlay branch is an ancestor, with its history retained |
| Native Experience component | Separate proprietary repository; not imported or relicensed |

## Historical G02 attribution implementation

Upstream exposes an About card in the patcher, a tile-font title-screen version
hook, and two ending-roll bitmap lines. The original game's SEGA About resource
is separate and remains unchanged; no new in-game dialog was introduced.

G02 adds `VO PATCH EX 0.1-dev` at title tile row 48, columns 43–78, above the existing
right-aligned upstream version on row 50. It uses the same CURSOR/PRINT functions,
state gates and patch-generation path. The About card leads with VO PATCH EX, hyp36rmax and the included Controller/Display
scope, followed by Pairomaniac and original artist SirRockEmSockEm.
`0.1-dev` denotes a local development identity, not a published release.

### Ending-roll addition: NEEDS VALIDATION

The original SEGA staff and both upstream lines are preserved byte-for-byte.
No VO PATCH EX/hyp36rmax ending line is claimed as implemented.

The current mechanism replaces five blank blocks with five entries totaling 20
rows: 7 blank  + 3 text  + 1 blank  + 2 text  + 7 blank. Additional entries cannot be
inserted without changing that block contract; composite bitmaps could use some
vertical space but also require additional resource storage and loader counts.
The existing bitmaps already append 121 tiles (15,488 bytes) and 210 map cells
(420 bytes), totaling 15,908 bytes. `_write_credits` documents 13,648 bytes of
headroom (594,072 minus 580,424), yet also gives a different 15,524-byte growth
figure. These inconsistent comments are not proof of an actual runtime overflow,
but they cannot establish safe remaining capacity for new tiles. A verified
Retail/JPRE loader-allocation bound is required before extending those files.
Existing tests confirm original pixels, roll length and byte-exact resource
restoration; they do not prove additional allocation capacity.

Missing either credit resource retains upstream's skip-all-attribution behavior.
Resource backup, Restore Original and original About resources are unchanged.
No modified game asset is included in Git or a public package.

## Historical G02 generated-image changes

Only the TITLEVER assembly blob changes; every other assembly/table blob and all
ending bitmaps remain exact. The blob grows from 109 to 155 bytes. Annex alignment
therefore changes subsequent symbol addresses by 48 bytes; generated relocation
and hook operands follow the existing linker. Historical image tests rebuild
reference recipes with exactly the hash-pinned new TITLEVER blob, retaining
whole-image equality assertions. Independent x86 tests check both title strings,
coordinates, state gates, stack and displaced load for Retail/JPRE.

The all-on Retail/JPRE hashes are updated only for this reviewed attribution
change. OEM and original Japanese images lack new pristine validation and are
not newly certified by G02. Display state signatures and physical behavior still
require the integration acceptance matrix.

## License boundaries and notices

`LICENSE` remains Pairomaniac's MIT notice. Preserve its copyright and permission
text, existing VO_Patch lineage and SirRockEmSockEm artwork attribution. Pinned
cnc-ddraw is MIT, copyright 2025 FunkyFr3sh; retain its notice with distributed
wrapper copies. Preserve Python/runtime and toolchain notices where distributed.
No blanket grant is made for SEGA assets or the separate native Experience code.

Public packages must contain only reviewed patcher/helper/runtime files and
required notices, applied to user-provided game data. Historical private UAT archives containing
game assets are excluded. Current installable UAT archives contain no game assets. Reachable-history scans supplement, rather than
replace, artifact review; `.gitignore` cannot remove existing history.

## Branch authorities and upstream updates

Experience starts at reviewed F04B `0737ebf99bf3f1bdfe672eab83e47d0b6261a8a6`,
which already contains Controller HEAD `73639a4d369dba02c97842906828f588ee4602f5`.
No duplicate merge or cherry-pick is needed. `Controllers-Expansion` preserves
that controller authority while singular `Controller-Expansion` remains for
existing workflow/public links. Display-Expansion remains independent. Unified-Overlay-Menu-Expansion preserves the older Unified-Overlay ancestry.
Its current implementation and historical checkpoints are indexed in
[the overlay documentation](../overlay/README.md); neither branch is merged into Experience.

Local `upstream/pairomaniac` tracks remote `upstream/main` at
`441921828611fa0d159525939c50d6ad4ab00d43`. Keep it free of project commits.
For a future pulse: inspect upstream changes, record old/new SHAs, review license
and overlapping files, integrate through a normal reviewed merge on the relevant
module authority, run complete tests and Windows acceptance, then merge the
validated descendant into Experience. Never force-push or rewrite upstream
history. No new upstream changes are automatically merged.

At G02, Experience was the intended future default/release authority. Remote
settings, CI triggers and public branch names were unchanged by that checkpoint.

## Patcher branding

The project URL is https://github.com/hyp36rmax/VO_PATCH_EX. The window title is
`V-On Patcher EX`; its executable remains `v-on-patcher.exe`. The derivative
header preserves the original logo and adds the approved EX source beneath PATCHER.
See [asset provenance](../../assets/BRANDING.md). The original icon, ending-roll
resources, title-screen attribution and upstream license remain unchanged.

## G04 repository preparation

Experience includes B01-F02 through adf46270ce1b7922f5bca3677387a801469caa2c.
The G02 byte-size discussion above records that attribution change, not every later
Experience modification. Controller-Expansion remains the public controller authority;
Controllers-Expansion is an existing local alias. The canonical repository is
hyp36rmax/VO_PATCH_EX; its remote default was Controller-Expansion during G04-P02. Experience is now
the remote default; the Controllers + Display Expansion release remains staged.
