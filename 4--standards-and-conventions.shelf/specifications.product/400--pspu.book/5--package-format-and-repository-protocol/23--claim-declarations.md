---
title: Claim Declarations
description: Links a package provides besides its files, under /usr or outside it, and why only one package in an environment can claim a path.
---

A **claim** is a link that a package provides besides its files, at an
absolute path, with its target:

```toml
[claims]
"/init" = "usr/sbin/prelude"
"/usr/bin/sh" = "dash"
```

A claim says which package provides a name that several packages could:
the shell at `/usr/bin/sh`, or the initramfs's `/init`. Composing creates
the link.

## Rules

A claim's path MUST be absolute and normal, with no empty, `.` or `..`
component and no trailing `/`. Its target MUST NOT be empty. Neither MAY
hold a NUL byte.

A claim under `/usr` is a symbolic link in the closure. A claim elsewhere is
made only when a closure is composed into a root, since a closure is only a
`/usr` (§5.24).

## One claimant

When packages are composed together, a consumer MUST refuse:

- two packages claiming one path, even with one target, since a claim says
  who provides a name;
- a claim at a path one of the packages holds, or beneath one of its files,
  links or claims;
- a claim of `/usr` itself, or of `/usr/inventory` or beneath it (§5.13).
