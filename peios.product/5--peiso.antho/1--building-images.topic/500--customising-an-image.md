---
title: Customising an image
type: how-to
description: Put your own files, first-boot scripts, features, extra packages and medium contents into a Peios image, adjust the packers, and know what each choice costs.
related:
  - peios/peiso/reference/the-spec
  - peios/peiso/building-images/quick-start
  - peios/peiso/editions-and-upgrades/editions
---

peiso's job is to make a custom Peios image an ordinary thing to build. The release stays what the edition says it is; everything you add on top is yours, and peiso writes it all down in `customisations.toml` beside the build so two images from the same release differ *auditably* rather than silently.

This page goes through the additions in the order the build applies them. All of them are optional.

## Extra packages

```toml
[[package]]
name    = "bash"
version = ">= 5.2"        # optional
```

Resolved together with the edition's closure from the spec's sources, so a conflict fails the build. See [The spec](~peios/peiso/reference/the-spec).

## Files

```toml
[[file]]
src  = "overlay/motd"                        # relative to the spec
dest = "usr/etc/motd"                        # inside the root
sddl = "O:SYG:SYD:(A;;GA;;;SY)(A;;FR;;;WD)" # optional
```

The file is copied into the composed root before anything is packed, so a `dest` under `boot/initramfs/` lands in the initramfs — a hook you are still writing, say — and one under `lcl/` lands in the operator tree.

`sddl` gives the file a [security descriptor](~peios/security-descriptors/sddl). Peios has no file modes; the descriptor is the whole of a file's access control. peiso compiles the SDDL and writes it into the squashfs as the file's `security.peios.sd` attribute — the same route as the firmware signatures, and just as privilege-free. Without `sddl` the file gets whatever the mount synthesises for an object with no descriptor, which follows its parent. The initramfs carries no attributes at all, so `sddl` on a file under `boot/initramfs/` is refused.

> [!NOTE]
> An injected file has no owning package. Nothing verifies it, nothing upgrades it, and `peipkg` does not know it exists. That is fine for a motd, a hook under development or a site's own policy file; the moment a file matters, make it a package.

## First-boot scripts

```toml
[[autorun]]
src  = "scripts/setup.sh"
name = "50-setup"         # optional; default: the file's name
```

The script is placed, executable, in `/lcl/policy/autorun.d/`, which peinit runs in order after the registry is serving and before it plans its services. peiso's own entries there are `10-apply-seeds.sh` (the release's registry seeds) and `20-features.sh`; a name that sorts after those runs once the release's policy is in place, which is what a script usually wants.

Whether a script runs once is the script's business. The idiom is to end with `rm -- "$0"` — on an installed system that is once; on the live medium the removal is an overlay whiteout that does not survive a reboot, so the script runs again against the fresh tmpfs registry, which is usually what a live image needs. The script runs with peinit's identity at that phase, not as a logged-in user.

## Features

```toml
[[feature]]
name  = "dynamic-boot"
state = "enable"          # or "install"; default enable
```

Generates `20-features.sh`, which runs `feat add <name>` (install then enable) or `feat install <name>` per entry, in order, and removes itself. The feature's definition must be in the root — usually by a `[[package]]` that ships it (`feat-dynamic-boot` here). Services a feature creates start on the same boot, since autoruns finish before peinit enumerates them.

## Files on the medium

```toml
[[medium]]
src  = "docs/"            # a file or a directory
dest = "docs"
```

Placed in the ISO's data area beside `rootfs.squashfs` and `repo/`. The live system mounts the medium at `/media/peios`, so this appears at `/media/peios/docs`. It is on the stick, not in the system: use it for payloads an installer or a script will read from the medium, or for things a person should find on it.

## The packers

```toml
[squashfs]
compression = "zstd"                     # any mksquashfs -comp; default zstd
exclude     = ["usr/share/doc"]          # root-relative; default none

[initramfs]
exclude = ["var/state/peipkg", "lcl/conf/peipkg"]   # the default; replaces it

[boot]
cmdline_extra = "loglevel=3"             # appended to live-boot's command line
```

`initramfs.exclude` *replaces* the default list rather than adding to it, so an explicit `[]` packs everything; the two defaults are the initramfs root's package database and repository configuration, which belong to the real root. `boot.cmdline_extra` is appended to the command line the boot package ships and baked into the UKI — there is no full replacement, because the shipped line carries `init=` and the console, and losing those quietly is how a custom image fails to boot.

Not a knob: the ISO's label. `live-boot` finds the medium by it.

## The record

Every build writes `customisations.toml` beside the root:

```toml
# What this spec added beyond the release. Written by peiso.

[[file]]
src  = "/home/me/site/overlay/motd"
dest = "usr/etc/motd"
sddl = "O:SYG:SYD:(A;;GA;;;SY)(A;;FR;;;WD)"

[[autorun]]
src  = "/home/me/site/scripts/setup.sh"
name = "50-setup"

[[feature]]
name  = "dynamic-boot"
state = "enable"
```

Together with `compose.lock.toml` (every package that was resolved) it is the complete answer to "what is in this image that is not in the release".
