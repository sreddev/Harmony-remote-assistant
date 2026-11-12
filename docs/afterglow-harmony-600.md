# Afterglow and the Harmony 600: the whole process

How this project used [Afterglow](https://github.com/harmonic-afterglow/afterglow) to back up a
Logitech Harmony 600 over USB without Logitech's software, and to read the backup back into devices,
commands and activities. Every step below was run on 11 November 2026 on Windows 11 with Python 3.15.
**Nothing was ever written to the remote.**

Related: [harmony-explorations-evaluation.md](harmony-explorations-evaluation.md) evaluates the other
project that can build a configuration for this remote.

## Contents

1. [Results](#1-results)
2. [Folder layout](#2-folder-layout)
3. [Setting up](#3-setting-up)
4. [Backing up the remote](#4-backing-up-the-remote)
5. [Reading the backup](#5-reading-the-backup)
6. [How the 600 support was worked out](#6-how-the-600-support-was-worked-out)
7. [What was added to Afterglow](#7-what-was-added-to-afterglow)
8. [Tests](#8-tests)
9. [Known limits and open points](#9-known-limits-and-open-points)
10. [Safety rules followed](#10-safety-rules-followed)
11. [Sources and licences](#11-sources-and-licences)

## 1. Results

| | |
|---|---|
| Remote | Harmony 600, USB `046d:c122`, skin 71, architecture 14, firmware 0.3, board 1.1.0, flash `0x15:0x1C` |
| Backup | 666,177 bytes, `backups/harmony-skin71-20261111-195845/` |
| Devices | TV (Samsung, 71 commands, 55 named), AVR (54, 52 named), HiFi (Panasonic-type IR, 50, 20 named) |
| Activities | **Muzica** (AVR on, HiFi off, keys to the AVR); **Tivù** (TV on, keys to the TV) |
| IR codes | all 175 commands recovered as waveforms |
| Verification | 35 of 36 named TV keys send the Samsung command byte of that name |
| Text | every screen the remote can show reads as text |

Command names come from two places: the 600's key table for the keypad, and the label beside each
side key on the device and activity pages. A command no key and no page uses keeps a numbered name
(`Command 2F`), because the configuration holds no name for it.

## 2. Folder layout

| Path | What it is |
|---|---|
| `afterglow/` | Afterglow, cloned from GitHub, with the uncommitted Harmony 600 support (section 7) |
| `backups/harmony-skin71-20261111-195845/` | the remote's backup: `config.ezhex`, `usercfg.bin`, `identity.json`, `SHA256SUMS.json`, and `project.json` written by the reader |
| `tools/` | this project's scripts (table below) |
| `vendor/afterglow-dlls/` | `libconcord-6.dll` and its dependencies, extracted from Afterglow's Windows release; `SOURCE.txt` says from where |
| `.venv/` | a virtual environment holding only `pytest`, for Afterglow's tests |
| `harmony-explorations/`, `logitech-harmony-ir-archive/` | for the evaluation, not used by this process |

| Script | Touches the remote | What it does |
|---|---|---|
| `tools/lifeboat_read.py` | reads only | identifies the remote, then backs up its configuration |
| `tools/read_600_config.py` | no | imports a backup with Afterglow and prints devices, commands, activities |
| `tools/pyi_dlls.py` | no | extracts DLLs from a PyInstaller executable without running it |
| `tools/gspm600_probe.py` | no | tries candidate section mappings with the Harmony One reader |
| `tools/gspm600_matrix.py` | no | offers every 600 section to every One section parser |
| `tools/glyph_atlas.py` | no | draws every glyph of the image's fonts into a PNG |
| `tools/make_600_glyph_shapes.py` | no | writes the 600 glyph-shape table from the codes read off the atlas |

## 3. Setting up

### 3.1 Get Afterglow

```sh
git clone https://github.com/harmonic-afterglow/afterglow.git afterglow
```

The format layer needs only the Python standard library. The GUI needs PyQt6 and was not used.

### 3.2 Get libconcord for Windows

Afterglow talks to the remote through libconcord. Its Windows release bundles `libconcord-6.dll`;
taking it from there avoids building Concordance with MinGW.

```sh
gh release download v0.3.0-beta.6 -R harmonic-afterglow/afterglow \
    -p afterglow-windows-x86_64.exe -p SHA256SUMS
sha256sum afterglow-windows-x86_64.exe        # must match the line in SHA256SUMS
python -I tools/pyi_dlls.py afterglow-windows-x86_64.exe vendor/afterglow-dlls
```

`pyi_dlls.py` reads the PyInstaller archive at the end of the executable and writes out its `.dll`
entries; nothing in the executable runs. All the DLLs are needed, because libconcord links libcurl,
libzip, hidapi and libusb, which bring their own.

### 3.3 Close MyHarmony

MyHarmony's USB plugin uses the same HID interface. Close every `MyHarmony.exe` before any USB step,
so two programs never talk to the remote at once.

### 3.4 No driver change

Afterglow's "direct access" switches a remote to Windows' WinUSB driver, but only for
`VID_046D&PID_C11F` (Harmony 900, 1000 and 1100); `windows_driver.py` names no other. The 600 is a
plain HID device that libconcord reaches through hidapi, so nothing is installed or changed.

## 4. Backing up the remote

```sh
python tools/lifeboat_read.py --dlls vendor/afterglow-dlls --identify-only   # identity, nothing saved
python tools/lifeboat_read.py --dlls vendor/afterglow-dlls                   # identity and backup
```

The script imports Afterglow's own `concord.Remote` and calls only `identity()`, `save_config()` and
`read_config()`. It writes a folder `backups/harmony-skin<skin>-<timestamp>/` holding:

- `config.ezhex`: the configuration as Concordance and Afterglow write it back, an XML header around the blob;
- `usercfg.bin`: the raw blob, identical to the payload inside `config.ezhex`;
- `identity.json` and `SHA256SUMS.json`.

The backup took 46 seconds. **Keep a copy off this computer**: it is the only way back to the
remote's current setup if Logitech's service closes.

## 5. Reading the backup

```sh
python tools/read_600_config.py backups/harmony-skin71-20261111-195845/config.ezhex
```

It unpacks the `.ezhex`, runs Afterglow's importer (which picks the `harmony-600` profile from the
header), prints the result and writes `project.json` beside the backup. The project is in Afterglow's
own format, so it can later be opened by anything that reads Afterglow projects.

Afterglow's own check gives the same answer:

```sh
PYTHONPATH=afterglow/src python -c "import sys; from afterglow import selfcheck; \
    sys.exit(selfcheck.import_check(sys.argv[1]))" backups/<folder>/config.ezhex
# imported 3 devices, signals {'waveform': 175}
```

## 6. How the 600 support was worked out

Each step was measured on the backup; the format details are in
[afterglow/docs/harmony_600/README.md](../afterglow/docs/harmony_600/README.md).

1. **The format.** `usercfg.bin` opens with `GSPM`, the Harmony One's image. Its end vector, its
   `PTYY` close and its two-lane XOR checksum follow the One's rules exactly; the base address
   (`0x030000`), a header constant (`0x1400`) and the section index (18 slots) differ.
2. **The sections.** `gspm600_matrix.py` offered every 600 slot to every One section parser. Five
   parsers each accepted exactly one slot, which showed that from section 9 on the 600's slots are the
   One's minus one, and that the One's touch-template section has no counterpart.
3. **The devices.** Section 0's state variables name them (`TV_Power_2`, `AVR_Power_2`,
   `HiFi_Power_2`). Section 5 declares 175 commands. The 600's command objects carry an extra leading
   atom; once that was allowed, all 175 were linked, and 18 presses with no lead-in silence decoded too.
4. **The text.** No glyph was recognised, because the 600's LCD fonts are not in Afterglow's table.
   `glyph_atlas.py` drew every glyph; the codes were read by eye and confirmed across five fonts;
   `make_600_glyph_shapes.py` turned them into a shape table, which now reads every screen.
5. **The screens.** Following pointers showed the 600's slot record is the One's without its template
   byte, so each page has its own key register.
6. **The keys.** The One's 40 key codes gave wrong names. harmony-explorations' measured table of the
   600's 54 keys replaced them; the television's Samsung codes confirmed it (35 of 36).
7. **The page labels.** Each side key's label is drawn as text at a corner of the page. The corner is
   the key: 8 top left, 2 top right, 9 bottom left, 34 bottom right, settled for the top pair by the
   television's HDMI and Source codes. An import names a command after the one key that sends it alone.
8. **The activities.** Each activity's start shows "Starting <name>" first, which names it.

## 7. What was added to Afterglow

Committed in `afterglow/` on the local branch `harmony-600-readonly` (not pushed):

| File | Purpose |
|---|---|
| `src/afterglow/library/remotes/harmony-600/profile.json` | the profile: skin 71, arch 14, status **`read-only`** |
| `src/afterglow/backends/harmony_600/__init__.py` | the package |
| `src/afterglow/backends/harmony_600/backend.py` | import only; `build_project` raises `ReadOnly` |
| `src/afterglow/backends/harmony_600/layout.py` | the 600's layout, and `active()`, which runs the One's reader under it |
| `src/afterglow/backends/harmony_600/keys.py` | the 600's 54 scan codes |
| `src/afterglow/backends/harmony_600/pages.py` | side-key labels and the renaming of placeholder commands |
| `src/afterglow/backends/harmony_600/glyph-shapes.json` | the LCD glyph shapes |
| `docs/harmony_600/README.md`, `docs/README.md` | the format document and its index entry |

`layout.active()` takes a lock, points the Harmony One modules' constants and a few of their functions
at the 600's versions, and puts every one back when the read ends. No One file was edited.

Writing is refused twice: the profile's `read-only` status stops Afterglow building or writing for the
600 anywhere in the application, and the backend refuses to build.

## 8. Tests

```sh
cd afterglow
../.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_catalogue.py \
    tests/test_harmony_one_backend.py tests/test_harmony_one_import.py tests/test_docs.py
```

- The non-GUI tests pass. Tests that open Afterglow's interface fail with "needs PyQt6", because the
  environment has no PyQt6; none fails because of the 600 changes.
- `tests/test_docs.py` passes: the new document is indexed and every citation resolves.
- **`tests/test_removability.py` fails for `harmony_one`**, because `harmony_600` imports it. See
  section 9.
- The imported devices pass Afterglow's `project_devices.validate`, and no activity refers to a
  command that does not exist.

## 9. Known limits and open points

- **Not yet acceptable upstream** (the branch is local). Afterglow requires every backend to be deletable with `rm -r`, and
  the 600 backend depends on the One's. Either the 600 gets its own copy of the reader, as the 800 did,
  or the shared parts move somewhere both can use; that is the maintainers' decision. Section 7's
  changes would also need tests named as invariants, and real configurations stay out of the
  repository.
- **Numbered commands.** 16 TV, 2 AVR and 30 HiFi commands are used by no key and no page, so the
  image gives them no name.
- **Unmeasured keys.** All Off, Enter and the two arrows below the screen have no known scan code.
- **One image.** Every rule was measured on one configuration; skin 73 and other setups may differ.
- **No device models.** The configuration stores no make or model; MyHarmony keeps those in the account.
- **Reading only.** Building and writing a 600 configuration is not part of this support.

## 10. Safety rules followed

- No write command was sent to the remote; every USB call was `identity`, `save_config` or `read_config`.
- MyHarmony was closed during USB access.
- The release executable was checked against its published SHA-256, and only its DLLs were extracted.
- No driver was installed or switched.
- The 600 profile is `read-only`, so Afterglow refuses to build or write for it.

## 11. Sources and licences

| | Licence | Used for |
|---|---|---|
| [Afterglow](https://github.com/harmonic-afterglow/afterglow) | GPL-3.0 | the importer, the One reader, the backup calls |
| [Concordance / libconcord](https://github.com/jaymzh/concordance) | GPL-3.0 | USB access through Afterglow's build |
| [harmony-explorations](https://github.com/dannybloe/harmony-explorations) | MIT | the 600's key table |

Changes made inside `afterglow/` are derived from GPL-3.0 code and carry its licence if shared.
