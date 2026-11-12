# Harmony remote assistant

Keeping a Logitech Harmony 600 configurable without Logitech's servers: how the MyHarmony software
works, backing the remote up over USB, reading that backup locally with
[Afterglow](https://github.com/harmonic-afterglow/afterglow), and the route to building new
configurations with [harmony-explorations](https://github.com/dannybloe/harmony-explorations).

Nothing here writes to a remote.

## Documents

| Document | What it covers |
|---|---|
| [docs/afterglow-harmony-600.md](docs/afterglow-harmony-600.md) | the whole Afterglow process: setup, backup, reading, the 600 support, tests, limits |
| [docs/harmony-explorations-evaluation.md](docs/harmony-explorations-evaluation.md) | whether harmony-explorations can build a new configuration for the 600 |
| [patches/afterglow/](patches/afterglow/) | the read-only Harmony 600 support for Afterglow, as a `git am` patch; its format document is inside the patch (`docs/harmony_600/README.md`) |
| `Harmony-600-Project-Log.mhtml` | the project log: status, results, open decisions |
| `MyHarmony-Teardown.mhtml` | how the MyHarmony software works |
| `Harmony-Offline-Plan.mhtml` | proposals for working without Logitech, with a USB simulator |

The `.mhtml` files open in Edge or Chrome. Their HTML sources are in `research/myharmony/pages/`.

## Folders

| Folder | What it holds |
|---|---|
| `tools/` | the project's scripts; each says at the top whether it touches the remote |
| `vendor/afterglow-dlls/` | libconcord for Windows and its dependencies, from Afterglow's release (GPL; see `SOURCE.txt`) |
| `research/myharmony/` | the helper tools and page sources from the MyHarmony analysis |
| `patches/afterglow/` | the Afterglow change |

## Not in this repository

- **Remote backups.** A backup lists what is set up in someone's home. Make your own with
  `tools/lifeboat_read.py` and keep it private.
- **Material extracted from MyHarmony** (its app packages, assemblies, protocol templates and
  scripts). It is Logitech's software; the documents describe it, and `research/myharmony/tools/`
  can extract it again from an installed copy.
- **The two projects this one builds on**, Afterglow and harmony-explorations, and the IR archive.
  Clone them beside this folder.

## Quick start

```sh
git clone https://github.com/harmonic-afterglow/afterglow.git afterglow
git -C afterglow am ../patches/afterglow/*.patch          # the read-only Harmony 600 support

# close MyHarmony first
python tools/lifeboat_read.py --dlls vendor/afterglow-dlls --identify-only   # who is connected
python tools/lifeboat_read.py --dlls vendor/afterglow-dlls                   # back up
python tools/read_600_config.py backups/<folder>/config.ezhex               # read a backup
```

## Credits and licences

| | Licence |
|---|---|
| [Afterglow](https://github.com/harmonic-afterglow/afterglow); the patch is derived from it | GPL-3.0 |
| [Concordance / libconcord](https://github.com/jaymzh/concordance), the DLLs | GPL-3.0 |
| [harmony-explorations](https://github.com/dannybloe/harmony-explorations), the 600's key table | MIT |
| [logitech-harmony-ir-archive](https://github.com/pickysysadmin/logitech-harmony-ir-archive) | CC0 |

Harmony is a trademark of Logitech. This project is independent and not affiliated with Logitech.
