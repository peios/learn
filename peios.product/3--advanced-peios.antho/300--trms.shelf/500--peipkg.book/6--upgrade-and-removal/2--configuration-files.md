---
title: Configuration Files
description: Configuration under /usr/etc is seed configuration, not effective configuration — modified detection, what is recorded, and why.
---

A package's configuration under `/usr/etc/` is *seed* configuration: the
package's defaults, not the running system's effective configuration.

## Modified detection

When an upgrade would replace a configuration file, peipkg compares the
file's current on-disk content hash against the hash recorded for it at
install.

- **Unmodified** — the content matches what was recorded. The file is
  replaced like any other.
- **Modified** — the content differs. The operator's file is left in
  place, the new version's default is written beside it as
  `<name>.peipkg-new`, and the divergence is surfaced in the operation
  report.

The check applies to paths under `/usr/etc/`, and also to paths under a
bare `/etc/` — the latter only so that packages installed before the
layout moved to `/usr/etc/` keep their protection. It does not permit
installing to `/etc/`, which is a merged view rather than storage.

## What is recorded

On the modified branch, the file peipkg writes is the `.peipkg-new`
sibling, but the ownership row it records names the original path and
carries the *new* version's hash.

Two things follow. `peipkg verify` compares the recorded hash against
what is on disk, so it reports that file as modified on every run,
permanently, for a file peipkg itself deliberately preserved. And the
`.peipkg-new` sibling is recorded nowhere, so it is owned by no package,
is not removed by an uninstall, and is not attributed by `peipkg owns`.

## Interaction with the missing untouched category

Because §6.1's untouched category is not computed, a configuration file
whose content is *identical between the two package versions* is
classified as replaced. Modified detection then fires on the operator's
edit, writes a `.peipkg-new` carrying exactly the content the package
already shipped, and warns about a divergence from a version that
changed nothing.

## Where this is going

The intended end state is the one the filesystem layout describes:
runtime configuration is materialised by reconciller daemons from
registry state, operators do not edit configuration by hand, and an
upgrade replaces seed configuration unconditionally. Modified detection
is what prevents an upgrade destroying a hand-edited file until that
framework exists.

The two models converge rather than compete: once reconcillers claim a
set of paths, modified detection applies only to the unclaimed
remainder, and reconciller-managed seed files are replaced outright.
