---
title: Environment Profiles
description: A TOML file of the packages an environment asks for and what its root holds outside /usr, fragments it includes, and why it holds requests rather than their answer.
---

An **environment profile** describes an environment: the packages it asks
for, and what a root composed for it holds outside `/usr`.

```toml
arch = "x86_64"
include = ["layout.toml"]
dirs = ["proc", "sys", "tmp"]

[packages]
"net.busybox.busybox" = "1.37.0-1"
"dev.peios.prelude" = ">= 0.0.7"
"se.curl.curl" = "#stable"

[symlinks]
"init" = ":sbin/prelude"

[files]
"system/pso/store" = "/system/pso/store"
```

## Keys

| Key | Holds |
|---|---|
| `arch` | The architecture of its packages, the consumer's own by default |
| `include` | Profiles whose contents it holds too, relative to its directory |
| `packages` | Each package asked for, with the versions that will do |
| `symlinks` | Links a composed root holds, each path with its target |
| `dirs` | Empty directories a composed root holds |
| `files` | Files a composed root holds that no package ships, each path with its source |
| `include_artifacts` | `true` to give a composed root its packages in an artifact directory of its own |

Every key is OPTIONAL, and a consumer MUST refuse any other.

A value in `packages` is a constraint (§5.7), or `""` for any version; a
bare version asks for exactly that version. `#` and an index or channel,
optionally followed by a constraint, as in `"#stable"` or
`"#stable >= 1.36"`, asks for what that index holds (§5.29).

A link's target is written as given, unless it starts with `:`, which
stands for `usr`: `":sbin/prelude"` is `usr/sbin/prelude`, relative to the
root.

## Files from the machine

A profile's `files` gives a composed root files that belong to the
machine and not to any package, such as state a boot image has to carry.
Each key is a path in the composed root, relative to it, and each value
is the absolute path of the source.

A source is resolved against the root of the system the profile is
composed for, which is not always the system the consumer runs on. A
consumer MUST copy the source's content as it is when the root is
composed, and MUST refuse:

- a source that is absent, or is anything but a regular file;
- a path that is `usr` or beneath it, since `/usr` is the closure's;
- a path that is not relative and normal, with no empty, `.` or `..`
  component.

A file a profile names is not part of the closure and does not change
its identity (§5.24). Composing the same profile on two machines gives
the same closure and, where the sources differ, different roots.

> [!NOTE]
> A missing source is refused, not skipped. A root composed without a
> file its profile asked for is a boot image that starts and then fails
> for want of it, which is worse than no image.

## Requests, not answers

A profile holds requests. Composing it resolves them, with what they need
(§5.29), and the closure's inventory records what was chosen (§5.25). The
inventory is the exact answer; the profile is what was asked. A profile that
asks for exact versions of everything always composes the same environment.

## Fragments

A profile's `include` names other profiles, which it holds as well. Each
file's `arch` is for its own packages. A consumer MUST refuse:

- two files asking for one package differently;
- packages for two architectures;
- two links at one path with different targets, or a link where another
  file makes a directory;
- two files at one path with different sources, or a file at a path
  where a link or a directory is made;
- a file that includes itself, directly or not.

A file included twice by different routes changes nothing the second time.
