# Diagnostics and privacy

**Diagnostics are disabled by default.** Missing or invalid preferences also select
Off. Patcher installation feedback in the LOG panel is separate and remains active.

Open **F11 Extras**, select a Diagnostics level, and restart Virtual-On to start a
new diagnostic session. The selection is saved immediately in the existing
`player-displays.ini` under `[Diagnostics]`, `Level`; no repatching or manual editing
is needed. F11 is provided by the existing **Disable menu bar (Extras menu on F11)**
patch option. Keep that option enabled to use these controls. Upstream's network
match restriction on F-key dialogs remains unchanged.

| Level | Collection |
|---|---|
| Off | No routine events, collector process, observers, sampling, new logs or automatic export |
| Normal | Startup, shutdown, errors and recovery evidence |
| Detailed | Normal plus numeric hardware discovery, saved controller assignment changes, display selection/configuration and presentation summaries |
| Development | Detailed plus bounded movie-window geometry and technical troubleshooting evidence |

Selecting **Off** blocks new events immediately; an existing collector releases its
process/window observation resources at its next wakeup (within its 500 ms wait
interval). It does not restart when logging is re-enabled during that same game
session; restart as the dialog requests. Enabled levels can be changed during an
active diagnostic session. The preference persists across launches.

## Local records and export

Records are stored in the installed game's `diagnostics` folder. Development may
also write `diagnostics/display-save.log`; Detailed/Development presentation
summaries use `D04-P02B-presentation.log` beside the game. Writers are bounded and
stop appending when their limits are reached. Existing records are retained.

Select **Export Diagnostics...** in F11 to create a local ZIP and select it in
Explorer. The existing `EXPORT-DIAGNOSTICS.cmd` is another explicit export entry
point. Neither enables collection. When no records exist, the exporter explains
that there is nothing to export. Compression failure preserves raw records and
any previous export. Closing the game no longer exports automatically.

Exports contain version/game revision, allowlisted numeric configuration, events,
warning/error/recovery summaries and numeric projections of relevant existing logs.
They exclude game files, patched executables, credentials, monitor serials, user
paths and free-form device identifiers. Local save traces are not copied into the
archive. No screenshots, audio or raw controller inputs are collected. There are
no automatic uploads, network telemetry or background reports to the maintainer.

To remove old records, close Virtual-On, delete the `diagnostics` folder and any
`D04-P02B-presentation.log`, `VO-PATCH-EX-Diagnostics-*.zip` or
`RETURN-THIS-VO-PATCH-EX-*.zip` files in its installation folder. This does not
change the saved preference. Disable diagnostics first if you do not want new
records on the next launch. Automatic log deletion is not performed.

The export's retained return name is `RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip`.
The component identifier does not imply that a Windows acceptance pass occurred.

## Validation boundary

Automated tests cover default-Off behavior, level filtering, saved preferences,
retention, numeric sanitization, explicit export/failure handling and Retail/JPRE
F11 callback forwarding. Windows dialog navigation, physical display behavior and
GUI scaling require acceptance on Windows. Historical G03 preparation tools are
not included in the normal installable package or used as its launch path.
