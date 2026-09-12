---
title: Modified Files
description: A file whose content no longer matches the hash recorded at install — where the check runs, and what checking costs.
---

A file whose on-disk content no longer matches the hash recorded at
install has been modified since installation — by a person, by a
program, or by corruption.

## Where the check runs

peipkg compares recorded hashes against disk in three places.

`peipkg verify` does it on demand, across every recorded file, and
reports what differs.

An upgrade does it for configuration files, to decide whether to
preserve an operator's edit (§6.2).

An uninstall does it for configuration files too, and puts each
modified one to the operator before the removal is prepared: remove it
with the previous content kept as a backup, keep it as an unowned file,
or abort (§6.6).

> [!NOTE]
> A modified file at removal time is either a customisation that removal
> destroys, or an unauthorised modification of a system file. Surfacing
> it is what lets the operator tell which, and the choice is theirs.

## The cost of checking

Hashing every installed file at uninstall is expensive: a large package
on slow storage takes seconds. The check is therefore restricted to the
paths where customisation is expected — the configuration scope the
upgrade already uses, `/usr/etc/` and the legacy `/etc/` — and skipped
for binaries, libraries and data. A hand-patched binary is removed
without a question; `peipkg verify` is the tool for finding one.
