---
title: Dynamic profiles
type: how-to
description: Make a profile build its own image before the VM boots — the build command, the {out} token, cmdline from the builder, and prepare / --no-build.
related:
  - provium/configuration/provium-toml
  - provium/configuration/profiles
  - provium/running-tests/fixtures-and-dependencies
---

A static profile points at artifacts that already exist on disk:

```toml
[profiles.peios]
kernel  = "/build/peios/bzImage"
initrd  = "/build/peios/initrd.cpio.gz"
cmdline = "console=ttyS0 quiet"
```

That leaves a gap. You build the image with one tool, then run Provium with another, and nothing connects the two — so it's easy to test last week's image because you forgot to rebuild. A *dynamic* profile closes the gap: the profile owns a `build` command, Provium runs it, and the VM boots the fresh result.

This is the same idea as [`cmdline_file`](~provium/configuration/provium-toml#cmdline-file) — let the test consume the authoritative build instead of a hand-copied snapshot — applied to the whole image. This page covers both.

## Cmdline from the builder

Start with the smaller case. Image builders usually emit a kernel command line of their own — a `peiso` build, for instance, carries the one its boot package ships at `root/usr/share/live-boot/cmdline`. If you copy that string into your profile's `cmdline`, the two drift the moment the builder changes it (a new `init=`, a new console). Point `cmdline_file` at the builder's file instead:

```toml
[profiles.peios]
kernel       = "../dist/peios-experimental-2026.8/root/usr/lib/modules/<release>/vmlinuz-<release>"
initrd       = "../dist/peios-experimental-2026.8/root/system/boot/initramfs.cpio.gz"
cmdline_file = "../dist/peios-experimental-2026.8/root/usr/share/live-boot/cmdline"
```

Provium reads the file at boot, collapses its whitespace to single spaces, and uses it as the command line. You can still add tokens inline — they're appended *after* the file, so they win for last-wins kernel parameters:

```toml
cmdline_file = "../dist/peios-experimental-2026.8/root/usr/share/live-boot/cmdline"
cmdline      = "loglevel=7"     # verbose, on top of whatever the builder set
```

No manual copy means nothing to forget to update.

## Building the whole image

The `build` field takes a shell command. Provium runs it — once, before any VM boots — and only then reads the profile's `kernel` / `initrd` / `cmdline_file`:

```toml
[profiles.peios-full]
build        = "peiso iso specs/peios-full.toml --out {out}"
kernel       = "{out}/root/usr/lib/modules/<release>/vmlinuz-<release>"
initrd       = "{out}/root/system/boot/initramfs.cpio.gz"
cmdline_file = "{out}/root/usr/share/live-boot/cmdline"
```

Now `provium` builds `peios-full` before the suite runs, and tests boot exactly what was just built:

```lua
local vm = provium:vm("v", "peios-full"):boot()
```

The command runs with `sh -c`, inheriting your environment and streaming its output straight to the terminal. It runs from Provium's working directory — or, for a profile discovered via [`from_dir`](~provium/configuration/provium-toml#from-dir), from that profile's own directory. Either way, reference inputs (the manifest above) relative to that directory, so the suite stays portable across checkouts; there is deliberately no "build working directory" knob to tie it to one machine's layout.

## `{out}`: one directory, no drift

Look again at the example: `{out}` appears in the `build` command's `--out` *and* in every path field. That's the point. `{out}` expands — once, when the config loads — to this profile's build-output directory, so the place the build *writes* and the places Provium *reads* are guaranteed to be the same directory. You can't update one and forget the other, because there's only one.

Where does `{out}` point? By default, a per-profile directory under the Provium cache:

```
$XDG_CACHE_HOME/provium/builds/<profile>/     # e.g. ~/.cache/provium/builds/peios-full/
```

Set [`build_out`](~provium/configuration/provium-toml#build-out) to pin it somewhere specific — but you still only write the path once:

```toml
[profiles.peios-full]
build_out    = "/tmp/provium-builds/peios-full"
build        = "peiso iso specs/peios-full.toml --out {out}"
kernel       = "{out}/root/usr/lib/modules/<release>/vmlinuz-<release>"
# …
```

Provium creates the directory before running the build, but never wipes it — the build command owns its contents, so it's free to keep its own incremental-build caches there.

## When the build runs

| You run | What gets built |
|---|---|
| `provium` (the test suite) | Every profile that declares a `build`, up front, before the scheduler starts. |
| `provium console <profile>` | Just that profile. |
| `provium repl <profile>` | Just that profile. |
| `provium prepare [profile]` | That profile, or — with no argument — every profile with a `build`. No VM boots. |

The test runner builds *all* dynamic profiles rather than only the ones a run will touch, because tests choose their profiles at runtime from Lua (`provium:vm(name, profile)`) — Provium can't know in advance which a given run needs. If you keep several dynamic profiles and want to build only one, use `provium prepare <profile>` followed by `provium --no-build`.

Two controls shape this:

- **`provium prepare`** builds without booting. It even skips the pre-flight checks (`/dev/kvm`, networking, `CAP_NET_ADMIN`), so you can build an image on a machine that isn't set up to run VMs.
- **`provium --no-build`** skips the hook entirely for one run — for when you know the artifacts are already current and just want to boot.

## No staleness — that's the builder's job

Provium does not try to decide whether your image is up to date. It runs the `build` command **every** invocation and trusts the builder to be cheap when nothing has changed. Tracking inputs, hashing sources, and skipping unnecessary work is what build tools are for; reimplementing that inside a test harness would only get it subtly wrong.

The practical consequence: if your builder does a full rebuild every time, `provium` pays that cost every time. That's usually fine — Provium tends to be the *last* gate you run, where a clean build is what you want anyway — but if it bites, make the builder incremental (or use `--no-build` between source changes). Don't expect Provium to shortcut it.

### Making a builder incremental

Some builders have no incremental mode to reach for. `peiso root` is one: it composes from scratch and refuses a `--out` that already exists, so the obvious command has to clear its own output first —

```toml
build = "rm -rf {out}/root && peiso root shared.toml peiso.toml --out {out}/root"
```

— and that is a full compose on every `provium test`, however small the change. Where the tests themselves take a second, the build can be most of a minute of it.

The fix is a script beside the profile that decides for itself:

```sh
#!/bin/sh
# ./build.sh {out}
set -eu
out="$1"; root="$out/root"; stamp="$out/.build-stamp"

# Whatever the composition depends on. Name, size and mtime rather than
# content: a rebuilt package always moves one of them, and hashing a
# kernel package on every test run would defeat the point.
fingerprint() { cat shared.toml peiso.toml; ls -lL ../../pkgs/out/; }

new=$(fingerprint | sha256sum)
[ -d "$root" ] && [ "$new" = "$(cat "$stamp" 2>/dev/null)" ] && exit 0

rm -f "$stamp"          # an interrupted compose must not leave a stamp
rm -rf "$root"          # claiming the tree beside it is current
peiso root shared.toml peiso.toml --out "$root"
printf '%s' "$new" > "$stamp"
```

```toml
build = "./build.sh {out}"
```

A [discovered profile](~provium/configuration/profiles#one-directory-per-profile) runs its build in its own directory, so `./build.sh` and the paths inside it mean what they say where they are written.

Two details matter. Remove the stamp *before* the work rather than only writing it after, so a compose interrupted halfway is not mistaken for a current one on the next run. And keep the fingerprint cheap enough to run unconditionally — it is paid on every invocation, including the ones that do nothing.

## Fixtures rebuild when the image changes

Provium's [fixture cache](~provium/running-tests/fixtures-and-dependencies) keys each snapshot partly on the kernel and initrd's path, size, and modification time. A dynamic profile rebuilds its image every run, which usually changes those timestamps — so fixtures captured against the old image are treated as stale and rebuilt. That's correct (a freshly built kernel can behave differently), but it does mean a dynamic profile plus a large fixture tree pays a fixture rebuild each run on top of the image build. If that's too slow for the inner loop, `--no-build` keeps the image — and therefore its fixtures — warm between source changes.

## Failures abort — never fall through

A `build` command that exits non-zero stops the run:

```
provium: building profile `peios-full` → /home/you/.cache/provium/builds/peios-full
… builder output …
provium: profile `peios-full`: build command failed (exit status: 1)
```

This matters because a half-finished build often leaves the *previous* run's artifacts in place — they'd pass an existence check and boot cleanly, and you'd be testing a stale image while believing the build succeeded. Provium refuses to do that: a failed build is a failed run (exit code `2`), full stop.

## Worked example

A self-contained suite that builds its own image. The peiso spec lives in the suite, so a fresh clone can `provium` with nothing else set up:

```toml
# test-suite/provium.toml
[provium]
roots = ["tests"]

[profiles.peios-full]
build        = "peiso iso specs/peios-full.toml --out {out}"
kernel       = "{out}/root/usr/lib/modules/<release>/vmlinuz-<release>"
initrd       = "{out}/root/system/boot/initramfs.cpio.gz"
cmdline_file = "{out}/root/usr/share/live-boot/cmdline"
```

```
test-suite/
├── provium.toml
├── manifests/
│   └── peios-full.toml        # the image recipe, versioned with the tests
└── tests/
    └── smoke.test.lua
```

Day-to-day:

```bash
provium                       # build the image, then run the whole suite
provium --no-build            # skip the build; boot the last-built image
provium prepare               # build the image, don't run anything
provium console peios-full    # build, then drop to the guest's console
```

## See also

- [provium.toml reference](~provium/configuration/provium-toml) — the `build`, `build_out`, and `cmdline_file` fields.
- [Profiles](~provium/configuration/profiles) — patterns for static and multi-profile setups.
- [CLI reference](~provium/reference/cli) — `provium prepare` and `--no-build`.
