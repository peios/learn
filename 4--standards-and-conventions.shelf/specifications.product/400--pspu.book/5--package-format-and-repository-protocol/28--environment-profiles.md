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
```

## Keys

| Key | Holds |
|---|---|
| `arch` | The architecture of its packages, the consumer's own by default |
| `include` | Profiles whose contents it holds too, relative to its directory |
| `packages` | Each package asked for, with the versions that will do |
| `symlinks` | Links a composed root holds, each path with its target |
| `dirs` | Empty directories a composed root holds |
| `include_artifacts` | `true` to give a composed root its packages in an artifact directory of its own |

Every key is OPTIONAL, and a consumer MUST refuse any other.

A value in `packages` is a constraint (§5.7), or `""` for any version; a
bare version asks for exactly that version. `#` and an index or channel,
optionally followed by a constraint, as in `"#stable"` or
`"#stable >= 1.36"`, asks for what that index holds (§5.29).

A link's target is written as given, unless it starts with `:`, which
stands for `usr`: `":sbin/prelude"` is `usr/sbin/prelude`, relative to the
root.

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
- a file that includes itself, directly or not.

A file included twice by different routes changes nothing the second time.
