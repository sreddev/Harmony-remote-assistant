# Evaluation: harmony-explorations' builder for the Harmony 600

Can [harmony-explorations](https://github.com/dannybloe/harmony-explorations) build a new configuration
for this project's Harmony 600, so devices and activities can be changed without Logitech? Evaluated
on 11 November 2026 by reading the repository at commit `69c9804` (10 November 2026). **No code from it
was run**: installing its dependencies needs an explicit permission that was not given (section 6).

## Verdict

**Yes for the core, not yet as a finished tool.** The builder takes a recipe (a JSON list of devices
and activities), builds a whole Harmony 600 configuration from nothing, with no Logitech file as a
starting point, and the project has written such a build to a real 600 and run it. What is missing is
the convenience around it: turning an existing configuration back into an editable recipe, adding
devices through a search, and a safe procedure for writing to a remote the project has never seen.
Its application, FreeHarmony, can only list a configuration's contents today.

## 1. What the project is

| | |
|---|---|
| Repository | `dannybloe/harmony-explorations`, MIT licence |
| Language | TypeScript on Node 24 or later (runs `.ts` directly), pnpm workspace |
| Purpose | the research and libraries behind FreeHarmony |
| Application | [FreeHarmony](https://github.com/dannybloe/FreeHarmony), GPL-3.0, Electron, **no release**; its one script prints a configuration's devices and activities |
| Remotes on its bench | One, 300, 350, 515, 525, 600, 650, 700, 885, Touch |

The Harmony 600, 650 and 700 are one family to it (architecture 14). Its status page reports every byte
of a 600 configuration accounted for, and every device and activity name in its corpus read.

## 2. The parts that matter for the 600

| Package | Does |
|---|---|
| `packages/codec` | reads, composes and builds configurations; `bin/build-recipe.ts` builds one from a recipe |
| `packages/usb` | the HID transport and Harmony command protocol |
| `packages/base` | model table, key codes, checksums |
| `packages/keyreader` | a read-only WebHID page showing which key is pressed |

`build-recipe.ts` usage, as its header gives it (it opens no remote):

```sh
node packages/codec/bin/build-recipe.ts --setup <recipe.json> --out <file> \
     --built-at YYYY-MM-DDTHH:MM:SS [--archive <checkout> | --no-archive]
```

## 3. The recipe

Documented in `docs/recipe.md`. A recipe names the model, its devices in order and its activities:

- a device is a name plus a **catalogue entry**, `Manufacturer/Model`, from the IR archive, or a
  definition carried in the recipe with its commands;
- an activity has a name, a type (`WatchTV`, `WatchDvd`, `ListenToMusic`, `Custom`), its devices with
  their input and roles (`Display`, `Volume`, `ChannelChanging`, …), and optionally its screen buttons
  and sequences.

The IR archive it reads is
[pickysysadmin/logitech-harmony-ir-archive](https://github.com/pickysysadmin/logitech-harmony-ir-archive)
(CC0): about 276,000 devices, 13.3 million commands, each with Logitech's keycode and Pronto Hex. It is
cloned beside the repository in `logitech-harmony-ir-archive/` (2.3 GB checked out), where the
builder finds it by default.

## 4. What it can do for the 600 today

The project's requirement list for the 600, `todo/todo-harmony-600.md`, ticks a requirement only when
a test proves it: **16 of 68 are ticked.**

| Proven | Open |
|---|---|
| read a configuration off the remote, checked | read a configuration back into a recipe (R3) |
| understand it: devices, activities, keys, screens, codes | write *your* remote: record a new unit's identity and backup first (R6) |
| build a whole configuration from a recipe | find and add a catalogue device with power and inputs (R9, R10) |
| write it, verified by reading back, and the remote runs it | add a learned device (R11) |
| refuse what does not fit the model | rename or remove devices and activities (R12, R13, R25, R26) |
| export and import codes as Pronto Hex | change a key in an activity or device mode (R31, R32) |
| create activities with their devices and inputs | put commands on screen pages (R34, R35) |
| choose which activities the activity keys start | delays, repeats, channel tuning (R16 to R18) |
| named sequences with pauses | favourites (R45, R46) |
| back up a remote and restore the backup | remote settings (R47) |
| clear a remote with an empty configuration | |
| tell one unit from another | |

Its first-write review (`docs/review-before-first-write.md`) shows the care taken: the write path was
re-derived from the firmware and reviewed independently before the first write.

## 5. What it would take to rebuild this remote's setup

1. **Device models.** The backup holds no make or model; the recipe needs a catalogue entry for the
   Samsung TV, the AVR and the HiFi. Either the owner supplies them (MyHarmony lists them), or the
   recovered IR codes are matched against the archive's Pronto codes to find the code sets.
2. **A recipe** for the two activities:
   - Muzica: AVR as `Volume` and control, the AVR's input, HiFi off;
   - Tivù: the Samsung TV as `Display`, its input, its volume;
   - plus screen buttons taken from the backup's pages (`backups/.../project.json`).
3. **A build**, then a check of the result with this project's Afterglow 600 reader
   (`tools/read_600_config.py`), which reads the 600's format independently.
4. **A write**, only after explicit approval, with a fresh backup first. Restoring
   `backups/harmony-skin71-20261111-195845/config.ezhex` is the way back.

Steps 1 to 3 never touch the remote.

## 6. What blocked running it here

`npx pnpm install --frozen-lockfile` in `harmony-explorations/` was refused by the session's
permission system, because it downloads and runs third-party code. The dependencies are only
TypeScript tooling, but pnpm also links the workspace packages (`@harmony/codec`, `@harmony/lab`, …)
that the scripts import, so nothing in it runs without that step. Allowing it, or running it yourself,
is the next step:

```sh
cd harmony-explorations
npx pnpm@11.20.0 install --frozen-lockfile
```

## 7. Compared with Afterglow

| | Afterglow (with this project's 600 support) | harmony-explorations |
|---|---|---|
| Reads a 600 backup | yes, devices, codes, names, activities | yes |
| Backs up and restores over USB | yes, through libconcord | yes, its own USB stack |
| Builds a 600 configuration | no, read-only | yes, from a recipe, run on a real 600 |
| Device catalogue | its own archive build | the CC0 IR archive |
| Interface | PyQt6 GUI, 600 read-only | command-line scripts; FreeHarmony not released |
| Licence | GPL-3.0 | MIT (FreeHarmony GPL-3.0) |

The two complement each other: harmony-explorations builds, Afterglow's reader checks the result
independently.
