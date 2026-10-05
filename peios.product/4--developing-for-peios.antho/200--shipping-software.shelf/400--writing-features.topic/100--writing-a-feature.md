---
title: Writing a feature
type: how-to
description: Ship a feature with your package — its directory, its four lifecycle scripts and what they are given, feature.toml to say what it is, and the rules a script must keep.
related:
  - peios/features/overview
  - peios/features/using-feat
---

A [feature](~peios/features/overview) is how a package does more than put
files in place: define a service, change a setting, make something its
files rely on. Reach for one only when the package can't do without it.
A feature's scripts run as whoever turns it on, with that person's
authority and no more, and each one is code an Administrator has to trust.

## Its directory

A feature is a directory your package installs under
`/usr/libexec/features/<name>/`, read at `/libexec/features/<name>/`. Its
name is letters, digits, `-`, `_` and `.`. In it, any of:

| File | Runs |
|---|---|
| `install.sh` | To install it: set up what it needs, not yet in use. |
| `enable.sh` | To turn it on. |
| `disable.sh` | To turn it off, leaving what install set up. |
| `uninstall.sh` | To remove it: take away what install set up. |
| `feature.toml` | Nothing: it says what the feature is. |

Ship only the scripts that have something to do. A step with no script
just records the new state. Other files may sit beside them for the
scripts to use.

## What a script is given

Each script is run directly, so it needs a `#!` line and to be executable.
It runs:

- as whoever asked, with their token: `feat` adds no authority;
- in the feature's directory, so it can name the files beside it;
- with `FEAT_NAME`, `FEAT_DIR` and `FEAT_PHASE` (`install`, `enable`,
  `disable` or `uninstall`) set, beside the rest of the caller's
  environment;
- with the caller's standard output and error, or, under a program such as
  Feature Manager, with its output read line by line and shown, and its
  standard input empty.

A script that exits with anything but 0 has failed: the feature is left
interrupted, and the person is shown what the script said.

## The rules a script keeps

- **Be safe to run again.** Asking again after an interruption reruns the
  script from the start, whatever it had done. Set values rather than add
  to them; treat "already there" and "already gone" as done.
- **Be safe to run first.** An interrupted uninstall can be followed by an
  install, and an interrupted turn-on by a turn-off, so a script can't
  assume the step before it finished.
- **Say what you did, briefly.** Each line is shown to the person, under
  Feature Manager as the change runs. Start lines with the feature's name.
- **Fail with words.** Write why to standard error before exiting non-zero.
  It is what the person sees.
- **Ask nothing.** There may be no terminal, and standard input may be
  empty.
- **Undo what you do.** `uninstall.sh` takes away everything `install.sh`
  made; `disable.sh` reverses `enable.sh`.

## `feature.toml`

```toml
title = "Dynamic Boot"
description = """
Keeps this machine's boot image up to date. Two services, mkirf-watch and
mkuki-watch, make it again whenever the kernel, the initramfs or the kernel
command line changes, so a change to any of them is used at the next boot
without making the boot image by hand.

Turning it on or off takes effect at the next boot."""
```

| Member | Is |
|---|---|
| `title` | Its name, in Title Case, for people. Without one, its directory's name is shown. |
| `description` | What it does, in a sentence or a few. Wrap lines as you like: they are joined, and a blank line starts a new paragraph. Say when a change takes effect, if not at once. |

Both are optional, and members `feat` doesn't know are ignored. A
`feature.toml` that can't be read doesn't hide the feature: it is listed,
with the problem said beside it.

## Packaging it

Map the files into place in your package's `[files]`:

```toml
[files]
"src/feature.toml" = "usr/libexec/features/dynamic-boot/feature.toml"
"src/install.sh"   = "usr/libexec/features/dynamic-boot/install.sh"
"src/enable.sh"    = "usr/libexec/features/dynamic-boot/enable.sh"
"src/disable.sh"   = "usr/libexec/features/dynamic-boot/disable.sh"
"src/uninstall.sh" = "usr/libexec/features/dynamic-boot/uninstall.sh"
```

and depend on `dev.peios.peiosutils`, which ships `feat`, and on whatever
the scripts run. Installing the package runs none of them: the feature
waits, not installed, until someone turns it on.

Peios ships its own features the same way, one package each, named
`feat-<name>`: `dev.peios.feat-dynamic-boot` is a whole example.
