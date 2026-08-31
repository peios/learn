---
title: Running a build
type: how-to
description: The peiso commands, the Makefile that wraps them, booting and driving the result under QEMU, and the install test from a development medium.
related:
  - peios/peiso/building-images/quick-start
  - peios/peiso/reference/the-build-directory
  - peios/dwe/driving-a-machine
---

## The commands

```text
peiso root <spec.toml>... [--out <dir>] [--overwrite]
peiso iso  <spec.toml>... [--out <dir>] [--overwrite]
```

`peiso root` composes the spec's edition into a root tree and stops — useful for inspecting what a release contains, or for a root that will be packed some other way. `--out` names the directory; without it the root goes to the same place `iso` would put it.

`peiso iso` runs [the whole pipeline](~peios/peiso/building-images/the-build-pipeline) and prints the ISO's path on stdout as its last line; progress goes to stderr. Both commands work from any current directory — relative paths *inside* a spec resolve against that spec's own directory, and the output directory `dist/peios-…/` is relative to where you run.

A build refuses an output path where a root already sits. `--overwrite` replaces it and rebuilds — the rebuild loop after republishing a package — but replaces only something recognisably a composed root (it carries the package database) or an empty directory, never an arbitrary directory the path happens to name. `make iso` passes it, so rebuilding is the default there.

Both also take more than one spec, layering them left to right, so a statement of where packages come from can be shared across many builds that each name only what they build. [The spec](~peios/peiso/reference/the-spec#layering) has the rules.

There is no `--version`, `--edition` or `--dwe` flag. Everything that shapes an image is in the spec, so a build is reproducible from the file alone.

## The Makefile

`dist/release/Makefile` wraps the commands and the QEMU invocations that boot their output:

| Target | |
|---|---|
| `make iso` | build peiso from the tree, then `peiso iso experimental.toml` |
| `make iso-dev` | the same with the `dev.toml` layer: a low squashfs level, so the squash stage takes a fraction of the time and the image is somewhat larger — the edit-boot loop's target, never a release. It writes the same build directory as `iso`. |
| `make iso-dwe` | the same from `experimental-dwe.toml` |
| `make boot` | boot the newest plain build: UEFI, serial console, atriumd forwarded to `localhost:8080` |
| `make boot-dwe` | boot the newest DWE build with a vsock device (`DWE_CID`, default 3) |
| `make boot-quiet` / `boot-break` | add `peios.quiet=2` / `rd.break` to the command line via SMBIOS |
| `make boot-install` | boot the DWE build with a blank 8 GiB `disk.img` attached as `/dev/vdb` |
| `make boot-installed` | boot `disk.img` alone — no medium |
| `make clean-disk` / `make clean` | start the install test over / remove every build directory |

The build directory a target uses is the newest `../peios-experimental-<version>[-dwe]/`; only peiso knows a build's resolved version, so the Makefile looks rather than guesses.

## Driving the running system

`dist/release/drive.py` boots a build by the direct kernel path, waits for the login prompt, feeds a script to the console, and prints what the guest said:

```sh
./drive.py --no-disk probe.sh                 # in the live system
./drive.py --installed probe.sh               # on the installed disk
./drive.py --build ../peios-experimental-2026.9 --no-disk probe.sh
```

It talks to the ordinary autologin session — an administrator, not SYSTEM. For anything that needs SYSTEM, use a DWE build and [`dwe exec`](~peios/dwe/driving-a-machine).

## The install test

An installation medium is only proven by installing from it and booting what it produced. That takes a development build, because the installer must open the raw disk and the console account cannot (PEI-549):

```sh
make iso-dwe
make boot-install          # leave it running
```

then, from another terminal:

```sh
DWE_TARGET=vsock:3 dwe exec -- peios-install --yes --whole-disk /dev/vdb
```

The installer partitions and formats the disk, copies the live root, establishes trust in the medium repository on the target, replaces `live-boot` with `disk-boot` in both the root and its initramfs, writes a command line with the root filesystem's UUID, and rebuilds the target's initramfs and UKI. Then:

```sh
make boot-installed
```

boots the disk with nothing else attached. The initramfs hook is now `disk-boot`'s (`mount-root-disk.sh`); the login prompt on the serial console is the installed system. An installed system moves to the next release with [`upgrade-peios`](~peios/peiso/editions-and-upgrades/upgrading-peios).

> [!NOTE]
> A system installed from a DWE medium keeps `dwed` (PEI-550). Install from a plain medium once that path can be driven without SYSTEM.

## Variants

A variant is another spec file. `experimental-dwe.toml` is the Experimental spec plus `[devtools] dwe = true`, and builds into its own `…-dwe/` directory so it never overwrites the plain image. A spec that pins `version = "2026.8"` reproduces a release after newer ones exist; one that names a different `[[packages.repository]]` builds from another source.
