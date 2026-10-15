# UX01-R04 — Approved Unified Overlay layouts and editors

Status: **APPROVED & FROZEN**. Recorded from the owner's complete specification
provided on 2026-10-15. This document specifies the interface; it does not claim
implementation or Windows acceptance. Original F5, F6, F7 and F11 behavior,
configuration formats, controller ownership and installation remain authoritative.

## Main menu and navigation

Configuration: Controllers, Display, Graphics, Game Settings, Extras.
Separate session actions: Resume, Exit to Title, Quit Game. Resume is initially
selected. Both destructive session actions require fresh confirmation with Cancel
initially selected; Exit to Title is hidden at title and retains network restrictions.
Resume preserves the original pause state. Quit uses original shutdown.

ESC opens during eligible title, attract and gameplay, including paused gameplay;
video playback is excluded. ESC also goes Back or closes. Keyboard arrows and
Enter, mouse hover/click/scroll, P1 gamepad directions and twin-stick left lever
navigate. Existing menu accept confirms. Every submenu has selectable Back.
Controller Start retains original game functionality, ownership selection and
Pause/Resume. Raphnet's separate Pause and Start retain their established roles.
Keyboard and mouse remain recovery methods. Original F-keys remain operational
until full parity and physical acceptance; this milestone does not disable them.

## Controllers

Both players appear on one page, each with Profile, selectable Controller
assignment, and informational connection Status. Use actual session ownership;
do not infer connection from a profile label or create a second discovery system.

| Profile | Editor | Stick deadzone |
|---|---|---|
| Gamepad (XInput) | Named gameplay actions | Yes |
| Twin-Stick (XInput) | Fixed | Only when the actual mapping consumes axis thresholds |
| Twin-Stick (Custom) | Twelve-action editor | Only when the actual mapping consumes axis thresholds |
| Twin-Stick (Tanita) | Fixed | Hidden |
| Twin-Stick (HORI EX) | Fixed | Only when the actual mapping consumes axis thresholds |
| Twin-Stick (Raphnet DC) | Fixed | Hidden |
| Twin-Stick (Raphnet Saturn) | Fixed | Hidden |
| Keyboard (Simple) | Named keyboard actions | Hidden |
| Keyboard (Real) | Original two-lever editor | Hidden |

Deadzone presentation moves into Controllers in the overlay, with independent
player preferences and the existing 40% default. Original F11 remains intact.
Configure Buttons/Keys appears only for supported editors. Editors provide
Restore Defaults, Save, Cancel and Back. Save commits pending edits; Cancel
discards them; Back prompts about unsaved changes. Reuse existing capture,
reserved-input validation, release gates, timeout and cancellation.

| Gamepad / Simple action | Gamepad reference assignment |
|---|---|
| Move Forward / Backward / Left / Right | Left Stick Up / Down / Left / Right |
| Turn Left / Right | Right Stick Left / Right |
| Left Weapon / Right Weapon / Center Weapon | LT / RB / RT |
| Dash / Jump / Guard | LB / A / X |

Simple uses the same action names with original keyboard assignments.

| Two-lever action | Custom reference | Real keyboard P1 reference |
|---|---|---|
| Left Up / Down / Left / Right | D-pad Up / Down / Left / Right | 2 / W / Q / E |
| Left Trigger / Dash | LT / LB | Z / X |
| Right Up / Down / Left / Right | Y / A / X / B | R / F / D / G |
| Right Trigger / Dash | RT / RB | C / X |

The Assign Input view identifies player, action and current assignment, prompts
for the desired input, and provides Cancel. Reference layouts are not permission
to replace saved mappings or implement another binding engine.

## Display and Graphics

| Page | Controls |
|---|---|
| Display | Display Mode, Primary Display, conditional Secondary Display, Game Aspect Ratio, Advanced Settings, Apply Changes, Cancel, Back |
| Advanced Display | Local VS Split: Vertical / Horizontal; Back |
| Graphics | Resolution: 720p / 1080p; Sky; Field Graphic; Motion; Advanced Settings; Apply Changes; Cancel; Back |
| Advanced Graphics | Three original texture controls; Back |

Display modes: Single Display, Dual Display Versus, Dual Display Mirror.
Secondary appears only for dual modes. Aspects: 4:3, 16:9, 21:9, 32:9.
Preserve monitor discovery, validation, fallback, saved split preference and
next-launch application from F5. Explain restart requirements. Do not change
Windows desktop resolution or expose framebuffer dimensions. Complete Mirror
mirrors the complete presentation. Original Local VS behavior remains intact.

Verified texture labels are **Machine(1P)**, **Machine(2P)** and **Effects**.
Local VS Split appears only in Advanced Display. Motion remains on Graphics.
Original supported values and dependencies win over illustrative layout values.

## Game Settings

Preserve original categories and their category-specific Restore Defaults,
Save, Cancel and Back. Use original supported values and persistence.

| Category | Controls |
|---|---|
| 1P Mode | Play Time: Stage 1–5, Penalty Stage, Stage 6–8, Last Stage; Match Count: Stage 1–5, Penalty Stage, Stage 6–8; Difficulty |
| 2P VS | Play Time; Match Count |
| General | View Replay; View Posing; Display Ranking; Quick VR Select 1P; Quick VR Select 2P and Network VS; Demo Movie |
| Appendix | Machine Color Select; Enemy Color Random; Color Format |

Captured examples (including 2P Match Count Twice) are not necessarily factory
defaults. Hidden native controls do not become new overlay features; their
underlying state must survive edits to supported controls.

## Extras and diagnostics

Extras contains Game Utilities (Credits, Scorekeeping), Debug Settings,
Diagnostics and Back. Debug contains No Shot, SE, CD, Kill Player 1, Kill Player 2
and Back. Preserve original functions and confirm disruptive actions.

Diagnostics player-facing description:

> Diagnostics help identify issues with controllers, displays, game startup,
> and configuration. Logging is disabled by default. Enable it when
> troubleshooting an issue. All logs are stored locally. Nothing is uploaded
> automatically.

| Logging level | Description |
|---|---|
| Off | Diagnostics disabled; default |
| Normal | Startup information, warnings, errors |
| Detailed | Controller, display, configuration events |
| Development | Additional technical troubleshooting information |

Provide Logging Level, explicit Export Diagnostics and Back. Enabling requires
restart. Off stops new collection; retained logs remain available. Reuse the
existing consent, collection and export implementation.

## Configuration and acceptance boundary

All sections above are frozen. Reuse existing configuration authorities and
save/cancel boundaries, with no silently committed drafts or duplicate files.
The same authorities will remain usable by the original F-key menus. Physical
Windows acceptance, including active/paused presentation, follows integration
and automated validation; approval of this specification is not that acceptance.
